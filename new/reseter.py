import logging
import os
import subprocess
import sys
from adb import Adb
from adam import Adam


class FastbootReseter:
    def __init__(self, dev):
        assert isinstance(dev, Adb)
        self.adb_cmd = '{0} reboot-bootloader'.format(dev.adb_cmd)
        self.fastboot_cmd = '{0} reboot'.format(dev.fastboot_cmd)

    def __str__(self):
        return 'Reboot using Fastboot'

    def do_reset(self):
        logging.info('Execute command {0}'.format(self.adb_cmd))
        try:
            subprocess.check_call(self.adb_cmd, shell=True)
        except:
            logging.error('Failed reboot Bootloader - cmd: {0}'.format(self.adb_cmd))
            raise Exception('Failed reboot Bootloader')

        logging.info('Execute command {0}'.format(self.fastboot_cmd))
        try:
            subprocess.check_call(self.fastboot_cmd, shell=True)
        except:
            logging.error('Failed fastboot Bootloader - cmd: {0}'.format(self.fastboot_cmd))
            raise Exception('Failed fastboot Bootloader')


class AdamReseter:
    def __init__(self, adam):
        assert adam
        assert isinstance(adam, Adam)
        self.adam = adam

    def __str__(self):
        return 'Reboot using Adam'

    def do_reset(self):
        self.adam.turn_off()
        self.adam.turn_on()


class USBReseter:
    def __init__(self):
        self.exec_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reset_usb.sh')
        assert os.path.exists(self.exec_script_path)

    def __str__(self):
        return 'Reboot the machine USB hubs'

    def do_reset(self):
        subprocess.check_call('sudo {0}'.format(self.exec_script_path), shell=True)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )