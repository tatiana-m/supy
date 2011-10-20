#!/usr/bin/env python

from core import analysis,plotter
import calculables,steps,samples, ROOT as r

class trigger_ex_90gev(analysis.analysis) :

    def listOfSampleDictionaries(self) :
        return [samples.Photon.photon]

    def listOfSteps(self,config) :
        tags90 = ["HLT_Photon90_CaloIdVL_v%d"%i for i in range(1,4)] + ["HLT_Photon90_CaloIdVL_IsoL_v%d"%i for i in range(1,4)]
        tags90 = ["HLT_Photon90_CaloIdVL_v%d"%i for i in range(1,4)] + ["HLT_Photon90_CaloIdVL_IsoL_v%d"%i for i in range(1,4)]
        tags75 = ["HLT_Photon75_CaloIdVL_v%d"%i for i in range(1,7)] + ["HLT_Photon75_CaloIdVL_IsoL_v%d"%i for i in range(1,7)]


               #["HLT_Photon125_v%d"%i for i in range(1,3)] +
#        probe = "HLT_Photon135_v1"
#        probe = "HLT_Photon90_CaloIdVL_v1"
        probe = "HLT_Photon90_CaloIdVL_IsoL_v3"
#        print(tag)

        outList=[
            steps.Print.progressPrinter(),
  #          steps.Other.histogrammer("run", 100, 0, 200000),
   #         steps.Other.histogrammer("photonLeadingPtPat", 100, 0, 200),
            steps.Trigger.Counts(useCache = True),
    #        steps.Other.multiplicityFilter("photonIndicesPat", nMin = 1),
     #       steps.Trigger.hltTurnOnHistogrammer("photonLeadingPtPat", (100, 70, 200), probe, tags75 )

            ]
        return outList
    

    def listOfCalculables(self,config) :
        Photon = ("photon","Pat")
        flag = "photonIDTightFromTwikiPat"
        listOfCalculables = calculables.zeroArgs()
        listOfCalculables += calculables.fromCollections(calculables.Photon,[Photon])
        listOfCalculables.append(calculables.Photon.Indices(Photon, ptMin = 25, flagName = flag))

        return listOfCalculables

    def listOfSamples(self,config) :
        data = []
        from samples import specify 
        jw = calculables.Other.jsonWeight("cert/Cert_160404-167913_7TeV_PromptReco_Collisions11_JSON.txt") #1078/pb
        #data += specify(names = "Photon.Run2011A-May10ReReco-v1.AOD.Zoe_skim",    weights = jw, overrideLumi = 188.9)
        #data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Zoe1_skim",    weights = jw, overrideLumi =  70.0)
        #data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Zoe2_skim",    weights = jw, overrideLumi = 151.1)
        #data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Zoe3_skim",    weights = jw, overrideLumi =  74.4)
        #data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Rob1_skim",    weights = jw, overrideLumi = 167.1)
       #data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Rob2_skim",    weights = jw, overrideLumi = 119.7)
        #data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Rob3_skim",    weights = jw, overrideLumi = 180.2)
#        data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Rob4_80gev_skim",    weights = jw, overrideLumi =  69.3, nFilesMax = 1)
#        data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Rob4_skim",    weights = jw, overrideLumi =  69.3)
#        data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Darren1_skim", weights = jw, overrideLumi =  36.3)


        data += specify(names = "Photon.Run2011A-May10ReReco-v1.AOD.Darren1", )
        data += specify(names = "Photon.Run2011A-05Aug2011-v1.AOD.Bryn1", )
        data += specify(names = "Photon.Run2011A-PromptReco-v4.AOD.Bryn1", )
        data += specify(names = "Photon.Run2011A-PromptReco-v6.AOD.Bryn1", )
        data += specify(names = "Photon.Run2011B-PromptReco-v1.AOD.Bryn1", )
        data += specify(names = "Photon.Run2011B-PromptReco-v1.AOD.Bryn2", )
        data += specify(names = "Photon.Run2011B-PromptReco-v1.AOD.Bryn3", )

        return (data)

    def conclude(self,pars) :
        #make a pdf file with plots from the histograms created above
        org = self.organizer(pars)
        org.mergeSamples(targetSpec = {"name":"2011 Data", "color":r.kBlack, "markerStyle":20}, allWithPrefix = "Photon.Run2011")
        org.scale()
        plotter.plotter( org,
                         doLog = False,
                         psFileName = self.psFileName(org.tag),
                         ).plotAll()
