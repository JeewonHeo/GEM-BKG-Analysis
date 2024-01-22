import CRABClient
from CRABClient.UserUtilities import config

config = config()
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'step3_RAW2DIGI_RECO.py'

config.Data.inputDBS = 'global'
config.Site.storageSite = 'T3_KR_UOS'
config.Site.whitelist = ['T2_IT_Bari']
config.Data.inputBlocks = ["/ZeroBias/Run2023C-v1/RAW#3812b8b1-8941-484f-b4b7-6e67fc4331fa",
                     "/ZeroBias/Run2023C-v1/RAW#8eaffa39-24bd-489e-a6b2-6c92b7c1892f",
                     "/ZeroBias/Run2023C-v1/RAW#e030016f-a83e-43af-b37a-ae0ec8b5a9a5",

                     "/ZeroBias/Run2023C-v1/RAW#3812b8b1-8941-484f-b4b7-6e67fc4331fa",
                     "/ZeroBias/Run2023C-v1/RAW#e030016f-a83e-43af-b37a-ae0ec8b5a9a5",

                     "/ZeroBias/Run2023C-v1/RAW#3812b8b1-8941-484f-b4b7-6e67fc4331fa",
                     "/ZeroBias/Run2023C-v1/RAW#e030016f-a83e-43af-b37a-ae0ec8b5a9a5",

                     "/ZeroBias/Run2023C-v1/RAW#3812b8b1-8941-484f-b4b7-6e67fc4331fa",
                     "/ZeroBias/Run2023C-v1/RAW#e030016f-a83e-43af-b37a-ae0ec8b5a9a5",
                           ]
# config.Site.storageSite = 'T3_CH_CERNBOX'
# config.Site.outLFNDirBase = '/store/user/jheo/'
# config.Site.outLFNDirBase = 'gsiftp://eosuserftp.cern.ch/eos/user/j/jheo/'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.Data.publication = False
