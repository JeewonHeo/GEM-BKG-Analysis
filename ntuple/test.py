import os
import uproot
import argparse
import awkward as ak
import numpy as np


def flower_event(event_tree, lcut=150, rcut=200):
    l1adiff = event_tree["L1A_L1Adiff"].array()
    is_fe = ak.any(((l1adiff<rcut) & (l1adiff>lcut)), axis=1)
    return is_fe



input_path = 'nano_mu_custom_NANO.root'
output_path = 'output.root'
f = uproot.open(input_path)
e = f['Events']

oh_stat = e.arrays(filter_name="/gemOHStatus/", library="ak")
rechit = e.arrays(filter_name="/gemRecHit/", library="ak")

flower_idx = flower_event(e)

digi = e.arrays(filter_name="/gemDigi/", library="ak")[~flower_idx]
digi_station = ak.flatten(digi.gemDigi_station)
digi_region = ak.flatten(digi.gemDigi_region)
digi_layer = ak.flatten(digi.gemDigi_layer)
digi_chamber = ak.flatten(digi.gemDigi_chamber)
digi_ieta = ak.flatten(digi.gemDigi_roll)
digi_strip = ak.flatten(digi.gemDigi_strip)

save_dict = {}
# Event
save_dict['event'] = e['event'].array()
save_dict['eventTime'] = e['lumi_timestamp'].array()
save_dict['luminosityBlock'] = e['luminosityBlock'].array()
save_dict['instLumi'] = e['lumi_instLumi'].array()
save_dict['bunchId'] = e['bunchCrossing'].array()
save_dict['orbitNumber'] = e['orbitNumber'].array()
save_dict['flower_event'] = ak.Array(flower_idx)

# Hits
save_dict['region'] = e['gemRecHit_region'].array()
save_dict['layer'] = e['gemRecHit_layer'].array()
save_dict['chamber'] = e['gemRecHit_chamber'].array()
save_dict['ieta'] = e['gemRecHit_roll'].array()
save_dict['first_strip'] = e['gemRecHit_firstClusterStrip'].array()
save_dict['cluster_size'] = e['gemRecHit_clusterSize'].array()

# Status digis
save_dict['zsMask'] = oh_stat.gemOHStatus_zsMask
save_dict['vfatMask'] = oh_stat.gemOHStatus_vfatMask
save_dict['missingVFATs'] = oh_stat.gemOHStatus_missingVFATs
save_dict['activeVFATs'] = (oh_stat.gemOHStatus_vfatMask) & (~oh_stat.gemOHStatus_missingVFATs)
activeVFATs = (oh_stat.gemOHStatus_vfatMask) & (~oh_stat.gemOHStatus_missingVFATs)


rechit_activated_vfats = []
for i, (stat, rechit_event) in enumerate(zip(oh_stat, rechit)):
    activated_vfats = (stat.gemOHStatus_vfatMask) & (~stat.gemOHStatus_missingVFATs)
    stat_st = stat.gemOHStatus_station
    stat_re = stat.gemOHStatus_region
    stat_la = stat.gemOHStatus_layer
    stat_ch = stat.gemOHStatus_chamber
    region = rechit_event.gemRecHit_region
    layer = rechit_event.gemRecHit_layer
    chamber = rechit_event.gemRecHit_chamber

    
    event_rechits = []
    for re, la, ch in zip(region, layer, chamber):
        event_rechits.append(activated_vfats[(stat_st==1)&(stat_re==re)&(stat_la==la)&(stat_ch==ch)][0])
    rechit_activated_vfats.append(event_rechits)
# rechit_activated_vfats = ak.Array(rechit_activated_vfats)
save_dict["activatedVFATs"] = ak.Array(rechit_activated_vfats)


with uproot.recreate(output_path) as new_file:
    new_file["rec_hits"] = save_dict 
    for region in (-1, 1):
        reg_str = "M" if region==-1 else "P"
        for layer in (1, 2):
            for chamber in range(1, 37):
                ctype = "L" if chamber%2==0 else "S"
                h_name = f"occ_GE11-{reg_str}-{chamber}L{layer}-{ctype}"
                f_ieta = digi_ieta[(digi_station==1)&(digi_region==region)&(digi_layer==layer)&(digi_chamber==chamber)]
                f_strip = digi_strip[(digi_station==1)&(digi_region==region)&(digi_layer==layer)&(digi_chamber==chamber)]
                new_file[h_name] = np.histogram2d(f_strip.to_numpy(), f_ieta.to_numpy(), bins=(np.arange(0, 385), np.arange(1, 10)-0.5))

