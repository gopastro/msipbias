# Based on u3allio.c

import sys
from datetime import datetime
import u3
import numpy

class U3AnalogIn():
    def __init__(self, numChannels=2,
                 numIterations=1000, debug=False,
                 config=True):
        self.debug = debug
        self.dev = u3.U3()
        #self.caldata = self.dev.getCalibrationData()
        self.quickSample = 1
        self.longSettling = 0
        self.numChannels = numChannels
        #self.latestAinValues = [0] * self.numChannels
        self.numIterations = numIterations
        self.checkHV()
        if config:
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
        FIOEIOAnalog = (2 ** self.numChannels) - 1
        fios = FIOEIOAnalog & 0xFF
        eios = FIOEIOAnalog // 256
        self.dev.configIO(FIOAnalog=fios, EIOAnalog=eios)

        self.dev.getFeedback(u3.PortDirWrite(Direction=[0, 0, 0],
                                             WriteMask=[0, 0, 15]))

    def getVoltages(self, numIterations=None):
        if numIterations is None:
            numIterations = self.numIterations

        self.feedbackArguments = []
        #self.feedbackArguments.append(u3.DAC0_8(Value=125))
        #self.feedbackArguments.append(u3.PortStateRead())

        for i in range(self.numChannels):
            self.feedbackArguments.append(u3.AIN(i, 31,
                                                 QuickSample=self.quickSample,
                                                 LongSettling=self.longSettling))

        self.latestAinValues = numpy.zeros((self.numChannels, numIterations),
                                           dtype='float')
        start = datetime.now()
        # Call Feedback numIterations (default) times
        i = 0
        while i < numIterations:
            results = self.dev.getFeedback(self.feedbackArguments)
            for j in range(self.numChannels):
                # Figure out if the channel is low or high voltage to use the correct calibration
                if self.isHV is True and j < 4:
                    lowVoltage = False
                else:
                    lowVoltage = True
                self.latestAinValues[j, i] = self.dev.binaryToCalibratedAnalogVoltage(results[2 + j],
                                                                              isLowVoltage=lowVoltage, isSingleEnded=True)
            i += 1
        end = datetime.now()
        delta = end - start
        if self.debug:
            print "Time difference: %g seconds" % (delta.total_seconds())
        if self.debug:
            for channel in range(self.numChannels):
                print "Channel: %d, voltage: %.6f +/- %.6f" % (channel, self.latestAinValues[channel, :].mean(), self.latestAinValues[channel, :].std())
        return self.latestAinValues

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
    
