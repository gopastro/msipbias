from synth_prologix import Synthesizer
from microlambda_class import MicroLambda
from U3Analogin import U3AnalogIn
import numpy
import time
from msipbias.logging import logger

logger.name = __name__

freq_synth_powers = [(72.3, 13.0),
                     (72.4, 13.0),
                     (72.5, 13.0),
                     (72.6, 13.0),
                     (72.7, 13.0),
                     (72.8, 13.0),
                     (72.9, 13.0),
                     (73.0, 13.0),
                     (73.1, 13.0),
                     (73.2, 13.0),
                     (73.3, 13.0),
                     (73.4, 13.0),
                     (73.5, 13.0),
                     (73.6, 13.0),
                     (73.7, 13.0),
                     (73.8, 13.0),
                     (73.9, 13.0),
                     (74.0, 13.0),
                     (74.1, 13.0),
                     (74.2, 13.0),
                     (74.3, 13.0),
                     (74.4, 13.0),
                     (74.5, 13.0),
                     (74.6, 13.0),
                     (74.7, 13.0),
                     (74.8, 13.0),
                     (74.9, 13.0),
                     (75.0, 13.0),
                     (75.1, 13.0),
                     (75.2, 13.0),
                     (75.3, 13.0),
                    (75.4, 13.0),
                     (75.5, 13.0),
                     (75.6, 13.0),
                     (75.7, 13.0),
                     (75.8, 13.0),
                     (75.9, 13.0),
                     (76.0, 13.0),
                    (76.1, 13.0),
                     (76.2, 13.0),
                     (76.3, 13.0),
                     (76.4, 13.0),
                     (76.5, 13.0),
                     (76.6, 13.0),
                     (76.7, 13.0),
                     (76.8, 13.0),
                     (76.9, 12.2),
                     (77.0, 13.0),
                     (77.1, 13.0),
                     (77.2, 13.0),
                     (77.3, 13.0),
                     (77.4, 12.0),
                     (77.5, 13.0),
                     (77.6, 13.0),
                     (77.7, 13.0),
                     (77.8, 12.0),
                     (77.9, 13.0),
                     (78.0, 13.0),
                     (78.1, 13.0),
                     (78.2, 13.0),
                     (78.3, 11.4),
                     (78.4, 13.0),
                     (78.5, 12.2),
                     (78.6, 13.0),
                     (78.7, 13.0),
                     (78.8, 12.2),
                     (78.9, 13.0),
                     (79.0, 13.0),
                     (79.1, 13.0),
                     (79.2, 12.4),
                     (79.3, 13.0),
                     (79.4, 13.0),
                     (79.5, 13.0),
                     (79.6, 13.0),
                     (79.7, 12.8),
                     (79.8, 13.0),
                     (79.9, 13.0),
                     (80.0, 13.0),
                     (80.1, 13.0),
                     (80.2, 13.2),
                     (80.3, 13.0),
                     (80.4, 13.0),
                     (80.5, 13.0),
                     (80.6, 13.0),
                     (80.7, 13.0),
                     (80.8, 13.0),
                     (80.9, 13.0),
                     (81.0, 13.0),
                     (81.1, 13.0),
                     (81.2, 13.0),
                     (81.3, 13.0),
                     (81.4, 13.0),
                     (81.5, 13.0),
                     (81.6, 13.0),
                     (81.7, 13.0),
                     (81.8, 13.0),
                     (81.9, 13.0),
                     (82.0, 13.0),
                     (82.1, 13.0),
                     (82.2, 13.0),
                     (82.3, 13.0),
                     (82.4, 13.0),
                     (82.5, 13.0),
                     (82.6, 13.0),
                     (82.7, 13.0),
                     (82.8, 13.0),
                     (82.9, 13.0),
                     (83.0, 13.0),
                     (83.1, 13.0),
                     (83.2, 13.0),
                     (83.3, 13.0),
                     (83.4, 13.0),
                     (83.5, 13.0),
                     (83.6, 13.0),
                     (83.7, 13.0),
                     (83.8, 13.0),
                     (83.9, 13.0),
                     (84.0, 13.0),
                     (84.1, 13.0),
                     (84.2, 13.0),
                     (84.3, 13.0),
                     (84.4, 13.0),
                     (84.5, 13.0),
                     (84.6, 13.0),
                     (84.7, 14.2),
                     (84.8, 15.0),
                     (84.9, 16.0),
                     (85.0, 16.0),
                     (85.1, 16.0),
                     (85.2, 16.0),
                     (85.3, 16.0),
                     (85.4, 16.0),
                     (85.5, 16.0),
                     (85.6, 15.666666666700001),
                     (85.7, 15.333333333299999),
                     (85.8, 15.0),
                     (85.9, 14.666666666700001),
                     (86.0, 14.333333333299999),
                     (86.1, 14.0),
                     (86.2, 13.666666666700001),
                     (86.3, 13.333333333299999),
                     (86.4, 13.0),
                     (86.5, 13.0),
                     (86.6, 13.0),
                     (86.7, 13.0),
                     (86.8, 13.0),
                     (86.9, 13.0),
                     (87.0, 13.0),
                     (87.1, 13.0),
                     (87.2, 13.0),
                     (87.3, 13.0),
                     (87.4, 13.0),
                     (87.5, 13.0),
                     (87.6, 13.0),
                     (87.7, 13.0),
                     (87.8, 13.0),
                     (87.9, 13.0),
                     (88.0, 13.0),
                     (88.1, 13.0),
                     (88.2, 13.0),
                     (88.3, 13.0),
                     (88.4, 13.0),
                     (88.5, 13.0),
                     (88.6, 13.0),
                     (88.7, 13.2),
                     (88.8, 13.0),
                     (88.9, 13.2),
                     (89.0, 13.6),
                     (89.1, 13.0),
                     (89.2, 13.0),
                     (89.3, 13.0),
                     (89.4, 13.0),
                     (89.5, 13.0),
                     (89.6, 13.0),
                     (89.7, 13.0),
                     (89.8, 13.0),
                     (89.9, 13.4),
                     (90.0, 13.0),
                     (90.1, 13.333333333299999),
                     (90.2, 13.666666666700001),
                     (90.3, 14.0),
                     (90.4, 14.0),
                     (90.5, 14.0),
                     (90.6, 14.0),
                     (90.7, 14.8),
                     (90.8, 14.4),
                     (90.9, 14.0),
                     (91.0, 13.666666666700001),
                     (91.1, 13.333333333299999),
                     (91.2, 13.0),
                     (91.3, 13.0),
                     (91.4, 13.0),
                     (91.5, 13.0),
                     (91.6, 13.0),
                     (91.7, 13.0),
                     (91.8, 13.0),
                     (91.9, 13.0),
                     (92.0, 13.0),
                     (92.1, 13.0),
                     (92.2, 13.0),
                     (92.3, 13.0),
                     (92.4, 13.0),
                     (92.5, 13.0),
                     (92.6, 13.0),
                     (92.7, 13.0),
                     (92.8, 13.0),
                     (92.9, 13.0),
                     (93.0, 13.0),
                     (93.1, 13.0),
                     (93.2, 13.0),
                     (93.3, 13.0),
                     (93.4, 13.0),
                     (93.5, 13.0),
                     (93.6, 13.0),
                     (93.7, 13.2),
                     (93.8, 13.0),
                     (93.9, 13.0),
                     (94.0, 13.0)]


freqs = [72.3, 72.6, 72.9, 73.2, 73.5, 73.8, 74.1, 74.4, 74.7, 75.0, 75.3, 75.6, 75.9, 76.2, 76.5, 76.8, 77.1, 77.4, 77.7, 78.0, 78.3, 78.6, 78.9, 79.2, 79.5, 79.8, 80.1, 80.4, 80.7, 81.0, 81.3, 81.6, 81.9, 82.2, 82.5, 82.8, 83.1, 83.4, 83.7, 84.0, 84.3, 84.6, 84.9, 85.2, 85.5, 85.8, 86.1, 86.4, 86.7, 87.0, 87.3, 87.6, 87.9, 88.2, 88.5, 88.8, 89.1, 89.4, 89.7, 90.0, 90.3, 90.6, 90.9, 91.2, 91.5, 91.8, 92.1, 92.4, 92.7, 93.0, 93.3, 93.6, 93.9]

# New set of powers derived for Agilent E8257D
synth_powers = [13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 16, 16, 16, 15, 14, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13]

#synth_powers = [16, 13, 13, 16, 15, 14, 14, 14, 14, 14, 14, 16, 13, 13, 13, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 15, 14, 14, 14, 13, 13, 13, 13, 14, 14, 14, 15, 15, 15, 15, 15, 15, 16, 16, 15, 15, 15, 15, 15, 15, 15, 15, 15, 14, 14, 14, 14, 13, 13, 15, 15, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16]


class MSIPLOSystem():
    def __init__(self, debug=True, prologix_host='192.168.151.110',
                 prologix_port=1234, synth_address=19,
                 default_synth_power=13,
                 max_synth_power=16,
                 start_power_level_voltage=2.5,
                 min_synth_power=10,
                 numIterations=100,
                 maxLoopIterations=10,
                 check_pll=False):
        self.offset = 0.0125 # GHz
        self.debug = debug
        self.maxLoopIterations = maxLoopIterations
        # Open Synthesizer
        self.synth = Synthesizer(host=prologix_host,
                                 port=prologix_port,
                                 synth_address=synth_address)
        self.synth.set_mult(6)
        self.synth.output_on()  # in case RF was OFF
        self.default_synth_power = default_synth_power
        self.max_synth_power = max_synth_power
        self.min_synth_power = min_synth_power
        self.freqs = [l[0] for l in freq_synth_powers]
        self.synth_powers = [l[1] for l in freq_synth_powers]
        # Open Labjack to read voltages
        self.start_power_level_voltage = start_power_level_voltage
        if check_pll:
            self.labjack = U3AnalogIn(debug=self.debug,
                                      numIterations=numIterations,
                                      config=False)
        else:
            self.labjack = U3AnalogIn(debug=self.debug,
                                      numIterations=numIterations,
                                      config=True)            
        if not check_pll:
            # If checking for PLL status only do not disturb power level voltage
            print "Setting power level on msip_lo init %s" % self.start_power_level_voltage
            self.set_power_level_voltage(self.start_power_level_voltage)
        #self.power_level_voltage = self.start_power_level_voltage
        # Open YIG synth
        self.ml = MicroLambda(debug=self.debug)

    def getVoltages(self):
        volts = self.labjack.getVoltages()
        IFLevel = volts[0, :].mean()
        loopVoltage = volts[1, :].mean()
        return IFLevel, loopVoltage

    def set_power_level_voltage(self, voltage):
        if voltage < 0.0 or voltage > 5.0:
            if self.debug:
                print "Drain Power level voltage has to be in range of 0 to 5V"
            logger.error("Drain Power level voltage has to be in range of 0 to 5V")
            return None
        self.power_level_voltage = voltage
        self.labjack.setDAVoltage(0, self.power_level_voltage)
        if self.debug:
            logger.info("Set LO Power level to %.3f Volts" % self.power_level_voltage)
        time.sleep(0.010)
        return self.power_level_voltage
    
    def check_lock(self):
        self.IFLevel, self.loopVoltage = self.getVoltages()
        if self.IFLevel < -0.1:
            # level is pretty good
            if numpy.abs(self.loopVoltage) < 0.1:
                # already very low loopVoltage
                if self.debug:
                    logger.info("LO PLL Locked")
                return True
            else:
                logger.error("LO PLL Not Locked")
                return False
        else:
            logger.error("LO PLL Not Locked")
            return False

        
    def set_and_lock_frequency(self, flo, synth_power=None):
        """
        Set frequency flo in GHz for 3mm LO system 
        Sets corresponding YIG frequency and adjusts it 
        till stable lock is achieved
        """
        self.flo = flo - 0.1 #- ((2/6.)*1e-6)# remove 100 MHz offset and an additional 2kHz offset for synth
        if synth_power is not None:
            self.synth_power = synth_power
        else:
            self.synth_power = numpy.interp(self.flo, self.freqs, self.synth_powers)
        if self.debug:
            logger.info("Current synth Freq: %.6f GHz" % (self.synth.get_freq()/1e9))
        self.synth.set_freq(self.flo*1e9)
        time.sleep(0.2)
        self.synth.set_power_level(self.synth_power)
        time.sleep(1.0) # let synth settle
        if self.debug:
            logger.info("New synth Freq: %.6f GHz" % (self.flo))
            logger.info("New synth Power: %s dBm" % self.synth_power)
        self.yig_freq = (self.flo/4.) - self.offset # there may be a small offset to subtract
        self.ml.set_frequency(self.yig_freq)
        time.sleep(0.5)  # give YIG time to settle
        locked = False
        numLoop = 0
        while not locked:
            self.IFLevel, self.loopVoltage = self.getVoltages()
            if self.debug:
                logger.info("Loop iteration: %d, YIG Freq: %s GHz; IFLevel: %.6f, LoopVoltage: %.6f" % (numLoop, self.yig_freq, self.IFLevel, self.loopVoltage))
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
                                if self.debug:
                                    logger.error("Max synth power exceeded. breaking")
                                break
                            self.synth.set_power_level(self.synth_power)
                            time.sleep(1.0)
                            ifV, loopV = self.getVoltages()
                            if ifV > self.IFLevel:
                                if self.debug:
                                    logger.info("No change in IF power level")
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
                if self.debug:
                    logger.info("Max Loop Iterations %d exceeded. No lock achieved" % self.maxLoopIterations)
                break
        self.numLoop = numLoop
        if locked:
            # set power level voltage one more time
            self.set_power_level_voltage(self.power_level_voltage)            
            return True
        else:
            return False

    def close(self):
        self.synth.close()
        self.ml.close_cheetah()
        self.labjack.close()
        if self.debug:
            logger.info("Closing all MSIP LO connections")
