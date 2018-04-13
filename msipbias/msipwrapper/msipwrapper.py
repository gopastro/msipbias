from msipbias.chopper import Chopper
from msipbias.msiplo.msip_lo import MSIPLOSystem
from msipbias.biasmodule import BiasModule

class MSIPWrapper():
    def __init__(self, debug=False):
        self.debug = debug

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
        chop = chopper.chopper_state()
        chopper.close()
        return chop

    def pll_status(self):
        msiplo = MSIPLOSystem(debug=self.debug)
        lock_status = msiplo.check_lock()
        msiplo.close()
        return lock_status

    
