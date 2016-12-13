
#!/usr/bin/python
import logging
import threading
import subprocess
import os
import shutil
import sys
import time
from ConfigParser import RawConfigParser
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os import listdir, remove, makedirs, path, walk
from os.path import dirname, isfile, join, realpath
from subprocess import check_call, CalledProcessError
from zipfile import ZipFile
from hdcp_build_utils import Convert_To_yes_no
from adb_handler import AdbDevice

logger = logging.getLogger('HDCP Builder')


SCRIPTS_DIR = dirname(realpath(__file__))
ROOT_DIR = realpath(join(SCRIPTS_DIR, '..'))
HDCP_DIR = join(ROOT_DIR, 'HDCP')
GTESTS_DIR = join(ROOT_DIR, 'Testing', 'WorkSpace')

CUSTOMER_EXTERNAL_ZIP_FILENAME = "DxHDCP.zip"
CUSTOMER_EXTERNAL_ZIP_TARGET_DIR = "DxHDCP"

LINUX_BUILD_DIR = join(ROOT_DIR, '__build')
GTESTS_EXE_DIR = join(ROOT_DIR, "HDCP/Linux32_SW_hdcp_devices/GTest")
HDCP_TESTS_SO = ["libDxHdcp_SW.so", "libsrv_dxhdcp2.so", "libDxExternal_SW.so", "HdcpGTests", "libsrv_TestTZ.so"]
sys.path.append(path.abspath(ROOT_DIR))
bits_array = ["32bit", "64bit"]
build_array = ["debug", "release"]


class BuildSettingsQC(object):
    def __init__(self, args):
        self.platform_vendor = 'Qualcomm'
        self.device = AdbDevice(adb_path=args.adb_path, device=args.device)
        self.sn = args.device
        self.adb_path = args.adb_path
        self.build = args.build
        self.bits = args.bits
        self.platform_model = args.platform_model
        self.plat_ver = args.plat_ver
        self.scp_support = args.scp_support
        self.sub_plat = self.get_subplat()
        self.ref_name = "reference.%s.%s" % (self.platform_model, self.plat_ver)
        logger.info("sub_plat = {}".format(self.sub_plat))
        logger.info("ref_name = {}".format(self.ref_name))

    def get_subplat(self):
        config_path = join(ROOT_DIR, "TZInfra", "Platforms", "Qualcomm", "postbuild", "config.ini")
        cfg = RawConfigParser()
        cfg.read(config_path)
        return cfg.get(self.platform_model, 'subplat')


class BuildSettingsLinux(object):
    def __init__(self, args):
        self.platform_vendor = 'SW_Linux32'
        self.build = args.build
        self.bits = args.bits


class HdcpBuilderFactory(object):
    @staticmethod
    def getHdcpBuilder(args):
        if args.platform_vendor == 'SW_Linux32':
            settings = BuildSettingsLinux(args)
            return SWLinux32(settings)
        elif args.platform_vendor == 'Qualcomm':
            settings = BuildSettingsQC(args)
            return Qualcomm(settings)
        else:
            raise Exception("Not supported platform option - " + args.platform_vendor)


class Qualcomm(object):
    def __init__(self, settings):
        self.settings = settings
        self.ARTIFACTS_DIR = join(ROOT_DIR, "Artifacts_"+self.settings.platform_vendor+"_"+self.settings.platform_model+"_"+self.settings.plat_ver)
        if self.settings.bits == "both":
            self.bits_array = bits_array
        else :
            self.bits_array = ["%s"%self.settings.bits]

    def collect_artifacts(self):
        logger.info("Collecting Qualcomm HDCP and tests artifacts...")

        delete_old_and_collect_new_artifacts(self.settings.build,self.bits_array, self.ARTIFACTS_DIR)
        shutil.copy2(join(HDCP_DIR, "%s.zip" % self.settings.ref_name), self.ARTIFACTS_DIR)

        logger.info("Collect Qualcomm HDCP and tests artifacts - DONE")

    def build(self):
        logger.info("Building HDCP Product- Qualcomm...")

        start_time = time.time()

        ref_name = self.settings.ref_name

        # remove old build products
        remove_old_build_products()

        remove_old_test_build_products()

        # for qualcomm also remove ref_name package
        shutil.rmtree(join(HDCP_DIR, ref_name), ignore_errors=True)

        build_cmd = [
            './buildHdcp.sh',
            '-s', self.settings.sub_plat,
            '-c', self.settings.scp_support,
            '-f', CUSTOMER_EXTERNAL_ZIP_FILENAME
        ]

        logger.info("Build of product")
        logger.info(build_cmd)

        my_env = os.environ.copy()
        my_env['TEST_TZ_UUID'] = "ffffffff000000000000000000000017"
        check_call(build_cmd, cwd=HDCP_DIR, env=my_env)

        postbuild_cmd = [
            './postbuildHdcp.sh',
            '-m', self.settings.platform_model,
            '-v', self.settings.plat_ver
        ]

        logger.info("Postbuild of product")
        logger.info(' '.join(postbuild_cmd))

        check_call(postbuild_cmd, cwd=HDCP_DIR)

        self.extract_build_output_zip()
        # for qualcomm also extract refname zipped file
        with ZipFile(join(HDCP_DIR, "{}.zip".format(ref_name)), 'r') as z:
            z.extractall(join(HDCP_DIR, ref_name))

        logger.info("Build HDCP Product- Qualcomm - DONE.")

        duration_time = time.time() - start_time
        logger.info("Build duration: {} seconds".format(duration_time))

        self.build_test_tz_app(self.settings.platform_model, self.settings.plat_ver)

        for bits in self.bits_array:
            logger.info("Building Qualcomm internal and external tests %s ..." % bits)
            start_time = time.time()

            build = self.settings.build
            scp_support = self.settings.scp_support
            sub_plat = self.settings.sub_plat
            platform_model = self.settings.platform_model
            plat_ver = self.settings.plat_ver

            check_call(
                ['./build_test_qc_plat.sh',
                 'BUILD_VARIANT={}'.format(build),
                 'TARGET_PLATFORM_TYPE={}'.format(bits),
                 'SCP_SUPPORT={}'.format(scp_support),
                 'SUBPLAT_NAME={}'.format(sub_plat),
                 'PLAT={}'.format(platform_model),
                 'PLAT_VER={}'.format(plat_ver)],
                cwd=ROOT_DIR
            )

            check_call(
                ['./Compile.sh'],
                cwd=join(ROOT_DIR, 'QA_TST.%s.%s' % (build, bits), 'Scripts')
            )

            logger.info("Build Qualcomm internal and external tests %s - DONE." % bits)
            duration_time = time.time() - start_time
            logger.info("Build duration: %d seconds" % duration_time)

    @staticmethod
    def extract_build_output_zip():
        logger.info("Extract build output zip files")
        with ZipFile(join(HDCP_DIR, CUSTOMER_EXTERNAL_ZIP_FILENAME), 'r') as z:
            z.extractall(join(HDCP_DIR, CUSTOMER_EXTERNAL_ZIP_TARGET_DIR))

        with ZipFile(join(HDCP_DIR, "DxHDCPPackage.zip"), 'r') as z:
            z.extractall(join(HDCP_DIR, 'DxHDCPPackage'))


    @staticmethod
    def build_test_tz_app(platform_model, plat_ver):
        my_env = os.environ.copy()
        my_env['PLAT'] = platform_model
        my_env['PLAT_VER'] = plat_ver
        my_env['MY_BRANCH_PATH'] = ROOT_DIR
        my_env['TEST_TZ_UUID'] = "ffffffff000000000000000000000017"

        ptesting = join(ROOT_DIR, 'Testing', 'Tests', 'TestTZ')
        os.chdir(ptesting)
        check_call('./build_tz.sh', env=my_env)
        check_call('./qc_postbuild_tz.sh', env=my_env)
        src = join(ROOT_DIR, 'TZInfra', 'Platforms', 'Qualcomm', 'put_tz.sh')
        dst = join(ROOT_DIR, 'Testing', 'Tests', 'TestTZ', 'Service', 'workspace', 'postbuild_ws', 'out')
        os.chdir(dst)
        shutil.copy(src, '.')
        check_call('chmod 777 put_tz.sh', shell=True)
        check_call(['./put_tz.sh', '-t', 'TestTZ'], env=my_env)


    @staticmethod
    def register_subparser(subparsers):

        qualcomm_parser = subparsers.add_parser(
            'Qualcomm',
            help='Platform vendor = Qualcomm'
        )

        qualcomm_parser.add_argument(
            '-m',
            '--platform_model',
            default='MSM8996_LA2.0',
            help='platform model '
        )

        qualcomm_parser.add_argument(
            '-v',
            '--plat_ver',
            default='01450.1',
            help='platform ver'
        )

        qualcomm_parser.add_argument(
            '-c',
            '--scp_support',
            default='yes',
            choices=['yes', 'no'],
            help="use secure content path. "
        )

        qualcomm_parser.add_argument(
            '--adb_path',
            default='adb',
            help='Path to adb.'
        )

        qualcomm_parser.add_argument(
            '--device',
            help='Device id from adb devices. if omitted adb will pick default device.'
                 'mandatory in case more than 1 device is connected.'
        )

class SWLinux32(object):
    def __init__(self, settings):
        self.settings = settings
        self.ARTIFACTS_DIR = join(ROOT_DIR, "Artifacts_" + self.settings.platform_vendor)

    def collect_artifacts(self):
        logger.info("Collecting Linux32 HDCP and tests artifacts...")

        shutil.rmtree(self.ARTIFACTS_DIR, ignore_errors=True)
        makedirs(self.ARTIFACTS_DIR)

        # shutil.copytree(join(HDCP_DIR, "Linux32_SW_hdcp_devices"), ARTIFACTS_DIR)

        # create zip file for Linux32
        shutil.make_archive(
            join(self.ARTIFACTS_DIR, 'Linux32_SW_hdcp_devices'),
            'zip',
            join(HDCP_DIR, "Linux32_SW_hdcp_devices")
        )

        logger.info("Collecting Linux32 HDCP and tests artifacts - DONE")

    def build(self):
        logger.info("Building SW_Linux32...")
        build = self.settings.build
        # remove old data
        shutil.rmtree(join(SCRIPTS_DIR, 'Linux32_SW_hdcp_devices'), ignore_errors=True)
        shutil.rmtree(join(HDCP_DIR, 'Linux32_SW_hdcp_devices'), ignore_errors=True)
        check_call(
            'python project_builder.py -p SW_Linux32 config generate'.split(),
            cwd=ROOT_DIR
        )
        check_call(
            ('./buildHdcp.sh -p SW_Linux32 -b %s -f %s' % (build, CUSTOMER_EXTERNAL_ZIP_FILENAME)).split(),
            cwd=HDCP_DIR
        )
        self.gtests_linux()
        logger.info("Build SW_Linux32 - DONE")

    def gtests_linux(self):
        if self.settings.build == 'debug':
            build = "Debug"
        else:
            build = "Release"
        src_dir = "%s-%s_dynamic" % (self.settings.platform_vendor, build)
        gtests_source_dir = join(LINUX_BUILD_DIR, src_dir)
        gtests_target_dir = join(HDCP_DIR, "Linux32_SW_hdcp_devices/GTest/")
        # Copy data
        shutil.rmtree(gtests_target_dir, ignore_errors=True)
        # This will also create parent directory "GTest"
        shutil.copytree(join(GTESTS_DIR, "data"), join(gtests_target_dir, "data"))
        # copy configuration files
        shutil.copytree(join(GTESTS_DIR, "config"), join(gtests_target_dir, "config"))
        # HdcpGTests.cfg
        shutil.copyfile(join(GTESTS_DIR, "config","Linux","HdcpGTests.cfg"), join(gtests_target_dir, "HdcpGTests.cfg"))
        # Copy so and app files:
        for f in HDCP_TESTS_SO:
            shutil.copyfile(join(gtests_source_dir, f), join(gtests_target_dir, f))
        check_call('chmod a+x ' + join(gtests_target_dir, "HdcpGTests"), shell=True)


def get_parser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description="This script build and install HDCP  "
		"--build, --bits,--skip_install, --skip_build should be define before choosing platform"
    )

    subparsers = parser.add_subparsers(dest='platform_vendor', help='Platforms')

    linux_parser = subparsers.add_parser(
        'SW_Linux32',
        help='Platform vendor = SW_Linux32'
    )
    Qualcomm.register_subparser(subparsers)

    parser.add_argument(
        '-b',
        '--build',
        default='release',
        choices=['release', 'debug'],
        help='Build type. '
    )

    parser.add_argument(
        '--bits',
        default='both',
        choices=['32bit', '64bit', 'both'],
        help='choices=[32bit, 64bit,both]. '
    )

    return parser


def remove_all_zip_files_in_dir(directory):
    zip_files = [f for f in listdir(directory) if isfile(join(directory, f)) and f.endswith('.zip')]

    for f in zip_files:
        remove(join(directory, f))


def remove_old_build_products():
    logger.info("Remove old data")
    shutil.rmtree(join(HDCP_DIR, 'DxHDCP'), ignore_errors=True)
    shutil.rmtree(join(HDCP_DIR, 'DxHDCPPackage'), ignore_errors=True)

    # remove all zip files from HDCP_DIR
    remove_all_zip_files_in_dir(HDCP_DIR)


def remove_old_test_build_products():
    logger.info("Remove old test data")
    for bits in bits_array:
        for build in build_array:
            shutil.rmtree(join(ROOT_DIR, "QA_TST.%s.%s" % (build, bits)), ignore_errors=True)
            shutil.rmtree(join(ROOT_DIR, "INT_QA_TST.%s.%s" % (build, bits)), ignore_errors=True)

    # remove all zip files from ROOT_DIR
    remove_all_zip_files_in_dir(ROOT_DIR)


def delete_old_and_collect_new_artifacts(build,bits_array, ARTIFACTS_DIR):
    shutil.rmtree(ARTIFACTS_DIR, ignore_errors=True)
    makedirs(ARTIFACTS_DIR)

    shutil.copy2(join(HDCP_DIR, CUSTOMER_EXTERNAL_ZIP_FILENAME), ARTIFACTS_DIR)
    shutil.copy2(join(HDCP_DIR, "DxHDCPPackage.zip"), ARTIFACTS_DIR)

    for bits in bits_array:
        shutil.copy2(join(ROOT_DIR, "QA_TST.%s.%s.zip" % (build, bits)), ARTIFACTS_DIR)
        shutil.copy2(join(ROOT_DIR, "INT_QA_TST.%s.%s.zip" % (build, bits)), ARTIFACTS_DIR)
    copy_gtests_artifacts(ARTIFACTS_DIR)

def copy_gtests_artifacts(ARTIFACTS_DIR):
    gtestsdir=join(HDCP_DIR, "GTESTS")
    makedirs(gtestsdir)
    ptesting = join(ROOT_DIR, 'HDCP', 'obj', 'local', 'armeabi', 'HdcpGTests')
    shutil.copy2(ptesting, gtestsdir)
    ptesting = join(ROOT_DIR, 'Testing', 'WorkSpace', 'config', 'Android', 'HdcpGTests.cfg')
    shutil.copy2(ptesting, gtestsdir)
    shutil.make_archive(join(gtestsdir),'zip',join(HDCP_DIR, "GTESTS"))
    shutil.rmtree(gtestsdir, ignore_errors=True)


def unzip_all_artifacts(ARTIFACTS_DIR):
    for f in listdir(ARTIFACTS_DIR):
        filename, file_ext = path.splitext(f)
        # logger.info('hadling ' f)
        if file_ext == '.zip':
            unzipped_folder_path = join(ARTIFACTS_DIR, filename)

            shutil.rmtree(unzipped_folder_path, ignore_errors=True)

            with ZipFile(join(ARTIFACTS_DIR, f), 'r') as z:
                z.extractall(unzipped_folder_path)

            # logger.info('walking on on ' + unzipped_folder_path)
            for dirpath, dirs, files in walk(unzipped_folder_path):
                for fname in files:
                    # restore .sh executable rights
                    if path.splitext(fname)[1] == '.sh':
                        sh_script_path = join(dirpath, fname)
                        logger.info('changing permission on ' + sh_script_path)
                        check_call('chmod a+x ' + sh_script_path, shell=True)

                    # restore .sh executable rights
                    if 'QA_HDCP_Transmitter' in path.splitext(fname)[0] or 'QA_HDCP_Sink' in path.splitext(fname)[0]:
                        exec_path = join(dirpath, fname)
                        logger.info('changing permission on ' + exec_path)
                        check_call('chmod a+x ' + exec_path, shell=True)


def main():
    parser = get_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        stream=sys.stdout
    )

    start_time = time.time()

    builder = HdcpBuilderFactory.getHdcpBuilder(args)
    builder.build()
    builder.collect_artifacts()

    duration_time = time.time() - start_time

    logger.info("*********** duration: {} seconds ***********".format(duration_time))


if __name__ == '__main__':
    main()
