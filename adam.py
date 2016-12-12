import logging

__all__ = ['Adam']

logger = logging.getLogger('ADAM')


class Adam(object):
    """
    in order to use this class please make sure the following package is installed: python-pymodbus
    if not- install it as following:
    sudo apt-get install python-pymodbus
    """
    class Error(Exception):
        pass

    class Connection(object):
        coil_base_address = 16

        def __init__(self, ip):
            from pymodbus.client.sync import ModbusTcpClient as ModbusClient  # sudo apt-get install python-pymodbus
            from pymodbus.exceptions import ModbusException
            self.client_class = ModbusClient
            self.client_exception_class = ModbusException
            self.ip = ip
            self.client = None

        def __enter__(self):  # context management enter

            try:
                self.client = self.client_class(self.ip)
                self.client.connect()
            except self.client_exception_class:
                logger.exception('ModbusClient connection failed - IP:' + self.ip)
                raise Adam.Error('Adam connection error - IP:' + self.ip)
            # raise Exception('Could not connect to adam at ip ' + self.ip)
            return self

        def set_port(self, port, mode):
            assert isinstance(mode, bool)
            assert str(port)  # str() since port can be 0
            try:
                rq = self.client.write_coil(self.coil_base_address + port, mode)
                if not rq.function_code < 0x80:
                    raise Adam.Error('Adam set_port failed [function_code={}]'.format(rq.function_code))
                rq = self.client.write_coil(self.coil_base_address + port, not mode)
                if not rq.function_code < 0x80:
                    raise Adam.Error('Adam set_port failed [function_code={}]'.format(rq.function_code))
            except self.client_exception_class:
                logger.exception('write_coil failed')
                raise Adam.Error('Adam set_port failed')

        def is_on(self, port):
            try:
                result = self.client.read_coils(self.coil_base_address + port)
                return True if result.bits[0] else False
            except self.client_exception_class:
                logger.exception('read_coils failed port=' + str(port))
                raise Adam.Error('Adam is_on failed')

        def __exit__(self, exc_type, exc_val, exc_tb):  # context management exit
            if self.client:
                try:
                    self.client.close()
                    self.client = None
                except self.client_exception_class:
                    logger.exception('ModbusClient.close() failed' )
                    raise Adam.Error('Adam disconnect failed')

        def __del__(self):  # dtor
            assert not self.client, 'client was not closed properly'

    def __init__(self, ip, power_port, usb_port):
        self.ip = ip
        self.power_port = int(power_port)
        self.usb_port = int(usb_port)

    def turn_off(self):
        with Adam.Connection(self.ip) as adam:
            if adam.is_on(self.power_port):
                print("Turning off port %d" % self.power_port)
                adam.set_port(self.power_port, True)
            if str(self.usb_port) and adam.is_on(self.usb_port):
                print("Turning off port %d" % self.usb_port)
                adam.set_port(self.usb_port, True)

    def turn_on(self):
        with Adam.Connection(self.ip) as adam:
            if not adam.is_on(self.power_port):
                print("Turning on port %d" % self.power_port)
                adam.set_port(self.power_port, False)
            if str(self.usb_port) and not adam.is_on(self.usb_port):
                print("Turning on port %d" % self.usb_port)
                adam.set_port(self.usb_port, False)

    def get_state(self):
        """
        Read status of ADAM port (turned off/on).
        :return: Return 1- if port is turned on, 0- if port is turned off.
        """
        with Adam.Connection(self.ip) as adam:
            status = adam.is_on(self.power_port)

        logger.info('device status is: {0}'.format(status))

        return status

    def is_adam_valid(self):
        """
        :return: Return True if self.adam_ip is available, otherwise False.
        """
        return self.get_state() < 2

    @staticmethod
    def is_supported():
        try:
            from pymodbus.client.sync import ModbusTcpClient
            return True
        except ImportError:
            return False

##('10.45.52.40', 0)
