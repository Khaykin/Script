#!/usr/bin/python

# from adb_handler import AdbDevice
from __future__ import print_function
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
from subprocess import check_call
from os.path import dirname, join, realpath

import PDU_Control


#pdu_factory = PduOutletFactory()
#disable_pdu = pdu_factory
#pdu_outlet = pdu_factory.get_outlet('TA_OUTLET_MSM8974')
#control_pdu = pdu_factory.get_outlet('TA_OUTLET_MSM8974')

CURRENT_DIR =dirname(realpath(__file__))

class Control(object):

    def __init__(self, outlet):
        pdu_factory = PDU_Control.PduOutletFactory()
        self.outlet = pdu_factory.get_outlet(outlet)


    def do_off(self):
        self.outlet.set_off()


    def do_on(self):
        self.outlet.set_on()



def get_parser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='This script perform power management of DUT -',
        epilog='Choose required options',
        prog='Power management of DUT')

    parser.add_argument(
        '--self-test',
        action='store_true',
        help='Perform internal health-check'
    )

    parser.add_argument(
        '-s',
        '--show-all',
        action='store_true',
        help='Show all PDU. '
    )

    parser.add_argument(
        '-e',
        '--enable-pdu',
        action='append',
        choices=PDU_Control.TA_OUTLET_CONFIG.keys(),
        help='Enable Pdu.'
    )

    parser.add_argument(
        '-d',
        '--disable-pdu',
        action='append',
        choices=PDU_Control.TA_OUTLET_CONFIG.keys(),
        help='Disable Pdu',
    )

    parser.add_argument(
        '-p',
        '--enable-usb',
        action='store_true',
        help='Enable usb port',
    )

    parser.add_argument(
        '-o',
        '--disable-usb',
        action='store_true',
        help='Disable usb port',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.self_test:
        PDU_Control.healthcheck()
    elif args.disable_pdu:
        for outlet in args.disable_pdu:
            c = Control(outlet)
            c.do_off()
    elif args.enable_pdu:
        for outlet in args.enable_pdu:
            c = Control(outlet)
            c.do_on()
    else:
        print('For help use -h or --help')
   # print args.disable_pdu
   #print args.enable_pdu




if __name__ == '__main__':
    main()