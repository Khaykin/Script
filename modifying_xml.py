#Pulling .xml files from new device
import os
import sys
from adb_handler import AdbDevice
myadb = AdbDevice()
#try:
myadb.adb_command('root')
#except(RuntimeError, TypeError, NameError):
#       print("Error occurred")
        #sleep(SLEEP_TIME_AFTER_ADB_ROOT)
#try:
myadb.adb_command('remount')
#except:
#   print("Error occurred")

#try:
myadb.adb_command('pull /system/etc/wfdconfig.xml')
#except:
#   print("Error occurred")

#try:
myadb.adb_command('pull /system/etc/wfdconfigsink.xml')
#except:
#   print("Error occurred")


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


