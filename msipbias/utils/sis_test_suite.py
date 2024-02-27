import os
import time
import logging
import datetime

from msipbias.biasmodule import BiasModule
from .ifproc_corba import IFProc
from msipbias.msiplo.msip_lo import MSIPLOSystem
import matplotlib.pyplot as plt

class SISTestSuite(object):
    def __init__(self, directory, debug=True):
        self.debug = debug
        logfile = datetime.datetime.now().strftime('sistest_%Y_%m_%d_%H%M.log')
        logging.basicConfig(filename=logfile,
                            level=logging.INFO,
                            format='%(asctime)s %(levelname)s: %(message)s')
        if not os.path.exists(directory):
            self._print("making directory %s" % directory)
            os.makedirs(directory)
        self.bm = BiasModule(debug=debug)
        plt.ion() # this command allows to show the plot inside a loop

    def _print(self, msg, loglevel=logging.INFO, ):
        if self.debug:
            print(msg)
        logging.log(level=loglevel, msg=msg)

    def sweep_iv_bothpols(self, vmin, vmax, step=0.05):
        lisdic = []
        for v in numpy.arange(vmin, vmax, step):
            for polar in (0, 1):        
                for sis in (1, 2):
                    dic = {}
                    if sis == 1:
                        vout = v
                    else:
                        vout = -v
                    self.bm.set_sis_mixer_voltage(vout, sis=sis, polar=polar)
                    time.sleep(0.002)
                dic['vj1'] = self.bm.get_sis_voltage(sis=1, polar=polar)
                dic['ij1'] = self.bm.get_sis_current(sis=1, polar=polar)
                dic['vj2'] = self.bm.get_sis_voltage(sis=2, polar=polar)
                dic['ij2'] = self.bm.get_sis_current(sis=2, polar=polar)
                dic['polar'] = polar
                lisdic.append(dic)
        return pd.DataFrame(lisdic)
