import os
import sys
import ROOT
import uproot
import argparse
import numpy as np
from copy import deepcopy
from array import array
from tqdm import tqdm
from glob import glob
# sys.path.append('/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/backgorund')
from background import select_hot_strips, select_hot_strips_fit, get_on_vfats
ROOT.gROOT.SetBatch(True)

def filter_rechits(file_path, out_path, run_number, hot_strips, bad_chambers, off_bx):
    f = ROOT.TFile.Open(file_path)
    gem_bkg_dir = f.gemBackground
    rec_hits = gem_bkg_dir.rec_hits
    tot_hits = rec_hits.GetEntries()
    out_file = ROOT.TFile.Open(out_path, "RECREATE")
    tree = ROOT.TTree("rec_hits", "gem_rec_hits")
    h_instlumi = ROOT.TH1F("instlumi", "instlumi", 30, 0, 30000)
    h_bxon = ROOT.TH1F("bx_on", "bx_on", 30, 0, 30000)
    h_bxoff = ROOT.TH1F("bx_off", "bx_off", 30, 0, 30000)
    h_bunchcross= ROOT.TH1F("BXID", "BXID", 3600, 0, 3600)
    h_events = gem_bkg_dir.Get("events")
    h_bad_chamber = {
            "PL1": ROOT.TH2D("bad_chamber_PL1", "bad chamber GE1/1-P-L1", 36, 0.5, 36.5, 30, 0, 30000),
            "PL2": ROOT.TH2D("bad_chamber_PL2", "bad chamber GE1/1-P-L2", 36, 0.5, 36.5, 30, 0, 30000),
            "ML1": ROOT.TH2D("bad_chamber_ML1", "bad chamber GE1/1-M-L1", 36, 0.5, 36.5, 30, 0, 30000),
            "ML2": ROOT.TH2D("bad_chamber_ML2", "bad chamber GE1/1-M-L2", 36, 0.5, 36.5, 30, 0, 30000),
            "PL1_on": ROOT.TH2D("bad_chamber_PL1_on", "bad chamber GE1/1-P-L1_on", 36, 0.5, 36.5, 30, 0, 30000),
            "PL2_on": ROOT.TH2D("bad_chamber_PL2_on", "bad chamber GE1/1-P-L2_on", 36, 0.5, 36.5, 30, 0, 30000),
            "ML1_on": ROOT.TH2D("bad_chamber_ML1_on", "bad chamber GE1/1-M-L1_on", 36, 0.5, 36.5, 30, 0, 30000),
            "ML2_on": ROOT.TH2D("bad_chamber_ML2_on", "bad chamber GE1/1-M-L2_on", 36, 0.5, 36.5, 30, 0, 30000),
            "PL1_off": ROOT.TH2D("bad_chamber_PL1_off", "bad chamber GE1/1-P-L1_off", 36, 0.5, 36.5, 30, 0, 30000),
            "PL2_off": ROOT.TH2D("bad_chamber_PL2_off", "bad chamber GE1/1-P-L2_off", 36, 0.5, 36.5, 30, 0, 30000),
            "ML1_off": ROOT.TH2D("bad_chamber_ML1_off", "bad chamber GE1/1-M-L1_off", 36, 0.5, 36.5, 30, 0, 30000),
            "ML2_off": ROOT.TH2D("bad_chamber_ML2_off", "bad chamber GE1/1-M-L2_off", 36, 0.5, 36.5, 30, 0, 30000),
            }

    h_2d = {}
    for re in ['M', "P"]:
        for la in [1, 2]:
            h_2d[f"{re}_L{la}"] = ROOT.TH2D(f"GE{re}/1-L{la}", f"GE{re}1L{la}", 36, 1, 37, 8, 1, 9)

    a_instLumi = array('f', [0])
    a_region = array('i', [0])
    a_layer = array('i', [0])
    a_chamber = array('i', [0])
    a_ieta = array('i', [0])
    a_event= array('l', [0])
    a_event_time= array('l', [0])
    a_bunchId= array('i', [0])
    a_first_strip= array('i', [0])
    a_cluster_size= array('i', [0])
    a_scale = array("f", [0])

    tree.Branch("instLumi", a_instLumi, "instLumi/F")
    tree.Branch("region", a_region, "region/I")
    tree.Branch("layer", a_layer, "layer/I")
    tree.Branch("chamber", a_chamber, "chamber/I")
    tree.Branch("ieta", a_ieta, "ieta/I")
    tree.Branch("event", a_event, "event/I")
    tree.Branch("eventTime", a_event_time, "eventTime/I")
    tree.Branch("bunchId", a_bunchId, "bunchId/I")
    tree.Branch("first_strip", a_first_strip, "first_strip/I")
    tree.Branch("cluster_size", a_cluster_size, "cluster_size/I")
    tree.Branch("scale", a_scale, "scale/F")

    # fill_factor = 2448 / 3564  # 8149, 8220
    # fill_factor = 2450 / 3564  # 8456
    fill_factor = 1  # Don't use in ZeroBias ??
    event_per_sec = 10**9 / (8 * 25)  # 1/ 8bx / 25ns
    area = {
        1: [829.832, 672.621],
        2: [762.952, 623.335],
        3: [582.477, 487.737],
        4: [536.375, 452.607],
        5: [412.741, 357.334],
        6: [380.546, 331.901],
        7: [294.870, 263.171],
        8: [272.121, 244.628]
        }
    event_num = 0
    for hit in tqdm(rec_hits, total=tot_hits):
        flower_event = hit.flower_event
        if flower_event: continue

        big_cluster_event = hit.big_cluster_event
        if big_cluster_event: continue

        chamber_err = hit.chamber_error
        bunch_id = hit.bunchId
        # if bunch_id not in off_bx: continue

        if chamber_err:
            region_str = "M" if hit.region == -1 else "P"
            h_bad_chamber[f"{region_str}L{hit.layer}"].Fill(hit.chamber, hit.instLumi)
            if bunch_id not in off_bx:
                h_bad_chamber[f"{region_str}L{hit.layer}_on"].Fill(hit.chamber, hit.instLumi)
            else:
                h_bad_chamber[f"{region_str}L{hit.layer}_off"].Fill(hit.chamber, hit.instLumi)
            continue

        region = hit.region
        region_str = 'M' if region == -1 else 'P'
        layer = hit.layer
        gem_label = f"GE11-{region_str}-L{layer}"
        chamber = hit.chamber
        # if bad_chambers[gem_label][chamber-1]: continue

        ieta = hit.ieta
        first_strip = hit.first_strip
        cluster_size = hit.cluster_size
        hit_label = f"{gem_label}-{chamber}"
        bad_strips = hot_strips[hit_label][ieta]
        hit_cluster = [digi for digi in range(first_strip, first_strip + cluster_size)]

        include_hot_strip = False
        for digi in hit_cluster:
            if digi in bad_strips:
                include_hot_strip = True
                break
        if include_hot_strip: continue

        on_vfats = get_on_vfats(hit)
        including_nonactivated_ieta = False
        for tmp_ieta in range(1, 9):
            if len(on_vfats[tmp_ieta]) == 0:
                including_nonactivated_ieta = True
                break

        if including_nonactivated_ieta:
            h_bad_chamber[f"{region_str}L{layer}"].Fill(hit.chamber, hit.instLumi)
            continue

        event = hit.event
        inst_lumi = hit.instLumi
        if event_num != event:
            event_num = event
            h_instlumi.Fill(inst_lumi)
            if bunch_id not in off_bx:
                h_bxon.Fill(inst_lumi)
            else:
                h_bxoff.Fill(inst_lumi)
            h_bunchcross.Fill(bunch_id)

        on_strips = [digi for section in on_vfats[ieta] \
                for digi in range(section*128, 128 + section*128)]
        bad_strips = [digi for digi in bad_strips if digi in on_strips]

        good_strip_ratio = 1 - len(bad_strips) / (128 * len(on_vfats[ieta]))

        good_eta_part_area = area[ieta][chamber%2] * good_strip_ratio
        scale = fill_factor * event_per_sec / good_eta_part_area

        h_2d[f"{region_str}_L{layer}"].Fill(chamber, ieta)
        a_instLumi[0] = inst_lumi
        a_region[0] = region
        a_layer[0] = layer
        a_chamber[0] = chamber
        a_ieta[0] = ieta
        a_event[0] = event
        a_event_time[0] = hit.eventTime
        a_bunchId[0] = bunch_id
        a_first_strip[0] = first_strip
        a_cluster_size[0] = cluster_size
        a_scale[0] = scale
        tree.Fill()

    out_file.WriteObject(h_events, "events")
    out_file.WriteObject(h_bad_chamber["PL1"], "bad_chamber_PL1")
    out_file.WriteObject(h_bad_chamber["PL2"], "bad_chamber_PL2")
    out_file.WriteObject(h_bad_chamber["ML1"], "bad_chamber_ML1")
    out_file.WriteObject(h_bad_chamber["ML2"], "bad_chamber_ML2")
    out_file.WriteObject(h_bad_chamber["PL1_on"], "bad_chamber_PL1_on")
    out_file.WriteObject(h_bad_chamber["PL2_on"], "bad_chamber_PL2_on")
    out_file.WriteObject(h_bad_chamber["ML1_on"], "bad_chamber_ML1_on")
    out_file.WriteObject(h_bad_chamber["ML2_on"], "bad_chamber_ML2_on")
    out_file.WriteObject(h_bad_chamber["PL1_off"], "bad_chamber_PL1_off")
    out_file.WriteObject(h_bad_chamber["PL2_off"], "bad_chamber_PL2_off")
    out_file.WriteObject(h_bad_chamber["ML1_off"], "bad_chamber_ML1_off")
    out_file.WriteObject(h_bad_chamber["ML2_off"], "bad_chamber_ML2_off")
    out_file.WriteObject(h_instlumi, "instLumi")
    out_file.WriteObject(h_bxon, "bx_on")
    out_file.WriteObject(h_bxoff, "bx_off")
    out_file.WriteObject(h_bunchcross, "bunchCross")
    for histo in h_2d:
        out_file.WriteObject(h_2d[histo], histo)
    tree.Write()
    del tree
    out_file.Close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='get hits')
    parser.add_argument('--input_path', type=str,
            default="/eos/user/j/jheo/ZeroBias/8754_367416-v1/230705_093329/0000/histo_1.root")
    parser.add_argument('--output_path', type=str,
            default='filtered_hits/')
    parser.add_argument('--output_name', type=str,
            default='test.root')
    parser.add_argument('--dqm_path', type=str,
            default='/hdfs/user/jheo/dqm/')
    parser.add_argument('--run_number', type=int, default=359691)
    parser.add_argument('--run_era', type=str, default="Run2022E")
    args = parser.parse_args()

    with open('/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/bunch/InstLumi_8220_AVG_Lumi_HIGH.txt') as f:
    # with open('/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/bunch/InstLumi_8456_AVG_uncrt.txt') as f:
        lines = f.readlines()
        bxs = [line.split('\t') for line in lines][2:]
        off_bx = [int(bx[0]) for bx in bxs if not float(bx[1])]
    if not os.path.isdir(args.output_path):
        os.makedirs(args.output_path)
    hot_strips, bad_chambers = select_hot_strips(args.dqm_path, args.run_number, args.run_era)
    # hot_strips, bad_chambers = select_hot_strips_fit(args.dqm_path, args.run_number, args.run_era)
    filter_rechits(args.input_path, f"{args.output_path}/{args.output_name}", args.run_number, hot_strips, bad_chambers, off_bx)
