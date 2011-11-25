#!/usr/bin/env python

from core import analysis,plotter,utils
import calculables,steps,samples, ROOT as r

class pileup_study(analysis.analysis) :

    def parameters(self) :
        return {"jets" : ("ak5Jet","Pat"),
                "minJetPt" : 50.0,
                }
    
    def listOfSteps(self,config) :
        _jet = config["jets"]
        minJetPt = config["minJetPt"]
        
        outList=[
            steps.Print.progressPrinter(),
            steps.Other.histogrammer("vertexIndices", 20, -0.5, 19.5, title=";N vertices;events / bin", funcString="lambda x:len(x)"),       
            steps.Other.histogrammer("%sSumEt%s"%(_jet[0], _jet[1]), 50, 0, 1000,
                                     title = ";H_{T} (GeV) from %s%s ;events / bin"%(_jet[0], _jet[1])),


            steps.Other.histogrammer("%sIndices%s"%_jet,10,-0.5,9.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet,
                                                           funcString="lambda x:len(x)"),


            #steps.Other.skimmer(),
            ]
        return outList
    
    def listOfCalculables(self,config) :
        jets = config["jets"]
        minJetPt = config["minJetPt"]
        listOfCalculables = calculables.zeroArgs()
        listOfCalculables += calculables.fromCollections(calculables.Jet,[jets])
        listOfCalculables += [
            calculables.Jet.Indices( jets, ptMin = minJetPt, etaMax = 3.0, flagName = "JetIDloose"),
            calculables.Vertex.ID(),
            calculables.Vertex.Indices(),
            ]
        return listOfCalculables

    def listOfSampleDictionaries(self) :
        exampleDict = samples.SampleHolder()
        exampleDict.add("gJetsMC_spring11", '["/vols01/g_jets_mg_ht_200_inf_spring11_1_0_skim.root"]', xs = 485.0 ) #/pb
        exampleDict.add("gJetsMC_summer11", '["/vols01/g_jets_mg_ht_200_inf_summer11_1_0_skim.root"]', xs = 798.3 ) #pb
        return [exampleDict]

    def listOfSamples(self,config) :
        w = calculables.Photon.summerToSpring(var = "vertexIndices")
        return (samples.specify(names = "gJetsMC_spring11", color = r.kBlack, nFilesMax=1) +
                samples.specify(names = "gJetsMC_summer11", color = r.kRed, nFilesMax=1, weights = w) )

    def conclude(self,pars) :
        #make a pdf file with plots from the histograms created above
        org = self.organizer(pars)
#        org.scale(1000)
        org.scale(toPdf=True)
        dateString = utils.getCommandOutput("date +%H_%M")["stdout"].replace("\n","")
        plotter.plotter( org,
                         psFileName = self.psFileName(org.tag).replace(".ps","%s.ps"%dateString),
                         #samplesForRatios = ("gJetsMC_spring11","gJetsMC_summer11"),
                         samplesForRatios = ("gJetsMC_spring11","gJetsMC_summer11.summerToSpring"),
                         sampleLabelsForRatios = ("Spring11","Summer11"),
                         ).plotAll()
