# Based on u3allio.c

import sys
from datetime import datetime
import u3
import numpy

class U3DigitalIO():
    def __init__(self, numChannels=4,
                 debug=False):
        """
        U3 - HV labjack used as a digital input/output
        In the screw terminal, FIO4, FIO5, FIO6 and FIO7
        are digital input/outputs
        """
        self.debug = debug
        self.dev = u3.U3()
        self.caldata = self.dev.getCalibrationData()
        self.numChannels = numChannels
        self.directions = [0, 0, 0, 0]  # default direction set to input
        self.checkHV()
        self.configIO()

    def checkHV(self):
        # Check if the U3 is an HV
        if self.dev.configU3()['VersionInfo'] & 18 == 18:
            self.isHV = True
        else:
            self.isHV = False
        if self.debug:
            print "Device U3 is HV:%s" % self.isHV
            
    def configIO(self):
        directions = []
        for chan in range(4, 8):
            directions.append(self.dev.getFeedback(u3.BitDirRead(chan))[0])
        print "Current directions: %s (0: input; 1: output)" % directions
        for i, chan in enumerate(range(4, 8)):
            self.dev.getFeedback(u3.BitDirWrite(chan, self.directions[i]))
        print "Directions set to: %s (0: input; 1: output)" % self.directions

    def setDirection(self, chan, direction):
        if chan not in (4, 5, 6, 7):
            print "Channels should be one of 4, 5, 6, 7"
            return
        if direction not in (0, 1):
            print "Direction should be 0 (input) or 1 (output)"
            return
        self.dev.getFeedback(u3.BitDirWrite(chan, direction))
        self.directions[chan-4] = direction
        print "Directions set to: %s (0: input; 1: output)" % self.directions

    def getDigitalState(self, chan):
        """
        If chan is an input returns Bit State
        """
        if self.directions[chan-4] == 0:
            return self.dev.getFeedback(u3.BitStateRead(chan))[0]

    def setDigitalState(self, chan, state):
        """
        If chan is an output sets Bit State
        """
        if state not in (0, 1):
            print "state should be 0 or 1"
            return
        if self.directions[chan-4] == 1:
            self.dev.getFeedback(u3.BitStateWrite(chan, state))

    def close(self):
        self.dev.close()
    
