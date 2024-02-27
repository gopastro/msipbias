# CORBA imports
import sys
try:
    import CORBA
except ImportError:
    sys.path.insert(0, '/usr/local/omniORB-4.1.3/x86-linux/lib/python2.5/site-packages')
    import CORBA
import IfProcDataModule
import numpy
import time

class IFProc(object):
    def __init__(self):
        self.ifproc = None
        self.setup_corba()
        self.atten = {}

    def setup_corba(self):
        orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        obj = orb.string_to_object("corbaloc:iiop:ifproc:1099/IfProc")
        self.ifproc = obj._narrow(IfProcDataModule.IfProcDataORB)
        if self.ifproc is None:
            raise Exception("CORBA Error", "Object reference is None")
        print "%s initialized" % self.ifproc.getObjectName()

    def set_atten(self, atten, chan):
        self.ifproc.setIfProcAttenuatorIndexed(atten, chan)
        self.atten[chan] = atten
        time.sleep(0.1)

    def get_atten(self, chan):
        att = self.ifproc.getIfProcAttenuatorIndexed(chan)
        self.atten[chan] = att
        return att

    def get_level(self, chan):
        return self.ifproc.getIfProcLevelIndexed(chan)

    def get_avg_levels(self, chan, nmeas=5):
        levels = numpy.zeros(nmeas, dtype='float')
        for i in xrange(nmeas):
            levels[i] = self.get_level(chan)
            time.sleep(0.2)
        return level.mean()

    def get_all_atten(self):
        all_att = self.ifproc.getIfProcAttenuator()
        self.atten = dict((i, all_att[i]) for i in range(len(all_att)))

    def set_all_CO(self, value):
        if value in (0, 1):
            allCO = [value] * 32
            self.ifproc.setIfProcCoFilter(allCO)
    
    def get_all_CO(self):
        return numpy.array(self.ifproc.getIfProcCoFilter())

    def get_all_levels(self):
        return numpy.array(self.ifproc.getIfProcLevel())
    
    
