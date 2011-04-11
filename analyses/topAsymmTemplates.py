#!/usr/bin/env python

import os,analysis,steps,calculables,samples,organizer,plotter,utils,math
import ROOT as r

class topAsymmTemplates(analysis.analysis) :
    def parameters(self) :
        return {"sample" : {"compare":["mg","pythia"],
                            "mg":"mg",
                            "pythia":"pythia"
                            },
                "effectiveLumi" : None
                }

    def listOfCalculables(self, pars) :
        outList  = calculables.zeroArgs()
        outList += [
            calculables.Vertex.ID(),
            calculables.Vertex.Indices(),
            ]
        return outList
    
    def listOfSteps(self, pars) :
        return [steps.Print.progressPrinter(),
                steps.Filter.label("q direction"), steps.Top.mcTruthQDir(),
                steps.Filter.label("non-qqbar"),   steps.Top.mcTruth(qqbar=False),
                steps.Filter.label("qqbar"),       steps.Top.mcTruth(qqbar=True),
                steps.Filter.label("all"),         steps.Top.mcTruth(),
                steps.Filter.OR([steps.Filter.value('genTTbarIndices',min=0,index='lplus'),
                                 steps.Filter.value('genTTbarIndices',min=0,index='lminus')]),
                steps.Top.mcTruth(),
                ]
    
    def listOfSampleDictionaries(self) :
        return [samples.mc]

    def listOfSamples(self,pars) :
        from samples import specify
        eL = pars["effectiveLumi"]

        if type(pars["sample"]) is list :
            return (specify( names = "tt_tauola_%s"%pars["sample"][0], effectiveLumi = eL) +
                    specify( names = "tt_tauola_%s"%pars["sample"][1], effectiveLumi = eL, color = r.kRed) )

        sample = "tt_tauola_%s"%pars["sample"]
        return (
            specify( names = sample, effectiveLumi = eL, color = r.kBlack,     weightName = "wTopAsymN30") +
            specify( names = sample, effectiveLumi = eL, color = r.kBlue,      weightName = "wTopAsymN20") +
            specify( names = sample, effectiveLumi = eL, color = r.kGreen+3,   weightName = "wTopAsymN10") +
            specify( names = sample, effectiveLumi = eL, color = r.kGreen,     weightName = "wTopAsymP00") +
            specify( names = sample, effectiveLumi = eL, color = r.kYellow-3,  weightName = "wTopAsymP10") +
            specify( names = sample, effectiveLumi = eL, color = r.kOrange,    weightName = "wTopAsymP20") +
            specify( names = sample, effectiveLumi = eL, color = r.kRed,       weightName = "wTopAsymP30")
            )
    
    def conclude(self) :
        for tag in self.sideBySideAnalysisTags() :
            #organize
            org=organizer.organizer( self.sampleSpecs(tag) )
            org.scale(toPdf=True)
            
            #plot
            pl = plotter.plotter(org,
                                 psFileName = self.psFileName(tag),
                                 doLog = False,
                                 #compactOutput = True,
                                 #noSci = True,
                                 pegMinimum = 0.1,
                                 blackList = ["lumiHisto","xsHisto","nJobsHisto"],
                                 )
            pl.plotAll()
