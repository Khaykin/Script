#!/usr/bin/python

import subprocess
import os
import sys
import platform

class AdbDevice(object):
    def __init__(self, adb_path='adb', device=None):
        # type: (object, object) -> object
        self.adb_cmd = ("%s -s %s" % (adb_path, device)) if device else adb_path


    def adb_command(self, cmd, timeout=120):
        if sys.platform.startswith('linux'):
            cmd = "timeout %s %s %s" % (str(timeout), self.adb_cmd, cmd)
        else:
            cmd = "%s %s" % (self.adb_cmd, cmd)
            print("Execute command: %s" % str(cmd))
            subprocess.check_call(cmd, shell=True)


    def adb_command_and_get_output(self, cmd, timeout=120):
        print("Execute command: %s" % str(cmd))
        if sys.platform.startswith('linux'):

            return subprocess.check_output(
                "timeout %s %s %s" % (str(timeout), self.adb_cmd, cmd),
                stderr=subprocess.STDOUT,
                shell=True
            )
        else:
            return subprocess.check_output(
                "%s %s" % (self.adb_cmd, cmd),
                stderr=subprocess.STDOUT,
                shell=True
            )

