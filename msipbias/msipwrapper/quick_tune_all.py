from msipbias.biasmodule import BiasModule
#from ifproc_corba import IFProc
#from msipbias.msipwrapper import MSIPWrapper
from msipbias.msiplo.msip_lo import MSIPLOSystem

sis_voltages = {
    222: {0: {1: -8.2, 2: 8.1},
          1: {1: -8.3, 2: 8.2}
          },
    226: {0: {1: -8.1, 2: 8.1},
          1: {1: -8.3, 2: 8.2}
          },
    230: {0: {1: -8.1, 2: 8.0},
          1: {1: -8.3, 2: 8.2}
          },
    234: {0: {1: -8.0, 2: 8.0},
          1: {1: -8.2, 2: 8.1}
          },
    238: {0: {1: -8.0, 2: 7.9},
          1: {1: -8.2, 2: 8.1}
          },
    242: {0: {1: -7.9, 2: 7.9},
          1: {1: -8.1, 2: 8.0}
          },
    246: {0: {1: -7.8, 2: 7.8},
          1: {1: -8.1, 2: 8.0}
          },
    250: {0: {1: -7.8, 2: 7.8},
          1: {1: -8.0, 2: 7.9}
          },
    254: {0: {1: -7.8, 2: 7.7},
          1: {1: -8.0, 2: 7.9}
          },                            
    258: {0: {1: -7.7, 2: 7.7},
          1: {1: -7.9, 2: 7.9}
          },                                
    262: {0: {1: -7.7, 2: 7.7},
          1: {1: -7.9, 2: 7.9}
          },                                

    
    }

magnet_currents = {
    222: {0: 21, 1: 22},
    226: {0: 21, 1: 22},
    230: {0: 21, 1: 22},
    234: {0: 30, 1: 30},
    238: {0: 30, 1: 30},
    242: {0: 30, 1: -25},
    246: {0: 30, 1: -25},
    250: {0: 30, 1: 30},
    254: {0: 30, 1: 30},
    258: {0: 30, 1: 30},
    262: {0: 30, 1: 30},                            
    }

power_level_voltages = {
    221: 1.5,
    222: 1.5,
    226: 1.8,
    230: 1.8,
    234: 1.8,
    238: 1.6,
    242: 1.0,
    246: 0.5,
    250: 1.0,
    254: 1.0,
    258: 1.0,
    262: 1.0,
    }

def check_and_turn_on_LNAs(bm):
    lisdic = bm.monitor_lna()
    if lisdic[0]['VD1'] < 0.4:
        # LNAs are off
        bm.turn_on_LNA(polar=0)
        bm.turn_on_LNA(polar=1)
    return

def tune_freq(lofreq):
    bm = init_bm()
    check_and_turn_on_LNAs(bm)
    msiplo = MSIPLOSystem()
    available_freqs = list(sis_voltages.keys())
    freq = min(available_freqs, key=lambda x:abs(x - lofreq))
    for polar in (0, 1):
        for mixer in (1, 2):
            bm.set_sis_mixer_voltage(sis_voltages[freq][polar][mixer], sis=mixer, polar=polar)
        bm.set_magnet_current(magnet_currents[freq][polar], magnet=2, polar=polar)
    msiplo.set_power_level_voltage(power_level_voltages[freq])
    bm.close()
    msiplo.close()



sis_voltages_222 = {
    0: {1: -8.1,
        2: 8.1},
    1: {1: -8.5,
        2: 8.4}
    }    

magnet_currents_222 = {
    0: 21,
    1: 22
    }


sis_voltage_226 = {
    0: {1: -8.1,
        2: 8.1},
    1: {1: -8.4,
        2: 8.3}
    }        

magnet_currents_226 = {
    0: 21,
    1: 22
    }

sis_voltage_230 = {
    0: {1: -8.1,
        2: 8.0},
    1: {1: -8.4,
        2: 8.3}
    }        

magnet_currents_230 = {
    0: 21,
    1: 22
    }

sis_voltage_234 = {
    0: {1: -8.0,
        2: 7.95},
    1: {1: -8.3,
        2: 8.2}
    }        

magnet_currents_234 = {
    0: 25,
    1: -20
    }

sis_voltage_238 = {
    0: {1: -7.95,
        2: 7.94},
    1: {1: -8.2,
        2: 8.2}
    }        

magnet_currents_238 = {
    0: 25,
    1: -20
    }

sis_voltage_242 = {
    0: {1: -8.2,
        2: 7.99},
    1: {1: -8.2,
        2: 8.0}
    }

magnet_currents_242 = {
    0: -20,
    1: 22
    }


    


sis_voltages_255 = {
    0: {1: -7.6,
        2: 7.6},
    1: {1: -7.6,
        2: 7.6}
    }


sis_voltages_233 = {
    0: {1: -7.9,
        2: 7.9},
    1: {1: -8.0,
        2: 8.0}
    }

sis_voltages_222 = {
    0: {1: -7.8,
        2: 7.8},
    1: {1: -7.8,
        2: 7.8}
    }

#sis_voltages_222_opt = {
#    0: {1: -8.2,
#        2: 8.0},
#    1: {1: -8.2,
#        2: 8.1}
#    }

sis_voltages_222_opt = {
   0: {1: -7.9,
       2: 7.8},
   1: {1: -8.0,
       2: 8.0}
   }

# sis_voltages_222_opt = {
#     0: {1: -8.2,
#         2: 8.0},
#     1: {1: -8.4,
#         2: 8.2}
#     }

magnet_currents_255 = {
    0: 24.5,
    1: -23.3
    }

magnet_currents_222 = {
    0: 22,
    1: 23
    }

magnet_currents_233 = {
    0: -20,
    1: -20
    }

def init_bm():
    bm = BiasModule(debug=True)
    return bm

def tune_255():
    bm = init_bm()
    for polar in (0, 1):
        for mixer in (1, 2):
            bm.set_sis_mixer_voltage(sis_voltages_255[polar][mixer], sis=mixer, polar=polar)
        bm.set_magnet_current(magnet_currents_255[polar], magnet=2, polar=polar)
    bm.close()
    
def tune_222():
    bm = init_bm()
    for polar in (0, 1):
        for mixer in (1, 2):
            bm.set_sis_mixer_voltage(sis_voltages_222[polar][mixer], sis=mixer, polar=polar)
        bm.set_magnet_current(magnet_currents_222[polar], magnet=2, polar=polar)    
    bm.close()

def tune_222_opt():
    bm = init_bm()
    for polar in (0, 1):
        for mixer in (1, 2):
            bm.set_sis_mixer_voltage(sis_voltages_222_opt[polar][mixer], sis=mixer, polar=polar)
        bm.set_magnet_current(magnet_currents_222[polar], magnet=2, polar=polar)    
    bm.close()    


def tune_233():
    bm = init_bm()
    for polar in (0, 1):
        for mixer in (1, 2):
            bm.set_sis_mixer_voltage(sis_voltages_233[polar][mixer], sis=mixer, polar=polar)
        bm.set_magnet_current(magnet_currents_233[polar], magnet=2, polar=polar)    
    bm.close()
    

def tune_arb(voltages):
    """
    voltages is a dictionary for 2 pols and two mixer voltages
    """
    bm = init_bm()
    for polar in (0, 1):
        bm.set_sis_mixer_voltage(-voltages[polar][0], sis=1, polar=polar)
        bm.set_sis_mixer_voltage(voltages[polar][0], sis=2, polar=polar)
    bm.close()
    
