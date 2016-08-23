#!/usr/bin/python

import sys
import subprocess
from adb_handler import AdbDevice

myadb = AdbDevice()
myadb.adb_command('wait-for-device devices')
myadb.adb_command('root')
myadb.adb_command('remount')


try:
    myadb.adb_command('shell "rm /system/vendor/lib/libDxHdcp.so"')
except:
    print 'bla1'
    pass
try:
    myadb.adb_command('shell "rm /system/vendor/lib64/libDxHdcp.so"')
except:
    print 'bla2'
    pass


