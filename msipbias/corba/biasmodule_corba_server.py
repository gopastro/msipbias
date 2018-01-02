#!/usr/bin/env python

import sys
from omniORB import CORBA, PortableServer
import CosNaming, BiasCorba, BiasCorba__POA
from msipbias.biasmodule import BiasModule

class Bias_i (BiasCorba__POA.BiasModuleCorba):
    def __init__(self):
        self.bm = BiasModule()
    
    def getTemperature(self, channel):
        if channel not in range(1, 7):
            return 0.0
        if channel <= 3:
            polar = 0
        else:
            polar = 1
        sensor = ((channel -1) % 3) + 1
        return self.bm.get_temperature(sensor=sensor, polar=polar)

class BiasModuleServer:
    def __init__(self):
        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.poa = orb.resolve_initial_references("RootPOA")

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
            testContext.bind(name, bo)
            print "New BiasModule object bound"
        except CosNaming.NamingContext.AlreadyBound:
            testContext.rebind(name, bo)
            print "BiasModule binding already existed -- rebound"

        #Activate the poa
        poaManager = self.poa._get_the_POAManager()
        poaManager.activate()
        print self.orb.object_to_string(eo)

        self.orb.run()

 
