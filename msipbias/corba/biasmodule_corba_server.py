#!/usr/bin/env python

import sys
from omniORB import CORBA, PortableServer
import CosNaming, BiasCorba, BiasCorba__POA
from msipbias.biasmodule import BiasModule

function_dictionary = {
    'getTemperature': 'get_temperature',
    'getMagnetCurrent': 'get_magnet_current',
    'getMagnetVoltage': 'get_magnet_voltage',
    'getSISCurrent': 'get_sis_current',
    'getSISVoltage': 'get_sis_voltage',
    'getLNADrainVoltage': 'get_lna_drain_voltage',
    'getLNADrainCurrent': 'get_lna_drain_current',
    'getLNAGateVoltage': 'get_lna_gate_voltage',
    'setMagnetCurrent': 'set_magnet_current',
    'setSISVoltage': 'set_sis_mixer_voltage',
    'setLNADrainVoltage': 'set_lna_drain_voltage',
    'setLNADrainCurrent': 'set_lna_drain_current',    
    }

class Bias_i (BiasCorba__POA.BiasModuleCorba):
    def __init__(self):
        #self.bm = BiasModule()
        self.bm = None

    def open_bias_module(self):
        self.bm = BiasModule()

    def close_bias_module(self):
        self.bm.close_cheetah()
        self.bm = None

    def getQuantity(self, name, *args):
        if self.bm is None:
            self.open_bias_module()
        fn = getattr(self.bm, function_dictionary.get(name))
        qty = fn(*args)
        self.close_bias_module()
        return qty

    def setQuantity(self, name, *args):
        if self.bm is None:
            self.open_bias_module()
        fn = getattr(self.bm, function_dictionary.get(name))
        fn(*args)
        self.close_bias_module()
        #return qty    
    
    def getTemperature(self, channel, dbwrite):
        if channel not in range(1, 7):
            return 0.0
        if channel <= 3:
            polar = 0
        else:
            polar = 1
        sensor = ((channel -1) % 3) + 1
        args = [sensor, polar]
        return self.getQuantity('getTemperature', *args)

    def getMagnetCurrent(self, magnet, polar):
        if magnet not in (1, 2):
            magnet = 2
        if polar not in (0, 1):
            polar = 0
        args = [magnet, polar]
        return self.getQuantity('getMagnetCurrent', *args)

    def getMagnetVoltage(self, magnet, polar):
        if magnet not in (1, 2):
            magnet = 2
        if polar not in (0, 1):
            polar = 0
        args = [magnet, polar]
        return self.getQuantity('getMagnetVoltage', *args)
    
    def getSISVoltage(self, sis, polar):
        if sis not in (1, 2):
            sis = 1
        if polar not in (0, 1):
            polar = 0
        args = [sis, polar]
        return self.getQuantity('getSISVoltage', *args)

    def getSISCurrent(self, sis, polar):
        if sis not in (1, 2):
            sis = 1
        if polar not in (0, 1):
            polar = 0
        args = [sis, polar]
        return self.getQuantity('getSISCurrent', *args)
    
    def getLNADrainVoltage(self, lna, stage, polar):
        if lna not in (1, 2):
            lna = 1
        if stage not in (1, 2, 3):
            stage = 1
        if polar not in (0, 1):
            polar = 0
        args = [lna, stage, polar]
        return self.getQuantity('getLNADrainVoltage', *args)

    def getLNADrainCurrent(self, lna, stage, polar):
        if lna not in (1, 2):
            lna = 1
        if stage not in (1, 2, 3):
            stage = 1
        if polar not in (0, 1):
            polar = 0
        args = [lna, stage, polar]
        return self.getQuantity('getLNADrainCurrent', *args)

    def getLNAGateVoltage(self, lna, stage, polar):
        if lna not in (1, 2):
            lna = 1
        if stage not in (1, 2, 3):
            stage = 1
        if polar not in (0, 1):
            polar = 0
        args = [lna, stage, polar]
        return self.getQuantity('getLNAGateVoltage', *args)

    def setMagnetCurrent(self, Imag, magnet, polar):
        if magnet not in (1, 2):
            magnet = 2
        if polar not in (0, 1):
            polar = 0
        args = [Imag, magnet, polar]
        self.setQuantity('setMagnetCurrent', *args)

    def setSISVoltage(self, voltage, sis, polar):
        if sis not in (1, 2):
            sis = 1
        if polar not in (0, 1):
            polar = 0
        args = [voltage, sis, polar]
        self.setQuantity('setSISVoltage', *args)

    def setLNADrainVoltage(self, voltage, lna, stage, polar):
        if lna not in (1, 2):
            lna = 1
        if stage not in (1, 2, 3):
            stage = 1
        if polar not in (0, 1):
            polar = 0
        args = [voltage, lna, stage, polar]        
        self.setQuantity('setLNADrainVoltage', *args)

    def setLNADrainCurrent(self, current, lna, stage, polar):
        if lna not in (1, 2):
            lna = 1
        if stage not in (1, 2, 3):
            stage = 1
        if polar not in (0, 1):
            polar = 0
        args = [current, lna, stage, polar]        
        self.setQuantity('setLNADrainCurrent', *args)
        
        
class BiasModuleServer:
    def __init__(self):
        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.poa = self.orb.resolve_initial_references("RootPOA")

        self.bi = Bias_i()
        self.bo = self.bi._this()

        #Obtain a reference to the root naming context
        obj = self.orb.resolve_initial_references("NameService")
        rootContext = obj._narrow(CosNaming.NamingContext)

        if rootContext is None:
            print "Failed to narrow the root naming context"
            sys.exit(1)

        # Bind a context named "test.my_context" to the root context
        name = [CosNaming.NameComponent("test", "my_context")]
        try:
            testContext = rootContext.bind_new_context(name)
            print "New test context bound"
        except CosNaming.NamingContext.AlreadyBound, ex:
            print "Test context already exists"
            obj = rootContext.resolve(name)
            testContext = obj._narrow(CosNaming.NamingContext)
            if testContext is None:
                print "test.mycontext exists but is not a NamingContext"
                sys.exit(1)

        # Bind the Bias object to the test context
        name = [CosNaming.NameComponent("BiasModule", "Object")]
        try:
            testContext.bind(name, self.bo)
            print "New BiasModule object bound"
        except CosNaming.NamingContext.AlreadyBound:
            testContext.rebind(name, self.bo)
            print "BiasModule binding already existed -- rebound"

        #Activate the poa
        poaManager = self.poa._get_the_POAManager()
        poaManager.activate()
        print self.orb.object_to_string(self.bo)

        self.orb.run()

 
