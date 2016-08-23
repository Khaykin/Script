#!/usr/bin/python
import re
from adb_handler import AdbDevice


# class ExceptionCounter(Exception):
#     def __init__(self):
#         self.num_exception = 0
#
#     def check_for_exception(self, func):
#         try:
#             self.func()
#         except Exception:
#             self.num_exception += 1


def get_owner(adb, my_file):
    bits = adb.adb_command_and_get_output('shell ls -l ' + my_file)
    bits_list = bits.split()
    return bits_list[0].startswith('l'), bits_list[1], bits_list[2]


def set_owner(adb, my_file, group, owner):
    adb.adb_command('shell chown {group}:{owner} {file}'.format(group=group, owner=owner, file=my_file))


def process_file():

    # Changing network configuration (WCNSS_qcom_cfg.ini)
    with open('WCNSS_qcom_cfg.ini', '+') as fh:
        file_data = fh.read()
        # Replace the target string
        file_data = re.sub(
        pattern=["r'gEnableImps=\d*'", "r'gEnableBmps=\d*'", "r'gDot11Mode=\d*'"],
        repl=["r'gEnableImps=0'", "r'gEnableBmps=0'", "r'gEnableBmps=0'"],
        string=file_data)
        # Write the file out again
        fh.write(file_data)
        print 'WCNSS_qcom_cfg.ini modified: \ngEnableImps=0'
    # Replace the target string
    #file_data = re.sub(
    #    pattern=r'gEnableBmps=\d*',
    #    repl=,
    #    string=file_data)
    # Write the file out again
    #with open('WCNSS_qcom_cfg', 'w') as fh:
    #    fh.write(file_data)
    print 'WCNSS_qcom_cfg modified: \ngEnableBmps=0'
    # Replace the target string
    #file_data = re.sub(
    #    pattern=r'gDot11Mode=\d*',
    #    repl='gDot11Mode=3',
    #    string=file_data)
    # Write the file out again
    #with open('WCNSS_qcom_cfg.ini', 'w') as fh:
    #    fh.write(file_data)
    print 'WCNSS_qcom_cfg modified: \ngDot11Mode=3'


def main():
    # Changing network configuration (WCNSS_qcom_cfg.ini)
    with open('WCNSS_qcom_cfg.ini', 'r') as fh:
        file_data = fh.read()
    # Replace the target string
    file_data = re.sub(
        pattern=r'gEnableImps=\d*',
        repl='gEnableImps=0',
        string=file_data)
    # Replace the target string
    file_data = re.sub(
        pattern=r'gEnableBmps=\d*',
        repl='gEnableBmps=0',
        string=file_data)
    # Replace the target string
    file_data = re.sub(
        pattern=r'gDot11Mode=\d*',
        repl='gDot11Mode=3',
        string=file_data)
    print(file_data)
    with open('WCNSS_qcom_cfg.ini', 'w') as fh:
        fh.write(file_data)




    adb_dev = AdbDevice()
    adb_dev.adb_command('wait-for-device devices')
    adb_dev.adb_command('root')
    adb_dev.adb_command('remount')

    files = [
        "/system/etc/wifi/WCNSS_qcom_cfg.ini",
        "/system/etc/firmware/wlan/qca_cld/WCNSS_qcom_cfg.ini",
        "/data/misc/wifi/WCNSS_qcom_cfg.ini"
    ]

    file_found = False
    for my_file in files:
        try:
            is_link, group, owner = get_owner(adb_dev, my_file)
            if is_link:
                print 'found link - ignoring: ' + my_file
                continue
            adb_dev.adb_command('pull ' + my_file)
            print 'WCNSS_qcom_cfg.ini pulled from ' + my_file
            process_file()
            print 'WCNSS_qcom_cfg.ini modified'
            adb_dev.adb_command('push WCNSS_qcom_cfg.ini ' + my_file)
            adb_dev.adb_command('shell chmod 644 ' + my_file)
            set_owner(adb_dev, my_file, group, owner)
            print 'pushed to ' + my_file
            file_found = True
        except Exception as e:
            print 'Not found:' + my_file + ' Error:' + str(e)
            pass
    if not file_found:
        print 'WCNSS_qcom_cfg.ini not exist on device'

    print 'Networking configuration successfully changed'


if __name__ == '__main__':
    main()






    # pull WCNSS_qcom_cfg.ini






