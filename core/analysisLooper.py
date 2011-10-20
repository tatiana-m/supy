import copy,array,os,cPickle,tempfile,collections
import wrappedChain,utils,steps,configuration
from autoBook import autoBook
import ROOT as r
#####################################
class analysisLooper :
    """class to set up and loop over events"""

    def __init__(self, mainTree = None, otherTreesToKeepWhenSkimming = None, leavesToBlackList = None,
                 localStem = None, globalStem = None, subDir = None, steps = None, calculables = None, inputFiles = None, name = None,
                 nEventsMax = None, quietMode = None) :

        for arg in ["mainTree", "otherTreesToKeepWhenSkimming", "leavesToBlackList", "steps", "calculables",
                    "localStem", "globalStem", "subDir", "inputFiles", "name", "nEventsMax", "quietMode"] :
            setattr(self, arg, eval(arg))

        self.outputDir = self.globalDir #the value will be modified in self.prepareOutputDirectory()
        self.inputDir = self.globalDir 
        self.checkSteps()

    @property
    def globalDir(self) : return "%s/%s/"%(self.globalStem, self.subDir)
    @property
    def outputFileStem(self) :  return "%s/%s"%(self.outputDir, self.name)
    @property
    def inputFileStem(self) :  return "%s/%s"%(self.inputDir, self.name)
    @property
    def pickleFileName(self) : return "%s%s"%(self.outputFileStem, ".pickledData")

    def checkSteps(self) :
        for iStep,step in enumerate(self.steps) :
            if iStep : continue
            assert step.name=="Master", "The master step must occur first."
            assert step.isSelector, "The master step must be a selector."
        selectors = [ (s.name,s.moreNames) for s in self.steps if s.isSelector ]
        for sel in selectors : assert 1==selectors.count(sel), "Duplicate selector (%s,%s) is not allowed."%sel
        inter = set(s.name for s in self.steps if not issubclass(type(s),wrappedChain.wrappedChain.calculable)).intersection(set(c.name for c in self.calculables))
        if inter: print "Steps and calculables cannot share names { %s }"%', '.join(n for n in inter)
        
    def childName(self, nSlices, iSlice) : return "%s_%d_%d"%(self.name,nSlices,iSlice)
    def slice(self, nSlices, iSlice) :
        assert iSlice<nSlices, "How did you do this?"
        out = copy.deepcopy(self)
        out.inputFiles = out.inputFiles[iSlice::nSlices]
        out.globalDir = "%s/%s"%(self.globalDir,self.name)
        out.outputDir = "%s/%s"%(self.outputDir,self.name)
        out.name = self.childName(nSlices,iSlice)
        return out
        
    def __call__(self) :
        self.prepareOutputDirectory()
        self.setupChains()
        self.setupSteps()
        self.loop()
        self.endSteps()
        self.writeRoot()
        self.writePickle()
        self.deleteChains()
        self.moveFiles()
        if not self.quietMode : print utils.hyphens

    def loop(self) :
        if self.nEventsMax!=0 :
            chainWrapper = wrappedChain.wrappedChain( self.chains[self.mainTree],
                                                      calculables = self.calculables,
                                                      useSetBranchAddress = not any([step.requiresNoSetBranchAddress() for step in self.steps]),
                                                      leavesToBlackList = self.leavesToBlackList,
                                                      maxArrayLength = configuration.maxArrayLength(),
                                                      trace = configuration.trace(),
                                                      cacheSizeMB = configuration.ttreecacheMB(),
                                                      )
            for step in filter(lambda s: (issubclass(type(s),wrappedChain.wrappedChain.calculable) and
                                          hasattr(s,"source") and
                                          hasattr(s.source,"tracedKeys")), self.steps) :
                step.tracer = step.source
                step.source.tracedKeys |= step.priorFilters

            [ all(step(eventVars) for step in self.steps) for eventVars in chainWrapper.entries(self.nEventsMax) ]

            for step in filter(lambda s: s.tracer and s.name in s.tracer.tracedKeys, self.steps) : step.tracer.tracedKeys.remove(step.name)
            self.recordLeavesAndCalcsUsed( chainWrapper.activeKeys(), chainWrapper.calcDependencies() )
        else : self.recordLeavesAndCalcsUsed([], {})

    def recordLeavesAndCalcsUsed(self, activeKeys, calculableDependencies) :
        calcs = dict([(calc.name,calc) for calc in self.calculables])
        def calcTitle(key) : return "%s%s%s"%(calcs[key].moreName, calcs[key].moreName2, configuration.fakeString() if calcs[key].isFake() else "")
        self.calculablesUsed = set([ (key,calcTitle(key)) for key,isLeaf,keyType in activeKeys if not isLeaf ])
        self.leavesUsed      = set([ (key,       keyType) for key,isLeaf,keyType in activeKeys if isLeaf ])
        self.calculableDependencies = collections.defaultdict(set)
        for key,val in calculableDependencies.iteritems() :
            self.calculableDependencies[key] = set(map(lambda c: c if type(c)==tuple else (c,c),val))
        
    def prepareOutputDirectory(self) :
        utils.mkdir(self.localStem)
        self.tmpDir = tempfile.mkdtemp(dir = self.localStem)
        self.outputDir = self.outputDir.replace(self.globalStem, self.tmpDir)
        utils.mkdir(self.outputDir)
        
    def moveFiles(self) :
        utils.mkdir(self.globalDir)
        os.system("rsync -a %s/ %s/"%(self.outputDir, self.globalDir))
        os.system("rm -r %s"%self.tmpDir)
        
    def setupChains(self) :
        self.chains = dict( [(item,r.TChain("chain%d"%iItem)) for iItem,item in enumerate([self.mainTree]+self.otherTreesToKeepWhenSkimming)])
        for (dirName,treeName),chain in self.chains.iteritems() :
            for infile in self.inputFiles : chain.Add("%s/%s/%s"%(infile, dirName, treeName))
            r.SetOwnership(chain, False)

        if not self.quietMode :
            nFiles = len(self.inputFiles)
            nEventsString = str(self.chains[self.mainTree].GetEntries()) if configuration.computeEntriesForReport() else "(number not computed)"
            print utils.hyphens
            print "The %d \"%s\" input file%s:"%(nFiles, self.name, "s" if nFiles>1 else '')
            print '\n'.join(self.inputFiles[:2]+["..."][:len(self.inputFiles)-1]+self.inputFiles[2:][-2:])
            print "contain%s %s events."%(("s" if nFiles==1 else ""), nEventsString)
            print utils.hyphens

    def deleteChains(self) : #free up memory (http://wlav.web.cern.ch/wlav/pyroot/memory.html)
        for chain in self.chains.values() : utils.delete(chain)
        for step in self.steps :
            for name,hist in list(step.book.iteritems()) :
                utils.delete(hist)
                #del step.book[name]
        
    def setupSteps(self, withBook = True, minimal = False) :
        r.gROOT.cd()
        current = r.gDirectory
        priorFilters = []
        self.steps[0].books = []

        for step in self.steps :
            step.setOutputFileStem(self.outputFileStem)
            step.setInputFileStem(self.inputFileStem)
            step.priorFilters = set(priorFilters)
            if step.isSelector and step!=self.steps[0] : priorFilters.append((step.name,step.moreNames))

            if withBook : 
                current = current.mkdir(step.name)
                step.book = autoBook(current)
                self.steps[0].books.append(step.book)

            if minimal : continue
            step.tracer = wrappedChain.keyTracer(None) if configuration.trace() and (step.isSelector or issubclass(type(step),wrappedChain.wrappedChain.calculable)) else None
            if self.quietMode : step.makeQuiet()
            assert step.isSelector ^ hasattr(step,"uponAcceptance"), "Step %s must implement 1 and only 1 of {select,uponAcceptance}"%step.name
            step.setup(self.chains[self.mainTree], self.mainTree[0])

    def endSteps(self) : [ step.endFunc(self.chains) for step in self.steps ]
        
    def writeRoot(self) :
        def writeFromSteps() :
            while "/" not in r.gDirectory.GetName() : r.gDirectory.GetMotherDir().cd()
            for step in self.steps :
                r.gDirectory.mkdir(step.name, step.moreNames).cd()
                for hist in [step.book[name] for name in step.book.fillOrder] : hist.Write()
                if configuration.trace() and step.isSelector :
                    r.gDirectory.mkdir("Calculables").cd()
                    for key in step.tracer.tracedKeys : r.gDirectory.mkdir(key)
                    r.gDirectory.GetMother().cd()
    
        def writeNodesUsed() :
            while "/" not in r.gDirectory.GetName() : r.gDirectory.GetMotherDir().cd()
            r.gDirectory.mkdir("Leaves",".").cd()
            for leaf in self.leavesUsed: r.gDirectory.mkdir(*leaf)
            r.gDirectory.GetMother().cd()
            r.gDirectory.mkdir("Calculables",".").cd()
            for calc in self.calculablesUsed :
                r.gDirectory.mkdir(*calc).cd()
                for dep in self.calculableDependencies[calc[0]] : r.gDirectory.mkdir(dep[0]+dep[1],dep[1])
                r.gDirectory.GetMother().cd()
            r.gDirectory.GetMother().cd()

        outputFile = r.TFile(self.steps[0].outputFileName, "RECREATE")
        writeNodesUsed()
        writeFromSteps()
        outputFile.Close()

    def writePickle(self) :
        def pickleJar(step) :
            inter = set(step.varsToPickle()).intersection(set(['nPass','nFail','outputFileName']))
            assert not inter, "%s is trying to pickle %s, which %s reserved for use by analysisStep."%(step.name, str(inter), "is" if len(inter)==1 else "are")
            return dict([ (item, getattr(step,item)) for item in step.varsToPickle()+['nPass','nFail']] +
                        [('outputFileName', getattr(step,'outputFileName').replace(self.outputDir, self.globalDir))])

        utils.writePickle( self.pickleFileName,
                           [ [pickleJar(step) for step in self.steps], self.calculablesUsed, self.leavesUsed] )

    def readyMerge(self, nSlices) :
        foundAll = True
        for iSlice in range(nSlices) :
            pickleFileBlocks = self.pickleFileName.split('/')
            pickleFileBlocks.insert(-1,self.name)
            pickleFileBlocks[-1] = pickleFileBlocks[-1].replace(self.name,self.childName(nSlices,iSlice))
            pickleFileName = '/'.join(pickleFileBlocks)
            if not os.path.exists(pickleFileName) :
                print "Can't find file : %s"%pickleFileName
                foundAll = False
        return foundAll

    def mergeFunc(self, nSlices) :
        cleanUpList = []
        self.setupSteps(minimal = True)
        self.calculablesUsed = set()
        self.leavesUsed = set()
        products = [collections.defaultdict(list) for step in self.steps]
        
        for iSlice in range(nSlices) :
            pickleFileBlocks = self.pickleFileName.split('/')
            pickleFileBlocks.insert(-1,self.name)
            pickleFileBlocks[-1] = pickleFileBlocks[-1].replace(self.name,self.childName(nSlices,iSlice))
            cleanUpList.append( '/'.join(pickleFileBlocks[:-1]) )
            dataByStep,calcsUsed,leavesUsed = utils.readPickle( '/'.join(pickleFileBlocks) )
            self.calculablesUsed |= calcsUsed
            self.leavesUsed |= leavesUsed
            for stepDict,data in zip(products, dataByStep) :
                for key,val in data.iteritems() : stepDict[key].append(val)
    
        for step,stepDict in filter(lambda s: s[0].isSelector, zip(self.steps, products)) :
            step.increment(True, sum(stepDict["nPass"]))
            step.increment(False,sum(stepDict["nFail"]))
                
        self.printStats()
        print utils.hyphens
        for iStep,step,stepDict in zip(range(len(self.steps)),self.steps,products) :
            if iStep : rootFile.cd('/'.join(step.name for step in self.steps[:iStep+1] ))
            step.mergeFunc(stepDict)
            if not iStep: rootFile = r.TFile.Open(self.steps[0].outputFileName, "UPDATE")
        rootFile.Close()
        for dirName in cleanUpList : os.system("rm -fr %s"%dirName)

    def printStats(self) :
        print utils.hyphens
        print self.name
        
        if configuration.printNodesUsed() :
            print utils.hyphens
            print "Leaves accessed:"
            print str([x[0] for x in self.leavesUsed]).replace("'","")
            print utils.hyphens
            print "Calculables accessed:"
            print str([x[0] for x in self.calculablesUsed]).replace("'","")

        print utils.hyphens
        print "Calculables' configuration:"
        print '\n'.join("%s\t\t%s"%calc for calc in self.calculablesUsed if calc[1])
                
        #print step statistics
        if not len(self.steps) : return
        print utils.hyphens
        width = self.steps[0].integerWidth
        print "Steps:%s" % ("nPass ".rjust(width) + "(nFail)".rjust(width+2)).rjust(len(utils.hyphens)-len("Steps:"))
        for step in self.steps :
            step.printStatistics()
        print utils.hyphens

#####################################
