import os
import uproot
import argparse
import awkward as ak
import numpy as np

input_path = 'out.root'
output_path = 'test.root'
f = uproot.open(input_path)
e = f['Events']

# oh_stat = e.arrays(filter_name="/gemOHStatus/", library="ak")
# rechit = e.arrays(filter_name="/gemRecHit/", library="ak")
# 
# flower_idx = flower_event(e)

digi = e.arrays(filter_name="/gemDigi/", library="ak")#[~flower_idx]
digi_station = ak.flatten(digi.gemDigi_station)
digi_region = ak.flatten(digi.gemDigi_region)
digi_layer = ak.flatten(digi.gemDigi_layer)
digi_chamber = ak.flatten(digi.gemDigi_chamber)
digi_ieta = ak.flatten(digi.gemDigi_roll)
digi_strip = ak.flatten(digi.gemDigi_strip)

with uproot.recreate(output_path) as new_file:
    for region in (-1, 1):
        reg_str = "M" if region==-1 else "P"
        for layer in (1, 2):
            for chamber in range(1, 37):
                ctype = "L" if chamber%2==0 else "S"
                h_name = f"occ_GE11-{reg_str}-{chamber}L{layer}-{ctype}"
                f_ieta = digi_ieta[(digi_station==1)&(digi_region==region)&(digi_layer==layer)&(digi_chamber==chamber)]
                f_strip = digi_strip[(digi_station==1)&(digi_region==region)&(digi_layer==layer)&(digi_chamber==chamber)]
                new_file[h_name] = np.histogram2d(f_strip.to_numpy(), f_ieta.to_numpy(), bins=(np.arange(0, 385), np.arange(1, 10)-0.5))


