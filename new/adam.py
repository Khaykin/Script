import ConfigParser
import logging
import os
import sys
from time import sleep
from pymodbus.client.sync import ModbusTcpClient as ModbusClient  # sudo apt-get install python-pymodbus


class Adam(object):
    DEFAULT_ADAM_FILE = '/opt/adam/adammapping.txt'
    OUTPUT_COIL_ADDR_BASE = 16
    """
    in order to use this class please make sure the following package is installed: python-pymodbus
    if not- install it as following:
    sudo apt-get install python-pymodbus or pip install pymodbus
    """
    def __init__(self, adam_ip, adam_port, adam_usb_port=None):
        self.adam_ip = adam_ip
        self.adam_port = adam_port
        self.adam_usb_port = adam_usb_port
        self.client = ModbusClient(adam_ip)

    def __connect(self):
        for i in range(5):
            if self.client.connect():
                return
            logging.error('connection to ADAM failed... sleep 5s and try again')
            self.__disconnect()
            sleep(5)
            self.client = ModbusClient(self.adam_ip)
        raise Exception('Could not connect to adam at ip ' + self.adam_ip)

    def __disconnect(self):
        self.client.close()

    def __set_port(self, port, mode, timeout):
        assert isinstance(mode, bool)
        rq = self.client.write_coil(self.OUTPUT_COIL_ADDR_BASE + port, mode)
        assert (rq.function_code < 0x80)  # test that we are not an error
        sleep(1)
        rq = self.client.write_coil(self.OUTPUT_COIL_ADDR_BASE + port, not mode)
        assert (rq.function_code < 0x80)  # test that we are not an error
        logging.info('sleep {0} seconds'.format(timeout))
        sleep(timeout)

    def turn_off(self, timeout=40):
        if self.state != 0:
            self.__connect()
            self.__set_port(self.adam_port, True, timeout)
            if self.adam_usb_port:
                self.__set_port(self.adam_usb_port, True, timeout)
            self.__disconnect()

    def turn_on(self, timeout=40):
        if self.state != 1:
            self.__connect()
            self.__set_port(self.adam_port, False, timeout)
            if self.adam_usb_port:
                self.__set_port(self.adam_usb_port, False, timeout)
            self.__disconnect()

    @property
    def state(self):
        """
        Read status of ADAM port (turned off/on).
        :return: Return 1- if port is turned on, 0- if port is turned off.
        """
        self.__connect()
        result = self.client.read_coils(self.OUTPUT_COIL_ADDR_BASE + self.adam_port)
        res = result.bits[0]
        if res:  # True- means that port is turned on
            status = 1
        else:
            status = 0

        logging.info('device status is: {0}'.format(status))
        self.__disconnect()

        return status

    def is_adam_valid(self):
        """
        :return: Return True if self.adam_ip is available, otherwise False.
        """
        return self.state < 2

    @classmethod
    def adam_discovery(cls):
        if not os.path.exists(cls.DEFAULT_ADAM_FILE):
            logging.error('Adam Config File {0} Not Found'.format(cls.DEFAULT_ADAM_FILE))
            return

        config_parser = ConfigParser.RawConfigParser()
        config_parser.read(cls.DEFAULT_ADAM_FILE)
        adam_dev_list = list(config_parser._sections.values())
        logging.info('detected the following adam devices: {0}'.format(*adam_dev_list))
        if adam_dev_list:
            return Adam(adam_dev_list[0]['adamip'], adam_dev_list[0]['adamport'], adam_dev_list[0]['adamportusb'])

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )