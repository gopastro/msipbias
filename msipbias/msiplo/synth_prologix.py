import socket

class Synthesizer:
    #def __init__(self, host='192.168.1.101',
    def __init__(self, host='192.168.151.110',
                 port=1234, synth_address=20):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.synth_address = synth_address
        self.set_gpib_address()
        self.idstr = self.idstring()
        
    def set_gpib_address(self):
        self.sock.send('++addr %d\n' % self.synth_address)
        # put in auto 0 mode
        self.sock.send('++auto 0\n')

    def ask(self, msg, readlen=128):
        """Send and receive something"""
        self.sock.send('%s\n' % msg)
        self.sock.send('++read eoi\n')
        ret = self.sock.recv(readlen)
        return ret.strip()

    def write(self, msg):
        """Send something"""
        self.sock.send('%s\n' % msg)
        
    def idstring(self):
        """returns ID String"""
        #elf.sock.send('*IDN?\n')
        #elf.sock.send('++read eoi\n')
        #ds = self.sock.recv(128)
        ids = self.ask('*IDN?')
        return ids

    def get_mult(self):
        """Get Frequency Multiplier"""
        self.mult = float(self.ask('FREQ:MULT?'))
        return self.mult

    def set_mult(self, multiplier):
        """ Set frequency Multiplier"""
        self.write('FREQ:MULT %d' % multiplier)
    
    def get_freq(self):
        """Get current CW frequency"""
        return float(self.ask('FREQ:CW?'))

    def set_freq(self, freq):
        """Set CW frequency in Hz"""
        if freq<1e9:
            fstr = "%s MHz" % (freq/1.e6)
        else:
            fstr = "%s GHz" % (freq/1.e9)
        self.write('FREQ:CW %s' % fstr)
  
    def get_power_level(self):
        """Get RF power level in dBm"""
        power = float(self.ask('SOUR:POW:LEVEL?'))
        print "Power = %g dBm" % power
        return power

    def set_power_level(self, power):
        """Set RF power level in dBm"""
        self.write('SOUR:POW:LEVEL %s' % power)

    def output_status(self):
        """returns output status of RF signal"""
        op = int(self.ask("OUTPUT:STATE?"))
        if op == 1:
            return "ON"
        else:
            return "OFF"

    def output_off(self):
        "Turn RF output off"""
        self.write("OUTPUT:STATE OFF")

    def output_on(self):
        "Turn RF output on"""
        self.write("OUTPUT:STATE ON")

    def close(self):
        self.sock.close()
        
