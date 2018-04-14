from U3DigitalIO import U3DigitalIO
import time
from msipbias.logging import logger

logger.name = __name__

class Chopper():
    def __init__(self, timeout=1.0, debug=False):
        """
        1mm Chopper System
        Uses the Labjack Digital IO module
        FIO4 is connected to Chopper Command (and is an output bit)
        FIO6 is connected to Amb sensor (input)
        FIO7 is connected to Sky sensor (input)
        """
        self.debug = debug
        self.timeout = timeout
        self.u3dig = U3DigitalIO(debug=self.debug)
        #self.chopper_out()
        
    def chopper_in(self):
        if self.debug:
            logger.info("Setting Chopper in")
        self.u3dig.setDigitalState(4, 1)
        time.sleep(self.timeout)
        self.ambient = self.u3dig.getDigitalState(6)
        self.sky = self.u3dig.getDigitalState(7)
        if self.ambient == 0 and self.sky == 1:
            return 'load'
        else:
            return 'error'

    def chopper_out(self):
        if self.debug:
            logger.info("Setting Chopper out")
        self.u3dig.setDigitalState(4, 0)
        time.sleep(self.timeout)
        self.ambient = self.u3dig.getDigitalState(6)
        self.sky = self.u3dig.getDigitalState(7)
        if self.ambient == 1 and self.sky == 0:
            return 'sky'
        else:
            return 'error'

    def chopper_state(self):
        self.ambient = self.u3dig.getDigitalState(6)
        self.sky = self.u3dig.getDigitalState(7)        
        if self.ambient == 0 and self.sky == 1:
            return 'load'
        elif self.ambient == 1 and self.sky == 0:
            return 'sky'
        else:
            return 'error'
        
    def close(self):
        self.u3dig.close()

        
