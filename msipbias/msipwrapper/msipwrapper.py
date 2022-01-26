from msipbias.chopper import Chopper
from msipbias.msiplo.msip_lo import MSIPLOSystem
from msipbias.biasmodule import BiasModule
import time

class MSIPWrapper():
    def __init__(self, debug=False, lo_power_voltage=2.5):
        self.debug = debug
        self.lock_status = False
        self.chopper_status = 'SKY'
        self.lo_power_voltage = lo_power_voltage
        print "Initializing with LO power voltage: %s" % self.lo_power_voltage
        
    def chopper_in(self):
        chopper = Chopper(debug=self.debug)
        chop = chopper.chopper_in()
        chopper.close()
        return chop

    def chopper_out(self):
        chopper = Chopper(debug=self.debug)
        chop = chopper.chopper_out()
        chopper.close()
        return chop

    def chopper_state(self):
        chopper = Chopper(debug=self.debug)
        self.chopper_status = chopper.chopper_state()
        chopper.close()
        return self.chopper_status

    def pll_status(self):
        msiplo = MSIPLOSystem(debug=self.debug, check_pll=True,
                              start_power_level_voltage=self.lo_power_voltage)
        self.lock_status = msiplo.check_lock()
        msiplo.close()
        return self.lock_status

    def set_lo_frequency(self, frequency):
        """
        Given frequency of LO at 1mm wavelength
        call the MSIP LO System and locks the YIG and
        the whole LO chain for appropriate frequency
        Returns True if lock achieved, False if not
        """
        msiplo = MSIPLOSystem(debug=self.debug,
                              start_power_level_voltage=self.lo_power_voltage)
        self.lock_status = msiplo.set_and_lock_frequency(frequency/3.0)
        self.lo_power_voltage = msiplo.power_level_voltage
        msiplo.close()
        return self.lock_status

    def set_lo_power(self, voltage):
        """
        Sets the drain voltage of the last MMIC
        in LO chain to a voltage betwee 0 and 5.0 V
        Larger voltages result in larger LO power
        """
        # don't want to change LO so set check_pll True
        msiplo = MSIPLOSystem(debug=self.debug, check_pll=True, 
                              start_power_level_voltage=self.lo_power_voltage)
        self.lo_power_voltage = msiplo.set_power_level_voltage(voltage)
        msiplo.close()
        return self.lo_power_voltage

    def get_lo_power(self):
        return self.lo_power_voltage

    def lo_synth_off(self):
        try:
            msiplo = MSIPLOSystem(debug=self.debug, check_pll=True, 
                                  start_power_level_voltage=self.lo_power_voltage)
            msiplo.synth_output_off()
            time.sleep(2.0)
            status = msiplo.get_synth_output_status()
            msiplo.close()
            return status
        except:
            return "ERR"

    def lo_synth_on(self):
        try:
            msiplo = MSIPLOSystem(debug=self.debug, check_pll=True, 
                                  start_power_level_voltage=self.lo_power_voltage)
            msiplo.synth_output_on()
            time.sleep(2.0)
            status = msiplo.get_synth_output_status()
            msiplo.close()
            return status
        except:
            return "ERR"
        
    def get_temperature(self, channel):
        bm = BiasModule(debug=self.debug)
        lisdic = bm.monitor_temperature()
        dic = {}
        for l in lisdic:
            dic[l['channel']] =l['temperature']
        bm.close()
        return dic.get(channel)
