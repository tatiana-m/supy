import topAsymmShell,steps,calculables,samples,plotter,utils,organizer
import os,math,ROOT as r

class topAsymm(topAsymmShell.topAsymmShell) :
    def parameters(self) :
        pars = super(topAsymm,self).parameters()
        pars["topBsamples"] = { "pythia"   : ("tt_tauola_fj",["tt_tauola_fj.wNonQQbar.nvr",
                                                              "tt_tauola_fj.wTopAsymP00.nvr"
                                                              ]),
                                "madgraph" : ("FIXME",[]),
                                }["pythia"]
        return pars

    def listOfSteps(self, pars) :
        obj = pars["objects"]
        lepton = obj[pars["lepton"]["name"]]
        lPtMin = pars["lepton"]["ptMin"]
        lEtaMax = pars["lepton"]["etaMax"]
        bVar = ("%s"+pars["bVar"]+"%s")%calculables.Jet.xcStrip(obj["jet"])

        return ([
            steps.Print.progressPrinter(),
            steps.Other.histogrammer("genpthat",200,0,1000,title=";#hat{p_{T}} (GeV);events / bin"),
            ] + self.dataCleanupSteps(pars) + [
            calculables.Other.Ratio("nVertex", binning = (15,-0.5,14.5), thisSample = pars['baseSample'],
                                    target = ("SingleMu",[]), groups = [('qcd_mg',[]),
                                                                        ('qcd_py6',[]),
                                                                        ('w_jets_fj_mg',[]),
                                                                        ('tt_tauola_fj',['tt_tauola_fj'+s
                                                                                         for s in ['','.wNonQQbar.nvr','.wTopAsymP00.nvr']])
                                                                        ]),
            ] + self.xcleanSteps(pars) + [
            steps.Histos.value("%sTriggeringPt%s"%lepton, 200,0,200),
            steps.Filter.value("%sTriggeringPt%s"%lepton, min = lPtMin),
            steps.Histos.value(obj["sumPt"],50,0,1500),
            steps.Histos.value("rho",100,0,40),
            ] + self.selectionSteps(pars, withPlots = True) + [
            #steps.Filter.stop(),#####################################
            steps.Filter.multiplicity("TopReconstruction",min=1),
            steps.Histos.value("TopRatherThanWProbability",100,0,1),
            steps.Filter.label("selection complete"),

            calculables.Other.Discriminant( fixes = ("","TopW"),
                                            left = {"pre":"w_jets_fj_mg", "tag":"top_muon_pf", "samples":[]},
                                            right = {"pre":"tt_tauola_fj", "tag":"top_muon_pf", "samples": ['tt_tauola_fj'+s
                                                                                                            for s in ['.wNonQQbar.nvr',
                                                                                                                      '.wTopAsymP00.nvr']]},
                                            dists = {"%sKt%s"%obj["jet"] : (25,0,150),
                                                     "%sB0pt%s"%obj["jet"] : (30,0,300),
                                                     "%s3absEta%s"%obj["jet"] : (20,0,4),
                                                     # |eta| of lepton
                                                     "fitTopHadChi2"     : (20,0,100),
                                                     #"fitTopRawHadWmass" : (30,0,180), 
                                                     #"fitTopChi2"        : (20,0,200),
                                                     "mixedSumP4.pt"     : (30,0,180),
                                                     #"fitTopLeptonPt"    : (30,0,180),  # not so powerful?
                                                     "fitTopDeltaPhiLNu" : (20,0,math.pi),
                                                     "TopRatherThanWProbability" : (20,0,1),
                                                     },
                                            ),
            calculables.Other.Discriminant( fixes = ("","TopQCD"),
                                            left = {"pre":"SingleMu", "tag":"QCD_muon_pf", "samples":[]},
                                            right = {"pre":"tt_tauola_fj", "tag":"top_muon_pf", "samples": ['tt_tauola_fj'+s
                                                                                                            for s in ['.wNonQQbar.nvr',
                                                                                                                      '.wTopAsymP00.nvr']]},
                                            dists = {"%sKt%s"%obj["jet"] : (25,0,150),
                                                     "%sB0pt%s"%obj["jet"] : (30,0,300),
                                                     "%s3absEta%s"%obj["jet"] : (20,0,4),
                                                     "%sMt%s"%obj['muon']+"mixedSumP4" : (30,0,180),
                                                     #"mixedSumP4.pt"     : (30,0,180),
                                                     #"fitTopLeptonPt"    : (30,0,180),
                                                     #"fitTopDeltaPhiLNu" : (20,0,math.pi),
                                                     },
                                            ),
            steps.Filter.stop(),#####################################

            steps.Histos.multiplicity("%sIndices%s"%obj["jet"]),
            steps.Top.discriminateNonTop(pars),
            #steps.Filter.label('dNonQQ'),  steps.Top.discriminateQQbar(('fitTop','')),
            steps.Top.Asymmetry(('fitTop','')),
            steps.Top.kinFitLook("fitTopRecoIndex"),
            ])
    
    def listOfSamples(self,pars) :
        from samples import specify
        def data() :
            names = { "electron": ["SingleElectron.Run2011A-PromptReco-v1.Burt"],
                      "muon": (specify(names = ["SingleMu.Run2011A-PR-v4.FJ.Burt",
                                                "SingleMu.Run2011A-May10-v1.FJ.Burt",
                                                ])+#, nFilesMax = 1, nEventsMax = 1000)+
                               []) }
            return names[pars["lepton"]["name"]]

        def qcd_py6_mu(eL) :
            q6 = [0,5,15,20,30,50,80,120,150,None]
            iCut = q6.index(15)
            return specify( effectiveLumi = eL, color = r.kOrange, weights = "nvr",
                            names = ["qcd_py6fjmu_pt_%s"%("%d_%d"%(low,high) if high else "%d"%low) for low,high in zip(q6[:-1],q6[1:])[iCut:]] )
        def qcd_mg(eL) :
            qM = ["%d"%t for t in [50,100,250,500,1000][1:]]
            return specify( effectiveLumi = eL, color = r.kBlue,
                            names = ["qcd_mg_ht_%s_%s"%t for t in zip(qM,qM[1:]+["inf"])])
        def ttbar_mg(eL) :
            intrinsicR = -0.05
            return (specify( names = "tt_tauola_mg", effectiveLumi = eL, color = r.kBlue,  weights = "wNonQQbar") +
                    #specify( names = "tt_tauola_mg", effectiveLumi = eL, color = r.kRed,  weights = "wQQbar") +
                    #specify( names = "tt_tauola_mg", effectiveLumi = eL, color = r.kOrange,   weights = calculables.Top.wTopAsym(-0.30, intrinsicR = intrinsicR)) +
                    #specify( names = "tt_tauola_mg", effectiveLumi = eL, color = r.kYellow-3, weights = calculables.Top.wTopAsym( 0.00, intrinsicR = intrinsicR)) +
                    #specify( names = "tt_tauola_mg", effectiveLumi = eL, color = r.kRed,      weights = calculables.Top.wTopAsym( 0.30, intrinsicR = intrinsicR)) +
                    [])

        def ttbar_py(eL) :
            return (specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kBlue, weights = ["wNonQQbar","nvr"]) +
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kGreen, weights = [ calculables.Top.wTopAsym(-0.4), "nvr" ] )+
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kGreen, weights = [ calculables.Top.wTopAsym(-0.3), "nvr" ] )+
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kGreen, weights = [ calculables.Top.wTopAsym(-0.2), "nvr" ] )+
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kGreen, weights = [ calculables.Top.wTopAsym(-0.1), "nvr" ] )+
                    specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kOrange, weights = [ calculables.Top.wTopAsym(0), "nvr" ] ) +
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kRed, weights = [ calculables.Top.wTopAsym(0.1), "nvr" ] )+
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kRed, weights = [ calculables.Top.wTopAsym(0.2), "nvr" ] )+
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kRed, weights = [ calculables.Top.wTopAsym(0.3), "nvr" ] )+
                    # specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kRed, weights = [ calculables.Top.wTopAsym(0.4), "nvr" ] )+
                    [])

        def ewk(eL, skimp=True) :
            return specify( names = "w_jets_fj_mg", effectiveLumi = eL, color = 28, weights = "nvr" )
            EWK = {}
            EWK["electron"] = specify( names = "w_enu_fj", effectiveLumi = eL, color = 28)
            EWK["muon"] = specify( names = "w_munu_fj", effectiveLumi = eL, color = 28)
            EWK["other"] = specify( names = "w_taunu_fj", effectiveLumi = eL, color = r.kYellow-3)
            if skimp : return EWK[pars["lepton"]["name"]]+specify( names = "w_jets_fj_mg", effectiveLumi = None, color = 28 )
            return sum(EWK.values(),[])



        return  ( data() +
                  #qcd_py6_mu(None) +
                  #ewk(None) +
                  #ttbar_py(None) +
                  [])





    ############################################3
    ############################################3
    ############################################3
    ############################################3







    def concludeAll(self) :
        super(topAsymm,self).concludeAll()
        #self.meldNorm()
        #self.meldWpartitions()

    def meldNorm(self) :
        meldSamples = {"top_muon_pf" : ["SingleMu","P00","NonQQbar"],
                       "Wlv_muon_pf" : ["SingleMu"],
                       "QCD_muon_pf" : ["SingleMu"]}
        fdists = [{key:{"observed":(),"components":[]}} for key in ["dphiLnu"]]
        
        organizers = [organizer.organizer(tag, [s for s in self.sampleSpecs(tag) if any(item in s['name'] for item in meldSamples[tag])])
                      for tag in [p['tag'] for p in self.readyConfs]]
        for org,color in zip(organizers,[r.kBlack,r.kRed,r.kBlue]) :
            org.mergeSamples(targetSpec = {"name":"t#bar{t}", "color":r.kViolet}, sources=["tt_tauola_fj.wNonQQbar","tt_tauola_fj.wTopAsymP00"])
            org.mergeSamples(targetSpec = {"name":"Data 2011", "color":color, "markerStyle":(20 if "top" in org.tag else 1)}, allWithPrefix="SingleMu")

            iData = org.indexOfSampleWithName("Data 2011")
            before = next(org.indicesOfStep("label","selection complete"))
            #distTup = org.steps[next(iter(filter(lambda i: before<i, org.indicesOfStepsWithKey(dist))))][dist]
            #data = [distTup[iData].GetBinContent(i) for i in range(distTup[iData].GetNbinsX()+2)]
            #if "top" in org.tag :
            #    fdists[dist]["observed"] = data
            #    signal = data
            #    iTT = org.indexOfSampleWithName("t#bar{t}")
            #    templates.append([distTup[iTT].GetBinContent(i) for i in range(distTup[iTT].GetNbinsX()+2)])
            #    print "t#bar{t}"
            #else :
            #    templates.append(data)
            #    print org.tag
            org.scale(toPdf=True)

        #import fractions
        #cs = fractions.componentSolver(signal, templates, 1e4)
        #with open() as file : print >> file, cs
        #stuff = fractions.drawComponentSolver(cs)
        #stuff[0].Print("fractions.eps")
            
        melded = organizer.organizer.meld(organizers = organizers)
        pl = plotter.plotter(melded,
                             psFileName = self.psFileName(melded.tag),
                             doLog = False,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             ).plotAll()

    def meldWpartitions(self) :
        samples = {"top_muon_pf" : ["w_"],
                   "Wlv_muon_pf" : ["w_","SingleMu"],
                   "QCD_muon_pf" : []}
        organizers = [organizer.organizer(tag, [s for s in self.sampleSpecs(tag) if any(item in s['name'] for item in samples[tag])])
                      for tag in [p['tag'] for p in self.readyConfs]]
        for org in organizers :
            org.mergeSamples(targetSpec = {"name":"Data 2011", "color":r.kBlack, "markerStyle":20}, allWithPrefix="SingleMu")
            org.mergeSamples(targetSpec = {"name":"w_mg", "color":r.kRed if "Wlv" in org.tag else r.kBlue, "markerStyle": 22}, sources = ["w_jets_fj_mg.nvr"])
            org.scale(toPdf=True)

        melded = organizer.organizer.meld("wpartitions",filter(lambda o: o.samples, organizers))
        pl = plotter.plotter(melded,
                             psFileName = self.psFileName(melded.tag),
                             doLog = False,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             ).plotAll()


    def conclude(self,pars) :
        org = self.organizer(pars)
        for suf in ["N40","N20","N10","P10","P20","P40"] : org.drop('tt_tauola_fj.wTopAsym%s.nvr'%suf)
        org.drop("w_munu_fj")
        org.mergeSamples(targetSpec = {"name":"Data 2011", "color":r.kBlack, "markerStyle":20}, allWithPrefix="SingleMu")
        org.mergeSamples(targetSpec = {"name":"t#bar{t}", "color":r.kViolet}, sources=["tt_tauola_fj.wNonQQbar.nvr","tt_tauola_fj.wTopAsymP00.nvr"])
        org.mergeSamples(targetSpec = {"name":"qcd_py6", "color":r.kBlue}, allWithPrefix="qcd_py6")
        org.mergeSamples(targetSpec = {"name":"t#bar{t}.q#bar{q}.N30", "color":r.kRed}, sources = ["tt_tauola_fj.wTopAsymN30.nvr","tt_tauola_fj.wNonQQbar.nvr"][:1])
        org.mergeSamples(targetSpec = {"name":"t#bar{t}.q#bar{q}.P30", "color":r.kGreen}, sources = ["tt_tauola_fj.wTopAsymP30.nvr","tt_tauola_fj.wNonQQbar.nvr"][:1])
        # org.mergeSamples(targetSpec = {"name":"standard_model", "color":r.kGreen+2}, sources = ["qcd_py6","w_munu_fj.nvr","t#bar{t}","w_jets_fj_mg.nvr"], keepSources = True)
        org.scale(toPdf=True)
        
        pl = plotter.plotter(org, psFileName = self.psFileName(org.tag+"_log"),
                             pegMinimum = 0.01,
                             #samplesForRatios = ("Data 2011","standard_model"),
                             #sampleLabelsForRatios = ("data","s.m."),
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             detailedCalculables = True,
                             ).plotAll()

        pl = plotter.plotter(org, psFileName = self.psFileName(org.tag+"_nolog"),
                             doLog = False,
                             #samplesForRatios = ("Data 2011","standard_model"),
                             #sampleLabelsForRatios = ("data","s.m."),
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             #detailedCalculables = True,
                             ).plotAll()

        #self.optimizeCut(org,signal = "t#bar{t}", background = "standard_model", var = "TopRatherThanWProbability")
        #org.printFormattedCalculablesGraph()
        #with open("topAsymm.gv","write") as file : print>>file, org.calculablesDotFile

    def optimizeCut(org, signal = "", background = "", var = "", FOM = lambda s,b: s/math.sqrt(s+b) ) :
        
        iSignal = org.indexOfSampleWithName(signal)
        iBack = org.indexOfSampleWithName(background)
        iStep = next( org.indicesOfStepsWithKey(var) )

        sHist = org.steps[iStep][var][iSignal]
        bHist = org.steps[iStep][var][iBack]
        bins = sHist.GetNbins()+2
        S = [sHist.GetBinContent(i) for i in range(bins)]
        B = [bHist.GetBinContent(i) for i in range(bins)]
        

        mDist = bHist.Clone("%s_fom"%var)
        mDist.Reset()
        iSeed = max((FOM(s,b),i) for i,s,b in zip(range(bins),S,B))[1]

        iL = iR = iSeed
        
            
        
