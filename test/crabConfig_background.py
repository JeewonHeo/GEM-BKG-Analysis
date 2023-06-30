import CRABClient
from CRABClient.UserUtilities import config

config = config()
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'step3_RAW2DIGI_RECO.py'

config.Data.inputDBS = 'global'
config.Site.storageSite = 'T3_KR_UOS'
config.Site.outLFNDirBase = '/store/user/jheo/'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.Data.publication = False
