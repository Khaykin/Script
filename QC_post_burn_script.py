#!/usr/bin/python


import os
import sys
import time
import re
from adb_handler import AdbDevice
adb_dev = AdbDevice()

# =======================
#     MENUS FUNCTIONS
# =======================

# Main menu
def main_menu():

    print "Please choose the menu you want to start:"
    print "\n1.Enabling content protection in WFD press 1"
    print "\n2.Changing network configuration press 2"
    print "\n3.Enable WFD client app press 3"
    print "\n4.RPMB Provisioning Test Key\n  and partition erasing press 4"
    print "\n5.Enabling battery charging via USB port press 5"
    print "\n6.Configuring mtp/adb settings press 6"
    print "\n7.Reboot the device to complete configuring press 7"
    print "\n9.Back to main menu press 9"
    print "\n0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)

    return


# Execute menu
def exec_menu(choice):

    ch = choice.lower()
    if ch == '':
        menu_actions['main_menu']()
    else:
        try:
            menu_actions[ch]()
        except KeyError:
            print "Invalid selection, please try again.\n"
            menu_actions['main_menu']()
    return


# Menu 1
def enable_content_protection():

    adb_dev.adb_command('pull /system/etc/wfdconfig.xml')
    bits = adb_dev.adb_command_and_get_output('shell ls -l /system/etc/wfdconfig.xml')
    bits_list = bits.split()
    # Modifying wfdconfig.xml ( Enable HDCP for Transmitter )
    # Modifying ContentProtection value to valid=1
    import xml.etree.cElementTree as etree
    tree = etree.parse(r"wfdconfig.xml")
    root = tree.getroot()  # Reading the file
    cp = root.find(".//Capability/ContentProtection/Valid")
    for i in cp.iter('Valid'):  # Method to modifying an XML File
        i.text = str(1)
        print '##########################################'
        print 'wfdconfig.xml modified: \nContentProtection: ' + i.tag + " = " + i.text
        print '##########################################'
    tree.write(r'wfdconfig.xml')
    # Pushing modified wfdconfig.xml files to device
    adb_dev.adb_command('push wfdconfig.xml /system/etc/')
    adb_dev.adb_command('shell chmod 644 /system/etc/wfdconfig.xml')
    adb_dev.adb_command('shell chown {0}:{1} {2}'.format(bits_list[1], bits_list[2], '/system/etc/wfdconfig.xml'))

    bits = adb_dev.adb_command_and_get_output('shell ls -l /system/etc/wfdconfigsink.xml')
    bits_list = bits.split()
    adb_dev.adb_command('pull /system/etc/wfdconfigsink.xml')
    # Modifying wfdconfigsink.xml ( Enable HDCP for Sink )
    # Modifying ContentProtection value to valid=1
    tree = etree.parse(r"wfdconfigsink.xml")
    root = tree.getroot()  # Reading the file
    cp = root.find(".//Capability/ContentProtection/Valid")
    for i in cp.iter('Valid'):  # Method to modifying an XML File
        i.text = str(1)
        print '##########################################'
        print 'wfdconfigsink.xml modified: \nContentProtection: ' + i.tag + " = " + i.text
        print '##########################################'
    # Pushing modified wfdconfigsink.xml files to device
    tree.write(r'wfdconfigsink.xml')
    adb_dev.adb_command('push wfdconfigsink.xml /system/etc/')
    adb_dev.adb_command('shell chmod 644 /system/etc/wfdconfigsink.xml')
    adb_dev.adb_command('shell chown {0}:{1} {2}'.format(bits_list[1], bits_list[2], '/system/etc/wfdconfigsink.xml'))

    print '##########################################'
    # Pushing modified .xml files to device
    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():

    menu_actions['main_menu']()


# Menu 2
def set_network_configuration():

    def get_owner(adb, my_file):
        bits = adb.adb_command_and_get_output('shell ls -l ' + my_file)
        bits_list = bits.split()
        return bits_list[0].startswith('l'), bits_list[1], bits_list[2]


    def set_owner(adb, my_file, group, owner):
        adb.adb_command('shell chown {group}:{owner} {file}'.format(group=group, owner=owner, file=my_file))

    def process_file():
        # Changing network configuration (WCNSS_qcom_cfg.ini)
        with open('WCNSS_qcom_cfg.ini', 'r') as fh:
            file_data = fh.read()
        # Replace the target string
        file_data = re.sub(
            pattern=r'gEnableImps=\d*',
            repl='gEnableImps=0',
            string=file_data)
        print 'WCNSS_qcom_cfg.ini modified: \ngEnableImps=0'
        # Replace the target string
        file_data = re.sub(
            pattern=r'gEnableBmps=\d*',
            repl='gEnableBmps=0',
            string=file_data)
        print 'WCNSS_qcom_cfg modified: \ngEnableBmps=0'
        # Replace the target string
        file_data = re.sub(
            pattern=r'gDot11Mode=\d*',
            repl='gDot11Mode=3',
            string=file_data)
        print 'WCNSS_qcom_cfg modified: gDot11Mode=3'
        # Write the file to file
        with open('WCNSS_qcom_cfg.ini', 'w') as fh:
            fh.write(file_data)


    files = ["/system/etc/wifi/WCNSS_qcom_cfg.ini",
             "/system/etc/firmware/wlan/qca_cld/WCNSS_qcom_cfg.ini",
             "/data/misc/wifi/WCNSS_qcom_cfg.ini"
    ]
    file_found = False
    # pull and push WCNSS_qcom_cfg.ini
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
            print 'File error:' + my_file + ' Error:' + str(e)
            pass
    if not file_found:
        print 'WCNSS_qcom_cfg.ini not exist on device'

    print '##########################################'
    print '    Networking configuration file \n        successfully changed'
    print '##########################################'
    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():
    
    menu_actions['main_menu']()


# Menu 3
def enable_wfd_client_app():
    # Pushing libwfddhcpcp.so to enable WFD client app
    files = [("lib/libwfdhdcpcp.so", "/system/vendor/lib"),
             ("lib64/libwfdhdcpcp.so", " /system/vendor/lib64")]
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

    not_found_count = 0
    for file, target in files:
        try:
            if os.path.isfile(file):  # Verifying existing of .so files
                adb_dev.adb_command('push ' + file + ' ' + target)
            else:
                raise 'File Not Found'
        except:
            not_found_count += 1
            print '===== ' + file + ' ===== not found in ' + SCRIPT_DIR + ','
            print 'find and copy from:'
            print "<Qcom source Android tree root>/out/target/product/<product name>/system/vendor/"
            pass

    if not_found_count == 0:
        print '##########################################'
        print '        WFD client app ENABLED            '
        print '##########################################'
    else:
        print '##########################################'
        print '        WFD client app DISABLED            '
        print '##########################################'

    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():
    
    menu_actions['main_menu']()


# Menu 4
def enable_rpmb_provisioning():
    
    # RPMB Provisioning Test Key'
    adb_dev.adb_command('shell "echo 1 | qseecom_sample_client -v sampleapp 14 1"')
    time.sleep(5)
    print '##########################################'
    print '       RPMB provisioning done'
    print '##########################################'
    adb_dev.adb_command('shell "echo y | qseecom_sample_client -v sampleapp 15 1"')
    print '##########################################'
    print 'RPMB partition erased'
    print '##########################################'
    time.sleep(5)
    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():
    
    menu_actions['main_menu']()


# Menu 5
def enable_usb_charging():
    
    # Configuring enabling battery charging
    adb_dev.adb_command('shell setprop persist.usb.chgdisabled 0')
    print '##########################################'
    print '           USB charging enabled'
    print '##########################################'
    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():
    
    menu_actions['main_menu']()


# Menu 6
def set_config_mtp():
    
    # Configuring mtp/adb settings
    adb_dev.adb_command('shell setprop persist.sys.usb.config mtp,adb')
    # Perform of "setprop..." can drop device from ADB,
    # Restart of server help to wake up ADB server and renew connection.
    adb_dev.adb_command('kill-server')
    time.sleep(10)
    adb_dev.adb_command('start-server')
    adb_dev.adb_command('wait-for-device devices')
    print '##########################################'
    print ('       Device configured as MTP')
    print '##########################################'
    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():
    
    menu_actions['main_menu']()


# Menu 7
def enable_device_reboot():

    adb_dev = AdbDevice()
    # Reboot the device for complete configuring
    print '##########################################'
    print ('       The device will reboot ')
    print '##########################################'
    adb_dev.adb_command('reboot')
    time.sleep(15)
    adb_dev.adb_command('wait-for-device devices')
    adb_dev.adb_command('root')
    time.sleep(15)
    adb_dev.adb_command('remount')

    choice = raw_input("Back to main menu press 9 or 0 to Quit")
    exec_menu(choice)
    return


# Back to main menu
def back():
    
    menu_actions['main_menu']()


# =======================
#    MENUS DEFINITIONS
# =======================

# Menu definition
menu_actions = {
    'main_menu': main_menu,
    '1': enable_content_protection,
    '2': set_network_configuration,
    '3': enable_wfd_client_app,
    '4': enable_rpmb_provisioning,
    '5': enable_usb_charging,
    '6': set_config_mtp,
    '7': enable_device_reboot,
    '9': back,
    '0': exit,
}


# =======================
#      MAIN PROGRAM
# =======================

# Main Program
if __name__ == "__main__":
    #main_menu()

    adb_dev.adb_command('wait-for-device devices')
    adb_dev.adb_command('root')
    print '      Wait for 15 seconds'
    time.sleep(15)
    adb_dev.adb_command('remount')
    print 'Cheking and if exist removing default HDCP HLOS binaries'
    adb_dev.adb_command('shell "if [ -f /system/vendor/lib/libDxHdcp.so ]; then rm /system/vendor/lib/libDxHdcp.so; fi;"')
    adb_dev.adb_command('shell "if [ -f /system/vendor/lib64/libDxHdcp.so ]; then rm /system/vendor/lib64/libDxHdcp.so; fi;"')

    main_menu()








