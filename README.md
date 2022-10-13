# GEM Background study

## setting up CMSSW environment & release
```bash
source /cvmfs/cms.cern.ch/cmsset_default.sh

cmsrel CMSSW_12_4_6

cd CMSSW_12_4_6/src

cmsenv

```

## clone & go into the repo
```bash
git clone git@github.com:JeewonHeo/gem-background.git

cd gem-background/
```

## usage
need voms before use 'getHitsFromAOD.py'
```console
$ voms-proxy-init -voms cms

$ python3 getHitsFromAOD.py -h
usage: getHitsFromAOD.py [-h] [--dqm_path DQM_PATH] [--run_number RUN_NUMBER] [--data_path DATA_PATH] [--out_path OUT_PATH]

get hits

optional arguments:
  -h, --help            show this help message and exit
  --dqm_path DQM_PATH
  --run_number RUN_NUMBER
  --data_path DATA_PATH
  --out_path OUT_PATH

$ python3 getHitsFromAOD.py
```

## get lumi vs hitrate from hits
need dqm file
```bash
$ python3 getHistos.py -h
usage: getHistos.py [-h] [--dqm_path DQM_PATH] [--threshold THRESHOLD]
                    [--input_path INPUT_PATH] [--out_path OUT_PATH]
                    [--each_chamber EACH_CHAMBER]

draw histos

optional arguments:
  -h, --help            show this help message and exit
  --dqm_path DQM_PATH
  --threshold THRESHOLD
  --input_path INPUT_PATH
  --out_path OUT_PATH
  --each_chamber EACH_CHAMBER
```
