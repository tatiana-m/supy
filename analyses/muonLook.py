#!/usr/bin/env python

from core import analysis,organizer,plotter,utils
import os,steps,calculables,samples
import ROOT as r

class muonLook(analysis.analysis) :
    def parameters(self) :
        objects = self.vary()
        fields =                                                  [ "jet",                        "jetId",     "muonsInJets",           "met",
                                                                    "compJet",                "compJetId", "compMuonsInJets",        "compMet",
                                                                    "muon",                    "electron",          "photon",         "rechit"]

        objects["caloAK5JetMet_recoLepPhot"]   = dict(zip(fields, [("xcak5Jet","Pat"),       "JetIDloose",             False, "metP4AK5TypeII",
                                                                   ("xcak5JetPF","Pat"),     "JetIDtight",              True,        "metP4PF",
                                                                   ("muon","Pat"),     ("electron","Pat"),  ("photon","Pat"),           "Calo",
                                                                   ]))
        
        #objects["pfAK5JetMet_recoLepPhot"]     = dict(zip(fields, [("xcak5JetPF","Pat"),     "JetIDtight",              True,        "metP4PF",
        #                                                           ("xcak5Jet","Pat"),       "JetIDloose",             False, "metP4AK5TypeII",
        #                                                           ("muon","Pat"),     ("electron","Pat"),  ("photon","Pat"),             "PF",
        #                                                           ]))

        return { "objects": objects,
                 #"nJetsMinMax" :      dict([ ("ge2",(2,None)),  ("2",(2,2)),  ("ge3",(3,None)),  ("3",(3,3)) ]       [0:1] ),
                 #"mcSoup" :           dict([ ("pythia6","py6"), ("pythia8","py8"), ("madgraph","mg") ] [0:1] ),
                 "etRatherThanPt" : [True,False][0],
                 "lowPtThreshold" : 30.0,
                 "lowPtName" : "lowPt",
                 "highPtThreshold" : 50.0,
                 "highPtName" : "highPt",
                 "tanBeta" : [None, 3, 10, 50][0],
                 "thresholds": self.vary(dict( [("275",        (275.0, 325.0, 100.0, 50.0)),#0
                                                ("325",        (325.0, 375.0, 100.0, 50.0)),#1
                                                ("375",        (375.0, None,  100.0, 50.0)),#2
                                                ("325_scaled", (325.0, 375.0,  86.7, 43.3)),#3
                                                ("275_scaled", (275.0, 325.0,  73.3, 36.7)),#4
                                                ("225_scaled", (225.0, 275.0,  60.0, 30.0)),#5
                                                ][2:] )),

                 "triggerList":tuple(["HLT_Mu15_v%d" %i for i in range(2,7)]+
                                     ["HLT_Mu20_v%d" %i for i in range(1,6)]+
                                     ["HLT_Mu24_v%d" %i for i in range(1,6)]+
                                     ["HLT_Mu30_v%d" %i for i in range(1,6)]+
                                     ["HLT_Mu40_v%d" %i for i in range(1,4)]+
                                     ["HLT_Mu100_v%d"%i for i in range(1,4)])
                 }

    def calcListJet(self, obj, etRatherThanPt, ptMin, lowPtThreshold, lowPtName, highPtThreshold, highPtName) :
        def calcList(jet, met, photon, muon, electron, muonsInJets, jetIdFlag) :
            outList = [
                calculables.XClean.xcJet(jet,
                                         applyResidualCorrectionsToData = False,
                                         gamma = photon,
                                         gammaDR = 0.5,
                                         muon = muon,
                                         muonDR = 0.5,
                                         correctForMuons = not muonsInJets,
                                         electron = electron,
                                         electronDR = 0.5),
                calculables.Jet.Indices( jet, ptMin = ptMin,           etaMax = 3.0, flagName = jetIdFlag),
                calculables.Jet.Indices( jet, ptMin = lowPtThreshold,  etaMax = 3.0, flagName = jetIdFlag, extraName = lowPtName),
                calculables.Jet.Indices( jet, ptMin = highPtThreshold, etaMax = 3.0, flagName = jetIdFlag, extraName = highPtName),
                
                calculables.Jet.SumP4(jet),
                calculables.Jet.SumP4(jet, extraName = lowPtName),
                calculables.Jet.SumP4(jet, extraName = highPtName),
                calculables.Jet.DeltaPhiStar(jet, extraName = lowPtName),
                calculables.Jet.DeltaPseudoJet(jet, etRatherThanPt),
                calculables.Jet.AlphaT(jet, etRatherThanPt),
                calculables.Jet.AlphaTMet(jet, etRatherThanPt, met),
                calculables.Jet.MhtOverMet((jet[0], jet[1]+highPtName), met = "%sPlus%s%s"%(obj["met"], obj["muon"][0], obj["muon"][1])),                
                calculables.Jet.deadEcalDR(jet, extraName = lowPtName, minNXtals = 10),
                ]
            return outList+calculables.fromCollections(calculables.Jet, [jet])

        outList = calcList(obj["jet"], obj["met"], obj["photon"], obj["muon"], obj["electron"], obj["muonsInJets"], obj["jetId"])
        if all([("comp"+item in obj) for item in ["Jet", "Met","MuonsInJets","JetId"]]) :
            outList += calcList(obj["compJet"], obj["compMet"], obj["photon"], obj["muon"], obj["electron"], obj["compMuonsInJets"], obj["compJetId"])
        return outList

    def calcListOther(self, obj, triggers) :
        return [
            calculables.XClean.IndicesUnmatched(collection = obj["photon"], xcjets = obj["jet"], DR = 0.5),
            calculables.XClean.IndicesUnmatched(collection = obj["electron"], xcjets = obj["jet"], DR = 0.5),

            calculables.Muon.Indices( obj["muon"], ptMin = 10, combinedRelIsoMax = 0.15),
            calculables.Electron.Indices( obj["electron"], ptMin = 10, simpleEleID = "95", useCombinedIso = True),
            calculables.Photon.Indices(obj["photon"],  ptMin = 25, flagName = "photonIDLooseFromTwikiPat"),
            #calculables.Photon.Indices(obj["photon"],  ptMin = 25, flagName = "photonIDTightFromTwikiPat"),

            calculables.Other.metPlusParticles(met = obj["met"], particles = obj["muon"]),
            calculables.Other.SumP4(obj["muon"]),
            
            calculables.Vertex.ID(),
            calculables.Vertex.Indices(),
            calculables.Other.lowestUnPrescaledTrigger(triggers),
            ]
    
    def listOfCalculables(self, params) :
        obj = params["objects"]
        outList  = calculables.zeroArgs()
        outList += calculables.fromCollections(calculables.Muon, [obj["muon"]])
        outList += calculables.fromCollections(calculables.Electron, [obj["electron"]])
        outList += calculables.fromCollections(calculables.Photon, [obj["photon"]])
        outList += self.calcListOther(obj, params["triggerList"])
        outList += self.calcListJet(obj, params["etRatherThanPt"], params["thresholds"][3],
                                    params["lowPtThreshold"], params["lowPtName"], params["highPtThreshold"], params["highPtName"])
        return outList
    
    def listOfSteps(self, params) :
        _jet = params["objects"]["jet"]
        _electron = params["objects"]["electron"]
        _muon = params["objects"]["muon"]
        _photon = params["objects"]["photon"]
        _met  = params["objects"]["met"]
        _etRatherThanPt = params["etRatherThanPt"]
        _et = "Et" if _etRatherThanPt else "Pt"

        htUpper = [steps.Other.variableLessFilter(params["thresholds"][1],"%sSum%s%s"%(_jet[0], _et, _jet[1]), "GeV")] if params["thresholds"][1]!=None else []
        return [
            steps.Print.progressPrinter(),
            steps.Trigger.lowestUnPrescaledTriggerFilter(),
            steps.Trigger.l1Filter("L1Tech_BPTX_plus_AND_minus.v0"),
            
            steps.Trigger.physicsDeclaredFilter(),
            steps.Other.monsterEventFilter(),
            steps.Other.histogrammer("genpthat",200,0,1000,title=";#hat{p_{T}} (GeV);events / bin"),
            steps.Trigger.hltPrescaleHistogrammer(params["triggerList"]),

            steps.Filter.pt ("%sP4%s"%_muon, min = 32.0,            indices = "%sIndices%s"%_muon, index = 0),
            steps.Filter.eta("%sP4%s"%_muon, min = -2.1, max = 2.1, indices = "%sIndices%s"%_muon, index = 0),
            ]+(
            steps.Other.multiplicityPlotFilter("vertexIndices",     nMin = 1,           xlabel = "N vertices") +
            steps.Other.multiplicityPlotFilter("%sIndices%s"%_muon, nMin = 2, nMax = 2, xlabel = "N muons")
            )+[
            #steps.Other.skimmer(),            
            
            steps.Muon.muonHistogrammer(_muon, 1),
            steps.Muon.diMuonHistogrammer(_muon),
            steps.Filter.value("%sDiMuonMass%s"%_muon, min = 80.0, max = 110.0),
            steps.Other.histogrammer("%sDiMuonMass%s"%_muon, 80, 50., 130., title = ";#mu#mu mass (GeV);events / bin"),
            
            ]+(
            steps.Other.multiplicityPlotFilter("%sIndices%s"%_electron,          nMax = 0, xlabel = "N electrons") +
            steps.Other.multiplicityPlotFilter("%sIndices%s"%_photon,            nMax = 0, xlabel = "N photons") +
            steps.Other.multiplicityPlotFilter("%sIndicesOther%s"%_jet,          nMax = 0, xlabel = "number of %s%s above p_{T}#semicolon failing ID or #eta"%_jet) +
            steps.Other.multiplicityPlotFilter("%sIndicesOther%s"%_muon,         nMax = 0, xlabel = "number of %s%s above p_{T}#semicolon failing ID or #eta"%_muon) +
            steps.Other.multiplicityPlotFilter("%sIndicesUnmatched%s"%_electron, nMax = 0, xlabel = "N electrons unmatched") +
            steps.Other.multiplicityPlotFilter("%sIndicesUnmatched%s"%_photon,   nMax = 0, xlabel = "N photons unmatched") +
            steps.Other.multiplicityPlotFilter("%sIndices%s"%_jet, nMin = 2, xlabel="number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts"%_jet)
            )+[
            steps.Jet.uniquelyMatchedNonisoMuons(_jet), 
            
            #many plots
            steps.Trigger.lowestUnPrescaledTriggerHistogrammer(),
            steps.Other.passFilter("singleJetPlots1"),
            steps.Jet.singleJetHistogrammer(_jet, 1),
            steps.Other.passFilter("jetSumPlots1"), 
            steps.Jet.cleanJetHtMhtHistogrammer(_jet,_etRatherThanPt),
            steps.Other.histogrammer("%sSum%s%s"%(_jet[0], _et, _jet[1]), 50, 0, 2500, title = ";H_{T} (GeV) from %s%s %ss;events / bin"%(_jet[0], _jet[1], _et)),
            
            #ht and leading jet cuts
            steps.Other.variableGreaterFilter(params["thresholds"][0],"%sSum%s%s"%(_jet[0], _et, _jet[1]), "GeV"),
            ] + htUpper + [
            steps.Jet.jetPtSelector(_jet, params["thresholds"][2], 0),
            steps.Jet.jetPtSelector(_jet, params["thresholds"][2], 1),
            steps.Jet.jetEtaSelector(_jet,2.5,0),
            
            #mht/ht cut
            steps.Filter.value("%sMhtOverHt%s"%_jet, min = 0.4),
            steps.Other.histogrammer("%sIndices%s"%_jet, 20, -0.5, 19.5,
                                     title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet, funcString="lambda x:len(x)"),
            
            #some histograms
            #steps.Other.histogrammer("%sDeltaPhiStar%s%s"%(_jet[0], _jet[1], params["lowPtName"]), 20, 0.0, r.TMath.Pi(),
            #                         title = ";#Delta#phi*;events / bin", funcString = 'lambda x:x["DeltaPhiStar"]'),
            #steps.Other.histogrammer(_met,100,0.0,500.0,title=";"+_met+" (GeV);events / bin", funcString = "lambda x: x.pt()"),
            #steps.Other.passFilter("kinematicPlots1"),
            #
            steps.Other.deadEcalFilter(jets = _jet, extraName = params["lowPtName"], dR = 0.3, dPhiStarCut = 0.5),
            
            ##play with boson pT
            #steps.Filter.pt("%sDiMuon%s"%_muon, min =   0.0),
            #steps.Other.histogrammer("%sIndices%s"%_jet, 20, -0.5, 19.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet, funcString="lambda x:len(x)"),
            #steps.Filter.pt("%sDiMuon%s"%_muon, min =  50.0),
            #steps.Other.histogrammer("%sIndices%s"%_jet, 20, -0.5, 19.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet, funcString="lambda x:len(x)"),
            #steps.Filter.pt("%sDiMuon%s"%_muon, min = 100.0),
            #steps.Other.histogrammer("%sIndices%s"%_jet, 20, -0.5, 19.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet, funcString="lambda x:len(x)"),
            #steps.Filter.pt("%sDiMuon%s"%_muon, min = 150.0),
            #steps.Other.histogrammer("%sIndices%s"%_jet, 20, -0.5, 19.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet, funcString="lambda x:len(x)"),
            
            steps.Other.histogrammer("%sMht%sOver%s" %(_jet[0], _jet[1]+params["highPtName"], _met+"Plus%s%s"%_muon), 100, 0.0, 3.0,
                                     title = ";MHT %s%s / %s;events / bin"%(_jet[0], _jet[1], _met+"Plus%s%s"%_muon)),
            steps.Other.variableLessFilter(1.25,"%sMht%sOver%s" %(_jet[0], _jet[1]+params["highPtName"], _met+"Plus%s%s"%_muon)),
            
            #alphaT cut
            steps.Jet.alphaHistogrammer(cs = _jet, deltaPhiStarExtraName = params["lowPtName"], etRatherThanPt = _etRatherThanPt),
            #steps.Jet.alphaMetHistogrammer(cs = _jet, deltaPhiStarExtraName = params["lowPtName"], etRatherThanPt = _etRatherThanPt, metName = _met),
            #
            steps.Other.variableGreaterFilter(0.55,"%sAlphaT%s%s"%(_jet[0],"Et" if _etRatherThanPt else "Pt",_jet[1])),
            ##]), #end cutSorter
            #
            #steps.Other.histogrammer("vertexIndices", 20, -0.5, 19.5, title=";N vertices;events / bin", funcString="lambda x:len(x)"),
            steps.Other.histogrammer("%sIndices%s"%_jet, 20, -0.5, 19.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet, funcString="lambda x:len(x)"),
            
            #out of stats
            #steps.Jet.cleanJetHtMhtHistogrammer(_jet,_etRatherThanPt),
            #steps.Other.histogrammer("%sDeltaPhiStar%s%s"%(_jet[0], _jet[1], params["lowPtName"]), 20, 0.0, r.TMath.Pi(), title = ";#Delta#phi*;events / bin", funcString = 'lambda x:x["DeltaPhiStar"]'),
            
            #steps.Other.skimmer(),
            #steps.Other.cutBitHistogrammer(self.togglePfJet(_jet), self.togglePfMet(_met)),
            #steps.Print.eventPrinter(),
            #steps.Print.jetPrinter(_jet),
            #steps.Print.particleP4Printer(_muon),
            #steps.Print.particleP4Printer(_photon),
            #steps.Print.recHitPrinter("clusterPF","Ecal"),
            #steps.Print.htMhtPrinter(_jet),
            #steps.Print.alphaTPrinter(_jet,_etRatherThanPt),
            #steps.Gen.genParticlePrinter(minPt=10.0,minStatus=3),
            #       
            #steps.Other.pickEventSpecMaker(),
            #steps.Displayer.displayer(jets = _jet,
            #                          muons = _muon,
            #                          met       = params["objects"]["met"],
            #                          electrons = params["objects"]["electron"],
            #                          photons   = params["objects"]["photon"],                            
            #                          recHits   = params["objects"]["rechit"],recHitPtThreshold=1.0,#GeV
            #                          scale = 400.0,#GeV
            #                          etRatherThanPt = _etRatherThanPt,
            #                          deltaPhiStarExtraName = params["lowPtName"],
            #                          deltaPhiStarCut = 0.5,
            #                          deltaPhiStarDR = 0.3,
            #                          mhtOverMetName = "%sMht%sOver%s"%(_jet[0], _jet[1]+params["highPtName"], _met+"Plus%s%s"%_muon),
            #                          jetsOtherAlgo = params["objects"]["compJet"],
            #                          metOtherAlgo  = params["objects"]["compMet"],
            #                          markusMode = False,
            #                          ),
            steps.Other.histogrammer("%sSumEt%s"%_jet, 40, 0, 1000, title = ";H_{T} (GeV) from %s%s E_{T}s;events / bin"%_jet),
            ] + [steps.Other.variableGreaterFilter(375.0+100*iBin, "%sSumEt%s"%_jet, suffix = "GeV") for iBin in range(1,6)]
    
    def listOfSampleDictionaries(self) :
        return [samples.MC.mc, samples.Muon.muon]

    def listOfSamples(self,params) :
        from samples import specify

        def data() :
            jw = calculables.Other.jsonWeight("cert/Cert_160404-167151_7TeV_PromptReco_Collisions11_JSON.txt") #869/pb            
            out = []
            out += specify(names = "SingleMu.Run2011A-PR-v4.FJ.Burt2_2mu_skim",   weights = jw, overrideLumi = 216.43)
            out += specify(names = "SingleMu.Run2011A-PR-v4.FJ.Burt_2mu_skim",    weights = jw, overrideLumi = 294.45)
            out += specify(names = "SingleMu.Run2011A-May10-v1.FJ.Burt_2mu_skim", weights = jw, overrideLumi = 186.55)
            return out

        eL = 3000 # 1/pb
        #return data()
        return (data() +\
                specify(names = "tt_tauola_mg_2mu_skim", effectiveLumi = eL) +\
                specify(names = "dyll_jets_mg_2mu_skim", effectiveLumi = eL) +\
                specify(names = "w_jets_mg_2mu_skim",    effectiveLumi = eL)
                )
    
    def conclude(self, conf) :
        org = self.organizer(conf)

        ##for skimming only
        #utils.printSkimResults(org)            

        lineWidth = 3; goptions = "hist"
        org.mergeSamples(targetSpec = {"name":"2011 Data", "color":r.kBlack, "markerStyle":20}, allWithPrefix="SingleMu.Run2011A")
        org.mergeSamples(targetSpec = {"name":"t#bar{t}",  "color":r.kOrange, "lineWidth":lineWidth, "goptions":goptions}, allWithPrefix="tt")
        org.mergeSamples(targetSpec = {"name":"DY->ll",    "color":r.kBlue,   "lineWidth":lineWidth, "goptions":goptions}, allWithPrefix="dyll")
        org.mergeSamples(targetSpec = {"name":"W + jets",  "color":r.kRed,    "lineWidth":lineWidth, "goptions":goptions}, allWithPrefix="w_jets")
        org.mergeSamples(targetSpec = {"name":"s.m.",      "color":r.kGreen,  "lineWidth":lineWidth, "goptions":goptions},
                         sources = ["t#bar{t}", "DY->ll", "W + jets"], keepSources = True)
        
        org.scale() if not self.parameters()["tanBeta"] else org.scale(100.0)
            
        #plot
        pl = plotter.plotter(org,
                             psFileName = self.psFileName(org.tag),
                             samplesForRatios = ("2011 Data","DY->ll"),
                             sampleLabelsForRatios = ("data","DY"),
                             showStatBox = True,
                             #doLog = False,
                             linYAfter = ("value", "0.40<=xcak5JetMhtOverHtPat"),
                             pegMinimum = 0.1,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             )
        pl.plotAll()
