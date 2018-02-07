# Based on u3allio.c

import sys
from datetime import datetime
import u3
import numpy

class U3DAC():
    def __init__(self, debug=False):
        """
        U3 - HV labjack used as a digital to analog output
        In the screw terminal, DAC0 and DAC1 are 
        are D/A outputs
        """
        self.debug = debug
        self.dev = u3.U3()
        self.caldata = self.dev.getCalibrationData()
        self.checkHV()

    def checkHV(self):
        # Check if the U3 is an HV
        if self.dev.configU3()['VersionInfo'] & 18 == 18:
            self.isHV = True
        else:
            self.isHV = False
        if self.debug:
            print "Device U3 is HV:%s" % self.isHV
            
    def setDAVoltage(self, dacNumber, voltage):
        if dacNumber not in (0, 1):
            print "dacNumber should be one of 0, 1"
            return
        if voltage < 0.0 or voltage > 5.0:
            print "voltage should be in range of 0 to 5V"
            return
        DAC_VALUE = self.dev.voltageToDACBits(voltage, dacNumber=dacNumber,
                                       is16Bits=False)
        self.dev.getFeedback(u3.DAC0_8(DAC_VALUE))
        if self.debug:
            print "dacNumber: %d set to %s V" % (dacNumber, voltage)

    def close(self):
        self.dev.close()
    
