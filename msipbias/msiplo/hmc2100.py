"""Utility script that is used to control the
ethernet-controlled Hittite synthesize HMC 2100
to set frequencies, power level, turn RF on or off,
and to check status"""

#import urllib2
#import urllib
import socket
import re
from optparse import OptionParser
import sys

def status_check(host='hmc2100', port=50000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    s.connect((host, int(port)))
    retstr = get_status(s)
    s.close()
    return retstr

def get_status(sock):
    sock.send('FREQ:CW?\n')
    freq = float(sock.recv(200))
    sock.send('POW?\n')
    power = float(sock.recv(200))
    sock.send('OUTP:STATE?\n')
    state = bool(int(sock.recv(200).strip()))
    if state:
        rf = "ON"
    else:
        rf = "OFF"
    return "Status of HMC 2100 (on %s):\nCW: %s Hz; Pow: %s dBm; RF Status: %s" % ('hmc2100', freq, power, rf)

if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-H", "--host", dest="hostname",
                      default="localhost:50001",
                      help="hostname to connect like: 192.168.22.200:50000 or localhost:50001 [default: %default]")
    parser.add_option("-s", "--status", dest="status",
                      action="store_true", default=False,
                      help="return status of HMC2100")
    parser.add_option("-p", "--power", dest="powerlevel",
                      type=float, 
                      help="power level for HMC2100")
    parser.add_option("-f", "--frequency", dest="frequency",
                      type=float, 
                      help="set frequency (in Hz)")
    parser.add_option("-r", "--rf", dest="rf",
                      choices=["ON", "OFF"],
                      type="choice",
                      help="choices are ON or OFF")
    (options, args) = parser.parse_args()
    powerlevel = options.powerlevel
    frequency = options.frequency
    hostname = options.hostname
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    h, p = hostname.split(':')
    s.connect((h, int(p)))
    if options.status:
        mystr = get_status(s)
        print mystr
        sys.exit(0)
    if options.powerlevel is not None:
        s.send("POW %f\n" % options.powerlevel)
    if options.frequency is not None:
        s.send("FREQ:CW %s\n" % options.frequency)
    if options.rf is not None:
        if options.rf == "ON":
            s.send("OUTP:STATE 1\n")
        elif options.rf == "OFF":
            s.send("OUTP:STATE 0\n")
    mystr = get_status(s)
    print mystr
            
