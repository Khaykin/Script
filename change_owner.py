#!/usr/bin/python


from adb_handler import AdbDevice
myadb = AdbDevice()


def change_owner(my_file):
    bits = myadb.adb_command_and_get_output('shell ls -l ' + my_file)
    bits_list = bits.split()
    myadb.adb_command('shell chown {group}:{owner} {file}'.format(group=bits_list[1], owner=bits_list[2], file=my_file))


def main():
    my_file = '/system/etc/wifi/WCNSS_qcom_cfg.ini'
    change_owner(my_file)


if __name__ == '__main__':
    main()