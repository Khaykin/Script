
#!/usr/bin/python
import logging
import re
import sys
import time
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from os.path import dirname, join, realpath
from subprocess import check_call
from adb_handler import AdbDevice
import shutil
from os import listdir, remove, makedirs, path, walk
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


logger = logging.getLogger('HDCP Builder')


SCRIPTS_DIR = dirname(realpath(__file__))
ROOT_DIR = realpath(join(SCRIPTS_DIR, '..'))
HDCP_DIR = join(ROOT_DIR, 'HDCP')



class BB_tests(object):
    def __init__(self, settings):
        self.settings = settings
        self.platform=settings.platform
        self.sink_version=settings.sink_version
        self.source_version=settings.source_version
        self.all_permutations=settings.all_permutations
        self.device = AdbDevice(adb_path=settings.adb_path, device=settings.device)
        self.sn=settings.device
        self.skip_linux_build_install=settings.skip_linux_build_install
        self.ARTIFACTS_DIR = join(ROOT_DIR, "BB_Tests_Artifatcts")


    def run_bb_tests(self):
        if self.all_permutations is not True:
            self.run_bb_version(self.source_version,self.sink_version)
        else:
            # 2.2 2.2
            self.run_bb_version('2.2', '2.2')
            # 2.2 2.0
            self.run_bb_version('2.2', '2.0')
            # 2.1 2.2
            self.run_bb_version('2.1', '2.2')
            # 2.0 2.2
            self.run_bb_version('2.0', '2.2')
            # 2.2 2.1
            self.run_bb_version('2.2', '2.1')


    def run_bb_version(self,sink_version,source_version):
        logger.info("Run BB tests")
        logger.info("platform = %s"%self.platform)
        logger.info("sink version = %s, source_version= %s"%(sink_version, source_version))
        if self.platform == "linux_linux":
            # update version in config file
            self.update_config(sink_version, "/tmp/hdcp/Dx_Rcv_HDCP.cfg")
            self.update_config(source_version, "/tmp/hdcp/Dx_Tsmt_HDCP.cfg")
            # run tests
            check_call('./run_all_permutations_linux_linux.sh %s %s' % (source_version, sink_version), cwd=SCRIPTS_DIR, shell=True)
        else:
            # run linux vs QC
            if self.device.check_conection(self.sn) == False:
                raise Exception("Device not connect. please check!!!")
            # build and install hdcp in linux
            if self.skip_linux_build_install is not True:
                check_call('python build_hdcp_and_tests.py SW_Linux32', cwd=SCRIPTS_DIR, shell=True)
                check_call('python install_hdcp_and_tests.py SW_Linux32', cwd=SCRIPTS_DIR, shell=True)
            # update version in config file and push to device
            if self.platform == "qualcomm_linux":
                self.update_config(source_version,join(SCRIPTS_DIR,"..","Testing","WorkSpace","config","Android","DxHDCP.cfg"))
                self.update_config(sink_version, "/tmp/hdcp/Dx_Rcv_HDCP.cfg")
            else:
                self.update_config(sink_version,join(SCRIPTS_DIR,"..","Testing","WorkSpace","config","Android","DxHDCP.cfg"))
                self.update_config(source_version, "/tmp/hdcp/Dx_Tsmt_HDCP.cfg")
            self.device.push_to_device(join(SCRIPTS_DIR, "..","Testing","WorkSpace","config","Android","DxHDCP.cfg"),'system/etc')
            # run tests
            check_call('./run_all_permutations_linux_qualcomm.sh %s %s %s'%(self.platform, source_version, sink_version), cwd=SCRIPTS_DIR, shell=True)


    def update_config(self, version, configname):
        logger.info("update_config")
        if version=="2.2":
            update="3"
        elif version=="2.1":
            update="2"
        elif version == "2.0":
            update = "1"

        with open(configname, 'r+t') as fh:
            config = fh.read()
            logger.debug(config)
            fh.seek(0)
            config = re.sub(r'^DxHdcpVer\s*=\s*\S+', 'DxHdcpVer=' + update, config, flags=re.MULTILINE)
            fh.write(config)
            fh.truncate()

    def set_version(self,configname):
        cfg = RawConfigParser()
        cfg.read(configname)
        return cfg.set()
        with open(configname) as configfile:
            cfg.write(configfile)


    def collect_artifacts(self):
        logger.info("Collecting tests artifacts...")

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



def get_parser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description="This script run BB tests - "
    )

    parser.add_argument(
        '-s',
        '--sink_version',
        choices=['2.2', '2.1', '2.0'],
        help='HDCP protocol version to run on Sink. '
    )

    parser.add_argument(
        '-t',
        '--source_version',
        choices=['2.2', '2.1', '2.0'],
        help='HDCP protocol version to run on Source. '
    )

    parser.add_argument(
        '-p',
        '--platform',
        choices=['qualcomm_linux', 'linux_qualcomm', 'linux_linux'],
        required=True,
        help='choose which platform to run. '
    )

    parser.add_argument(
        '--all_permutations',
        action='store_true',
        default='False',
        help="run_all_permutations. "
    )

    parser.add_argument(
        '-n',
        '--skip_linux_build_install',
        action='store_true',
        default='False',
        help="skip build hdcp and install on linux will runing bb tests linux vs qualcomm. "
    )

    parser.add_argument(
        '-v',
        action='store_true',
        dest='verbosity',
        help="run in verbose mode"
    )
    parser.add_argument(
        '--adb_path',
        default='adb',
        help='Path to adb.'
    )

    parser.add_argument(
        '--device',
        help='Device id from adb devices. if omitted adb will pick default device.'
             'mandatory in case more than 1 device is connected.'
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if not args.verbosity else logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        stream=sys.stdout
    )

    start_time = time.time()

    builder = BB_tests(args)
    builder.run_bb_tests()

    duration_time = time.time() - start_time

    logger.info("*********** duration: {} seconds ***********".format(duration_time))


if __name__ == '__main__':
    main()
