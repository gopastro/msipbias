#!/usr/bin/env python

import sys
from omniORB import CORBA
import BiasModuleCorba, CosNaming

class BiasCorbaClient:
    def __init__(self):
        self.orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
        self.obj = orb.resolve_initial_references("NameService")
        rootContext = obj._narrow(CosNaming.NamingContext)
        if rootContext is None:
            print "Failed to narrow the root naming context"
            sys.exit(1)

        # Resolve the name "text.my_context/BiasModule.Object"
        name = [CosNaming.NameComponent("test", "my_context"),
                CosNaming.NameComponent("BiasModule", "Object")]
        try:
            obj = rootContext.resolve(name)
        except CosNaming.NamingContext.NotFound, ex:
            print "Name not found"
            sys.exit(1)

        self.bo = obj._narrow(BiasCorba.BiasModuleCorba)
        if self.bo is None:
            print "Object reference is not an BiasCorba::BiasModuleCorba"
            sys.exit(1)

    def getTemperature(self, channel):
        temp = self.bo.getTemperature(channel)
        return temp
