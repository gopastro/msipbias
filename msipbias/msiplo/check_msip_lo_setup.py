from msip_lo import MSIPLOSystem
import numpy
import pandas as pd
 
def check_lo_setup(start_freq=72.0, stop_freq=94.0,
                   freq_step=0.3):
    frequencies = numpy.arange(start_freq, stop_freq, freq_step)
    lisdic = []
    msiplo = MSIPLOSystem()
    for frequency in frequencies:
        dic = {}
        locked = msiplo.set_and_lock_frequency(frequency)
        dic['LOFrequency'] = msiplo.flo
        dic['Locked'] = locked
        dic['YIGFrequency'] = msiplo.yig_freq
        dic['IFLevel'] = msiplo.IFLevel
        dic['LoopVoltage'] = msiplo.loopVoltage
        dic['numLoop'] = msiplo.numLoop
        dic['SynthPower'] = msiplo.synth_power
        lisdic.append(dic)
    return pd.DataFrame(lisdic)

