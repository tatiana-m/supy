import copy,array,os,collections,math,ROOT as r
import steps.Master
from core.analysisStep import analysisStep
from core import utils

#####################################
class Asymmetry(analysisStep) :
    def __init__(self, collection) :
        self.collection = collection
        for item in ["LeptonCharge","SignedLeptonRapidity","RelativeLeptonRapidity",
                     "DeltaAbsYttbar","DirectedDeltaYttbar","Beta","DirectedDeltaYLHadt",
                     "DirectedLTopRapidity","DirectedHTopRapidity"] :
            setattr(self,item,("%s"+item+"%s")%collection)
        self.bins = 18

    def uponAcceptance(self,ev) :
        for charge in ["",["Negative","Positive"][max(0,ev[self.LeptonCharge])]] :
            self.book.fill(ev[self.SignedLeptonRapidity], "leptonSignedY"+charge, self.bins,-3,3, title = "%s;leptonSignedY;events / bin"%charge)
            self.book.fill(ev[self.RelativeLeptonRapidity], "leptonRelativeY"+charge, self.bins,-3,3, title = "%s;#Delta y;events / bin"%charge)
            self.book.fill(ev[self.DirectedLTopRapidity], "dirLtopY"+charge, self.bins,-3,3, title = "%s;y_{ltop};events / bin"%charge)
            self.book.fill(ev[self.DirectedHTopRapidity], "dirHtopY"+charge, self.bins,-3,3, title = "%s;y_{htop};events / bin"%charge)

        self.book.fill( ev[self.DeltaAbsYttbar],      'ttbarDeltaAbsY',    self.bins, -3, 3, title = ';#Delta|Y|_{ttbar};events / bin' )
        self.book.fill( ev[self.DirectedDeltaYttbar], 'ttbarSignedDeltaY', self.bins, -4, 4, title = ';sumP4dir * #Delta Y_{ttbar};events / bin' )
        self.book.fill( ev[self.DirectedDeltaYLHadt], 'lHadtDeltaY',       self.bins, -4, 4, title = ';#Delta Y_{lhadt};events / bin')
        self.book.fill( ev[self.Beta],                'ttbarBeta',         self.bins, -math.sqrt(2), math.sqrt(2), title = ';#beta_{ttbar};events / bin')
#####################################
class Spin(analysisStep) :
    def __init__(self, collection) :
        self.collection = collection
        for item in ['CosHelicityThetaL', 'CosHelicityThetaQ'] :
            setattr(self,item,('%s'+item+'%s')%collection)
        self.bins = 18

    def uponAcceptance(self,ev) :
        cosTL = ev[self.CosHelicityThetaL]
        cosTQ = ev[self.CosHelicityThetaQ]
        self.book.fill( cosTL, 'CosHelicityThetaL', self.bins, -1, 1, title = ';CosHelicityThetaL;events / bin' )
        self.book.fill( cosTQ, 'CosHelicityThetaQ', self.bins, -1, 1, title = ';CosHelicityThetaQ;events / bin' )
        self.book.fill( cosTL*cosTQ, 'helicityCos2', self.bins, -1, 1, title = ';helicityCos2;events / bin' )
        self.book.fill( (cosTL, cosTQ), 'vs_CosHelicityThetaL_CosHelicityThetaQ', (self.bins,self.bins), (-1,-1), (1,1),
                        title = ';CosHelicityThetaL;CosHelicityThetaQ;events / bin')
#####################################
class kinFitLook(analysisStep) :
    def __init__(self,indexName) : self.moreName = indexName
    def uponAcceptance(self,ev) :
        index = ev[self.moreName]
        topReco = ev["TopReconstruction"][index]
        residuals = topReco["residuals"]
        lepTopM = topReco['lepTopP4'].M()
        hadTopM = topReco['hadTopP4'].M()
        lepWM = topReco['lepW'].M()
        hadWM = topReco['hadW'].M()
        rawHadWM = topReco['hadWraw'].M()

        for name,val in residuals.iteritems() :
            self.book.fill(val, "topKinFit_residual_%s"%name+self.moreName, 50,-7,7, title = ";residual %s;events / bin"%name)

        #self.book.fill( (topReco["dS"],topReco["dL"]), "topKinFit_DSoverDL"+self.moreName, (100,100), (0,0), (30,30), title = ";ds;dL;events / bin")
        #self.book.fill( (topReco["sigmaS"],topReco["sigmaL"]), "topKinFit_SigmaSoverSigmaL"+self.moreName, (100,100), (0,0), (30,30), title = ";#sigma_{s};#sigma_{L};events / bin")
        #self.book.fill((residuals["hadP"],residuals["hadQ"]), "topKinFit_residual_had_PQ"+self.moreName, (100,100),(-5,-5),(5,5), title = ';residual hadP;residual hadQ;events / bin')
        #self.book.fill((residuals["lepS"],residuals["lepL"]), "topKinFit_residual_lep_SL"+self.moreName, (100,100),(-5,-5),(5,5), title = ';residual lepS;residual lepL;events / bin')

        self.book.fill( lepWM, "wMassLepFit"+self.moreName, 60, 0, 180, title = ';fit mass_{W} (leptonic);events / bin')
        self.book.fill( hadWM, "wMassHadFit"+self.moreName, 60, 0, 180, title = ';fit mass_{W} (hadronic);events / bin')
        self.book.fill( rawHadWM, "wMassHadRaw"+self.moreName, 60, 0, 180, title = ';raw mass_{W} (hadronic);events / bin')
        self.book.fill( lepTopM, "topMassLepFit"+self.moreName, 100,0,300, title = ";fit mass_{top} (leptonic);events / bin" )
        self.book.fill( hadTopM, "topMassHadFit"+self.moreName, 100,0,300, title = ";fit mass_{top} (hadronic);events / bin" )
        self.book.fill( (lepTopM, hadTopM), "topMassesFit"+self.moreName, (100,100),(0,0),(300,300),
                        title = ";fit mass_{top} (leptonic); fit mass_{top} (hadronic);events / bin",)
        
        self.book.fill( topReco['chi2'], "topRecoChi2"+self.moreName, 50, 0 , 600, title = ';ttbar kin. fit #chi^{2};events / bin')
        self.book.fill( math.log(1+topReco['chi2']), "topRecoLogOnePlusChi2"+self.moreName, 50, 0 , 7, title = ';ttbar kin. fit log(1+#chi^{2});events / bin')
        self.book.fill( math.log(1+topReco['key']), "topRecoLogOnePlusKey"+self.moreName, 50, 0 , 7, title = ';ttbar kin. fit log(1+#chi^{2}-2logP);events / bin')

        #hadX2 = math.log(1+topReco['hadChi2'])
        #lepX2 = math.log(1+topReco['lepChi2'])
        #bound = ("_bound" if topReco['lepBound'] else "_unbound")

        #self.book.fill( hadX2, "topRecoLHadX2"+self.moreName, 50, 0 , 10, title = ';ttbar kin. fit log(1+#chi^{2}_{had});events / bin')
        #self.book.fill( lepX2, "topRecoLLepX2"+self.moreName, 50, 0 , 10, title = ';ttbar kin. fit log(1+#chi^{2}_{lep});events / bin')
        #self.book.fill( lepX2, "topRecoLLepX2"+bound+self.moreName, 50, 0 , 10, title = ';ttbar kin. fit log(1+#chi^{2}_{lep});events / bin')
        #self.book.fill( (lepX2,hadX2), "topRecoVsLX2"+self.moreName, (50,50),(0,0),(10,10), title = ";log(1+#chi^{2}_{lep});log(1+#chi^{2}_{had});events / bin" )
#####################################
class combinatorialBG(analysisStep) :
    def __init__(self,jets=None) : self.jets = jets        
    def uponAcceptance(self,ev) :
        maxP = ev["TopComboQQBBMaxProbability"]
        iTrue = ev['genTopRecoIndex']
        recos = ev['TopReconstruction']
        jetIndices = set()
        hadIndices = set()
        bIndices = set()
        for iReco in [iTrue]+list(set(range(len(recos)))-set([iTrue])) :
            reco = recos[iReco]
            tag = "correct" if iReco==iTrue else "incorrect"
            indicesB = ev['%sIndicesBtagged%s'%self.jets]

            iPQHL = reco['iPQHL']
            iPQH = iPQHL[:-1]
            iHL = iPQHL[2:]

            iB2 = max(iHL, key = lambda i: indicesB.index(i))
            iiB2 = indicesB.index(iB2)
            self.book.fill(math.log(1+reco['chi2']), "logOnePlusChi2_"+tag, 50,0,7, title = ';%s ttbar kin. fit log(1+#chi^{2});events / bin'%tag )
            self.book.fill(math.log(1+reco['key']), 'logOnePlusKey_'+tag, 50,0,7, title = ';%s log(1+key);events / bin'%tag)
            self.book.fill( (math.log(1+reco['chi2']),math.log(1-2*math.log(reco['probability']))), "logOnePlus_chi2p_"+tag, (50,50),(0,0),(7,4), title = ";%s log(1+#chi^{2});log(1-2log(P));events / bin"%tag)
            
            if iPQHL not in jetIndices :
                jetIndices.add(iPQHL)
                p = ev['TopComboQQBBProbability'][iPQH[:2]+tuple(sorted(iHL))]
                self.book.fill( math.log(1-2*math.log(reco['probability'])), "logOnePlus_m2p_"+tag, 50,0,4, title = ";%s log(1-2log(P));events / bin"%tag)
                for i in range(4) : self.book.fill( ev["%sIndices%s"%self.jets].index(sorted(iPQHL)[i]), "iJ_j%d_"%i+tag, 10,-0.5,9.5, title = ';%s index of topjet%d;events / bin'%(tag,i) )

            if iPQH not in hadIndices :
                hadIndices.add(iPQH)
                mW,mT = ev["%sComboPQBRawMassWTop%s"%self.jets][iPQH]
                dmW,dmT = ev["%sComboPQBDeltaRawMassWTop%s"%self.jets][iPQH]
                self.book.fill(mW, "rawMassHadW_"+tag,60,0,180, title = ";raw mass_{W} had (%s);events / bin"%tag)
                self.book.fill(mT, "rawMassHadT_"+tag,100,0,300, title = ";raw mass_{t} had (%s);events / bin"%tag)
                topMass = 172; wMass = 80.4
                self.book.fill((dmT,dmW), "rawDeltaMassHadTW_"+tag,(100,60),(-topMass,-wMass),(300-topMass,180-wMass), title= ";(%s) raw had #Delta mass_{T};raw had #Delta mass_{W};events / bin"%tag)

            if self.jets and iHL not in bIndices :
                bIndices.add(iHL)
                indicesPt = ev['%sIndices%s'%self.jets]
                self.book.fill(indicesB.index(iB2), "iB_b2_"+tag, 10,-0.5,9.5, title = ';b-ordered index of second b (%s);events / bin'%tag)
                self.book.fill(indicesPt.index(iB2), "iPt_b2_"+tag, 10,-0.5,9.5, title = ';pt-ordered index of second b (%s);events / bin'%tag)

#####################################
class topProbLook(analysisStep) :
    def __init__(self, jets) :
        self.indicesGenB = "%sIndicesGenB%s"%jets
        self.indicesGenWqq = "%sIndicesGenWqq%s"%jets
        self.indices = "%sIndices%s"%jets
    def uponAcceptance(self,ev) :
        maxProb = ev["TopComboMaxProbability"]
        trueCombo = tuple( sorted(ev[self.indicesGenB]) + sorted(ev[self.indicesGenWqq]) )
        multiplicity = len(ev[self.indices])
        for key,val in ev["TopComboProbability"].iteritems() :
            tag = "true" if key == trueCombo else "other"
            self.book.fill(val, "topProbability"+tag, 100,0,1, title = ";%s top probability;events / bin"%tag)
            self.book.fill(val/maxProb, "topRelProbability"+tag, 100,0,1, title = ";%s top probability/ maxTopProb;events / bin"%tag)
            self.book.fill((val/maxProb,multiplicity), "topRelProbabilityByMulti"+tag, (100,10),(0,0),(1,10), title = ";%s top probability/ maxTopProb;jet multiplicity;events / bin"%tag)
            self.book.fill((maxProb,val), "topProbability_vMax"+tag, (100,100),(0,0),(1,1), title = ";maxTopProb;%s top probability;events / bin"%tag)
        self.book.fill(maxProb, "TopComboMaxProbability", 100,0,1, title = ';TopComboMaxProbability;events / bin')
        self.book.fill((maxProb,multiplicity), "TopComboMaxProbabilityLen"+self.indices, (100,10), (0,-0.5), (1,9.5), title = ';TopComboMaxProbability;jet multiplicity;events / bin')
#####################################
class combinatoricsLook(analysisStep) :
    def __init__(self,indexName, jets = None) :
        self.moreName = indexName
        self.jets = jets
    def uponAcceptance(self,ev) :
        topReco = ev["TopReconstruction"]
        index = ev[self.moreName]
        for s in ['lep','nu','bLep','bHad','q'] :
            self.book.fill(ev['%sDeltaRTopRecoGen'%s][index], s+'DeltaRTopRecoGen', 50,0,3, title = ';%s DeltaR reco gen;events / bin'%s)
        self.book.fill(index, self.moreName, 20, -0.5, 19.5, title = ';%s;events / bin'%self.moreName)
        self.book.fill(topReco[index]['probability'], "probability", 100,0,1, title = ';%s probability;events / bin'%self.moreName)

        if self.jets :
            self.book.fill((index,len(ev["%sIndices%s"%self.jets])), self.moreName+"%sMultiplicity%s"%self.jets, (20,10), (-0.5,-0.5), (19.5,9.5), title = ';%s;jet multiplicity;events / bin'%self.moreName)

        genTTbar = ev["genTopTTbar"]
        if not genTTbar : return
        genY = (ev["genP4"][genTTbar[0]].Rapidity(), ev["genP4"][genTTbar[1]].Rapidity())
        recoY = (topReco[index]['top'].Rapidity(),topReco[index]['tbar'].Rapidity())
        iLep = min(0,topReco[index]["lepCharge"])
        self.book.fill( recoY[iLep] - genY[iLep], "dRapidityLepTop", 100,-1,1, title=";lep top #Delta y_{reco gen};events / bin")
        self.book.fill( recoY[not iLep] - genY[not iLep], "dRapidityHadTop", 100,-1,1, title=";had top #Delta y_{reco gen};events / bin")
        self.book.fill( recoY[0]-recoY[1] - (genY[0]-genY[1]), "ddRapidityTTbar", 100,-1,1, title = ";#Delta y_{t#bar{t} reco}-#Delta y_{t#bar{t} gen};events / bin")

        iHad = max(0,topReco[index]["lepCharge"])
        genLepY = ev['genP4'][max(ev['genTTbarIndices'][item] for item in ['lplus','lminus'])].Rapidity()
        self.book.fill( recoY[iHad] - topReco[index]['lep'].Rapidity() - (genY[iHad]-genLepY), "ddRapidityLHadTop", 100,-1,1, title = ";#Delta y_{l-htop reco}-#Delta y_{l-htop gen};events / bin")
######################################
class discriminateNonTop(analysisStep) :
    def __init__(self, pars) :
        obj = pars['objects']
        lepCollection = obj[pars['lepton']['name']]
        self.MT = "%sMt%s"%lepCollection+"mixedSumP4"
        self.sumPt = obj["sumPt"]
        self.HT = "%sSumPt%s"%obj["jet"]
        self.jetP4 = "%sCorrectedP4%s"%obj["jet"]
        self.iJet = "%sIndices%s"%obj["jet"]
        self.bJet = "%sIndicesBtagged%s"%obj["jet"]        
        self.lepP4 = "%sP4%s"%lepCollection
        self.iLep = "%sSemileptonicTopIndex%s"%lepCollection
        self.kT = "%sKt%s"%obj["jet"]

    def uponAcceptance(self, ev) :
        jetP4 = ev[self.jetP4]
        iJet = ev[self.iJet]
        bJet = ev[self.bJet]
        lepP4 = ev[self.lepP4][ev[self.iLep]]
        
        self.book.fill( ev["mixedSumP4"].pt(), "met", 60, 0, 180, title = ';met;events / bin')
        self.book.fill( lepP4.pt(), "leptonPt", 60, 0, 180, title = ';lepton Pt;events / bin')
        self.book.fill( abs(lepP4.eta()), "leptonEta", 50, 0, 3, title = ';lepton |#eta|;events / bin')
        self.book.fill(ev[self.MT],self.MT,30,0,180, title = ";M_{T};events / bin")
        dphiLnu = abs(r.Math.VectorUtil.DeltaPhi(lepP4,ev["mixedSumP4"]))
        self.book.fill( dphiLnu, "dphiLnu", 20,0,math.pi, title = ";#Delta#phi l#nu;events / bin" )
        self.book.fill( (dphiLnu,ev[self.MT]), "dphiLnu_v_mt", (20,30),(0,0),(math.pi,180), title = ";#Delta#phi l#nu;M_{T};events / bin" )
        self.book.fill( ev[self.kT], "kT", 30, 0, 150, title = ";k_{T};events / bin")

        self.book.fill(ev[self.sumPt],self.sumPt,50,0,1500, title = ';%s;events / bin'%self.sumPt)
        self.book.fill(ev[self.HT],self.HT,50,0,1500, title = ';%s;events / bin'%self.HT)
        
        self.book.fill(jetP4[iJet[0]].pt(), "jetPtI0", 40,0,400, title = ';pT jets[0] pt;events / bin')
        self.book.fill(jetP4[bJet[0]].pt(), "jetPtB0", 40,0,400, title = ';b- jets[0] pt;events / bin')
        self.book.fill( abs(r.Math.VectorUtil.DeltaPhi(jetP4[bJet[0]],jetP4[bJet[1]])), "dphiBjets", 20,0,math.pi,
                        title = ";#Delta#phi leading b-tagged jets;events / bin" )
        for i in range(min(4,len(iJet))) :
            self.book.fill(abs(jetP4[iJet[i]].eta()), "jetEtaI%d"%i, 40,0,4, title = ';pT jets[%d] |#eta|;events / bin'%i)

#####################################
class discriminateQQbar(analysisStep) :
    def __init__(self, collection) :
        for item in ['DeltaPhi','PtOverSumPt','SumP4','CosThetaDaggerTT'] :
            setattr(self,item,('%s'+item+'%s')%collection)
        
    @staticmethod
    def phiMod(phi) : return phi + 2*math.pi*int(phi<0)

    def uponAcceptance(self,ev) :
        if not ev['genTopTTbar'] : return

        dphi = self.phiMod(ev[self.DeltaPhi])

        ### dphi is highly correlated with PtAsym and/or PtOverSumPt, but they are mostly uncorrelated to alpha
        #self.book.fill( (dphi,ev['genTopPtAsymttbar']), 'corrDphiPtAsym', (51,51), (0,-1),(2*math.pi,1), title=';dphi;ptasymm;events / bin' )
        #self.book.fill( (dphi,ev['genTopAlpha']), 'corrDphiAlpha', (51,10), (0,0),(2*math.pi,1), title=';dphi;#alpha;events / bin' )
        #self.book.fill( (ev['genTopTTbarPtOverSumPt'],ev['genTopAlpha']), 'corrPtAsymAlpha', (50,10), (0,0),(1,1), title=';(t+tbar)_{pt}/(t_{pt}+tbar_{pt});#alpha;events / bin' )

        self.book.fill( dphi, self.DeltaPhi, 51,0,2*math.pi, title = ';#Delta #phi_{ttbar};events / bin')
        self.book.fill( ev[self.PtOverSumPt], self.PtOverSumPt, 50,0,1, title = ';(t+tbar)_{pt}/(t_{pt}+tbar_{pt});events / bin')
        self.book.fill( ev[self.CosThetaDaggerTT], self.CosThetaDaggerTT, 50,-1,1, title = ';cos#theta^{#dagger}_{tt}')
        sumP4 = ev[self.SumP4]
        self.book.fill( abs(sumP4.Rapidity()), self.SumP4+'AbsRapidity', 50,0,3, title = ';y_{ttbar};events / bin')
        self.book.fill( abs(sumP4.Eta()), self.SumP4+'AbsEta', 40,0,10, title = ';|#eta_{ttbar}|;events / bin')
        self.book.fill( abs(sumP4.Pz()), self.SumP4+'AbsPz', 50,0,3000, title = ';|pz|_{ttbar};events / bin')
        
#####################################
class mcTruthQDir(analysisStep) :
    def __init__(self,withLepton = False, withNu = False) :
        self.withNu = withNu and withLepton
        self.withLepton = withLepton
        
    def uponAcceptance(self,ev) :
        if ev['isRealData'] : return
        genSumPz = ev['genSumP4'].pz()
        #for sumP4 in ['genTopNuP4','genTopTTbarSumP4','mixedSumP4','mixedSumP4Nu'][:4 if self.withNu else 3 if self.withLepton else 2] :
        #    self.book.fill( (genSumPz, ev[sumP4].pz()), "genSumP4_%s_pz"%sumP4, (100,100),(-3000,-3000),(3000,3000),
        #                    title = ";genSumP4 pz;%s pz;events/bin"%sumP4)

        qqbar = ev['genQQbar']
        if qqbar :
            qdir = 1 if ev['genP4'][qqbar[0]].pz()>0 else -1
            for sumP4 in ['genSumP4','genTopSumP4','mixedSumP4','mixedSumP4Nu'][:4 if self.withNu else 3 if self.withLepton else 2] :
                self.book.fill( qdir * ev[sumP4].pz(), "qdir_%s_pz"%sumP4, 100,-3000,3000, title = ';qdir * %s.pz;events/bin'%sumP4)
                self.book.fill( qdir * ev[sumP4].Eta(), "qdir_%s_eta"%sumP4, 100,-10,10, title = ';qdir * %s.eta;events/bin'%sumP4)
        
#####################################
class mcTruthAcceptance(analysisStep) :
    def uponAcceptance(self,ev) :
        if not ev['genTopTTbar'] : return

        indices = ev['genTTbarIndices']
        if not bool(indices['lplus'])^bool(indices['lminus']) : return
        lep = ev['genP4'][max(indices['lplus'],indices['lminus'])]
        iJets = [indices['b'],indices['bbar']] + indices['wplusChild' if indices['lminus'] else 'wminusChild']
        jets = [ev['genP4'][i] for i in iJets]
        iBlep = indices['b'] if indices['lplus'] else indices['bbar']
        
        self.book.fill(lep.eta(),"lepEta",31,-5,5, title=';#eta_{lep};events / bin')
        self.book.fill(max([abs(p4.eta()) for p4 in jets]), 'jetEtaMax', 30,0,5, title=';jet |#eta|_{max};events / bin')
        self.book.fill(max([abs(p4.eta()) for p4 in jets[:2]]), 'jetEtaMaxB', 30,0,5, title=';b jet |#eta|_{max};events / bin')
        self.book.fill(max([abs(p4.eta()) for p4 in jets[2:]]), 'jetEtaMaxLite', 30,0,5, title=';lite jet |#eta|_{max};events / bin')

        pts = [p4.pt() for p4 in jets]
        self.book.fill(min(pts), 'jetMinPt', 50,0,100, title=';jet pT_{min};events / bin')
        self.book.fill(min(pts[:2]), 'jetMinPtB', 50,0,100, title=';b jet pT_{min};events / bin')
        self.book.fill(min(pts[2:]), 'jetMinPtLite', 50,0,100, title=';lite jet pT_{min};events / bin')

        self.book.fill( max(pts[:2]) - min(pts[2:]), "diffBigBLittleQ", 50,-50,100,title=';pT_{maxb}-pT_{minq};events / bin' )
        self.book.fill( min(pts[:2]) - max(pts[2:]), "diffLittleBBigQ", 50,-50,100,title=';pT_{minb}-pT_{maxq};events / bin' )
        self.book.fill( sum(pts[:2]) - sum(pts[2:]), "diffSumBBSumQQ", 50,-50,100,title=';sumpT_{b}-sumpT_{q};events / bin' )
        
        self.book.fill(sum(pts), 'jetSumPt', 50, 0, 800, title=';#sum pT_{top jets};events / bin')
        self.book.fill(sum(pts)-ev['genP4'][iBlep].pt(), 'jetSumPtHad', 50, 0, 500, title=';hadronic #sum pT_{top jets};events / bin')

        self.book.fill( int(max(pts)==max(pts[:2])), "maxPtJetIsBjet", 2, 0 , 1, title = ';maxPt is bjet;events / bin')
        self.book.fill( int(max(pts[:2])>min(pts[2:])), "maxPtOrNextJetIsBjet", 2, 0 , 1, title = ';maxPt or next is bjet;events / bin')
        self.book.fill( int(sum(pts[:2])>sum(pts[2:])), "sumPtBB_gt_sumPtPQ", 2, 0 , 1, title = ';sumPt of bs > sumPt of pq;events / bin')
#####################################
class mcTruthTemplates(analysisStep) :
    def uponAcceptance(self,ev) :
        if not ev['genTopTTbar'] : return

        self.book.fill(ev['genTopAlpha'],'alpha',10,0,2,title=';genTopAlpha;events / bin')
        alpha = '_alpha%02d'%int(10*ev['genTopAlpha'])

        self.book.fill(ev['genTopCosThetaStarAvg'], 'cosThetaStarAvg%s'%alpha, 20, -1, 1, title = ';cosThetaStarAvg;events / bin')
        self.book.fill(ev['genTopCosThetaStarAngle'], 'cosThetaStarAngle%s'%alpha, 30, 0, 0.5*math.pi, title = ';cosThetaStarAngle;events / bin')

        self.book.fill(ev['genTopBoostZAlt'].Beta(), "boostz", 20, -1, 1, title = ';boost z;events / bin')
        self.book.fill(ev['genTopBeta'], 'genTopBeta', 20,-2,2, title = ";beta;events / bin")
        self.book.fill( (ev['genTopCosThetaStarAvg'],ev['genTopCosThetaStarAlt']), 'cts_v_ctsbar%s'%alpha, (100,100),(-1,-1),(1,1), title = ';costhetaQT;cosThetaQbarTbar;events/bin')
        #self.book.fill( (ev['genTopCosThetaStar'],ev['genTopAlpha']), 'cts_v_alpha', (25,25),(-1,0),(1,1), title = ';costhetaQT;#alpha;events/bin')
        #self.book.fill( (ev['genTopCosThetaStarAvg'],ev['genTopAlpha']), 'ctsavg_v_alpha', (25,25),(-1,0),(1,1), title = ';costhetaAvg;#alpha;%s events/bin')
        #self.book.fill(ev['genTopTTbarSumP4'].M(), "genttbarinvmass", 40,0,1000, title = ';ttbar invariant mass;events / bin' )
        #for i in [0,1]: self.book.fill(ev['genP4'][ev['genTopTTbar'][i]].M(), "topmass", 50, 120, 220, title = ';top mass;events / bin')
        
        qqbar = ev['genQQbar']
        genP4 = ev['genP4']
        qdir = 1 if qqbar and genP4[qqbar[0]].pz()>0 else -1
        genP4dir = 1 if ev['genSumP4'].pz() > 0 else -1
        
        self.book.fill(    qdir * ev['genTopDeltaYttbar'], 'genTopTrueDeltaYttbar', 31,-5,5, title = ';True Signed #Delta y_{ttbar};events / bin')
        self.book.fill(genP4dir * ev['genTopDeltaYttbar'], 'genTopMezDeltaYttbar', 31,-5,5, title = ';MEZ Signed #Delta y_{ttbar};events / bin')
        self.book.fill(        ev['genTopDeltaAbsYttbar'], 'genTopDeltaAbsYttbar', 31,-5,5, title = ';#Delta |y|_{ttbar};events / bin')

        indices = ev['genTTbarIndices']
        if indices['lplus'] and indices['lminus'] :
            dy = genP4[indices['lplus']].Rapidity() - genP4[indices['lminus']].Rapidity()
            self.book.fill(    qdir * dy, "genTopTrueDeltaYll", 31,-5,5, title = ';True Signed #Delta y_{ll};events / bin')
            self.book.fill(genP4dir * dy, "genTopMezDeltaYll", 31,-5,5, title = ';MEZ Signed #Delta y_{ll};events / bin')
        elif indices['lplus'] or indices['lminus'] :
            Q = 1 if indices['lplus'] else -1
            lRapidity = genP4[max(indices['lplus'],indices['lminus'])].Rapidity()
            dy = (lRapidity - ev['genSumP4'].Rapidity())
            for suf in ['','Positive' if Q>0 else 'Negative'] :
                self.book.fill(    qdir * Q * dy, "genTopTrueDeltaYlmiss"+suf, 31,-5,5, title = '%s;True Signed #Delta y_{lmiss};events / bin'%suf)
                self.book.fill(genP4dir * Q * dy, "genTopMezDeltaYlmiss"+suf, 31,-5,5, title = '%s;MEZ Signed #Delta y_{lmiss};events / bin'%suf)
                self.book.fill(    qdir * Q * lRapidity, "genTopTrueLRapidity"+suf, 31,-5,5, title = "%s;True Signed y_l;events / bin"%suf)
                self.book.fill(genP4dir * Q * lRapidity, "genTopMezLRapidity"+suf, 31,-5,5, title = "%s;MEZ Signed y_l;events / bin"%suf)
######################
class mcTruthAsymmetryBinned(analysisStep) :
    def __init__(self, binVar, bins, min, max, collection = ("genTop","")) :
        for item in ['bins', 'min', 'max'] : setattr(self,item,eval(item))
        self.asymmVar = "%sDeltaY%s"%collection
        self.binVar = ("%s"+binVar+"%s")%collection
        self.binName = "%s_%s"%(self.asymmVar, self.binVar) + "%03d"
        
    def uponAcceptance(self,ev) :
        qqbar = ev['genQQbar']
        genP4 = ev['genP4']
        qdir = 1 if qqbar and genP4[qqbar[0]].pz()>0 else -1

        binVar = ev[self.binVar]
        Dy = ev[self.asymmVar] * qdir
        self.book.fill(binVar, self.binVar, self.bins, self.min, self.max, title = ';%s;events / bin'%self.binVar )
        bin = min(self.book[self.binVar].FindFixBin(binVar),self.bins)
        self.book.fill(Dy, self.binName%bin, 2, -50, 50, title = ";%s %d;events / bin"%(self.asymmVar,bin))

    def outputSuffix(self) : return steps.Master.Master.outputSuffix()

    def varsToPickle(self) :
        return ["bins","min","max","binName","asymmVar","binVar"]

    @staticmethod
    def asymmetryFromHist(hist) :
        if not hist : return 0,0
        nMinus = hist.GetBinContent(1)
        nMinusE = hist.GetBinError(1)
        nPlus = hist.GetBinContent(2)
        nPlusE = hist.GetBinError(2)
        S = nPlus + nMinus
        asymm = float(nPlus - nMinus) / S
        err = 2./S**2 * math.sqrt((nPlus*nMinusE)**2+(nMinus*nPlusE)**2)
        return asymm,err

    def mergeFunc(self, products) :
        file = r.TFile.Open(self.outputFileName, "UPDATE")
        master = file.FindObjectAny("Master")
        asymm = [self.asymmetryFromHist(master.FindObjectAny(self.binName%(bin+1))) for bin in range(self.bins) ]
        binVarHist = master.FindObjectAny(self.binVar)
        binVarHist.GetDirectory().cd()

        asymmByBinVar = binVarHist.Clone("%s_%s"%(self.binVar,self.asymmVar))
        asymmByBinVar.SetTitle(";%s;%s"%(self.binVar,"A_{fb}"))
        asymmByBinVar.SetMinimum(-0.5)
        asymmByBinVar.SetMaximum(0.5)
        
        for i in range(self.bins) :
            print asymm[i]
            asymmByBinVar.SetBinContent(i+1,asymm[i][0])
            asymmByBinVar.SetBinError(i+1,asymm[i][1])
        asymmByBinVar.SetBinContent(self.bins+1,0)
        asymmByBinVar.SetBinError(self.bins+1,0)
        asymmByBinVar.Write()
        r.gROOT.cd()
        file.Close()
        #print "Output updated with %s."%asymmByBinVar.GetName()
