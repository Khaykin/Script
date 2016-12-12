import json
import logging
import os
import socket
import subprocess

from adam import Adam


class ResetFailure(Exception):
    pass


class AbstractReset(object):
    def do_reset(self):
        raise NotImplementedError()


class AdbReset(AbstractReset):
    def __init__(self, adb):
        self.adb = adb
        self.logger = logging.getLogger(self.__class__.__name__)

    def __str__(self):
        return 'Fastboot reset'

    def do_reset(self):
        self.logger.info('Reboot device')
        try:
            cmd = self.adb.raw_cmd(timeout_in_sec=40) + ' reboot'
            self.logger.debug('>>' + cmd)
            subprocess.check_call(cmd, shell=True)
            self.adb.wait_for_device()

        except subprocess.CalledProcessError:
            try:
                cmd = self.adb.raw_cmd(timeout_in_sec=40) + ' reboot bootloader'
                self.logger.debug('>>' + cmd)
                subprocess.check_call(cmd, shell=True)

                cmd = self.adb.raw_cmd(cmd='fastboot', timeout_in_sec=40) + ' reboot'
                self.logger.debug('>>' + cmd)
                subprocess.check_call(cmd, shell=True)

                self.adb.wait_for_device()

            except subprocess.CalledProcessError:
                self.logger.exception('AdbReset failed')
                raise ResetFailure('Failed to reboot via ADB')


class AdamReset(object):

    def __init__(self, adb, adam_):
        self.logger = logging.getLogger(self.__class__.__name__)
        assert adam_
        assert adb
        assert isinstance(adam_, Adam)
        self.adam = adam_
        self.adb = adb

    def __str__(self):
        return 'Reboot using Adam'

    def do_reset(self):
        self.logger.info('Reboot device')
        try:
            self.adam.turn_off()
            self.adam.turn_on()
            self.adb.wait_for_device()
        except Adam.Error:
            self.logger.exception('Failed to operate ADAM device')
            raise ResetFailure('Adam reset failed')
        except subprocess.CalledProcessError:
            self.logger.exception('No device detected :(')
            raise ResetFailure('Device is not ready')

    @classmethod
    def get_if_available(cls, adb):
        """
        detect ADAM by getting config value
        Returns: valid ADAM reset handler instance or None in case ADAM is not available for current host
        """
        logger = logging.getLogger(cls.__name__)

        adam_cfg = "/opt/adam/adam.json"
        '''
        adam.json should contain:
        {
            "ip": "<adam ip address>",
            "power_port": "<adam power port>",
            "usb_port": "<adam usb port>"
        }
        '''

        if not (os.path.isfile(adam_cfg) and Adam.is_supported()):
            logger.info('No Adam is available on that host')
            return None

        logger.info('adam detected: ' + adam_cfg)
        with open(adam_cfg, 'r') as fd:
            adam_metadata = json.load(fd)

        adam_ = Adam(**adam_metadata)  # passing kwargs - expecting that json will have keys according to ctor arguments
        return cls(adb=adb, adam_=adam_)


class UsbControllerReset(AdbReset):
    def __init__(self, adb):
        super(UsbControllerReset, self).__init__(adb)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exec_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reset_usb.sh')
        assert os.path.exists(self.exec_script_path)

    def __str__(self):
        return 'USB hubs + Reboot'

    def do_reset(self):
        self.logger.info('Reset USB hubs')
        try:
            subprocess.check_call('sudo {0}'.format(self.exec_script_path), shell=True)
        except subprocess.CalledProcessError:
            logging.exception('Failed to Reset USB controller')
            raise ResetFailure('Failed to Reset USB controller')
        super(UsbControllerReset, self).do_reset()

    @classmethod
    def get_if_available(cls, adb):
        logger = logging.getLogger(cls.__name__)
        if not socket.gethostname().startswith('ta-lab'):
            return None
        logger.info('UsbControllerReset detected')
        return cls(adb=adb)


if __name__ == "__main__":
    from adb import UsbAdb
    adb = UsbAdb(None)
    adam = AdamReset.get_if_available(adb)
    if adam:
        adam.adam.turn_on()

