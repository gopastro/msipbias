from cheetah_py import *
import sys

def freq_word(frequency):
    if frequency < 18:
        return 0x00, 0x00
    if frequency > 26.5:
        return 0xff, 0xff
    step = (26.5 - 18)/(2**16 - 1)
    b = int((frequency - 18.0)/step)
    lsb = b & 0x00ff
    msb = (b &0xff00) >> 8
    return (msb, lsb)

def send_bytes(handle, byte0, byte1, debug=True):
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
    if debug:
        print "Sent %s" % data_out

def send_frequency(handle, frequency, debug=True):
    msb, lsb = freq_word(frequency)
    send_bytes(handle, msb, lsb, debug=debug)

class MicroLambda(object):
    def __init__(self, debug=True):
        self.debug = debug
        self.find_devices()
        self.open_first_cheetah()
        self.configure_cheetah()

    def find_devices(self):
        # Find all the attached devices
        (self.numdevices, self.ports, self.unique_ids) = ch_find_devices_ext(16, 16)

        if self.numdevices > 0:
            if self.debug:
                print "%d device(s) found:" % self.numdevices

            # Print the information on each device
            for i in range(self.numdevices):
                port      = self.ports[i]
                unique_id = self.unique_ids[i]

                # Determine if the device is in-use
                inuse = "(avail)"
                if (port & CH_PORT_NOT_FREE):
                    inuse = "(in-use)"
                    port  = port & ~CH_PORT_NOT_FREE
                
                # Display device port number, in-use status, and serial number
                if self.debug:
                    print "    port = %d   %s  (%04d-%06d)" % \
                        (port, inuse, unique_id / 1000000, unique_id % 1000000)
                uid = "%04d-%06d" % (unique_id / 1000000, unique_id % 1000000)
                if uid == '1364-095363':
                    self.port = self.ports[i] # pick the first one
                    if self.debug:
                        print "Picking Port %d as the correct port for MSIP LO cheetah" % i
        else:
            print "No devices found."

    def open_first_cheetah(self):
        # Open the device
        self.handle = ch_open(self.port)
        if (self.handle <= 0):
            print "Unable to open Cheetah device on port %d" % self.port
            print "Error code = %d (%s)" % (self.handle, ch_status_string(self.handle))
            sys.exit(1)

        if self.debug:
            print "Opened Cheetah device on port %d" % self.port

        ch_host_ifce_speed_string = ""

        if (ch_host_ifce_speed(self.handle)):
            ch_host_ifce_speed_string = "high speed"
        else:
            ch_host_ifce_speed_string = "full speed"
        if self.debug:
            print "Host interface is %s" % ch_host_ifce_speed_string

    def configure_cheetah(self):
        # Ensure that the SPI subsystem is configured
        ch_spi_configure(self.handle, CH_SPI_POL_FALLING_RISING,
                         CH_SPI_PHASE_SETUP_SAMPLE,
                         CH_SPI_BITORDER_MSB, 0x0)
        if self.debug:
            print "SPI configuration set, clock idle high, LSB shift, SS[2:0] active low" 
        sys.stdout.flush()

        bitrate = 10000
        # Set the bitrate
        bitrate = ch_spi_bitrate(self.handle, bitrate)
        if self.debug:
            print "Bitrate set to %d kHz" % bitrate
        sys.stdout.flush()
    
    def set_frequency(self, frequency):
        send_frequency(self.handle, frequency, debug=self.debug)

    def close_cheetah(self):
        ch_close(self.handle)



