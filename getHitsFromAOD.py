# CMSSW_12_4_6
import sys
import ROOT
import uproot
import argparse
import numpy as np
from array import array
ROOT.gROOT.SetBatch(True)


def getHits(data_path, out_path): # , hot_strips):
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
    a_first_strip= array('i', [0])
    a_cluster_size= array('i', [0])

    tree.Branch("instLumi", a_instLumi, "instLumi/F")
    tree.Branch("region", a_region, "region/I")
    tree.Branch("layer", a_layer, "layer/I")
    tree.Branch("chamber", a_chamber, "chamber/I")
    tree.Branch("ieta", a_ieta, "ieta/I")
    tree.Branch("scale", a_scale, "scale/F")
    tree.Branch("event", a_event, "event/I")
    tree.Branch("first_strip", a_first_strip, "first_strip/I")
    tree.Branch("cluster_size", a_cluster_size, "cluster_size/I")

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

            good_eta_part_area = area[ieta][chamber%2] # * good_strip_ratio
            scale = fill_factor * eventpersec / good_eta_part_area
            a_instLumi[0] = inst_lumi
            a_region[0] = region
            a_layer[0] = layer
            a_chamber[0] = chamber
            a_scale[0] = scale
            a_ieta[0] = ieta
            a_event[0] = event_number
            a_first_strip[0] = first_strip
            a_cluster_size[0] = cluster_size
            tree.Fill()
            if region == 1:
                if layer == 1:
                    h_p_l1.Fill(chamber, ieta, scale / nEvent)
                elif layer == 2:
                    h_p_l2.Fill(chamber, ieta, scale / nEvent)
            elif region == -1:
                if layer == 1:
                    h_m_l1.Fill(chamber, ieta, scale / nEvent)
                elif layer == 2:
                    h_m_l2.Fill(chamber, ieta, scale / nEvent)

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
    parser.add_argument('--data_path', type=str,
            default="/store/data/Run2022D/ZeroBias/AOD/PromptReco-v1/000/357/696/00000/e433b4a1-2014-41ed-a1c0-c564df66b68d.root")
    parser.add_argument('--out_path', type=str,
            default='.')
    args = parser.parse_args()

    getHits(args.data_path, args.out_path)

