from cheetah_py import *
import sys
import time
from scipy import interpolate
import numpy
import pkg_resources
import cStringIO
from msipbias.utils import MSIPGeneralError

def binspace(number):
    s = bin(number)
    strs = []
    l = len(s)
    for i in range(l/4):
        if i == 0:
            strs.append(s[-4:])
        else:
            strs.append(s[-4*(i+1):-4*i])
    return ' '.join(reversed(strs))

# Command Mnemonics 0x0x for pol 0
# and 0x1x for pol 1 
DAC1_RESET_STROBE = 0x00   #Databit 1
DAC2_RESET_STROBE = 0x01   #Databit 1
DAC1_CLEAR_STROBE = 0x02   #Databit 1
ADC_CONVERT_STROBE = 0x03
DAC1_DATA_WRITE = 0x04
DAC2_DATA_WRITE = 0x05
ADC_DATA_READ = 0x06
MODE_10MHZ = 0x07
AREG_PARALLEL_WRITE = 0x08
BREG_PARALLEL_WRITE = 0x09
PARALLEL_READ = 0x0A

# AREG bytes
AREG = {
    'SELECT_LNA_VI' : int('0000 0000 0000'.replace(' ', ''), 2),
    'SELECT_SIS1_V' : int('0000 1000 0000'.replace(' ', ''), 2),
    'SELECT_SIS1_I' : int('0001 0000 0000'.replace(' ', ''), 2),
    'SELECT_SIS2_V' : int('0001 1000 0000'.replace(' ', ''), 2),
    'SELECT_SIS2_I' : int('0010 0000 0000'.replace(' ', ''), 2),
    'SELECT_MAGNET1_V' : int('0010 1000 0000'.replace(' ', ''), 2),
    'SELECT_MAGNET1_I' : int('0011 0000 0000'.replace(' ', ''), 2),
    'SELECT_MAGNET2_V' : int('0011 1000 0000'.replace(' ', ''), 2),
    'SELECT_MAGNET2_I' : int('0100 0000 0000'.replace(' ', ''), 2),
    'SELECT_HEATER_I' : int('0100 1000 0000'.replace(' ', ''), 2),
    'SELECT_TEMPERATURE' : int('0101 0000 0000'.replace(' ', ''), 2),

    'SELECT_TEMPERATURE_1' : int('0101 0000 0000'.replace(' ', ''), 2),
    'SELECT_TEMPERATURE_2' : int('0101 0010 0000'.replace(' ', ''), 2),
    'SELECT_TEMPERATURE_3' : int('0101 0100 0000'.replace(' ', ''), 2),

    'SELECT_LNA1_STAGE1_VD' : int('0000 0001 0000'.replace(' ', ''), 2),
    'SELECT_LNA1_STAGE2_VD' : int('0000 0001 0001'.replace(' ', ''), 2),
    'SELECT_LNA1_STAGE3_VD' : int('0000 0001 0010'.replace(' ', ''), 2),
    
    'SELECT_LNA1_STAGE1_ID' : int('0000 0001 0100'.replace(' ', ''), 2),
    'SELECT_LNA1_STAGE2_ID' : int('0000 0001 0101'.replace(' ', ''), 2),
    'SELECT_LNA1_STAGE3_ID' : int('0000 0001 0110'.replace(' ', ''), 2),
    
    'SELECT_LNA1_STAGE1_VG' : int('0000 0001 1000'.replace(' ', ''), 2),
    'SELECT_LNA1_STAGE2_VG' : int('0000 0001 1001'.replace(' ', ''), 2),
    'SELECT_LNA1_STAGE3_VG' : int('0000 0001 1010'.replace(' ', ''), 2),

    'SELECT_LNA2_STAGE1_VD' : int('0000 0001 1100'.replace(' ', ''), 2),
    'SELECT_LNA2_STAGE2_VD' : int('0000 0001 1101'.replace(' ', ''), 2),
    'SELECT_LNA2_STAGE3_VD' : int('0000 0001 1110'.replace(' ', ''), 2),
    
    'SELECT_LNA2_STAGE1_ID' : int('0000 0000 0000'.replace(' ', ''), 2),
    'SELECT_LNA2_STAGE2_ID' : int('0000 0000 0001'.replace(' ', ''), 2),
    'SELECT_LNA2_STAGE3_ID' : int('0000 0000 0010'.replace(' ', ''), 2),
    
    'SELECT_LNA2_STAGE1_VG' : int('0000 0000 0100'.replace(' ', ''), 2),
    'SELECT_LNA2_STAGE2_VG' : int('0000 0000 0101'.replace(' ', ''), 2),
    'SELECT_LNA2_STAGE3_VG' : int('0000 0000 0110'.replace(' ', ''), 2),
    }

dac1_drain_voltage_channel_selection = {
    # keys are a tuple - (lna, stage)
    # where lna goes from 1 to 3
    # and stage goes from 1 to 3
    # LNA 1
    (1, 1): 0,
    (1, 2): 1,
    (1, 3): 2,
    # LNA 2
    (2, 1): 4,
    (2, 2): 5,
    (2, 3): 6
    }

dac1_drain_current_channel_selection = {
    # keys are a tuple - (lna, stage)
    # where lna goes from 1 to 3
    # and stage goes from 1 to 3
    # LNA 1
    (1, 1): 8,
    (1, 2): 9,
    (1, 3): 10,
    # LNA 2
    (2, 1): 12,
    (2, 2): 13,
    (2, 3): 14
    }


# Addresses for DAC2 devices
SIS1_VOLTAGE_ADDRESS_DAC2 = 0 << 22
SIS2_VOLTAGE_ADDRESS_DAC2 = 1 << 22
MAGNET1_CURRENT_ADDRESS_DAC2 = 2 << 22
MAGNET2_CURRENT_ADDRESS_DAC2 = 3 << 22

def space_bin(num):
    """Helper function to show a number in binary format
    in 4 bits at a time
    """
    s = bin(num)
    L = len(s)
    diff = (L - 2) % 8
    if diff != 0:
        s = s[:2] + (diff+2) * '0' + s[2:]
    if (len(s) - 2) % 8 == 0:
        n = '0b '
        for i in range((len(s)-8)/8):
            n += s[2+i*8:2+(i+1)*8]
            n += ' '
    return n


def testBit(int_type, offset):
    mask = 1 << offset
    return (int_type & mask)

def setBit(int_type, offset):
    mask = 1 << offset
    return (int_type | mask)

def clearBit(int_type, offset):
    mask = ~(1 << offset)
    return (int_type & mask)

def cmd_by_polar(cmd, polar=0):
    if polar == 0:
        cmd = clearBit(cmd, 4)
    if polar == 1:
        cmd = setBit(cmd, 4)
    return cmd

# BREG values
def breg_lna_bias_enable(breg, lna_number):
    """
    lna_number should be 1 or 2
    Enables the LNA bias
    Returns the BREG value for this
    """
    if lna_number == 2:
        breg = setBit(breg, 4)
    elif lna_number == 1:
        breg = setBit(breg, 5)
    return breg

def breg_lna_bias_disable(breg, lna_number):
    """
    lna_number should be 1 or 2
    Enables the LNA bias
    Returns the BREG value for this
    """
    if lna_number == 2:
        breg = clearBit(breg, 4)
    elif lna_number == 1:
        breg = clearBit(breg, 5)
    return breg

def breg_hemt_led_on(breg):
    breg = setBit(breg, 1)
    return breg

def breg_hemt_led_off(breg):
    breg = clearBit(breg, 1)
    return breg

def breg_mixer_heater_on(breg):
    breg = setBit(breg, 0)
    return breg

def breg_mixer_heater_off(breg):
    breg = clearBit(breg, 0)
    return breg

def breg_mixer_bias_closed_loop(breg, sis=1):
    if sis == 1:
        breg = clearBit(breg, 3)
    elif sis == 2:
        breg = clearBit(breg, 2)
    return breg

def breg_mixer_bias_open_loop(breg, sis=1):
    if sis == 1:
        breg = setBit(breg, 3)
    elif sis == 2:
        breg = setBit(breg, 2)
    return breg

def get_sis_mixer_voltage(dword):
    """mV"""
    return 50.*(float(dword)/float(65536))

def get_sis_mixer_current(dword, Rs=5.):
    """mA"""
    return 20.*(float(dword)/float(65536))/Rs

def get_magnet_voltage(dword):
    """V"""
    return 10.*(float(dword)/float(65536))

def get_magnet_current(dword):
    """mA"""
    return 250.*(float(dword)/float(65536))

def get_lna_drain_voltage(dword):
    """V"""
    return 10.*(float(dword)/float(65536))

def get_lna_drain_current(dword):
    """mA"""
    return 100.*(float(dword)/float(65536))

def get_lna_gate_voltage(dword):
    """V"""
    return 10.*(float(dword)/float(65536))

def get_heater_current(dword):
    """mA"""
    return 606.*(float(dword)/float(65536))

def get_temperature_sensor_voltage(dword):
    """Returns Volts; but use manafacturer data sheet to get 
    K
    """
    return 10.*(float(dword)/float(65536))

def set_sis_mixer_voltage_word(Vj):
    """Returns Word for DAC2. Vj in mV"""
    return int(((Vj/50.) + 0.5) * 65536) & 0xFFFF

def set_magnet_current_word(Imag):
    """Returns word for DAC2; Imag in mA"""
    return int(((Imag/250.) + 0.5)*65536) & 0xFFFF

def set_lna_drain_voltage_word(Vd):
    """Returns word for DAC1; Vd in V"""
    return int((Vd/5.)*16384) & 0x3FFF

def set_lna_drain_current_word(Id):
    """Returns word for DAC1; Id in mA"""
    return int((Id/50.)*16384) & 0x3FFF

def get_magnet_current_bytes(Imag, magnet=1):
    if magnet == 1:
        dacaddress = MAGNET1_CURRENT_ADDRESS_DAC2
    elif magnet == 2:
        dacaddress = MAGNET2_CURRENT_ADDRESS_DAC2
    dacaddress = clearBit(dacaddress, 21)
    dacnumber = (dacaddress & 0xff0000) + \
                (set_magnet_current_word(Imag) & 0xffff)
    byte2 = (dacnumber & 0xFF0000) >> 16
    byte1 = (dacnumber & 0x00FF00) >> 8
    byte0 = (dacnumber & 0x0000FF)
    return [byte2, byte1, byte0]

def get_sis_voltage_bytes(Vj, sis=1):
    if sis == 1:
        dacaddress = SIS1_VOLTAGE_ADDRESS_DAC2
    elif sis == 2:
        dacaddress = SIS2_VOLTAGE_ADDRESS_DAC2
    dacaddress = clearBit(dacaddress, 21)
    dacnumber = (dacaddress & 0xff0000) + \
                (set_sis_mixer_voltage_word(Vj) & 0xffff)
    byte2 = (dacnumber & 0xFF0000) >> 16
    byte1 = (dacnumber & 0x00FF00) >> 8
    byte0 = (dacnumber & 0x0000FF)
    return [byte2, byte1, byte0]    

def get_lna_drain_voltage_bytes(Vd, lna=1, stage=1):
    channel = dac1_drain_voltage_channel_selection[(lna, stage)]
    #print channel
    # below 3 << 14 selects 1,1 for  REG1 and REG0 which are  in bits 14 & 15
    dacnumber = (((channel & 0xff) << 16) & 0xff0000) + \
                 (((3 << 14) & 0xffff) + (set_lna_drain_voltage_word(Vd) & 0x3fff))
    dacnumber = clearBit(dacnumber, 22)
    #dacnumber = dacnumber << 3  # Test to see if 26bytes is correct rather than 29
    #print dacnumber
    byte2 = (dacnumber & 0xFF0000) >> 16
    byte1 = (dacnumber & 0x00FF00) >> 8
    byte0 = (dacnumber & 0x0000FF)
    return [byte2, byte1, byte0]

def get_lna_drain_current_bytes(Id, lna=1, stage=1):
    channel = dac1_drain_current_channel_selection[(lna, stage)]
    #print channel
    # below 3 << 14 selects 1,1 for  REG1 and REG0 which are  in bits 14 & 15
    dacnumber = (((channel & 0xff) << 16) & 0xff0000) + \
                 (((3 << 14) & 0xffff) + (set_lna_drain_current_word(Id) & 0x3fff))
    dacnumber = clearBit(dacnumber, 22)
    #print dacnumber
    byte2 = (dacnumber & 0xFF0000) >> 16
    byte1 = (dacnumber & 0x00FF00) >> 8
    byte0 = (dacnumber & 0x0000FF)
    return [byte2, byte1, byte0]


def shift_bytes(bytes, shift=True):
    """
    Asuuming 5-bit command is always byte 0, we shift left by 3 bits the 
    entire number
    """
    if shift:
        outnumber = 0
        numbytes = len(bytes)
        for i in range(numbytes):
            outnumber += bytes[i] << ((numbytes - i -1)*8)
        outnumber = outnumber << 3
        outbytes = []
        for i in range(numbytes):
            outbytes.append((outnumber & (0xff << ((numbytes - i - 1)*8))) >> (numbytes - i - 1)*8)
        return outbytes
    else:
        return bytes
        
def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val    

def decode_adc_bytes(bytes):
    """
    Decodes the three bytes associated with an ADC data read
    operation.
    First byte has lowest 2 bits that are readable
    Second byte has all 8 bits
    Third byte has highest 6 bits
    """
    return ((bytes[0] & 0x03) << 14) + (bytes[1] << 6) + ((bytes[2] & 0xfc) >> 2)

def decode_adc_bytes2(bytes):
    """
    Decodes the three bytes associated with an ADC data read
    operation.
    First byte has lowest 1 bits that are readable
    Second byte has all 8 bits
    Third byte has highest 7 bits
    """
    return ((bytes[0] & 0x01) << 15) + (bytes[1] << 7) + ((bytes[2] & 0xfc) >> 1)

def is_adc_ready(byte):
    return bool((byte & 0x04) >> 2)

def is_dac1_ready(byte):
    return bool((byte & 0x02)>> 1)

class CheetahDevice(object):
    def __init__(self):
        pass

class BiasModule(object):
    def __init__(self, debug=False, gui_logger=None):
        self.debug = debug
        self.gui_logger = gui_logger
        self.gui_logger_pause = False
        self.error_code = ''
        self.device_info = []
        self.find_devices()
        self.open_first_cheetah()
        self.configure_cheetah()
        self.breg = 0x00
        self.curve10 = self.load_curve10_data()  # DT470 Curve 10
        self.curve600 = self.load_curve600_data()  # DT670 Curve 600
        # lna_bias_enabled: tuple of (polar, lna_number)
        self.lna_bias_enabled = {(0, 1): False,
                                 (0, 2): False,
                                 (1, 1): False,
                                 (1, 2): False
                                 }
        # sis_ivmode: tuple of (polar, sis_number)
        self.sis_ivmode = {(0, 1): 'Closed',
                           (0, 2): 'Closed',
                           (1, 1): 'Closed',
                           (1, 2): 'Closed'
                           }
        self.temperature_sensor_type = {(0, 1): 'DT670',
                                        (0, 2): 'DT470',
                                        (0, 3): 'DT670',
                                        (1, 1): 'DT670',
                                        (1, 2): 'DT470',
                                        (1, 3): 'DT670'
                                        }

    def bm_print(self, text):
        if self.debug:
            print text
        if self.gui_logger is not None:
            if not self.gui_logger_pause:
                self.gui_logger(text)
        
    def load_curve10_data(self, data_file='Curve10.txt'):
        dstr = pkg_resources.resource_string(__name__, data_file)
        sio = cStringIO.StringIO(dstr)
        data = numpy.loadtxt(sio, skiprows=1)
        v, T = data[:, 1], data[:, 0]
        return interpolate.splrep(numpy.flipud(v), numpy.flipud(T), s=0)

    def load_curve600_data(self, data_file='DT600.txt'):
        dstr = pkg_resources.resource_string(__name__, data_file)
        sio = cStringIO.StringIO(dstr)
        data = numpy.loadtxt(sio, skiprows=1)
        v, T = data[:, 1], data[:, 0]
        return interpolate.splrep(numpy.flipud(v), numpy.flipud(T), s=0)    
    
    def find_devices(self):
        # Find all the attached devices
        (self.numdevices, self.ports, self.unique_ids) = ch_find_devices_ext(16, 16)

        if self.numdevices > 0:
            self.bm_print("%d device(s) found:" % self.numdevices)

            # Print the information on each device
            for i in range(self.numdevices):
                dev = CheetahDevice()
                port      = self.ports[i]
                dev.port = port
                unique_id = self.unique_ids[i]
                dev.unique_id = unique_id
                
                # Determine if the device is in-use
                inuse = "(avail)"
                if (port & CH_PORT_NOT_FREE):
                    inuse = "(in-use)"
                    port  = port & ~CH_PORT_NOT_FREE
                dev.inuse = inuse
                dev.serial_number = "%04d-%06d" % (unique_id / 1000000, unique_id % 1000000)
                # Display device port number, in-use status, and serial number
                self.bm_print("    port = %d   %s  (%04d-%06d)" % \
                    (port, inuse, unique_id / 1000000, unique_id % 1000000))
                self.device_info.append(dev)
                uid = "%04d-%06d" % (unique_id / 1000000, unique_id % 1000000)
                if uid == '1364-087103':
                    self.port = self.ports[i] # pick the first one
                    self.bm_print("Choosing device %d as SIS bias control Cheetah device" % i)
        else:
            self.bm_print("No devices found.")
            raise MSIPGeneralError("CheetahUSB", "No Cheetah USB devices found")

    def open_first_cheetah(self):
        # Open the device
        try:
            self.handle = ch_open(self.port)
            if (self.handle <= 0):
                self.bm_print("Unable to open Cheetah device on port %d" % self.port)
                self.bm_print("Error code = %d (%s)" % (self.handle, ch_status_string(self.handle)))
                self.error_code = "Error code = %d (%s)" % (self.handle, ch_status_string(self.handle))
                raise MSIPGeneralError("CheetahUSB", "Unable to open Cheetah Device on port %d.\n Error code = %d (%s)" % (self.port, self.handle, ch_status_string(self.handle)))

            self.bm_print("Opened Cheetah device on port %d" % self.port)

            ch_host_ifce_speed_string = ""

            if (ch_host_ifce_speed(self.handle)):
                ch_host_ifce_speed_string = "high speed"
            else:
                ch_host_ifce_speed_string = "full speed"

            self.bm_print("Host interface is %s" % ch_host_ifce_speed_string)
            self.interface = ch_host_ifce_speed_string
            sys.stdout.flush()
        except:
            raise MSIPGeneralError("CheetahUSB", "Error opening Cheetah USB device")
        
    def configure_cheetah(self):
        # Ensure that the SPI subsystem is configured
        ch_spi_configure(self.handle, CH_SPI_POL_FALLING_RISING,
                         CH_SPI_PHASE_SETUP_SAMPLE,
                         CH_SPI_BITORDER_MSB, 0x0)
        self.bm_print("SPI configuration set, clock idle high, LSB shift, SS[2:0] active low" )
        sys.stdout.flush()

        bitrate = 10000
        # Set the bitrate
        bitrate = ch_spi_bitrate(self.handle, bitrate)
        self.bm_print("Bitrate set to %d kHz" % bitrate)
        sys.stdout.flush()

    def test_delay(self, cycles):
        data_in = array('B', [0 for i in range(1)])
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        ch_spi_queue_ss(self.handle, 1)
        #numcycles = ch_spi_queue_delay_cycles(self.handle, cycles)
        ch_spi_queue_byte(self.handle, 1, 0xaa)
        #ch_spi_queue_delay_ns(self.handle, 200)
        #ch_spi_queue_byte(self.handle, 1, 0x0)
        ch_spi_queue_ss(self.handle, 0)
        (count, data_in) = ch_spi_batch_shift(self.handle, 0)
        return count, data_in

    def test_async(self):
        # make a simple queue to just assert OE
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        ch_spi_batch_shift(self.handle, 0)

        data_out = array('B', [0 for i in range(1)])
        # queue the batch
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_ss(self.handle, 1)
        #numcycles = ch_spi_queue_delay_cycles(self.handle, cycles)
        data_out[0] = 0xd0
        #data_out[1] = 0x00
        ch_spi_queue_array(self.handle, data_out)
        ch_spi_queue_ss(self.handle, 0x0)


        ch_spi_async_submit(self.handle)
        # Collect batch the last batch.
        (ret, data_in) = ch_spi_async_collect(self.handle, 2)
        return ret, data_in

        
    def send_command(self, bytes, wait_cycles=8, shift=True):
        #print wait_cycles
        data_out = array('B', [0 for i in range(len(bytes))])
        sbytes = shift_bytes(bytes, shift=shift)
        for i, byte in enumerate(sbytes):
            data_out[i] = byte
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        # set slave select to deasserted state in case it was left low
        # from a previous interrupted transaction
        #ch_spi_queue_ss(self.handle, 0)
        ch_spi_queue_ss(self.handle, 1)
        #ch_spi_queue_byte(handle, 1, 0xFF)
        ch_spi_queue_array(self.handle, data_out)
        #for i, byte in enumerate(sbytes):
        #    ch_spi_queue_byte(self.handle, 1, byte)
        #dly = ch_spi_queue_delay_cycles(self.handle, 16)
        #print "Delayed by %d clock cycles" % dly
        #sys.stdout.flush()
        #ns = ch_spi_queue_delay_ns(self.handle, 250000)
        #print "  Queued delay of %d ns" % ns

        #time.sleep(0.1)
        #ch_spi_queue_ss(self.handle, 0)
        ch_spi_batch_shift(self.handle, 0)
        self.bm_print("Sent %s " % data_out)
        sys.stdout.flush()
        # clear the state of the bus
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_ss(self.handle, 0)
        ch_spi_queue_ss(self.handle, 1)
        ch_spi_queue_oe(self.handle, 0)
        ch_spi_batch_shift(self.handle, 0)

    def send_async_command(self, bytes, wait_cycles=8):
        data_out = array('B', [0 for i in range(len(bytes))])
        sbytes = shift_bytes(bytes)
        for i, byte in enumerate(sbytes):
            data_out[i] = byte
        # make a simple queue to just assert OE
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        ch_spi_batch_shift(self.handle, 0)

        # queue the batch
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_ss(self.handle, 1)

        ch_spi_queue_array(self.handle, data_out)
        ch_spi_queue_ss(self.handle, 0x0)

        ch_spi_async_submit(self.handle)
        # Collect batch the last batch.
        (ret, data_in) = ch_spi_async_collect(self.handle, 0)
        self.bm_print("Sent %s " % data_out)
        sys.stdout.flush()
        return ret, data_in
        

    def send_and_receive_command(self, bytes, num_bytes, wait_cycles=8):
        data_out = array('B', [0 for i in range(len(bytes))])
        data_in = array('B', [0 for i in range(num_bytes)])
        for i, byte in enumerate(bytes):
            data_out[i] = byte
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        ch_spi_queue_ss(self.handle, 0x1)
        #ch_spi_queue_byte(handle, 1, 0xFF)
        #ch_spi_queue_array(self.handle, data_out)
        for i, byte in enumerate(bytes):
            ch_spi_queue_byte(self.handle, 1, byte)
        dly = ch_spi_queue_delay_cycles(self.handle, wait_cycles)
        self.bm_print( "Delayed by %d clock cycles" % dly)
        sys.stdout.flush()
        #ns = ch_spi_queue_delay_ns(self.handle, 250000)
        #print "  Queued delay of %d ns" % ns

        time.sleep(0.1)
        ch_spi_queue_ss(self.handle, 0)
        data_in = ch_spi_batch_shift(self.handle, num_bytes)
        self.bm_print( "Sent %s" % data_out)
        return data_in
    
    def set_10MHz_mode(self, polar=0):
        self.send_async_command([cmd_by_polar(MODE_10MHZ, polar)])

    def parallel_read(self, polar=0):
        cmd = PARALLEL_READ
        if polar == 0:
            cmd = clearBit(cmd, 4)
        elif polar == 1:
            cmd = setBit(cmd, 4)
        data_in = array('B', [0])
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        ch_spi_queue_ss(self.handle, 0)
        ch_spi_queue_ss(self.handle, 0x1)
        #ch_spi_queue_byte(handle, 1, 0xFF)
        ch_spi_queue_byte(self.handle, 1, cmd<<3)
        ch_spi_queue_byte(self.handle, 1, 0x00)
        ch_spi_queue_delay_cycles(self.handle, 8)
        #ch_spi_queue_ss(self.handle, 0)
        self.bm_print( "Sent cmd %s" % (cmd << 3))
        sys.stdout.flush()
        (count, data_in) = ch_spi_batch_shift(self.handle, 2)
        #if count == 1:
        #print count, data_in
        sys.stdout.flush()
        return data_in

    def set_magnet_current(self, Imag, magnet=1, polar=0):
        bytes = get_magnet_current_bytes(Imag, magnet=magnet)
        #self.send_command([
        cmd = [cmd_by_polar(DAC2_DATA_WRITE, polar)]
        cmd.extend(bytes)
        self.send_command(cmd, wait_cycles=48)
        #ch_spi_queue_delay_cycles(self.handle, 6)
        #self.send_command(bytes, wait_cycles=36)

    def reset_dac1(self, polar=0):
        cmd = [cmd_by_polar(DAC1_RESET_STROBE, polar)]
        self.send_command(cmd, wait_cycles=6)

    def reset_dac2(self, polar=0):
        cmd = [cmd_by_polar(DAC2_RESET_STROBE, polar)]
        self.send_command(cmd, wait_cycles=6)
        
    def clear_dac1(self, polar=0):
        cmd = [cmd_by_polar(DAC1_CLEAR_STROBE, polar)]
        self.send_command(cmd, wait_cycles=6)

    def adc_convert_strobe(self, polar=0):
        self.send_command([cmd_by_polar(ADC_CONVERT_STROBE, polar)])

    # def shift_breg_parallel_bytes(self, cmd, breg):
    #     number = ((cmd << 8) & 0x1F00) + (breg & 0xFF)
    #     binword = bin(number)
    #     byte0 = int(binword[2:10], 2)
    #     byte1 = int((binword[10:]+'000'), 2)
    #     return [byte0, byte1]

    def sis_closed_loop(self, sis=1, polar=0):
        self.breg = breg_mixer_bias_closed_loop(self.breg, sis=sis)
        cmd = self.shift_breg_parallel_bytes(cmd_by_polar(BREG_PARALLEL_WRITE, polar),
                                             self.breg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.bm_print( "Operating SIS Mixer in Closed Loop: polar: %d, sis: %d" % (polar, sis))
        self.sis_ivmode[(polar, sis)] = 'Closed'

    def sis_open_loop(self, sis=1, polar=0):
        self.breg = breg_mixer_bias_open_loop(self.breg, sis=sis)
        cmd = self.shift_breg_parallel_bytes(cmd_by_polar(BREG_PARALLEL_WRITE, polar),
                                             self.breg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.bm_print( "Operating SIS Mixer in Open Loop: polar: %d, sis: %d" % (polar, sis))
        self.sis_ivmode[(polar, sis)] = 'Open'
        
    def lna_enable(self, lna=1, polar=0):
        self.breg = breg_lna_bias_enable(self.breg, lna_number=lna)
        cmd = self.shift_breg_parallel_bytes(cmd_by_polar(BREG_PARALLEL_WRITE, polar),
                                             self.breg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.bm_print( "Enabling LNA Bias: polar: %d, lna: %d" % (polar, lna))
        self.lna_bias_enabled[(polar, lna)] = True

    def lna_disable(self, lna=1, polar=0):
        self.breg = breg_lna_bias_disable(self.breg, lna_number=lna)
        cmd = self.shift_breg_parallel_bytes(cmd_by_polar(BREG_PARALLEL_WRITE, polar),
                                             self.breg)
        self.send_command(cmd, wait_cycles=18, shift=False)        
        self.lna_bias_enabled[(polar, lna)] = False
    
    def lna_enabled(self, lna=1, polar=0):
        """
        Check to see if LNA bias is enabled
        """
        return self.lna_bias_enabled[(polar, lna)]
    
    def mixer_heater_control_on(self, polar=0):
        self.breg = breg_mixer_heater_on(self.breg)
        cmd = [cmd_by_polar(BREG_PARALLEL_WRITE, polar)]
        cmd.append(self.breg)
        self.send_command(cmd, wait_cycles=18)

    def mixer_heater_control_off(self, polar=0):
        self.breg = breg_mixer_heater_off(self.breg)
        cmd = [cmd_by_polar(BREG_PARALLEL_WRITE, polar)]
        cmd.append(self.breg)
        self.send_command(cmd, wait_cycles=18)

    def hemt_led_control_on(self, polar=0):
        #print self.breg
        self.breg = breg_hemt_led_on(self.breg)
        #print self.breg
        #cmd = [cmd_by_polar(BREG_PARALLEL_WRITE, polar)]
        #cmd.append(self.breg)
        cmd = self.shift_breg_parallel_bytes(cmd_by_polar(BREG_PARALLEL_WRITE, polar),
                                             self.breg)
        #cmd = [cmd_by_polar(BREG_PARALLEL_WRITE, polar), self.breg]
        self.send_command(cmd, wait_cycles=18, shift=False)

    def hemt_led_control_off(self, polar=0):
        self.breg = breg_hemt_led_off(self.breg)
        #cmd = [cmd_by_polar(BREG_PARALLEL_WRITE, polar)]
        #cmd.append(self.breg)
        cmd = self.shift_breg_parallel_bytes(cmd_by_polar(BREG_PARALLEL_WRITE, polar),
                                             self.breg)
        #cmd = [cmd_by_polar(BREG_PARALLEL_WRITE, polar), self.breg]        
        self.send_command(cmd, wait_cycles=18, shift=False)
        #self.send_command(cmd, wait_cycles=18, shift=False)                
        
    def adc_data_read(self, polar=0):
        cmd = [cmd_by_polar(ADC_DATA_READ, polar)]
        data_in = array('B', [0 for i in range(3)])
        data_in2 = array('B', [0 for i in range(3)])
        ch_spi_queue_clear(self.handle)
        ch_spi_queue_oe(self.handle, 1)
        ch_spi_queue_ss(self.handle, 0x1)
        #ch_spi_queue_byte(handle, 1, 0xFF)
        ch_spi_queue_byte(self.handle, 1, cmd[0] << 3)
        ch_spi_queue_byte(self.handle, 1, 0x0)
        ch_spi_queue_byte(self.handle, 1, 0x0)
        #ch_spi_queue_byte(self.handle, 1, 0xff)
        #ch_spi_queue_byte(self.handle, 1, 0xff)
        #ch_spi_queue_delay_cycles(self.handle, 80)
        ch_spi_queue_ss(self.handle, 0)
        #ch_spi_queue_byte(self.handle, 1, 0x00)
        (count, data_in) = ch_spi_batch_shift(self.handle, 3)
        #if count == 1:
        self.bm_print( "Sent cmd %s" % (cmd[0] << 3))
        #print count, data_in
        sys.stdout.flush()
        #ch_spi_queue_clear(self.handle)
        #ch_spi_queue_oe(self.handle, 1)
        #ch_spi_queue_ss(self.handle, 0)
        #(count2, data_in2) = ch_spi_batch_shift(self.handle, 2)
        #print count2, data_in2
        #ch_spi_queue_clear(self.handle)
        #ch_spi_queue_ss(self.handle, 0x0)
        #
        #ch_spi_batch_shift(self.handle, 0)
        return data_in

    def shift_areg_parallel_output_bytes(self, cmd, areg):
        number = ((cmd << 12) & 0x1F000) + (areg & 0xFFF)
        binword = bin(number)
        #binword should have length 19 = prefix 0b+ 5 cmd bits + 12 areg
        #if not prepend number of zeros
        if len(binword) < 19:
            diff = 19 - len(binword)
            binword = binword[:2] + '0'*diff + binword[2:]
        byte0 = int(binword[2:10], 2)
        byte1 = int(binword[10:18], 2)
        byte2 = int((binword[18:] + '0000000'), 2)
        return [byte0, byte1, byte2]

    def shift_breg_parallel_bytes(self, cmd, breg):
        number = ((cmd << 11) & 0xF800) + ((breg & 0xFF) << 3)
        binword = bin(number)
        # binword should have length 18 = prefix 0b + 16bits
        if len(binword) < 18:
            diff = 18 - len(binword)
            binword = binword[:2] + '0'*diff + binword[2:]
        byte0 = int(binword[2:10], 2)
        #print "0x%x" % byte0
        byte1 = int(binword[10:], 2)
        #print "0x%x" % byte1
        return [byte0, byte1]

    def check_adc_ready(self, polar=0):
        """
        Keeps checking ADC until it is ready
        """
        adc_ready = False
        ct = 0
        while not adc_ready:
            din = self.parallel_read(polar=polar)
            if is_adc_ready(din[0]):
                adc_ready = True    
            ct += 1
            time.sleep(0.001)
        self.bm_print( "ADC Ready after %d parallel reads" % ct)
        return
    
    def get_magnet_voltage(self, magnet=1, polar=0):
        """
        Getting the magnet voltage through the ADC
        """
        self.areg = AREG['SELECT_MAGNET%d_V' % magnet]
        #cmd = [cmd_by_polar(AREG_PARALLEL_WRITE, polar)]
        #cmd.append(self.areg)
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        # adc_ready = False
        # while not adc_ready:
        #     din = self.parallel_read(polar=polar)
        #     if is_adc_ready(din[0]):
        #         adc_ready = True
        self.adc_convert_strobe(polar=polar)
        #adc_ready = False
        #while not adc_ready:
         #   din = self.parallel_read(polar=polar)
        #    if is_adc_ready(din[0]):
         #       adc_ready = True
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_magnet_voltage(dword)
    
    def get_magnet_current(self, magnet=1, polar=0):
        """
        Getting the magnet voltage through the ADC
        """
        self.areg = AREG['SELECT_MAGNET%d_I' % magnet]
        #cmd = [cmd_by_polar(AREG_PARALLEL_WRITE, polar)]
        #cmd.append(self.areg)
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        # adc_ready = False
        # while not adc_ready:
        #     din = self.parallel_read(polar=polar)
        #     if is_adc_ready(din[0]):
        #         adc_ready = True
        self.adc_convert_strobe(polar=polar)
        # adc_ready = False
        # while not adc_ready:
        #     din = self.parallel_read(polar=polar)
        #     if is_adc_ready(din[0]):
        #         adc_ready = True
        time.sleep(0.001)        
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        return get_magnet_current(dword)
        
    def _get_temp_sensor_voltage(self, sensor=1, polar=0):
        """
        Getting the temperature sensor voltage through the ADC
        """
        self.areg = AREG['SELECT_TEMPERATURE_%d' % sensor]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.bm_print( "Sending ADC Convert Strobe")
        self.adc_convert_strobe(polar=polar)
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_temperature_sensor_voltage(dword)

    def convert_volt_to_temperature(self, sensor, polar, voltage,
                                    sensor_type=None):
        if sensor_type is None:
            sensory_type = self.temperature_sensor_type((polar, sensor))
        if sensor_type == 'DT470':
            curve = self.curve10
        else:
            curve = self.curve600
        return float(interpolate.splev(voltage, curve, der=0))
    
    def get_temperature(self, sensor=1, polar=0, sensor_type=None):
        voltage = self._get_temp_sensor_voltage(sensor=sensor, polar=polar)
        self.bm_print( "Voltage: %s V" % voltage)
        return self.convert_volt_to_temperature(sensor, polar, voltage,
                                                sensor_type=sensor_type)

    def set_sis_mixer_voltage(self, Vj, sis=1, polar=0):
        bytes = get_sis_voltage_bytes(Vj, sis=sis)
        #self.send_command([
        cmd = [cmd_by_polar(DAC2_DATA_WRITE, polar)]
        cmd.extend(bytes)
        self.send_command(cmd, wait_cycles=48)
        #ch_spi_queue_delay_cycles(self.handle, 6)
        #self.send_command(bytes, wait_cycles=36)

    def get_sis_voltage(self, sis=1, polar=0):
        """
        Getting the SIS junction voltage through the ADC
        """
        self.areg = AREG['SELECT_SIS%d_V' % sis]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.adc_convert_strobe(polar=polar)
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_sis_mixer_voltage(dword)

    def get_sis_voltage_with_checks(self, sis=1, polar=0):
        """
        Getting the SIS junction voltage through the ADC
        """
        self.areg = AREG['SELECT_SIS%d_V' % sis]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.check_adc_ready(polar=polar)
        time.sleep(0.010)
        self.adc_convert_strobe(polar=polar)
        #time.sleep(0.001)
        self.check_adc_ready(polar=polar)
        time.sleep(0.010)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_sis_mixer_voltage(dword)
    
    def get_sis_current(self, sis=1, polar=0):
        """
        Getting the SIS junction current through the ADC
        """
        self.areg = AREG['SELECT_SIS%d_I' % sis]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.adc_convert_strobe(polar=polar)
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_sis_mixer_current(dword)    
        
    def set_lna_drain_voltage(self, Vd, lna=1, stage=1, polar=0):
        if not self.lna_enabled(lna=lna, polar=polar):
            self.lna_enable(lna=lna, polar=polar)
        #din = self.parallel_read(polar=polar)
        #print is_dac1_ready(din[0])
        bytes = get_lna_drain_voltage_bytes(Vd, lna=lna, stage=stage)
        #self.send_command([
        cmd = [cmd_by_polar(DAC1_DATA_WRITE, polar)]
        cmd.extend(bytes)
        self.send_command(cmd, wait_cycles=48)
        #ch_spi_queue_delay_cycles(self.handle, 6)
        #self.send_command(bytes, wait_cycles=36)

    def set_lna_drain_current(self, Id, lna=1, stage=1, polar=0):
        if not self.lna_enabled(lna=lna, polar=polar):
            self.lna_enable(lna=lna, polar=polar)
        #din = self.parallel_read(polar=polar)
        #print is_dac1_ready(din[0])
        bytes = get_lna_drain_current_bytes(Id, lna=lna, stage=stage)
        #self.send_command([
        cmd = [cmd_by_polar(DAC1_DATA_WRITE, polar)]
        cmd.extend(bytes)
        self.send_command(cmd, wait_cycles=48)
        
    def get_lna_drain_voltage(self, lna=1, stage=1, polar=0):
        """
        Getting the LNA Drain voltage through the ADC
        """
        self.areg = AREG['SELECT_LNA_VI'] | AREG['SELECT_LNA%1d_STAGE%1d_VD' % (lna, stage)]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.adc_convert_strobe(polar=polar)
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_lna_drain_voltage(dword)

    def get_lna_drain_current(self, lna=1, stage=1, polar=0):
        """
        Getting the LNA Drain Current through the ADC
        """
        self.areg = AREG['SELECT_LNA_VI'] | AREG['SELECT_LNA%1d_STAGE%1d_ID' % (lna, stage)]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.adc_convert_strobe(polar=polar)
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_lna_drain_current(dword)

    def get_lna_gate_voltage(self, lna=1, stage=1, polar=0):
        """
        Getting the LNA Gate Voltage through the ADC
        """
        self.areg = AREG['SELECT_LNA_VI'] | AREG['SELECT_LNA%1d_STAGE%1d_VG' % (lna, stage)]
        cmd = self.shift_areg_parallel_output_bytes(cmd_by_polar(AREG_PARALLEL_WRITE, polar),
                                                    self.areg)
        self.send_command(cmd, wait_cycles=18, shift=False)
        self.adc_convert_strobe(polar=polar)
        time.sleep(0.001)
        din = self.adc_data_read(polar=polar)
        dword = twos_comp(decode_adc_bytes2(din), 16)
        self.bm_print( "DWORD: %s"  % dword)
        return get_lna_gate_voltage(dword)
        
    def close_cheetah(self):
        ch_close(self.handle)
        
def send_bytes(handle, byte0, byte1):
    data_out = array('B', [0 for i in range(2)])
    data_out[0] = byte0  # MSB
    data_out[1] = byte1  # LSB
    ch_spi_queue_clear(handle)
    ch_spi_queue_oe(handle, 1)
    ch_spi_queue_ss(handle, 0x1)
    #ch_spi_queue_byte(handle, 1, 0xFF)
    ch_spi_queue_array(handle, data_out)
    ch_spi_queue_ss(handle, 0)
    ch_spi_batch_shift(handle, 0)
    print "Sent %s" % data_out

def send_frequency(handle, frequency):
    msb, lsb = freq_word(frequency)
    send_bytes(handle, msb, lsb)
