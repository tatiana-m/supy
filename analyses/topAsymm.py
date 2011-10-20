import topAsymmShell,steps,calculables,samples
from core import plotter,utils,organizer
import os,math,copy,ROOT as r

class topAsymm(topAsymmShell.topAsymmShell) :
    ########################################################################################

    def parameters(self) :
        pars = super(topAsymm,self).parameters()
        pars["topBsamples"] = { "pythia"   : ("tt_tauola_fj",["tt_tauola_fj.wNonQQbar.nvr",
                                                              "tt_tauola_fj.wTopAsymP00.nvr"
                                                              ]),
                                "madgraph" : ("FIXME",[]),
                                }["pythia"]
        return pars
    ########################################################################################

    def listOfCalculables(self, pars) :
        calcs = super(topAsymm,self).listOfCalculables(pars)
        calcs.append( calculables.Other.TriDiscriminant(LR = "DiscriminantWQCD", LC = "DiscriminantTopW", RC = "DiscriminantTopQCD") )
        calcs.append( calculables.size("%sIndices%s"%pars['objects']['jet']))
        return calcs
    ########################################################################################

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
                                    target = ("SingleMu",[]), groups = [('qcd_mg',[]),('qcd_py6',[]),('w_jets_fj_mg',[]),
                                                                        ('tt_tauola_fj',['tt_tauola_fj%s.nvr'%s for s in ['','.wNonQQbar','.wTopAsymP00']])]),
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
            calculables.Other.Discriminant( fixes = ("","TopQqQg"),
                                            left = {"pre":"qq", "tag":"top_muon_pf", "samples":['tt_tauola_fj.wNonQQbar.nvr']},
                                            right = {"pre":"qg", "tag":"top_muon_pf", "samples":['tt_tauola_fj.wTopAsymP00.nvr']},
                                            dists = {"fitTopPtOverSumPt" : (20,0,1),
                                                     "fitTopCosThetaDaggerTT" : (40,-1,1),
                                                     "fitTopSumP4AbsEta" : (21,0,7),
                                                     "%sIndices%s.size"%obj["jet"] : (10,-0.5,9.5)
                                                     },
                                            correlations = True,
                                            bins = 14),
            #steps.Filter.stop(),#####################################
            calculables.Other.Discriminant( fixes = ("","TopW"),
                                            left = {"pre":"w_jets_fj_mg", "tag":"top_muon_pf", "samples":[]},
                                            right = {"pre":"tt_tauola_fj", "tag":"top_muon_pf", "samples": ['tt_tauola_fj.%s.nvr'%s for s in ['wNonQQbar','wTopAsymP00']]},
                                            correlations = True,
                                            dists = {"%sKt%s"%obj["jet"] : (25,0,150),
                                                     "%sB0pt%s"%obj["jet"] : (30,0,300),
                                                     "%s3absEta%s"%obj["jet"] : (20,0,4),
                                                     "fitTopHadChi2"     : (20,0,100),
                                                     "mixedSumP4.pt"     : (30,0,180),
                                                     #"fitTopLeptonPt"    : (30,0,180),  # not so powerful?
                                                     "fitTopDeltaPhiLNu" : (20,0,math.pi),
                                                     "TopRatherThanWProbability" : (20,0,1),
                                                     }),
            calculables.Other.Discriminant( fixes = ("","TopQCD"),
                                            left = {"pre":"SingleMu", "tag":"QCD_muon_pf", "samples":[]},
                                            right = {"pre":"tt_tauola_fj", "tag":"top_muon_pf", "samples": ['tt_tauola_fj.%s.nvr'%s for s in ['wNonQQbar','wTopAsymP00']]},
                                            correlations = True,
                                            dists = {"%sKt%s"%obj["jet"] : (25,0,150),
                                                     "%sB0pt%s"%obj["jet"] : (30,0,300),
                                                     "%s3absEta%s"%obj["jet"] : (20,0,4),
                                                     "%sMt%s"%obj['muon']+"mixedSumP4" : (30,0,180),
                                                     "%sDeltaPhiB01%s"%obj["jet"] : (20,0,math.pi),
                                                     #"mixedSumP4.pt"     : (30,0,180),
                                                     #"fitTopLeptonPt"    : (30,0,180),
                                                     #"fitTopDeltaPhiLNu" : (20,0,math.pi),
                                                     }),
            calculables.Other.Discriminant( fixes = ("","WQCD"),
                                            left = {"pre":"w_jets_fj_mg", "tag":"top_muon_pf", "samples":[]},
                                            right = {"pre":"SingleMu", "tag":"QCD_muon_pf", "samples":[]},
                                            correlations = True,
                                            dists = {"%sB0pt%s"%obj["jet"] : (30,0,300),
                                                     "%sMt%s"%obj['muon']+"mixedSumP4" : (30,0,180),
                                                     "%sDeltaPhiB01%s"%obj["jet"] : (20,0,math.pi),
                                                     "fitTopCosHelicityThetaL": (20,-1,1),
                                                     }),
            #steps.Filter.stop(),#####################################
            steps.Histos.multiplicity("%sIndices%s"%obj["jet"]),
            steps.Histos.value("TriDiscriminant",50,-1,1),
            steps.Top.Asymmetry(('fitTop','')),
            steps.Top.Spin(('fitTop','')),
            #steps.Top.kinFitLook("fitTopRecoIndex"),
            steps.Filter.value("TriDiscriminant",min=-0.68,max=0.8),
            steps.Histos.value("TriDiscriminant",50,-1,1),
            steps.Top.Asymmetry(('fitTop','')),
            steps.Top.Spin(('fitTop','')),
            steps.Filter.value("TriDiscriminant",min=-.56,max=0.72),
            steps.Histos.value("TriDiscriminant",50,-1,1),
            steps.Top.Asymmetry(('fitTop','')),
            steps.Top.Spin(('fitTop','')),
            ])
    ########################################################################################

    def listOfSamples(self,pars) :
        from samples import specify

        def data( trial = False ) :
            return specify( names = ["SingleMu.Run2011A-PR-v4.FJ.Burt","SingleMu.Run2011A-May10-v1.FJ.Burt",][:1 if trial else None],
                            nFilesMax = 1 if trial else None, nEventsMax = 1000 if trial else None)
        def qcd_py6_mu(eL = None) :
            q6 = [0,5,15,20,30,50,80,120,150,None]
            iCut = q6.index(15)
            return specify( effectiveLumi = eL, weights = "nvr",
                            names = ["qcd_py6fjmu_pt_%s"%("%d_%d"%(low,high) if high else "%d"%low) for low,high in zip(q6[:-1],q6[1:])[iCut:]] )  if "Wlv" not in pars['tag'] else []
        def qcd_mg(eL = None) :
            qM = ["%d"%t for t in [50,100,250,500,1000][1:]]
            return specify( effectiveLumi = eL, color = r.kBlue,
                            names = ["qcd_mg_ht_%s_%s"%t for t in zip(qM,qM[1:]+["inf"])]) if "Wlv" not in pars['tag'] else []
        def ttbar_mg(eL = None) :
            return (specify( names = "tt_tauola_mg", effectiveLumi = eL, color = r.kBlue, weights = ["wNonQQbar","nvr"]) +
                    sum([specify( names = "tt_tauola_mg", effectiveLumi = eL, color = color, weights = [calculables.Top.wTopAsym( asym, intrinsicR = -0.05), "nvr" ])
                         for asym,color in [(0.0,r.kOrange),(-0.3,r.kGreen),(0.3,r.kRed)]], [])
                    )[: 0 if "QCD" in pars['tag'] else 2 if 'Wlv' in pars['tag'] else None]
        def ttbar_py(eL = None) :
            return (specify(names = "tt_tauola_fj", effectiveLumi = eL, color = r.kBlue, weights = ["wNonQQbar","nvr"]) +
                    sum( [specify(names = "tt_tauola_fj", effectiveLumi = eL, color = color, weights = [ calculables.Top.wTopAsym(asym), "nvr" ] )
                          for asym,color in [(0.0,r.kOrange), (-0.3,r.kGreen),(0.3,r.kRed),
                                             (-0.6,r.kYellow),(0.6,r.kYellow),
                                             (-0.5,r.kYellow),(0.5,r.kYellow),
                                             (-0.4,r.kYellow),(0.4,r.kYellow),
                                             (-0.2,r.kYellow),(0.2,r.kYellow),
                                             (-0.1,r.kYellow),(0.1,r.kYellow),
                                             ]], [])
                    )[: 0 if "QCD" in pars['tag'] else 2 if 'Wlv' in pars['tag'] else None]
        def ewk(eL = None) :
            return specify( names = "w_jets_fj_mg", effectiveLumi = eL, color = 28, weights = "nvr" ) if "QCD" not in pars['tag'] else []

        return  ( data() + qcd_py6_mu() + ewk() + ttbar_py() )
    ########################################################################################

    ########################################################################################
    def concludeAll(self) :
        self.rowcolors = [r.kBlack, r.kGray+3, r.kGray+2, r.kGray+1, r.kViolet+4]
        #super(topAsymm,self).concludeAll()
        #self.meldWpartitions()
        #self.meldQCDpartitions()
        self.meldScale()
        for var in ['lHadtDeltaY',
                    'leptonRelativeY',
                    'ttbarBeta',
                    'ttbarDeltaAbsY',
                    'ttbarSignedDeltaY' ] : self.templateFit(var)

    def conclude(self,pars) :
        org = self.organizer(pars)
        org.mergeSamples(targetSpec = {"name":"Data 2011", "color":r.kBlack, "markerStyle":20}, allWithPrefix="SingleMu")
        org.mergeSamples(targetSpec = {"name":"qcd_py6", "color":r.kBlue}, allWithPrefix="qcd_py6")
        org.mergeSamples(targetSpec = {"name":"t#bar{t}", "color":r.kViolet}, sources=["tt_tauola_fj.wNonQQbar.nvr","tt_tauola_fj.wTopAsymP00.nvr"])
        org.mergeSamples(targetSpec = {"name":"t#bar{t}.q#bar{q}.N30", "color":r.kRed}, sources = ["tt_tauola_fj.wTopAsymN30.nvr","tt_tauola_fj.wNonQQbar.nvr"][:1])
        org.mergeSamples(targetSpec = {"name":"t#bar{t}.q#bar{q}.P30", "color":r.kGreen}, sources = ["tt_tauola_fj.wTopAsymP30.nvr","tt_tauola_fj.wNonQQbar.nvr"][:1])
        org.mergeSamples(targetSpec = {"name":"standard_model", "color":r.kGreen+2}, sources = ["qcd_py6","t#bar{t}","w_jets_fj_mg.nvr"], keepSources = True)
        for ss in filter(lambda ss: 'tt_tauola' in ss['name'],org.samples) : org.drop(ss['name'])

        orgpdf = copy.deepcopy(org)
        orgpdf.scale( toPdf = True )
        org.scale( lumiToUseInAbsenceOfData = 1.1e3 )

        names = [ss["name"] for ss in org.samples]
        kwargs = {"detailedCalculables": False,
                  "blackList":["lumiHisto","xsHisto","nJobsHisto"],
                  "samplesForRatios" : next(iter(filter(lambda x: x[0] in names and x[1] in names, [("Data 2011","standard_model")])), ("","")),
                  "sampleLabelsForRatios" : ("data","s.m."),
                  "detailedCalculables" : True,
                  "rowColors" : self.rowcolors,
                  }
        
        plotter.plotter(org, psFileName = self.psFileName(org.tag+"_log"),  doLog = True, pegMinimum = 0.01, **kwargs ).plotAll()
        plotter.plotter(org, psFileName = self.psFileName(org.tag+"_nolog"), doLog = False, **kwargs ).plotAll()

        kwargs["samplesForRatios"] = ("","")
        kwargs["dependence2D"] = True
        plotter.plotter(orgpdf, psFileName = self.psFileName(org.tag+"_pdf"), doLog = False, **kwargs ).plotAll()

    def meldWpartitions(self) :
        samples = {"top_muon_pf" : ["w_"],
                   "Wlv_muon_pf" : ["w_","SingleMu"],
                   "QCD_muon_pf" : []}
        organizers = [organizer.organizer(tag, [s for s in self.sampleSpecs(tag) if any(item in s['name'] for item in samples[tag])])
                      for tag in [p['tag'] for p in self.readyConfs]]
        if len(organizers)<2 : return
        for org in organizers :
            org.mergeSamples(targetSpec = {"name":"Data 2011", "color":r.kBlack, "markerStyle":20}, allWithPrefix="SingleMu")
            org.mergeSamples(targetSpec = {"name":"w_mg", "color":r.kRed if "Wlv" in org.tag else r.kBlue, "markerStyle": 22}, sources = ["w_jets_fj_mg.nvr"])
            org.scale(toPdf=True)

        melded = organizer.organizer.meld("wpartitions",filter(lambda o: o.samples, organizers))
        pl = plotter.plotter(melded,
                             psFileName = self.psFileName(melded.tag),
                             doLog = False,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             rowColors = self.rowcolors,
                             ).plotAll()

    def meldQCDpartitions(self) :
        samples = {"top_muon_pf" : ["qcd_py6fjmu"],
                   "Wlv_muon_pf" : [],
                   "QCD_muon_pf" : ["qcd_py6fjmu","SingleMu"]}
        organizers = [organizer.organizer(tag, [s for s in self.sampleSpecs(tag) if any(item in s['name'] for item in samples[tag])])
                      for tag in [p['tag'] for p in self.readyConfs]]
        if len(organizers)<2 : return
        for org in organizers :
            org.mergeSamples(targetSpec = {"name":"Data 2011", "color":r.kBlack, "markerStyle":20}, allWithPrefix="SingleMu")
            org.mergeSamples(targetSpec = {"name":"qcd_py6mu", "color":r.kRed if "QCD" in org.tag else r.kBlue, "markerStyle": 22}, allWithPrefix="qcd_py6fjmu")
            org.scale(toPdf=True)

        melded = organizer.organizer.meld("qcdPartitions",filter(lambda o: o.samples, organizers))
        pl = plotter.plotter(melded,
                             psFileName = self.psFileName(melded.tag),
                             doLog = False,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             rowColors = self.rowcolors,
                             ).plotAll()

    def meldScale(self) :
        meldSamples = {"top_muon_pf" : ["SingleMu","tt_tauola_fj","w_jets"],
                       #"Wlv_muon_pf" : ["w_jets"],
                       "QCD_muon_pf" : ["SingleMu"]}
        
        organizers = [organizer.organizer(tag, [s for s in self.sampleSpecs(tag) if any(item in s['name'] for item in meldSamples[tag])])
                      for tag in [p['tag'] for p in self.readyConfs if p["tag"] in meldSamples]]
        if len(organizers) < len(meldSamples) : return
        for org in organizers :
            org.mergeSamples(targetSpec = {"name":"t#bar{t}", "color":r.kViolet}, sources=["tt_tauola_fj.wNonQQbar.nvr","tt_tauola_fj.wTopAsymP00.nvr"], keepSources = True)
            org.mergeSamples(targetSpec = {"name":"w_jets", "color":r.kRed}, allWithPrefix = "w_jets")
            org.mergeSamples(targetSpec = {"name":"Data 2011",
                                           "color":r.kBlue if "QCD_" in org.tag else r.kBlack,
                                           "markerStyle":(20 if "top" in org.tag else 1)}, allWithPrefix="SingleMu")

        self.orgMelded = organizer.organizer.meld(organizers = organizers)
        dist = "TriDiscriminant"
        before = next(self.orgMelded.indicesOfStep("label","selection complete"))
        distTup = self.orgMelded.steps[next(iter(filter(lambda i: before<i, self.orgMelded.indicesOfStepsWithKey(dist))))][dist]

        templateSamples = ['top.t#bar{t}','top.w_jets','QCD.Data 2011']
        templates = [None] * len(templateSamples)
        for ss,hist in zip(self.orgMelded.samples,distTup) :
            contents = [hist.GetBinContent(i) for i in range(hist.GetNbinsX()+2)]
            if ss['name'] == "top.Data 2011" :
                observed = contents
                nEventsObserved = sum(observed)
            elif ss['name'] in templateSamples :
                templates[templateSamples.index(ss['name'])] = contents
            else : pass
        
        from core.fractions import componentSolver,drawComponentSolver
        cs = componentSolver(observed, templates, 1e4)
        csCanvas = drawComponentSolver(cs)
        contours = utils.optimizationContours(cs.components[0], sum(cs.components[1:]), left=True, right=True)
        utils.tCanvasPrintPdf(csCanvas[0], "%s/measuredFractions"%self.globalStem)
        utils.tCanvasPrintPdf(contours[0], "%s/contours"%self.globalStem)
        with open(self.globalStem+"/measuredFractions.txt","w") as file : print >> file, cs
        with open(self.globalStem+'/templates.txt','w') as file : print >> file, cs.components

        fractions = dict(zip(templateSamples,cs.fractions))
        
        for iSample,ss in enumerate(self.orgMelded.samples) :
            if ss['name'] in fractions : self.orgMelded.scaleOneRaw(iSample, fractions[ss['name']] * nEventsObserved / distTup[iSample].Integral(0,distTup[iSample].GetNbinsX()+1))
        
        melded = copy.deepcopy(self.orgMelded)
        for ss in filter(lambda ss: 'tt_tauola_fj' in ss['name'], melded.samples) : melded.drop(ss['name'])
        melded.mergeSamples(targetSpec = {"name":"S.M.", "color":r.kGreen+2}, sources = ['top.w_jets','top.t#bar{t}','QCD.Data 2011'], keepSources = True, force = True)
        pl = plotter.plotter(melded, psFileName = self.psFileName(melded.tag),
                             doLog = False,
                             blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                             rowColors = self.rowcolors,
                             samplesForRatios = ("top.Data 2011","S.M."),
                             sampleLabelsForRatios = ('data','s.m.')
                             ).plotAll()
    


    def templateFit(self, var, qqFrac = 0.15) :
        if not hasattr(self,'orgMelded') : print 'orgMelded is not present!' ; return
        from core import templateFit
        import numpy as np

        org = self.orgMelded
        topQQs = [s['name'] for s in org.samples if 'wTopAsym' in s['name']]
        asymm = [eval(name.replace("top.tt_tauola_fj.wTopAsym","").replace(".nvr","").replace("P",".").replace("N","-.")) for name in topQQs]

        def nparray(name, scaleToN = None) :
            hist = distTup[ org.indexOfSampleWithName(name) ]
            bins = np.array([hist.GetBinContent(j) for j in range(hist.GetNbinsX()+2)])
            if scaleToN : bins *= (scaleToN / sum(bins))
            return bins

        outName = self.globalStem + '/templateFit_%s_%d'%(var,qqFrac*100)
        canvas = r.TCanvas()
        canvas.Print(outName+'.ps[')
        for iStep in org.indicesOfStepsWithKey(var) :
            distTup = org.steps[iStep][var]

            nTT = sum(nparray('top.t#bar{t}'))
            observed = nparray('top.Data 2011')
            base = ( nparray('QCD.Data 2011') +
                     nparray('top.w_jets') +
                     nparray('top.tt_tauola_fj.wNonQQbar.nvr', scaleToN = (1-qqFrac) * nTT )
                     )
            templates = [base +  nparray(qqtt, qqFrac*nTT ) for qqtt in topQQs]

            TF = templateFit.templateFitter(observed, templates, asymm)
            print utils.roundString(TF.value, TF.error , noSci=True)
            stuff = templateFit.drawTemplateFitter(TF, canvas)
            canvas.Print(outName+'.ps')
            #stuff[0].cd(3).SetLogy(1)
            #stuff[0].Print(outName+'.ps')

        canvas.Print(outName+'.ps]')
        os.system('ps2pdf %s.ps %s.pdf'%(outName,outName))
        os.system('rm %s.ps'%outName)
