import re,copy
from core import configuration
import Displayer,Filter,Gen,Histos,Jet,Master,Muon,Other,Photon,Print,Top,Trigger,Xclean
#####################################
def adjustSteps(inSteps, dataOrMc = None) :
    outSteps = []
    blackList = getattr(configuration, "stepsToDisableFor%s"%dataOrMc)()
    histoBlackList = getattr(configuration, "histogramsToDisableFor%s"%dataOrMc)()
    for step in inSteps :
        disable = False
        if step.name in blackList : disable = True
        from steps.Other import histogrammer
        if isinstance(step, histogrammer) :
            for matchString in histoBlackList :
                vars = [step.var] if type(step.var) is str else step.var
                for var in vars :
                    if re.search(matchString, var) : disable = True
        outSteps.append(step)
        if disable : outSteps[-1].disable()
    return outSteps
#####################################
def adjustStepsForData(inSteps) : return adjustSteps(inSteps, "Data")
def adjustStepsForMc(inSteps)   : return adjustSteps(inSteps, "Mc")
#####################################
