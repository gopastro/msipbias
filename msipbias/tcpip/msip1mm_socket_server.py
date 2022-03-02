#!/usr/bin/python
"""
A class for receiving msip1mm monitor and control commands
via TCP/IP sockets
"""

import socket
import sys
import traceback
import time
#import logging
from msipbias.logging import logger
from msipbias.msipwrapper import MSIPWrapper

import SocketServer
logger.name = __name__

allowed_commands = ['lo1_freq', 'pll_status', 'chopper', 'lo_synth']

class MSIP1mmSocketServer():
    debug = 0
    status_bytes = []
    status_dict = {}

    def __init__(self, HOST='0.0.0.0', PORT=None):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if HOST:
                self.sock.bind((HOST, PORT))
            else:
                self.sock.bind((socket.gethostname(), PORT))
            self.conn = None
            self.addr = None
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.msip = MSIPWrapper(debug=True)
        except:
            self.printlog(str(self.formatExceptionInfo()))
            
    def formatExceptionInfo(self, maxTBlevel=5):
        """copied from Linux Journal article 5821"""
        cla, exc, trbk = sys.exc_info()
        excName = cla.__name__
        try:
            excArgs = exc.__dict__["args"]
        except KeyError:
            excArgs = "<no args>"
        excTb = traceback.format_tb(trbk, maxTBlevel)
        return (excName, excArgs, excTb)

    def printlog(self, *arguments):
        # if len(arguments) == 1:
        #     type=syslog.LOG_INFO
        #     msg = arguments[0]
        # else:
        #     type=arguments[0]
        #     msg=arguments[1]
        # if self.log == LOG_STDOUT:
        #     print msgtype[type], msg
        # else:
        #     syslog.syslog(type, msg)
        #print arguments
        logger.info(arguments)

    def listen(self, numconnections=10):
        self.sock.listen(numconnections)

    def accept(self):
        self.conn, self.addr = self.sock.accept()
        self.printlog("Connected by %s" % repr(self.addr))
        return True

    def recv(self, maxlen=1024):
        if self.conn:
            try:
                data = self.conn.recv(maxlen)
                return data
            except:
                self.printlog("No data")
                self.conn=None
                return None
        else:
            self.printlog("No connection")
    
    def process_msip_command(self):
        self.data = self.recv(1024)
        if not self.data:
            return False
        else:
            msg = self.data.strip().split()
            if not msg:
                self.send("No command issued\n")
                logger.error("No command sent")
                return True
            if not msg[0] in allowed_commands:
                logger.error("Request has to be one of %s" % allowed_commands)
                self.send("%s no_such_command\n" % self.data.strip())
                return True
            if msg[0] == 'pll_status':
                pll_status = self.pll_status()
                self.send("%s %s\n" % (msg[0], str(pll_status).lower()))
            elif msg[0] == 'chopper':
                if msg[1] == 'load':
                    chopper_status = self.chopper_in()
                    self.send("%s %s\n" % (msg[0], str(chopper_status).lower()))
                elif msg[1] == 'sky':
                    chopper_status = self.chopper_out()
                    self.send("%s %s\n" % (msg[0], str(chopper_status).lower()))
                elif msg[1] == 'status':
                    chopper_status = self.chopper_status()
                    self.send("%s %s\n" % (msg[0], str(chopper_status).lower()))
            elif msg[0] == 'lo1_freq':
                lock_status = self.set_lo_freq(msg[1])
                self.send("%s %s\n" % (msg[0], str(lock_status).lower()))
            elif msg[0] == 'lo_synth':
                if msg[1] == 'on':
                    lo_synth_status = self.lo_synth_RF_on()
                    self.send("%s %s\n" % (msg[0], str(lo_synth_status).lower()))
                elif msg[1] == 'off':
                    lo_synth_status = self.lo_synth_RF_off()
                    self.send("%s %s\n" % (msg[0], str(lo_synth_status).lower()))
            # elif msg[0] == 'close':
            #     self.spec_close()
            # elif msg[0] == 'snapshot':
            #     self.spec_snapshot()
            # elif msg[0] == 'snapsend':
            #     snaps = self.spec_snapsend()                                
            # #print self.data
            # logger.info("Received Data: %s" % self.data)
            # if msg[0] == 'snapsend':
            #     self.send("%s  %.2f %.2f %.2f %.2f\n" % (msg[0], snaps[0], snaps[1], snaps[2], snaps[3]))
            # else:
            #     self.send("%s DONE\n" % msg[0])
        return True

    # def config(self, mode, dump_time):
    #     specmode = spec_mode_dict.get(int(mode), 2)
    #     self.specw.config(mode=specmode, dump_time=float(dump_time))
    #     self.specw.spec.start_queue(1000)
        
        
    # def open(self, obs_num, subobs_num, scan_num, source_name, obspgm):
    #     self.specw.open(int(obs_num), int(subobs_num), int(scan_num),
    #                     source_name, obspgm)
        
    # def start(self):
    #     self.specw.start()

    # def stop(self):
    #     self.specw.stop()

    # def spec_close(self):
    #     self.specw.close()

    # def spec_snapshot(self):
    #     self.specw.snapshot()

    # def spec_snapsend(self):
    #     return self.specw.snapsend()        

    def pll_status(self):
        return self.msip.pll_status()
        
    def chopper_in(self):
        return self.msip.chopper_in()

    def chopper_out(self):
        return self.msip.chopper_out()

    def chopper_status(self):
        return self.msip.chopper_state()

    def set_lo_freq(self, freqstr):
        lo_frequency = float(freqstr)
        if (lo_frequency >= 250.0 and lo_frequency < 258.0) or (lo_frequency >= 230.0 and lo_frequency < 235.0):
            # Need to lower drain voltage for these frequencies
            print "Setting special frequency"
            self.msip = MSIPWrapper(debug=True, lo_power_voltage=0.75)
        else:
            self.msip = MSIPWrapper(debug=True)
        return self.msip.set_lo_frequency(lo_frequency)

    def lo_synth_RF_on(self):
        self.msip = MSIPWrapper(debug=True, lo_power_voltage=0.75)
        return self.msip.lo_synth_on()

    def lo_synth_RF_off(self):
        self.msip = MSIPWrapper(debug=True, lo_power_voltage=0.75)
        return self.msip.lo_synth_off()    

    def conn_close(self):
        if self.conn:
            self.conn.close()

    def send(self, msg):
        if self.conn:
            self.conn.send(msg)

    def receive_with_size(self, msglen):
        msg = ''
        while len(msg) < msglen:
            chunk = self.sock.recv(msglen-len(msg))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
        return msg

    
    def close(self):
        self.sock.close()


