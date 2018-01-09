from msip_lo import MSIPLOSystem
import numpy
import pandas as pd
 
def derive_synth_power_table(start_freq=72.0, stop_freq=94.0,
                   freq_step=0.3):
    frequencies = numpy.arange(start_freq, stop_freq, freq_step)
    lisdic = []
    msiplo = MSIPLOSystem()
    for frequency in frequencies:
        print "Locking to Frequency %s" % frequency
        dic = {}
        iflevels = []
        sps = []
        for synth_power in numpy.arange(10, 17, 1):
            locked = msiplo.set_and_lock_frequency(frequency,
                                                   synth_power=synth_power)
            if locked:
                iflevels.append(msiplo.IFLevel)
                sps.append(msiplo.synth_power)
        if iflevels:
            iflevels = numpy.array(iflevels)
            sps = numpy.array(sps)
            synth_power = sps[iflevels.argmin()]
        else:
            continue
        locked = msiplo.set_and_lock_frequency(frequency,
                                               synth_power=synth_power)
        dic['LOFrequency'] = msiplo.flo
        dic['Locked'] = locked
        dic['YIGFrequency'] = msiplo.yig_freq
        dic['IFLevel'] = msiplo.IFLevel
        dic['LoopVoltage'] = msiplo.loopVoltage
        dic['numLoop'] = msiplo.numLoop
        dic['SynthPower'] = msiplo.synth_power
        lisdic.append(dic)
    return pd.DataFrame(lisdic)

