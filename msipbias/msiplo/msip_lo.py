from synth_prologix import Synthesizer
from microlambda_class import MicroLambda
from U3Analogin import U3AnalogIn
import numpy
import time

freqs = [72.3, 72.6, 72.9, 73.2, 73.5, 73.8, 74.1, 74.4, 74.7, 75.0, 75.3, 75.6, 75.9, 76.2, 76.5, 76.8, 77.1, 77.4, 77.7, 78.0, 78.3, 78.6, 78.9, 79.2, 79.5, 79.8, 80.1, 80.4, 80.7, 81.0, 81.3, 81.6, 81.9, 82.2, 82.5, 82.8, 83.1, 83.4, 83.7, 84.0, 84.3, 84.6, 84.9, 85.2, 85.5, 85.8, 86.1, 86.4, 86.7, 87.0, 87.3, 87.6, 87.9, 88.2, 88.5, 88.8, 89.1, 89.4, 89.7, 90.0, 90.3, 90.6, 90.9, 91.2, 91.5, 91.8, 92.1, 92.4, 92.7, 93.0, 93.3, 93.6, 93.9]

synth_powers = [16, 13, 13, 16, 15, 14, 14, 14, 14, 14, 14, 16, 13, 13, 13, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 14, 14, 14, 13, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 16, 16, 15, 15, 15, 15, 15, 15, 15, 15, 15, 14, 14, 14, 14, 13, 13, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16]


class MSIPLOSystem():
    def __init__(self, debug=True, prologix_host='192.168.151.110',
                 prologix_port=1234, synth_address=19,
                 default_synth_power=13,
                 max_synth_power=16,
                 start_power_level_voltage=2.5,
                 min_synth_power=10,
                 numIterations=100,
                 maxLoopIterations=10):
        self.offset = 0.0125 # GHz
        self.debug = debug
        self.maxLoopIterations = maxLoopIterations
        # Open Synthesizer
        self.synth = Synthesizer(host=prologix_host,
                                 port=prologix_port,
                                 synth_address=synth_address)
        self.synth.set_mult(6)
        self.default_synth_power = default_synth_power
        self.max_synth_power = max_synth_power
        self.min_synth_power = min_synth_power
        # Open Labjack to read voltages
        self.start_power_level_voltage = start_power_level_voltage
        self.labjack = U3AnalogIn(debug=self.debug,
                                  numIterations=numIterations)
        self.labjack.setDAVoltage(0, self.start_power_level_voltage)
        self.power_level_voltage = self.start_power_level_voltage
        # Open YIG synth
        self.ml = MicroLambda(debug=self.debug)

    def getVoltages(self):
        volts = self.labjack.getVoltages()
        IFLevel = volts[0, :].mean()
        loopVoltage = volts[1, :].mean()
        return IFLevel, loopVoltage

    def set_power_level_voltage(self, voltage):
        if voltage < 0.0 or voltage > 5.0:
            print "Drain Power level voltage has to be in range of 0 to 5V"
            return
        self.power_level_voltage = voltage
        self.labjack.setDAVoltage(0, self.power_level_voltage)
        time.sleep(0.010)

    def check_lock(self):
        self.IFLevel, self.loopVoltage = self.getVoltages()
        if self.IFLevel < -0.1:
            # level is pretty good
            if numpy.abs(self.loopVoltage) < 0.1:
                # already very low loopVoltage
                return True
            else:
                return False
        else:
            return False

        
    def set_and_lock_frequency(self, flo, synth_power=None):
        """
        Set frequency flo in GHz for 3mm LO system 
        Sets corresponding YIG frequency and adjusts it 
        till stable lock is achieved
        """
        self.flo = flo - 0.1 # remove 100 MHz offset
        if synth_power is not None:
            self.synth_power = synth_power
        else:
            self.synth_power = numpy.interp(self.flo, freqs, synth_powers)
        if self.debug:
            print "Current synth Freq: %.6f GHz" % (self.synth.get_freq()/1e9)
        self.synth.set_freq(self.flo*1e9)
        time.sleep(0.2)
        self.synth.set_power_level(self.synth_power)
        time.sleep(1.0) # let synth settle
        if self.debug:
            print "New synth Freq: %.6f GHz" % (self.flo)
            print "New synth Power: %s dBm" % self.synth_power
        self.yig_freq = (self.flo/4.) - self.offset # there may be a small offset to subtract
        self.ml.set_frequency(self.yig_freq)
        time.sleep(0.5)  # give YIG time to settle
        locked = False
        numLoop = 0
        while not locked:
            self.IFLevel, self.loopVoltage = self.getVoltages()
            if self.debug:
                print "Loop iteration: %d, YIG Freq: %s GHz; IFLevel: %.6f, LoopVoltage: %.6f" % (numLoop, self.yig_freq, self.IFLevel, self.loopVoltage)
            if self.IFLevel < -0.1:
                # level is pretty good
                if numpy.abs(self.loopVoltage) < 0.1:
                    # already very low loopVoltage
                    locked = True
                else:
                    if self.loopVoltage > 0.0:
                        self.yig_freq -= 0.01 # reduce by 10 MHz
                    else:
                        self.yig_freq += 0.01 # increase by 10 MHz
                    self.ml.set_frequency(self.yig_freq)
                    time.sleep(0.5)
            else:
                print "Something wrong."
                #if self.flo > 74 and self.flo < 93:
                if self.flo > 95: # for now disable this 
                    # initially try lowering synth power
                    if self.synth_power > self.min_synth_power:
                        self.synth_power -= 1
                        self.synth.set_power_level(self.synth_power)
                        time.sleep(1.0)
                        ifV, loopV = self.getVoltages()
                        if ifV  > self.IFLevel:
                            # got worse - so perhaps go other direction
                            self.synth_power += 2
                            if self.synth_power >= self.max_synth_power:
                                #never exceed max synth power
                                print "Max synth power exceeded. breaking"
                                break
                            self.synth.set_power_level(self.synth_power)
                            time.sleep(1.0)
                            ifV, loopV = self.getVoltages()
                            if ifV > self.IFLevel:
                                print "No change in IF power level"
                                break
                    # try boosting synth power
                    #self.synth_power = 15
                    #self.synth.set_power_level(self.synth_power)
                    #time.sleep(1.0) # let synth settle
                    #if self.debug:
                    #    print "Boosting Synth power to 15 dBm"
                else:
                    break
            numLoop += 1
            if numLoop > self.maxLoopIterations:
                print "Max Loop Iterations %d exceeded. No lock achieved" % self.maxLoopIterations
                break
        self.numLoop = numLoop
        if locked:
            return True
        else:
            return False

    def close(self):
        self.synth.close()
        self.ml.close_cheetah()
        self.labjack.close()
    
