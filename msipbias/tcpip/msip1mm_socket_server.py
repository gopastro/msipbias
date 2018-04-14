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

allowed_commands = ['lo_freq', 'pll_status', 'chopper_in',
                    'chopper_out', 'chopper_status']

class MSIP1mmSocketServer():
    debug = 0
    status_bytes = []
    status_dict = {}

    def __init__(self, HOST=None, PORT=None):
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
            if not msg[0] in allowed_commands:
                logger.error("Request has to be one of %s" % allowed_commands)
                return False
            if msg[0] == 'pll_status':
                pll_status = self.pll_status()
                self.send("%s DONE; %s\n" % (self.data.strip(), str(pll_status)))
            elif msg[0] == 'chopper_in':
                chopper_status = self.chopper_in()
                self.send("%s DONE; %s\n" % (self.data.strip(), str(chopper_status)))
            elif msg[0] == 'chopper_out':
                chopper_status = self.chopper_out()
                self.send("%s DONE; %s\n" % (self.data.strip(), str(chopper_status)))
            elif msg[0] == 'chopper_status':
                chopper_status = self.chopper_status()
                self.send("%s DONE; %s\n" % (self.data.strip(), str(chopper_status)))
            elif msg[0] == 'lo_freq':
                lock_status = self.set_lo_freq(msg[1])
                self.send("%s DONE; %s\n" % (self.data.strip(), str(lock_status)))
            # elif msg[0] == 'close':
            #     self.spec_close()
            # elif msg[0] == 'snapshot':
            #     self.spec_snapshot()
            # elif msg[0] == 'snapsend':
            #     snaps = self.spec_snapsend()                                
            # #print self.data
            # logger.info("Received Data: %s" % self.data)
            # if msg[0] == 'snapsend':
            #     self.send("%s DONE; %.2f %.2f %.2f %.2f\n" % (self.data.strip(), snaps[0], snaps[1], snaps[2], snaps[3]))
            # else:
            #     self.send("%s DONE\n" % self.data.strip())
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
        return self.msip.set_lo_frequency(lo_frequency)
        
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



class SpecTCPHandler(SocketServer.BaseRequestHandler):
    '''Base class for msip1mm tcpip socket communications.
    Do not use this use the MSIP1mmSocketServer class instead
    '''
    def __init__(self, request, client_address, server):
        #self.logger = logging.getLogger('SpecRequestHandler')
        #self.logger.debug('__init__')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def setup(self):
        # any special setup we need here first
        self.msip = MSIPWrapper(debug=True)
        return SocketServer.BaseRequestHandler.setup(self)

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        msg = self.data.split()
        if not msg[0] in allowed_commands:
            print "Request has to be one of %s" % allowed_commands
        if msg[0] == 'lo_freq':
            self.lo_freq(msg[1])
        elif msg[0] == 'pll_status':
            pll_status = self.pll_status()
            self.request_sendall(str(pll_status))
        # elif msg[0] == 'start':
        #     self.start()
        # elif msg[0] == 'stop':
        #     self.stop()
        # elif msg[0] == 'close':
        #     self.close()

        def pll_status(self):
            return self.msip.pll_status()

