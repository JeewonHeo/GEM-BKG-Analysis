# CMSSW_12_4_6
import sys
import ROOT
import uproot
import argparse
import numpy as np
from array import array
ROOT.gROOT.SetBatch(True)


def selectHotStrips(dqm_path, run_number=357696):
    dqm_file = dqm_path + f"DQM_V0001_R000{run_number}__Muon__Run2022D-PromptReco-v1__DQMIO.root"
    dqm = uproot.open(dqm_file)
    digis = dqm[f"DQMData/Run {run_number}/GEM/Run summary/Digis"]
    regions = [-1, 1]
    layers = [1, 2]
    threshold = 2000
    hot_strips = {}
    for region in regions:
        region_str = 'M' if region== -1 else 'P'
        for layer in layers:
            gem_label = f"GE11-{region_str}-L{layer}"
            occs = digis[f"occupancy_{gem_label}"]
            for chamber in range(1,37):
                gem_chamber_label = gem_label + f"-{chamber}"
                LS = "L" if chamber % 2 == 0 else "S"
                chamber = "0" + str(chamber) if chamber < 10 else chamber
                occ_label = f"occ_GE11-{region_str}-{chamber}L{layer}-{LS}"
                occ = occs[occ_label].to_numpy()[0].T  # [ieta, strip]
                hot_in_chamber = np.argwhere(occ > threshold)
                hot_strips[gem_chamber_label] = {}
                for ieta in range(0,8):
                    hot_strips[gem_chamber_label][ieta+1] = list(hot_in_chamber[hot_in_chamber[:, 0]==ieta][:,1])
    return hot_strips

def getHits(data_path, out_path, hot_strips):
    bx = 8
    fill_factor = 2400 / 3564
    eventpersec = 10**9 / (bx * 25)

    dataname = "root://cms-xrd-global.cern.ch//" + data_path
    print(dataname)
    f = ROOT.TFile.Open(dataname)
    event_tree = f.Events
    nEvent = event_tree.GetEntries()
    event_tree.GetEntry(0)
    event_tree.SetBranchStatus("*", 0)
    event_tree.SetBranchStatus("*OnlineLuminosityRecord_onlineMetaDataDigis__RECO.*", 1)
    event_tree.SetBranchStatus("GEMDetIdGEMRecHitsOwnedRangeMap_gemRecHits__RECO.*", 1)
    event_tree.SetBranchStatus("*EventAuxiliary*", 1)
    print(f'{nEvent = }')

    out_path = out_path + '/' + dataname.split('/')[-1]  # out file name is same with data name
    print(out_path)
    outFile = ROOT.TFile.Open(out_path, "RECREATE")
    tree = ROOT.TTree("rec_hits", "gem_rec_hits")
    a_instLumi = array('f', [0])
    a_region = array('i', [0])
    a_layer = array('i', [0])
    a_chamber = array('i', [0])
    a_ieta = array('i', [0])
    a_scale = array('f', [0])
    a_event= array('i', [0])

    tree.Branch("instLumi", a_instLumi, "instLumi/F")
    tree.Branch("region", a_region, "region/I")
    tree.Branch("layer", a_layer, "layer/I")
    tree.Branch("chamber", a_chamber, "chamber/I")
    tree.Branch("ieta", a_ieta, "ieta/I")
    tree.Branch("scale", a_scale, "scale/F")
    tree.Branch("event", a_event, "event/I")

    for i in range(nEvent):
        if i % 500 == 0:
            print(f"[{i} / {nEvent}]")  # to show progress

        event_tree.GetEntry(i)
        event_number = event_tree.EventAuxiliary.event()
        inst_lumi = event_tree.OnlineLuminosityRecord_onlineMetaDataDigis__RECO.instLumi()
        h_instlumi.Fill(inst_lumi / 10000)
        gem_rec_hits = event_tree.GEMDetIdGEMRecHitsOwnedRangeMap_gemRecHits__RECO.product()

        for hit in gem_rec_hits:
            if hit.BunchX() != 0:
                print('bad Bunch')
                continue
            gem_id = hit.gemId()
            if not gem_id.isGE11(): continue
            region = gem_id.region()
            layer = gem_id.layer()
            chamber = gem_id.chamber()
            ieta = gem_id.ieta()
            region_str = 'M' if region== -1 else 'P'
            hit_label = f"GE11-{region_str}-L{layer}-{chamber}"
            first_strip = hit.firstClusterStrip()
            cluster_size = hit.clusterSize()
            hit_cluster = [j for j in range(first_strip, first_strip + cluster_size)]
            include_hot_strip = False
            bad_strips = hot_strips[hit_label][ieta]

            for strip in hit_cluster:
                if strip in bad_strips:
                    include_hot_strip = True
            if include_hot_strip == True: continue
            good_strip_ratio = 1 - len(bad_strips) / 384

            good_eta_part_area = area[ieta][chamber%2] * good_strip_ratio
            scale = fill_factor * eventpersec / good_eta_part_area
            a_instLumi[0] = inst_lumi
            a_region[0] = region
            a_layer[0] = layer
            a_chamber[0] = chamber
            a_scale[0] = scale
            a_ieta[0] = ieta
            a_event[0] = event_number
            tree.Fill()
            if region == 1:
                if layer == 1:
                    h_p_l1.Fill(chamber, ieta, scale)
                elif layer == 2:
                    h_p_l2.Fill(chamber, ieta, scale)
            elif region == -1:
                if layer == 1:
                    h_m_l1.Fill(chamber, ieta, scale)
                elif layer == 2:
                    h_m_l2.Fill(chamber, ieta, scale)

    outFile.WriteObject(h_p_l1, "GE11_P_L1")
    outFile.WriteObject(h_p_l2, "GE11_P_L2")
    outFile.WriteObject(h_m_l1, "GE11_M_L1")
    outFile.WriteObject(h_m_l2, "GE11_M_L2")
    outFile.WriteObject(h_instlumi, "instLumi")
    tree.Write()
    del tree
    outFile.Close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='get hits')
    parser.add_argument('--dqm_path', type=str,
            default="/store/user/jwheo/DQMGUI_data/Run2022/Muon_latest/")
    parser.add_argument('--run_number', type=int,
            default=357696)
    parser.add_argument('--data_path', type=str,
            default="/store/data/Run2022D/ZeroBias/AOD/PromptReco-v1/000/357/696/00000/e433b4a1-2014-41ed-a1c0-c564df66b68d.root")
    parser.add_argument('--out_path', type=str,
            default='.')
    args = parser.parse_args()

    hot_strips = selectHotStrips(args.dqm_path, args.run_number)

    xbins = [36, 0.5, 36.5]
    ybins = [8, 0.5, 8.5]
    h_p_l1 = ROOT.TH2D('GE11-P-L1', 'GE11-P-L1;chamber;ieta', *xbins, *ybins)
    h_p_l2 = ROOT.TH2D('GE11-P-L2', 'GE11-P-L2;chamber;ieta', *xbins, *ybins)
    h_m_l1 = ROOT.TH2D('GE11-M-L1', 'GE11-M-L1;chamber;ieta', *xbins, *ybins)
    h_m_l2 = ROOT.TH2D('GE11-M-L2', 'GE11-M-L2;chamber;ieta', *xbins, *ybins)
    h_instlumi = ROOT.TH1F('', 'instLumi;instLumi;nEvent', 20, 0, 2)

    # area[ieta] = [even_chamber_area, odd_chamber_area] --> From gem geometry
    area = {
    1: [829.832, 672.621],
    2: [762.952, 623.335],
    3: [582.477, 487.737],
    4: [536.375, 452.607],
    5: [412.741, 357.334],
    6: [380.546, 331.901],
    7: [294.87, 263.171],
    8: [272.121, 244.628]
    }

    getHits(args.data_path, args.out_path, hot_strips)

