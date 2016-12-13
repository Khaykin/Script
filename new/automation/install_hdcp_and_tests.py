#!/usr/bin/python

import logging
import threading
import subprocess
import os
import shutil
import sys
import time
from ConfigParser import RawConfigParser
from argparse import ArgumentParser, RawDescriptionHelpFormatter
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

sys.path.append(path.abspath(ROOT_DIR))
bits_array = ["32bit", "64bit"]


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
        if self.settings.bits == "both":
            self.bits_array = bits_array
        else :
            self.bits_array = ["%s"%self.settings.bits]

    def install(self):
        logger.info("Installing Qualcomm...")
        device = self.settings.device

        if device.check_conection(self.settings.sn) == False:
            raise Exception("Device not connect. please check!!!")
        self.adb_put_tz = ['-a', self.settings.adb_path.replace('/adb', '')] if self.settings.adb_path != "adb" else []

        device.disable_usb_tethering()
        device.root_and_remount()

        device_bits = device.adb_command_and_get_output(
            'shell "if [ -d /system/lib64 ]; then echo 64bit; else echo 32bit; fi;"').strip()
        logger.info("Detected {} platform".format(device_bits))

        # remove /data/tmp before install
        device.adb_command('shell "if [ -d /data/tmp ]; then rm -r /data/tmp; fi"')

        for bits in self.bits_array:
            if bits == "32bit":
                logger.info("Installing 32 bit binaries")
                self.install_product("32bit")
                self.install_tests("32bit")
            if (bits == "64bit") & (device_bits == "64bit"):
                logger.info("Installing 64 bit binaries")
                self.install_product("64bit")
                self.install_tests("64bit")

        self.push_gtests(device)

        device.enable_usb_tethering()
        logger.info("Installing Qualcomm - DONE")

    def install_tests(self, bits):
        logger.info("Installing tests on Qualcomm %s ..." % bits)

        build = self.settings.build

        push_test_files(self.settings, bits, ROOT_DIR)

        if self.settings.scp_support == 'yes':

            # push QA TZ
            put_tz_script_path = join(ROOT_DIR, 'TZInfra', 'Platforms', 'Qualcomm', 'put_tz.sh')

            logger.info("Push Trustzone for internal tests")
            tz_app_dir = join(
                ROOT_DIR,
                'INT_QA_TST.%s.%s' % (build, bits)
            )

            tz_app_name = 'IQATZ'
            cmd = [put_tz_script_path, '-d', tz_app_dir, '-t', tz_app_name] + self.adb_put_tz
            if self.settings.sn:
                cmd += ['-s', self.settings.sn]
            check_call(cmd)

            logger.info("SCP Supoort is yes : Push Trustzone for external tests")
            tz_app_dir = join(
                ROOT_DIR,
                'QA_TST.%s.%s' % (build, bits),
                'TZBuildScripts',
                'out'
            )
            tz_app_name = 'QATZ'
            cmd = [put_tz_script_path, '-d', tz_app_dir, '-t', tz_app_name] + self.adb_put_tz
            if self.settings.sn:
                cmd += ['-s', self.settings.sn]
            check_call(cmd)

        logger.info("Install tests on Qualcomm %s - DONE" % bits)

    def push_gtests(self , device):
        # push google tests

        device.delete_dir('/data/tmp/HdcpGTests')
        ptesting = join(ROOT_DIR, 'HDCP', 'obj', 'local', 'armeabi', 'HdcpGTests')
        device.adb_command('push ' + ptesting + ' /data/tmp/')

        # push executabler and tests config file
        ptesting = join(ROOT_DIR, 'Testing', 'WorkSpace', 'config', 'Android', 'HdcpGTests.cfg')
        device.push_to_device(ptesting ,'/data/tmp/')

    def install_product(self, bits):
        logger.info("Installing HDCP on Qualcomm...")

        device = self.settings.device
        ref_name = self.settings.ref_name
        b_build = self.settings.build.title()
        platform_model = self.settings.platform_model
        plat_ver = self.settings.plat_ver

        put_tz_script_path = join(ROOT_DIR, 'TZInfra', 'Platforms', 'Qualcomm', 'put_tz.sh')
        tz_app_dir = join(
            HDCP_DIR,
            ref_name,
            b_build,
            'tz_test',
            "%s-%s" % (platform_model, plat_ver)
        )
        tz_app_name = 'dxhdcp2'
        hlos_so_name = 'libDxHdcp.so'

        logger.info("Push TZ to device")
        cmd = [put_tz_script_path, '-d', tz_app_dir, '-t', tz_app_name, '-r'] + self.adb_put_tz
        if self.settings.sn:
            cmd += ['-s', self.settings.sn]
        check_call(cmd)

        logger.info("Push HLOS to device")
        so_path = join(HDCP_DIR, ref_name, b_build, 'hlos', bits, hlos_so_name)
        if bits == "32bit":
            dirname='/system/vendor/lib/{}'.format(hlos_so_name)
            device.delete_dir(dirname)
            device.push_to_device(so_path, 'system/lib')
        else:  # 64bit
            dirname='/system/vendor/lib64/{}'.format(hlos_so_name)
            device.delete_dir(dirname)
            device.push_to_device(so_path, '/system/lib64')

        cfg_path = join(ROOT_DIR, 'Testing', 'WorkSpace', 'config', 'Android', 'DxHDCP.cfg')
        # cfg_path = join(HDCP_DIR, 'DxHDCP', 'DxHDCP_Core', 'inc', 'DxHDCP.cfg')
        device.push_to_device(cfg_path, '/system/etc/DxHDCP.cfg')

        device.delete_dir('/data/tmp/Testing/')
        ptesting = join(ROOT_DIR, 'Testing', 'WorkSpace')
        device.push_to_device(ptesting, '/data/tmp/Testing/')

        logger.info("Install on Qualcomm - DONE")

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
            help='default: MSM8996_LA2.0 '
        )

        qualcomm_parser.add_argument(
            '-v',
            '--plat_ver',
            default='01450.1',
            help='default: 01450.1 '
        )

        qualcomm_parser.add_argument(
            '-c',
            '--scp_support',
            default='yes',
            choices=['yes', 'no'],
            help="use secure content path. "
                 "default:yes"
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

    def install(self):
        logger.info("Installing SW_Linux32...")

        target_dir = join(SCRIPTS_DIR, "Linux32_SW_hdcp_devices")
        shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(join(HDCP_DIR, "Linux32_SW_hdcp_devices"), target_dir)

        logger.info("Install SW_Linux32 to %s - DONE" % (target_dir))


def get_parser():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
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
             'default: release'
    )

    parser.add_argument(
        '--bits',
        default='both',
        choices=['32bit', '64bit', 'both'],
        help='choices=[32bit, 64bit,both]. '
             'default:32bit'
    )

    return parser



def push_test_files(settings, bits, qa_tst_parent):
    build = settings.build
    device = settings.device

    logger.info("Push external and internal tests to device - data and config files")

    check_call(
        ['./PushFilesToBoard.sh', device.adb_cmd],
        cwd=join(qa_tst_parent, 'QA_TST.%s.%s' % (build, bits), 'Scripts')
    )

    logger.info("Push external and internal tests to device - executables")
    check_call(
        ['./PushFilesToBoard.sh', device.adb_cmd],
        cwd=join(qa_tst_parent, 'INT_QA_TST.%s.%s' % (build, bits))
    )


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
    builder.install()

    duration_time = time.time() - start_time

    logger.info("*********** duration: {} seconds ***********".format(duration_time))


if __name__ == '__main__':
    main()
