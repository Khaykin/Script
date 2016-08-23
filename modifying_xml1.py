#Pulling .xml files from new device
import os
import sys
import time
import re
from adb_handler import AdbDevice

myadb = AdbDevice()
myadb.adb_command('adb wait-for-device devices')

print('waiting for device')
myadb.adb_command('adb root')
print 'Wait for 15 seconds'
time.sleep( 15 )
myadb.adb_command('adb remount')
myadb.adb_command('adb pull /system/etc/wfdconfig.xml')
myadb.adb_command('adb pull /system/etc/wfdconfigsink.xml')

# Modifying wfdconfig.xml ( Enable HDCP )
# Modifying ContentProtection value to valid=1

import xml.etree.cElementTree as etree
tree = etree.parse(r"D:wfdconfig.xml")
tree
root = tree.getroot()
cp = root.find(".//Capability/ContentProtection/Valid")
for i in cp.iter('Valid'):
	i.text = str(1)
for attr in cp.iter():
	print 'wfdconfig.xml modified: \nContentProtection: ' + attr.tag + " = " + attr.text
tree.write(r'wfdconfig.xml')


# Modifying wfdconfigsink.xml ( Enable HDCP )
# Modifying ContentProtection value to valid=1

import xml.etree.cElementTree as etree
tree = etree.parse(r"D:wfdconfigsink.xml")
tree
root = tree.getroot()
cp = root.find(".//Capability/ContentProtection/Valid")
for i in cp.iter('Valid'):
	i.text = str(1)
for attr in cp.iter():
	print 'wfdconfigsink.xml modified: \nContentProtection: ' + attr.tag + " = " + attr.text
tree.write(r'wfdconfigsink.xml')

# Pushing modified .xml files to device

myadb.adb_command('adb push wfdconfig.xml /system/etc/')
myadb.adb_command('adb push wfdconfigsink.xml /system/etc/')
print 'wfdconfigsink.xml & wfdconfig.xml pushed to device'
print ('<!--  enable HDCP by default -->') 
time.sleep(5)

#pull WCNSS_qcom_cfg.ini
myadb.adb_command('adb pull /system/etc/wifi/WCNSS_qcom_cfg.ini')

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
print 'WCNSS_qcom_cfg.ini modified: \ngEnableImps=0'
  
# Replace the target string
file_data = re.sub(
    pattern=r'gEnableBmps=\d*',
    repl='gEnableBmps=0',
    string=file_data)

# Write the file out again
with open('D:/Script/WCNSS_qcom_cfg', 'w') as file:
  file.write(file_data)
print 'WCNSS_qcom_cfg modified: \ngEnableBmps=0'
  
# Replace the target string
file_data = re.sub(
    pattern=r'gDot11Mode=\d*',
    repl='gDot11Mode=3',
    string=file_data)

# Write the file out again
with open('D:/Script/WCNSS_qcom_cfg.ini', 'w') as file:
  file.write(file_data)
print 'WCNSS_qcom_cfg modified: \ngDot11Mode=3'

#Push to device WCNSS_qcom_cfg.ini 

myadb.adb_command('adb push WCNSS_qcom_cfg.ini /system/etc/wifi/')
myadb.adb_command('adb push WCNSS_qcom_cfg.ini /system/etc/firmware/wlan/qca_cld/')
print 'WCNSS_qcom_cfg.ini pushed'
time.sleep(5)

#Pushing libwfddhcpcp.so to enable WFD client app 

myadb.adb_command('adb push lib/libwfdhdcpcp.so /system/vendor/lib')
myadb.adb_command('adb push lib64/libwfdhdcpcp.so /system/vendor/lib64')
print 'WFD client app enabled'
time.sleep(5)


# RPMB Provisioning Test Key
myadb.adb_command('adb shell "echo \'1\' | qseecom_sample_client -v sampleapp 14 1"')
time.sleep(5)
# RPMB partition erasing
myadb.adb_command('adb shell "echo \'y\' | qseecom_sample_client -v sampleapp 15 1"')

print 'RPMB provisioning done'
time.sleep(5)

#Configuring enabling battery charging
myadb.adb_command('adb shell setprop persist.usb.chgdisabled 0')
print 'USB charging enabled'

# Configuring mtp/adb settings

myadb.adb_command('adb shell setprop persist.sys.usb.config mtp,adb')

print ('=======Device configured as MTP=======')
print ('=======Please reboot the device=======')
print ('=======for to finish configuring======')










