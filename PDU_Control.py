# see: https://tobinsramblings.wordpress.com/2011/05/03/snmp-tutorial-apc-pdus/
#      https://github.com/wdennis/pysnmp-monitoring/blob/master/apc_pdu_legamps_syslogger.py
# This script enable/disable outlet power for APC PDUs (our PDU model is: AP8959EU3)
# PowerNet MIB v4.0.6 or higher is required for use PDUs with SNMP.
# PowerNet MIB can be downloaded from ftp://ftp.apc.com/apc/public/software/pnetmib/mib/
# In order to use MIB from pysnmp library, MIB should be pythonized,
# see http://stackoverflow.com/questions/17413123/how-to-make-custom-mib-pysnmp
#
# Usefull commands for debugging:
# walk all PDU entries:
# snmpwalk -m +C:/usr/share/snmp/mibs/powernet419.mib.txt -v 2c -c public 10.45.54.130 enterprises.318
# get socket status:
# snmpget -m +C:/usr/share/snmp/mibs/powernet419.mib.txt -v 2c -c public 10.45.54.130 PowerNet-MIB::sPDUOutletCtl.22 
# set socket status:
# snmpset -m +C:/usr/share/snmp/mibs/powernet419.mib.txt -v 2c -c private 10.45.54.130 PowerNet-MIB::sPDUOutletCtl.22 i 2
# snmpset -m +C:/usr/share/snmp/mibs/powernet419.mib.txt -v 2c -c private 10.45.54.130 PowerNet-MIB::sPDUOutletCtl.22 i 1
# Note: path to powernet419.mib.txt can be changed (depends on setup)


from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.smi import builder
import os

# From PowerNet-MIB declaration:
OUTLET_STATE_ON = 1  # outletOn
OUTLET_STATE_OFF = 2  # outletOff

TA_OUTLET_CONFIG = {
    'ta-lab-jsl13': {
        'pdu_ip': '10.45.54.130',
        'outlet_id': '5',
        'device':'MSM8996'
    },
    # 'TA_OUTLET_17': {
    #     'pdu_ip': '10.45.54.130',
    #     'outlet_id': '17'
    # },
    # 'TA_OUTLET_22': {
    #         'pdu_ip': '10.45.54.130',
    #         'outlet_id': '22'
    # },
    # 'TA_OUTLET_3': {
    #         'pdu_ip': '10.45.54.130',
    #         'outlet_id': '3'
    # },
    'TA_OUTLET_HDCP_MSM8996_2': {
        'pdu_ip': '10.45.54.130',
        'outlet_id': '7'
    }
}


class PduOutlet(object):
    def __init__(self, cmd_gen, pdu_ip, outlet_id):
        self.cmd_gen = cmd_gen
        self.pdu_ip = pdu_ip
        self.outlet_id = outlet_id

    def is_on(self):
        print('Get PDU socket state for PDU {}, outlet {}'.format(self.pdu_ip, self.outlet_id))
        error_indication, error_status, error_index, var_bind_table = self.cmd_gen.getCmd(
            cmdgen.CommunityData('public', mpModel=1),  # mpModel=1 == use SNMP v2c
            cmdgen.UdpTransportTarget((self.pdu_ip, 161)),
            cmdgen.MibVariable('PowerNet-MIB', 'sPDUOutletCtl', self.outlet_id),
            lookupNames=True,
            lookupValues=True
        )

        if error_indication:
            raise (Exception('SNMP engine-level error: {}'.format(error_indication)))
        elif error_status:
            raise (Exception('PDU returned SNMP error: {0:s} at {1:s}'.format(error_status.prettyPrint(),
                                                                              error_index and var_bind_table[-1][
                                                                                  int(error_index) - 1] or '?')))
        size = len(var_bind_table)
        if size != 1:
            raise (Exception('Wrong response data size is returned by SNMP Get command: '
                             'Received size: {}. Expected size: 1'.format(size)))
        result = var_bind_table[0][1]
        print("Get PSU socket status succeeded, result={}".format(result))

        assert (result == OUTLET_STATE_ON) or (result == OUTLET_STATE_OFF), \
            'PDU (ip{}, outlet_id{}) returned invalid state {}'.format(self.pdu_ip, self.outlet_id, result)

        return result == OUTLET_STATE_ON

    def __set_state(self, state):
        print('Set PDU socket status for PDU {}, outlet {} to value {}'.format(self.pdu_ip, self.outlet_id, state))
        error_indication, error_status, error_index, var_bind_table = self.cmd_gen.setCmd(
            cmdgen.CommunityData('private', mpModel=1),  # mpModel=1 == use SNMP v2c
            cmdgen.UdpTransportTarget((self.pdu_ip, 161)),
            (cmdgen.MibVariable('PowerNet-MIB', 'sPDUOutletCtl', self.outlet_id), state),
            lookupNames=True, lookupValues=True
        )

        if error_indication:
            raise (Exception('SNMP engine-level error: {}'.format(error_indication)))
        elif error_status:
            #        raise(Exception('PDU returned SNMP error: {0:s} at {1:s}'.format(errorStatus.prettyPrint(),
            #                        errorIndex and varBindTable[-1][int(errorIndex) - 1] or '?')))
            print('PDU returned SNMP error: {0:s} at {1:s}'.format(error_status.prettyPrint(),
                                                                   error_index and var_bind_table[-1][
                                                                       int(error_index) - 1] or '?'))
        size = len(var_bind_table)
        if size != 1:
            raise (Exception('Wrong response data size is returned by SNMP Set command: '
                             'Received size: {}. Expected size: 1'.format(size)))
        result = var_bind_table[0][1]
        if result != state:
            raise (Exception('Wrong response data is returned by SNMP Set command: '
                             'Received value: {}. Expected value: {}'.format(result, state)))
        print("Set PSU socket status succeeded, result={}".format(result))

    def set_on(self):
        self.__set_state(OUTLET_STATE_ON)

    def set_off(self):
        self.__set_state(OUTLET_STATE_OFF)


class PduOutletFactory(object):
    def __init__(self, config=TA_OUTLET_CONFIG):
        self.config = config
        # load MIBs
        self.cmd_gen = cmdgen.CommandGenerator()
        mib_builder = self.cmd_gen.snmpEngine.msgAndPduDsp.mibInstrumController.mibBuilder
        print('Setting MIB sources...')
        mib_dir = os.path.dirname(os.path.realpath(__file__))
        mib_builder.addMibSources(builder.DirMibSource(mib_dir))
        for x in mib_builder.getMibSources():
            print(x)
        print('done')

    def get_outlet(self, outlet_name):
        outlet_descriptor = self.config[outlet_name]
        pdu_ip = outlet_descriptor['pdu_ip']
        outlet_id = outlet_descriptor['outlet_id']
        return PduOutlet(self.cmd_gen, pdu_ip, outlet_id)


def healthcheck():
    pdu_factory = PduOutletFactory()
    pdu_outlet = pdu_factory.get_outlet('TA_OUTLET_MSM8996_1')

    pdu_outlet.set_on()
    assert pdu_outlet.is_on() is True

    pdu_outlet.set_off()
    assert pdu_outlet.is_on() is False

    pdu_outlet.set_on()
    assert pdu_outlet.is_on() is True

    pdu_outlet.set_off()
    assert pdu_outlet.is_on() is False


if __name__ == '__main__':
    # Unit test
    healthcheck()