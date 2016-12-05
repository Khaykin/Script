#!/usr/bin/python

# from adb_handler import AdbDevice
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter


def get_parser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='This script perform power management of DUT -',
        epilog='Choose required options',
        prog='Power management of DUT')

    parser.add_argument(

        '-u',
        '--unitest',
        choices=['Run self test'],
        help='Enabling unitest. '
    )

    parser.add_argument(
        '-a',
        '--all',
        required=False,
        help='Show all PDU. '
    )

    parser.add_argument(
        '-e',
        '--enable PDU',
        default='False',
        help='Enable_power_control. '
    )

    parser.add_argument(
        '-d',
        '--desable PDU',
        action='store_true',
        default='False',
        help='Disable power control',
    )

    parser.add_argument(
        '-p',
        '--enable usb',
        action='store_true',
        default='False',
        help='Enable usb control',
    )

    parser.add_argument(
        '-o',
        '--desable usb',
        action='store_true',
        default='False',
        help='Disable usb control',
    )

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()


if __name__ == '__main__':
    main()
