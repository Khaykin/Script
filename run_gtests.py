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

GTESTS_EXE_DIR = join(ROOT_DIR, "HDCP/Linux32_SW_hdcp_devices/GTest")
GTESTS = './HdcpGTests'


class HdcpBuilderFactory(object):
    @staticmethod
    def getHdcpBuilder(args):
        if args.platform_vendor == 'SW_Linux32':
            return SWLinux32(args)
        elif args.platform_vendor == 'Qualcomm':
            return Qualcomm(args)
        else:
            raise Exception("Not supported platform option - " + args.platform_vendor)


class Qualcomm(object):
    def __init__(self, settings):
        self.settings = settings
        self.device = AdbDevice(adb_path=settings.adb_path, device=settings.device)
        self.sn=settings.device
    def run_gtests(self):
        logger.info("Run Gtests on Qualcomm ")
        if self.device.check_conection(self.sn) == False:
            raise Exception("Device not connect. please check!!!")
        gtests = GTESTS
        if self.settings.g_tests_filter:
            gtests += ' --gtest_filter=%s' % self.settings.g_tests_filter

        self.device.adb_command_notimeout('shell "cd /data/tmp && %s"' % gtests)

    @staticmethod
    def register_subparser(subparsers):

        qualcomm_parser = subparsers.add_parser(
            'Qualcomm',
            help='Platform vendor = Qualcomm'
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

    def run_gtests(self):
        logger.info("Run Gtests on Linux ")

        gtests = GTESTS
        if self.settings.g_tests_filter:
            gtests += ' --gtest_filter=' + self.settings.g_tests_filter

        my_env = os.environ.copy()
        my_env['LD_LIBRARY_PATH'] = GTESTS_EXE_DIR

        check_call(gtests, cwd=GTESTS_EXE_DIR, env=my_env, shell=True)


def get_parser():
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description="This script run gtests "
		"--g_tests_filter should be define before choosing platform"
    )

    subparsers = parser.add_subparsers(dest='platform_vendor', help='Platforms')

    linux_parser = subparsers.add_parser(
        'SW_Linux32',
        help='Platform vendor = SW_Linux32'
    )

    Qualcomm.register_subparser(subparsers)

    parser.add_argument(
        '-f',
        '--g_tests_filter',
        help="Google tests filter. Rellevant only if --skip_g_tests was not specified."
             "default:None"
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        stream=sys.stdout
    )

    start_time = time.time()

    platform = HdcpBuilderFactory.getHdcpBuilder(args)

    platform.run_gtests()

    duration_time = time.time() - start_time

    logger.info("*********** duration: {} seconds ***********".format(duration_time))


if __name__ == '__main__':
    main()
