# Auto generated configuration file
# using: 
# Revision: 1.19 
# Source: /local/reps/CMSSW/CMSSW/Configuration/Applications/python/ConfigBuilder.py,v 
# with command line options: step3 -s RAW2DIGI,RECO --conditions auto:phase1_2023_realistic --datatier GEN-SIM-RECO -n 10 --eventcontent RECOSIM --geometry DB:Extended --era Run3 --filein file:step2.root --fileout file:step3_custom.root
import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Run3_cff import Run3

process = cms.Process('RECO',Run3)

# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.RawToDigi_cff')
process.load('Configuration.StandardSequences.Reconstruction_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.MessageLogger.cerr.FwkReport.reportEvery = 1

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1),
    output = cms.optional.untracked.allowed(cms.int32,cms.PSet)
)

# Input source
process.source = cms.Source("PoolSource",
                            fileNames = cms.untracked.vstring('file:/eos/cms/store/data/Run2023C/ZeroBias/RAW/v1/000/367/661/00000/876b3d34-abd8-4254-a78d-e319bc444e65.root'),
    secondaryFileNames = cms.untracked.vstring()
)

process.options = cms.untracked.PSet(
    # FailPath = cms.untracked.vstring(),
    IgnoreCompletely = cms.untracked.vstring(),
    Rethrow = cms.untracked.vstring(),
    # SkipEvent = cms.untracked.vstring(),
    accelerators = cms.untracked.vstring('*'),
    allowUnscheduled = cms.obsolete.untracked.bool,
    canDeleteEarly = cms.untracked.vstring(),
    deleteNonConsumedUnscheduledModules = cms.untracked.bool(True),
    dumpOptions = cms.untracked.bool(False),
    emptyRunLumiMode = cms.obsolete.untracked.string,
    eventSetup = cms.untracked.PSet(
        forceNumberOfConcurrentIOVs = cms.untracked.PSet(
            allowAnyLabel_=cms.required.untracked.uint32
        ),
        numberOfConcurrentIOVs = cms.untracked.uint32(0)
    ),
    fileMode = cms.untracked.string('FULLMERGE'),
    forceEventSetupCacheClearOnNewRun = cms.untracked.bool(False),
    makeTriggerResults = cms.obsolete.untracked.bool,
    numberOfConcurrentLuminosityBlocks = cms.untracked.uint32(0),
    numberOfConcurrentRuns = cms.untracked.uint32(1),
    numberOfStreams = cms.untracked.uint32(0),
    numberOfThreads = cms.untracked.uint32(1),
    printDependencies = cms.untracked.bool(False),
    sizeOfStackForThreadsInKB = cms.optional.untracked.uint32,
    throwIfIllegalParameter = cms.untracked.bool(True),
    wantSummary = cms.untracked.bool(False)
)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('step3 nevts:-1'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Output definition

process.RECOSIMoutput = cms.OutputModule("PoolOutputModule",
    dataset = cms.untracked.PSet(
        dataTier = cms.untracked.string('GEN-SIM-RECO'),
        filterName = cms.untracked.string('')
    ),
    fileName = cms.untracked.string('file:output.root'),
    outputCommands = cms.untracked.vstring('drop *',
                                           'keep GEMDetIdGEMSegmentsOwnedRangeMap_gemSegments__RECO',
                                           'keep *_gemRecHits_*_*',
                                           'keep *_muonGEMDigis_*_*',
                                           'keep *_tcdsDigis_*_*',
                                           'keep *_onlineMetaDataDigis_*_*',
                                           ),
    # outputCommands = process.RECOSIMEventContent.outputCommands,
    splitLevel = cms.untracked.int32(0)
)

# Additional output definition

# Other statements
from Configuration.AlCa.GlobalTag import GlobalTag
# process.GlobalTag = GlobalTag(process.GlobalTag, '124X_dataRun3_Prompt_v4', '')  # Fill 8220
# process.GlobalTag = GlobalTag(process.GlobalTag, '124X_dataRun3_Prompt_v10', '')  # Fill 8456
# process.GlobalTag = GlobalTag(process.GlobalTag, '130X_dataRun3_Prompt_v3', '')  # Fill 8754
process.GlobalTag = GlobalTag(process.GlobalTag, '140X_dataRun3_Prompt_v2', '')  # Fill 9518, 9701

# NTuplizer
process.load("CommonTools.UtilAlgos.TFileService_cfi")
process.gemBackground = cms.EDAnalyzer('gemBackground',
        muonGEMDigis = cms.InputTag("muonGEMDigis"),
        OHInputLabel = cms.InputTag("muonGEMDigis", "OHStatus"),
        VFATInputLabel = cms.InputTag("muonGEMDigis", "VFATStatus"),
        gemRecHits = cms.InputTag("gemRecHits"),
        onlineMetaDataDigis = cms.InputTag("onlineMetaDataDigis"),
        tcdsRecord = cms.InputTag("tcdsDigis", "tcdsRecord")
        )


# Path and EndPath definitions
process.raw2digi_step = cms.Path(process.muonGEMDigis*process.tcdsDigis*process.onlineMetaDataDigis)
process.reconstruction_step = cms.Path(process.gemLocalReco)
process.ntuplize_step = cms.Path(process.gemBackground)
process.endjob_step = cms.EndPath(process.endOfProcess)
process.RECOSIMoutput_step = cms.EndPath(process.RECOSIMoutput)

# Schedule definition
process.schedule = cms.Schedule(process.raw2digi_step,process.reconstruction_step,process.ntuplize_step,process.endjob_step)# ,process.RECOSIMoutput_step)
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)

# Customisation from command line

#Have logErrorHarvester wait for the same EDProducers to finish as those providing data for the OutputModule
from FWCore.Modules.logErrorHarvester_cff import customiseLogErrorHarvesterUsingOutputCommands
process = customiseLogErrorHarvesterUsingOutputCommands(process)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion
