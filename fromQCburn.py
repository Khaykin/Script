#!/usr/bin/python
import re
from adb_handler import AdbDevice







# Menu 2
def setNetworkConfiguration():
    print '##########################################'
    # pull WCNSS_qcom_cfg.ini
    print '##########################################' 
    def process_file():
        # Changing network configuration (WCNSS_qcom_cfg.ini)
        with open('WCNSS_qcom_cfg.ini', 'r') as fh:
          file_data = fh.read()
        # Replace the target string
        file_data = re.sub(
            pattern=r'gEnableImps=\d*',
            repl='gEnableImps=0',
            string=file_data)
        # Write the file out again
        with open('WCNSS_qcom_cfg.ini', 'w') as file:
          file.write(file_data)
        print '##########################################'
        print 'WCNSS_qcom_cfg.ini modified: \ngEnableImps=0'
        print '##########################################'
        # Replace the target string
        file_data = re.sub(
            pattern=r'gEnableBmps=\d*',
            repl='gEnableBmps=0',
            string=file_data)
        # Write the file out again
        with open('WCNSS_qcom_cfg', 'w') as file:
          file.write(file_data)
        print '##########################################'
        print 'WCNSS_qcom_cfg modified: \ngEnableBmps=0'
        print '##########################################'
        # Replace the target string
        file_data = re.sub(
            pattern=r'gDot11Mode=\d*',
            repl='gDot11Mode=3',
            string=file_data)
        # Write the file out again
        with open('WCNSS_qcom_cfg.ini', 'w') as file:
          file.write(file_data)
        print '##########################################'
        print 'WCNSS_qcom_cfg modified: \ngDot11Mode=3'
        print '##########################################'

    files = ["/system/etc/wifi/WCNSS_qcom_cfg.ini", "/system/etc/firmware/wlan/qca_cld/WCNSS_qcom_cfg.ini",
             "/data/misc/wifi/WCNSS_qcom_cfg.ini"]
    not_found_count = 0
    # pull WCNSS_qcom_cfg.ini
    for file in files:
        try:
            myadb.adb_command('pull ' + file)
            # myadb.adb_command('pull /system/etc/wifi/WCNSS_qcom_cfg.ini')
            print 'WCNSS_qcom_cfg.ini pulled from ' + file
            process_file()
            print 'WCNSS_qcom_cfg.ini modifyed'
            # file = True
            myadb.adb_command('push WCNSS_qcom_cfg.ini ' + file)
            myadb.adb_command('shell chmod 644 ' + file)
            myadb.adb_command('shell chown root:root ' + file)
            print 'pushed to ' + file
        except:
            not_found_count += 1
            print("Not found: %s %u times !!!" % (file, not_found_count))
            pass
    if not_found_count == 3:
        print 'WCNSS_qcom_cfg.ini not exist on device'
    else:
        print '##########################################'
        print '    Networking configuration file \n        successfully changed'
        print '##########################################'
    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return

# Back to main menu
def back():
    menu_actions['main_menu']()
 
# Exit program
def exit():
    sys.exit()