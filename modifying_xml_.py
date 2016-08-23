#Pulling .xml files from new device
import os
import sys
import time
from adb_handler import AdbDevice

myadb = AdbDevice()
myadb.adb_command('adb root')
print 'Wait for 15 seconds'
time.sleep( 15 )
myadb.adb_command('adb remount')
myadb.adb_command('adb pull /system/etc/wfdconfig.xml')
myadb.adb_command('adb pull /system/etc/wfdconfigsink.xml')
# Modifying ContentProtection value to valid=1
# Modifying wfdconfig.xml

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


#Modifying wfdconfigsink.xml

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


