#!/usr/bin/env python

import sys
from omniORB import CORBA
import BiasCorba, CosNaming

class BiasCorbaRemoteClient:
    def __init__(self, hostname='localhost'):
        sys.argv.extend(("-ORBInitRef", "NameService=corbaname::%s" % hostname))
        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.obj = self.orb.resolve_initial_references("NameService")
        rootContext = self.obj._narrow(CosNaming.NamingContext)
        if rootContext is None:
            print "Failed to narrow the root naming context"
            sys.exit(1)

        # Resolve the name "text.my_context/BiasModule.Object"
        name = [CosNaming.NameComponent("test", "my_context"),
                CosNaming.NameComponent("BiasModule", "Object")]
        try:
            self.obj = rootContext.resolve(name)
        except CosNaming.NamingContext.NotFound, ex:
            print "Name not found: %s" % name
            sys.exit(1)

        self.bo = self.obj._narrow(BiasCorba.BiasModuleCorba)
        if self.bo is None:
            print "Object reference is not an BiasCorba::BiasModuleCorba"
            sys.exit(1)

    def getTemperature(self, channel, dbwrite=False):
        temp = self.bo.getTemperature(channel, dbwrite)
        return temp

    def getMagnetCurrent(self, magnet, polar):
        return self.bo.getMagnetCurrent(magnet, polar)

    def getMagnetVoltage(self, magnet, polar):
        return self.bo.getMagnetVoltage(magnet, polar)
    
    def getSISCurrent(self, sis, polar):
        return self.bo.getSISCurrent(sis, polar)

    def getSISVoltage(self, sis, polar):
        return self.bo.getSISVoltage(sis, polar)    

    def getLNADrainVoltage(self, lna, stage, polar):
        return self.bo.getLNADrainVoltage(lna, stage, polar)

    def getLNADrainCurrent(self, lna, stage, polar):
        return self.bo.getLNADrainCurrent(lna, stage, polar)

    def getLNAGateVoltage(self, lna, stage, polar):
        return self.bo.getLNAGateVoltage(lna, stage, polar)
    
    def setMagnetCurrent(self, Imag, magnet, polar):
        self.bo.setMagnetCurrent(Imag, magnet, polar)    

    def setSISVoltage(self, voltage, sis, polar):
        return self.bo.setSISVoltage(voltage, sis, polar)

    def setLNADrainVoltage(self, voltage, lna, stage, polar):
        return self.bo.setLNADrainVoltage(voltage, lna, stage, polar)

    def setLNADrainCurrent(self, current, lna, stage, polar):
        return self.bo.setLNADrainCurrent(current, lna, stage, polar)

    def turnONLNA(self, polar):
        return self.bo.turnONLNA(polar)

    def turnOFFLNA(self, polar):
        return self.bo.turnOFFLNA(polar)    
    
