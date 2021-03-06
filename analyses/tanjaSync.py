#!/usr/bin/env python

import os,analysis,steps,calculables,samples,organizer,plotter
import ROOT as r

class tanjaSync(analysis.analysis) :
    def parameters(self) :
        objects = {}
        fields =                              [ "jet",             "met",            "muon",        "electron",        "photon",       "rechit", "muonsInJets", "jetPtMin"] 
        #objects["caloAK5_pfMET"] = dict(zip(fields, [("ak5Jet","Pat"), "metP4PF", ("muon","Pat"),("electron","Pat"),("photon","Pat"), "Calo" ,    False,        50.0]))
        objects["caloAK5"] = dict(zip(fields, [("ak5Jet","Pat"), "metP4AK5TypeII",("muon","Pat"),("electron","Pat"),("photon","Pat"), "Calo" ,    False,        50.0]))
        #objects["caloAK7"] = dict(zip(fields, [("xcak7Jet","Pat"), "metP4AK5TypeII",("muon","Pat"),("electron","Pat"),("photon","Pat"), "Calo" ,    False,        50.0]))
        #objects["jptAK5"]  = dict(zip(fields, [("xcak5JetJPT","Pat"),"metP4TC",     ("muon","Pat"),("electron","Pat"),("photon","Pat"), "Calo",     True ,        50.0]))
        #objects["pfAK5"]   = dict(zip(fields, [("xcak5JetPF","Pat"), "metP4PF",     ("muon","PF"), ("electron","PF"), ("photon","Pat"), "PF"  ,     True ,        50.0]))

        return { "objects": objects,
                 "nJetsMinMax" :      dict([ ("ge2",(2,None)),  ("2",(2,2)),  ("ge3",(3,None)) ]       [0:1] ),
                 "mcSoup" :           dict([ ("pythia6","py6"), ("pythia8","py8"), ("madgraph","mg") ] [0:1] ),
                 "jetId" :  ["JetIDloose","JetIDtight"] [0],
                 "etRatherThanPt" : [True,False]        [0],
                 #"jesAbs":  [1.0,1.1,0.9]               [:],
                 #"jesRel":  0,
                 }

    def listOfCalculables(self,params) :
        _jet = params["objects"]["jet"]
        _muon = params["objects"]["muon"]
        _electron = params["objects"]["electron"]
        _photon = params["objects"]["photon"]
        _jetPtMin = params["objects"]["jetPtMin"]
        _etRatherThanPt = params["etRatherThanPt"]
        _met = params["objects"]["met"]
        _correctForMuons = not params["objects"]["muonsInJets"]

        lowPtThreshold = 30.0
        lowPtName = "lowPt"
        
        return calculables.zeroArgs() +\
               calculables.fromCollections("calculablesJet",[_jet]) +\
               calculables.fromCollections("calculablesMuon",[_muon]) +\
               calculables.fromCollections("calculablesElectron",[_electron]) +\
               calculables.fromCollections("calculablesPhoton",[_photon]) +\
               [ #calculables.xcJet(_jet,
                 #                  gamma = _photon,
                 #                  gammaDR = 0.5,
                 #                  muon = _muon,
                 #                  muonDR = 0.5,
                 #                  correctForMuons = _correctForMuons,
                 #                  electron = _electron,
                 #                  electronDR = 0.5),
                 calculables.jetIndices( _jet, _jetPtMin,      etaMax = 3.0, flagName = params["jetId"]),
                 calculables.jetIndices( _jet, lowPtThreshold, etaMax = 3.0, flagName = params["jetId"], extraName = lowPtName),
                 calculables.muonIndices( _muon, ptMin = 10, combinedRelIsoMax = 0.15),
                 calculables.electronIndices( _electron, ptMin = 10, simpleEleID = "95", useCombinedIso = True),
                 #calculables.photonIndicesPat(  ptMin = 25, flagName = "photonIDLoosePat"),
                 calculables.photonIndicesPat(  ptMin = 25, flagName = "photonIDloosePat"),
                 #calculables.indicesUnmatched(collection = _photon, xcjets = _jet, DR = 0.5),
                 #calculables.indicesUnmatched(collection = _electron, xcjets = _jet, DR = 0.5)
                 ] \
                 + [ calculables.jetSumP4(_jet, mcScaleFactor = 1.0),
                     calculables.deltaPhiStar(_jet, ptMin = lowPtThreshold, extraName = lowPtName),
                     calculables.deltaPseudoJet(_jet, _etRatherThanPt),
                     calculables.alphaT(_jet, _etRatherThanPt),
                     calculables.alphaTMet(_jet, _etRatherThanPt, _met),
                    #calculables.mhtMinusMetOverMeff(_jet, _met, _etRatherThanPt),
                     calculables.mhtMinusMetOverMeff(_jet, "metP4PF", _etRatherThanPt),
                     ]

    def listOfSteps(self,params) :
        _jet  = params["objects"]["jet"]
        _electron = params["objects"]["electron"]
        _muon = params["objects"]["muon"]
        _photon = params["objects"]["photon"]
        _met  = params["objects"]["met"]
        _etRatherThanPt = params["etRatherThanPt"]

        outList=[
            steps.progressPrinter(),

            steps.hbheNoiseFilter(),
            steps.vertexRequirementFilter(),
            steps.techBitFilter([0],True),
            steps.physicsDeclared(),
            steps.monsterEventFilter(),
            steps.hltFilter("HLT_HT100U"),
            
            steps.histogrammer("%sIndicesOther%s"%_jet,10,-0.5,9.5, title=";number of %s%s above p_{T}#semicolon failing ID or #eta;events / bin"%_jet,
                               funcString="lambda x:len(x)"),
            steps.multiplicityFilter("%sIndicesOther%s"%_jet, nMax = 0),
            
            steps.histogrammer("%sIndices%s"%_jet,10,-0.5,9.5, title=";number of %s%s passing ID#semicolon p_{T}#semicolon #eta cuts;events / bin"%_jet,
                               funcString="lambda x:len(x)"),
            steps.multiplicityFilter("%sIndices%s"%_jet, nMin = params["nJetsMinMax"][0], nMax = params["nJetsMinMax"][1]),

            steps.preIdJetPtSelector(_jet,100.0,0),
            steps.jetEtaSelector(_jet,2.5,0),

            steps.preIdJetPtSelector(_jet,100.0,1),

            steps.variableGreaterFilter(350.0,"%sSumEt%s"%_jet, suffix = "GeV"),

            #steps.runLsEventFilter("tanjasEvents.txt"),
            #electron, muon, photon vetoes
            steps.multiplicityFilter("%sIndices%s"%_muon, nMax = 0),
            #steps.multiplicityFilter("%sIndicesOther%s"%_muon, nMax = 0),
            steps.multiplicityFilter("%sIndicesNonIso%s"%_muon, nMax = 0),
            steps.multiplicityFilter("%sIndices%s"%_electron, nMax = 0),
            #steps.multiplicityFilter("%sIndices%s"%_photon, nMax = 0),
            #steps.multiplicityFilter("%sIndicesUnmatched%s"%_electron, nMax = 0),
            #steps.multiplicityFilter("%sIndicesUnmatched%s"%_photon, nMax = 0),
            #steps.uniquelyMatchedNonisoMuons(_jet),
            
            ####many plots
            ###steps.passFilter("singleJetPlots1"),
            ###steps.singleJetHistogrammer(_jet),
            ###steps.passFilter("jetSumPlots1"), 
            ###steps.cleanJetHtMhtHistogrammer(_jet,_etRatherThanPt),
            ###steps.histogrammer(_met,100,0.0,500.0,title=";"+_met+" (GeV);events / bin", funcString = "lambda x: x.pt()"),
            ###steps.passFilter("kinematicPlots1"), 
            ###steps.alphaHistogrammer(_jet, _etRatherThanPt),
            ###steps.alphaMetHistogrammer(_jet, _etRatherThanPt, _met),
            ###
            ####signal selection
            ###steps.variablePtGreaterFilter(140.0,"%sSumP4%s"%_jet,"GeV"),
            steps.variableGreaterFilter(0.55,"%sAlphaT%s"%_jet),
            ###steps.histogrammer("mhtMinusMetOverMeff", 100, -1.0, 1.0, title = ";(MHT - PFMET)/(MHT+HT);events / bin"),
            ###steps.variableLessFilter(0.15,"mhtMinusMetOverMeff"),
            ###steps.deadEcalFilter(jets = _jet, dR = 0.3, dPhiStarCut = 0.5, nXtalThreshold = 5),
            #####steps.variableGreaterFilter(0.53,"%sAlphaTMet%s"%_jet),
            ###
            ####steps.skimmer(),
            ####steps.eventPrinter(),
            ####steps.jetPrinter(_jet),
            ####steps.particleP4Printer(_muon),
            ####steps.particleP4Printer(_photon),
            ####steps.recHitPrinter("clusterPF","Ecal"),
            ####steps.htMhtPrinter(_jet),
            ####steps.alphaTPrinter(_jet,_etRatherThanPt),
            ####steps.genParticlePrinter(minPt=10.0,minStatus=3),
            ####
            ####steps.displayer(jets = _jet,
            ####                muons = _muon,
            ####                met       = params["objects"]["met"],
            ####                electrons = params["objects"]["electron"],
            ####                photons   = params["objects"]["photon"],                            
            ####                recHits   = params["objects"]["rechit"],recHitPtThreshold=1.0,#GeV
            ####                scale = 400.0,#GeV
            ####                etRatherThanPt = _etRatherThanPt,
            ####                ),
            
            ]
        return outList

    def listOfSampleDictionaries(self) :
        return [samples.mc, samples.jetmet]

    def listOfSamples(self,params) :
        from samples import specify
        data = [                                                
           specify(name = "Tanja_sync",                nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "Run2010B_J_skim1",          nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "Run2010B_J_skim2",          nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "Run2010A_JM_skim",          nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "Run2010A_JMT_skim",         nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "2010_data_skim_calo",       nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "2010_data_skim_pf",         nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
          #specify(name = "test",                      nFilesMax = -1, color = r.kBlack   , markerStyle = 20),
            ]                                                       
        qcd_py6 = [                                                 
          ##specify(name = "v12_qcd_py6_pt30",          nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_py6_pt80",          nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_py6_pt170",         nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_py6_pt300",         nFilesMax = -1, color = r.kBlue    ),
          ##specify(name = "v12_qcd_py6_pt470",         nFilesMax = -1, color = r.kBlue    ),
          ##specify(name = "v12_qcd_py6_pt800",         nFilesMax = -1, color = r.kBlue    ),
          ##specify(name = "v12_qcd_py6_pt1400",        nFilesMax = -1, color = r.kBlue    ),
            ]                                                       
        g_jets_py6 = [                                              
            specify(name = "v12_g_jets_py6_pt30",       nFilesMax = -1, nEventsMax = 1000000, color = r.kGreen),
            specify(name = "v12_g_jets_py6_pt80",       nFilesMax = -1, nEventsMax =  100000, color = r.kGreen),
            specify(name = "v12_g_jets_py6_pt170",      nFilesMax = -1, nEventsMax =  100000, color = r.kGreen),
            ]                                                       
        qcd_py8 = [                                                 
          ##specify(name = "qcd_py8_pt0to15",           nFilesMax = -1, color = r.kBlue    ),
          ##specify(name = "qcd_py8_pt15to30",          nFilesMax = -1, color = r.kBlue    ),
          ##specify(name = "qcd_py8_pt30to50",          nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt50to80",          nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt80to120",         nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt120to170",        nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt170to300",        nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt300to470",        nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt470to600",        nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt600to800",        nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt800to1000",       nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt1000to1400",      nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt1400to1800",      nFilesMax = -1, color = r.kBlue    ),
            specify(name = "qcd_py8_pt1800",            nFilesMax = -1, color = r.kBlue    ),
            ]                                                       
        qcd_mg = [                                                  
            specify(name = "v12_qcd_mg_ht_50_100",      nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_mg_ht_100_250",     nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_mg_ht_250_500",     nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_mg_ht_500_1000",    nFilesMax = -1, color = r.kBlue    ),
            specify(name = "v12_qcd_mg_ht_1000_inf",    nFilesMax = -1, color = r.kBlue    ),
            ]                                                       
        g_jets_mg = [                                               
            specify(name = "v12_g_jets_mg_pt40_100",    nFilesMax = -1, color = r.kGreen   ),
            specify(name = "v12_g_jets_mg_pt100_200",   nFilesMax = -1, color = r.kGreen   ),
            specify(name = "v12_g_jets_mg_pt200",       nFilesMax = -1, color = r.kGreen   ),
            ]                                                       
        ttbar_mg = [                                                
            specify(name = "tt_tauola_mg_v12",          nFilesMax =  3, color = r.kOrange  ),
            ]                                                       
        ewk = [                                                     
            specify(name = "z_inv_mg_skim_v12",         nFilesMax = -1, color = r.kMagenta ),
            specify(name = "z_jets_mg_skim_v12",        nFilesMax = -1, color = r.kYellow-3),
            specify(name = "w_jets_mg_skim_v12",        nFilesMax = -1, color = 28         ),
            ]                                                       
        susy = [                                                    
            specify(name = "lm0_v12",                   nFilesMax = -1, color = r.kRed     ),
            specify(name = "lm1_v12",                   nFilesMax = -1, color = r.kRed+1   ),
            ]                                                   

        outList = []
        #if params["mcSoup"]=="py6" :
        #    outList+=qcd_py6
        #    outList+=g_jets_py6
        #    
        #if params["mcSoup"]=="py8" :
        #    outList+=qcd_py8
        #    outList+=g_jets_py6#no py8 available
        #    
        #if params["mcSoup"]=="mg":
        #    outList+=qcd_mg
        #    outList+=g_jets_mg

        outList+=data
        #outList+=ttbar_mg
        #outList+=ewk
        #outList+=susy

        ##uncomment for short tests
        #for i in range(len(outList)):
        #    o = outList[i]
        #    #if "2010" in o.name: continue
        #    outList[i] = specify(name = o.name, color = o.color, markerStyle = o.markerStyle, nFilesMax = 1, nEventsMax = 1000)
        
        return outList

    def mergeSamples(self, org, tag) :
        def py6(org, smSources) :
            org.mergeSamples(targetSpec = {"name":"qcd_py6_v12", "color":r.kBlue},
                             sources = ["v12_qcd_py6_pt%d"%i      for i in [80,170,300] ])
            smSources.append("qcd_py6_v12")

            org.mergeSamples(targetSpec = {"name":"g_jets_py6_v12", "color":r.kGreen},
                             sources = ["v12_g_jets_py6_pt%d"%i      for i in [30,80,170] ])
            smSources.append("g_jets_py6_v12")

        def py8(org, smSources) :
            lowerPtList = [0,15,30,50,80,120,170,300,470,600,800,1000,1400,1800]
            sources = ["qcd_py8_pt%dto%d"%(lowerPtList[i],lowerPtList[i+1]) for i in range(len(lowerPtList)-1)]
            sources.append("qcd_py8_pt%d"%lowerPtList[-1])
            org.mergeSamples(targetSpec = {"name":"qcd_py8", "color":r.kBlue}, sources = sources)
            smSources.append("qcd_py8")

            org.mergeSamples(targetSpec = {"name":"g_jets_py6_v12", "color":r.kGreen},
                             sources = ["v12_g_jets_py6_pt%d"%i      for i in [30,80,170] ])
            smSources.append("g_jets_py6_v12")

        def mg(org, smSources) :
            org.mergeSamples(targetSpec = {"name":"qcd_mg_v12", "color":r.kBlue},
                             sources = ["v12_qcd_mg_ht_%s"%bin for bin in ["50_100","100_250","250_500","500_1000","1000_inf"] ])
            smSources.append("qcd_mg_v12")
            
            org.mergeSamples(targetSpec = {"name":"g_jets_mg_v12", "color":r.kGreen},
                             sources = ["v12_g_jets_mg_pt%s"%bin for bin in ["40_100","100_200","200"] ])
            smSources.append("g_jets_mg_v12")

        smSources = ["tt_tauola_mg_v12", "z_inv_mg_skim_v12", "z_jets_mg_skim_v12", "w_jets_mg_skim_v12"]
        if "pythia6"  in tag : py6(org, smSources)
        if "pythia8"  in tag : py8(org, smSources)
        if "madgraph" in tag : mg (org, smSources)
        org.mergeSamples(targetSpec = {"name":"standard_model", "color":r.kGreen+3}, sources = smSources, keepSources = True)
        org.mergeSamples(targetSpec = {"name":"2010 Data", "color":r.kBlack, "markerStyle":20},
                         sources = ["Run2010B_J_skim1","Run2010B_J_skim2","Run2010A_JM_skim","Run2010A_JMT_skim"])
        
    def conclude(self) :
        for tag in self.sideBySideAnalysisTags() :
            #organize
            org=organizer.organizer( self.sampleSpecs(tag) )
            self.mergeSamples(org, tag)
            org.scale()

            pl = plotter.plotter(org,
                                 psFileName = self.psFileName(tag),
                                 samplesForRatios=("2010 Data","standard_model"),
                                 sampleLabelsForRatios=("data","s.m."),
                                 )
            pl.plotAll()

