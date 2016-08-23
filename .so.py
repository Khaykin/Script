#!/usr/bin/python

import os
from adb_handler import AdbDevice
myadb = AdbDevice()

def enable(check, file):
    #Pushing libwfddhcpcp.so to enable WFD client app
    files = ["/system/vendor/lib/libDxHdcp.so", "/system/vendor/lib64/libDxHdcp.so"]
    check = 'shell ls -l'
    #targets = ["/system/vendor/lib", " /system/vendor/lib64"]
    #SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    #print "Verify that files is found in " + SCRIPT_DIR

    #not_found_count = 0
    for file, in files:
        try:
            myadb.adb_command('shell "ecko ls -l | /system/vendor/lib/libDxHdcp.so ')  # Verifying existing of .so files
            print'gam'
            myadb.adb_command('shell ' + ' rm ' + file)
        except:
            #not_found_count += 1
            #print "Not found %s %u times !!!" % (file, not_found_count)
            print 'If ' + file + ' not found '
            pass
    return

#enable_wfd(lib64/libwfdhdcpcp.so,/system/vendor/lib64, "not found lib64")



# Verifying existing of .so files
#files = ["lib/libwfdhdcpcp.so", "lib64/libwfdhdcpcp.so"]
#not_found_count = 0
#for file in files:
#    try:

#        myadb.adb_command('push lib/libwfdhdcpcp.so ')
#        myadb.adb_command('push  )
 #   except:
#        SCRIPT_DIR = os.path.dirname(os.path.realpath("files"))
 #       print "Verify that file is found in " + SCRIPT_DIR
 #       not_found_count += 1
 #       print 'Not found ' + file + '\nCheck if you have libwfdhdcpcp.so files in local directory'
 #       pass
#if not_found_count != 0:
#    print "jopa1 raz"
#else:
 #   print "zaebok"

#else:
#myadb.adb_command('push lib/libwfdhdcpcp.so /system/vendor/lib')

#os.path.isfile("lib64/libwfdhdcpcp.so")
#myadb.adb_command('push lib64/libwfdhdcpcp.so /system/vendor/lib')
# Pushing libwfddhcpcp.so to enable WFD client app
