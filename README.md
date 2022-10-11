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
```console
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

