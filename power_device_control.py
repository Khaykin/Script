#!/usr/bin/python

# from adb_handler import AdbDevice
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
from subprocess import check_call
from os.path import dirname, join, realpath

from PDU_Control import  PduOutletFactory
import PDU_Control

pdu_factory = PduOutletFactory()
pdu_outlet = pdu_factory.get_outlet('TA_OUTLET_MSM8974')
control_pdu = pdu_factory.get_outlet('TA_OUTLET_MSM8974')

CURRENT_DIR =dirname(realpath(__file__))

class Control(object):
    def __init__(self, settings):
        self.control_pdu = None
        self.settings = settings
        self.control_pdu.set_on = settings.PDU_Control
        self.control_pdu.set_off = settings.PDU_Control
        self.control_pdu.pdu_outlet.set_on(False)
        self.control_pdu.pdu_outlet.set_on(True)



    def do_oof(self):
        self.control_pdu.set_off(True)
        check_call('python PDU_Control.py', cwd=CURRENT_DIR, shell=True)






def get_parser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='This script perform power management of DUT -',
        epilog='Choose required options',
        prog='Power management of DUT')

    parser.add_argument(
        '--self-test',
        action='store_true',
        default='False',
        help='Enabling unitest. '
    )

    parser.add_argument(
        '-s',
        '--show-all',
        required=False,
        help='Show all PDU. '
    )

    parser.add_argument(
        '-e',
        '--enable-pdu',
        default='False',
        help='Enable power PduOutlet. '
    )

    parser.add_argument(
        '-d',
        '--disable-pdu',
        action='store_true',
        default='False',
        help='Disable Pdu',
    )

    parser.add_argument(
        '-p',
        '--enable-usb',
        action='store_true',
        default='False',
        help='Enable usb port',
    )

    parser.add_argument(
        '-o',
        '--disable-usb',
        action='store_true',
        default='False',
        help='Disable usb port',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    print args.disable-pdu

    controller = Control(args)
    controller.do_oof()


if __name__ == '__main__':
    main()