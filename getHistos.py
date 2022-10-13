import os
import ROOT
import uproot
import argparse
import numpy as np
from pathlib import Path
ROOT.gROOT.SetBatch(True)


def selectHotStrips(dqm_path, run_number=357696, threshold=500):
    dqm_file = dqm_path + f"DQM_V0001_R000{run_number}__ZeroBias__Run2022D-PromptReco-v1__DQMIO.root"
    dqm = uproot.open(dqm_file)
    digis = dqm[f"DQMData/Run {run_number}/GEM/Run summary/Digis"]
    regions = [-1, 1]
    layers = [1, 2]
    hot_strips = {}
    for region in regions:
        region_str = 'M' if region== -1 else 'P'
        for layer in layers:
            gem_label = f"GE11-{region_str}-L{layer}"
            occs = digis[f"occupancy_{gem_label}"]
            for chamber in range(1, 37):
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


def histos(each_chamber=False):
    h = {}
    labels = r";Instantaneous Luminosity [10^{34}cm^{-2}s^{-1}];Hit rate [ Hz/cm^{2} ]"
    ran = [20, 0, 2]
    for region in [-1, 1]:
        for layer in [1, 2]:
            for ieta in range(1, 9):
                if each_chamber:
                    for chamber in range(1, 37):
                        h[f'{region}_{layer}_{chamber}_{ieta}'] = ROOT.TH1F("", labels, *ran)
                else:
                    h[f'{region}_{layer}_{ieta}_odd'] = ROOT.TH1F("", labels, *ran)
                    h[f'{region}_{layer}_{ieta}_even'] = ROOT.TH1F("", labels, *ran)
    return h


def draw(input_file, hot_strips, h, outfile_name="histos.root", each_chamber=False):
    f = ROOT.TFile(input_file, "r")
    instLumi = f.instLumi
    events = [instLumi.GetBinContent(i) for i in range(1,21)]
    tree = f.rec_hits

    xbins = [36, 0.5, 36.5]
    ybins = [8, 0.5, 8.5]
    h_p_l1 = ROOT.TH2D('GE11-P-L1', 'GE11-P-L1;chamber;ieta', *xbins, *ybins)
    h_p_l2 = ROOT.TH2D('GE11-P-L2', 'GE11-P-L2;chamber;ieta', *xbins, *ybins)
    h_m_l1 = ROOT.TH2D('GE11-M-L1', 'GE11-M-L1;chamber;ieta', *xbins, *ybins)
    h_m_l2 = ROOT.TH2D('GE11-M-L2', 'GE11-M-L2;chamber;ieta', *xbins, *ybins)
    h_instlumi = ROOT.TH1F('', 'instLumi;instLumi;nEvent', 20, 0, 2)


    nHits = tree.GetEntries()
    count = 0
    per = 0
    for entry in tree:
        if count % (nHits//100) == 0:
            print(per, '%')
            per += 1
        count += 1
        lumi = entry.instLumi
        if lumi < 12000 or lumi > 18000: continue
        region = entry.region
        layer = entry.layer
        chamber = entry.chamber
        scale = entry.scale
        ieta = entry.ieta
        first_strip = entry.first_strip
        cluster_size = entry.cluster_size
        region_str = 'M' if region == -1 else 'P'
        hit_label = f"GE11-{region_str}-L{layer}-{chamber}"
        hit_cluster = [j for j in range(first_strip, first_strip + cluster_size)]
        bad_strips = hot_strips[hit_label][ieta]

        include_hot_strip = False
        for strip in hit_cluster:
            if strip in bad_strips:
                include_hot_strip = True
                break
        if include_hot_strip == True: continue
        good_strip_ratio = 1 - len(bad_strips) / 384
        scale = scale / (good_strip_ratio * events[int(lumi//1000)])  # 17699 -> 17

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

        if each_chamber:
            h[f'{region}_{layer}_{chamber}_{ieta}'].Fill(lumi / 10000, scale)
        else:
            if chamber % 2 == 0:
                h[f'{region}_{layer}_{ieta}_even'].Fill(lumi / 10000, scale)
            else:
                h[f'{region}_{layer}_{ieta}_odd'].Fill(lumi / 10000, scale)


    cvs = ROOT.TCanvas('', '', 1600, 1200)
    for j, h in enumerate([h_p_l1, h_p_l2, h_m_l1, h_m_l2]):
        for i in range(1, 37):
            h.GetXaxis().SetBinLabel(h.GetXaxis().FindBin(i), str(i))
        for i in range(1, 9):
            h.GetYaxis().SetBinLabel(h.GetYaxis().FindBin(i), str(i))
        h.SetStats(0)
        cvs.SetGrid()
        cvs.SetRightMargin(0.11)
        h.Draw('colz')
        cvs.SaveAs(f'tmp{j}.png')


    pass


    if not os.path.isdir(f'lumipng_{threshold}'):
        os.mkdir(f'lumipng_{threshold}')

    if each_chamber:
        for region in [-1, 1]:
            region_str = 'M' if region == -1 else 'P'
            for layer in [1, 2]:
                for chamber in range(1, 37):
                    leg = ROOT.TLegend(0.2, 0.2, 0.5, 0.5)
                    cvs = ROOT.TCanvas('', '', 1600, 1200)
                    h[f'{region}_{layer}_{chamber}_8'].Draw('E1')
                    for ieta, c in zip(range(1, 9), [ROOT.kBlack, ROOT.kBlue, ROOT.kRed, ROOT.kGreen, ROOT.kOrange, ROOT.kViolet, ROOT.kYellow + 2, ROOT.kCyan + 2]):
                        h[f'{region}_{layer}_{chamber}_{ieta}'].SetStats(0)
                        leg.AddEntry(h[f'{region}_{layer}_{chamber}_{ieta}'], r'i_{#eta} = '+f'{ieta}','le')
                        h[f'{region}_{layer}_{chamber}_{ieta}'].SetMarkerSize(2)
                        h[f'{region}_{layer}_{chamber}_{ieta}'].SetMarkerStyle(22)
                        h[f'{region}_{layer}_{chamber}_{ieta}'].SetMarkerColor(c)
                        h[f'{region}_{layer}_{chamber}_{ieta}'].SetLineColor(c)
                        h[f'{region}_{layer}_{chamber}_{ieta}'].Draw('sameE1')
                    leg.SetFillStyle(0)
                    leg.SetBorderSize(0)
                    leg.Draw()
                    cvs.SaveAs(f"lumipng_{threshold}/GE11-{region_str}_{layer}_{chamber}.png")
    else:
        outFile = ROOT.TFile.Open(f"{outfile_name}", "RECREATE")
        for chamber in ['even', 'odd']:
            for region in [-1, 1]:
                region_str = 'M' if region == -1 else 'P'
                for layer in [1, 2]:
                    leg = ROOT.TLegend(0.2, 0.55, 0.5, 0.85)
                    cvs = ROOT.TCanvas('', '', 1600, 1200)
                    h[f'{region}_{layer}_8_{chamber}'].Draw('E1')
                    if region == -1:
                        if layer == 1:
                            activated_chambers = 17 if chamber == 'even' else 17
                        else:
                            activated_chambers = 15 if chamber == 'even' else 17
                    else:
                        if layer == 1:
                            activated_chambers = 17 if chamber == 'even' else 17
                        else:
                            activated_chambers = 17 if chamber == 'even' else 16

                    for ieta, c in zip(range(1, 9), [ROOT.kBlack, ROOT.kBlue, ROOT.kRed, ROOT.kGreen, ROOT.kOrange + 1, ROOT.kViolet, ROOT.kYellow + 3, ROOT.kCyan + 3]):
                        h[f'{region}_{layer}_{ieta}_{chamber}'].SetStats(0)
                        leg.AddEntry(h[f'{region}_{layer}_{ieta}_{chamber}'], r'i_{#eta} = '+f'{ieta}','le')
                        h[f'{region}_{layer}_{ieta}_{chamber}'].SetMarkerSize(2)
                        h[f'{region}_{layer}_{ieta}_{chamber}'].SetMarkerStyle(22)
                        h[f'{region}_{layer}_{ieta}_{chamber}'].SetMarkerColor(c)
                        h[f'{region}_{layer}_{ieta}_{chamber}'].SetLineColor(c)
                        h[f'{region}_{layer}_{ieta}_{chamber}'].Scale(1 / activated_chambers)
                        h[f'{region}_{layer}_{ieta}_{chamber}'].Draw('sameE1')
                        outFile.WriteObject(h[f"{region}_{layer}_{ieta}_{chamber}"], f"h_{region}_{layer}_{ieta}_{chamber}")
                    leg.SetFillStyle(0)
                    leg.SetBorderSize(0)
                    leg.Draw()
                    cvs.SaveAs(f"lumipng_{threshold}/GE11-{region_str}_{layer}_{chamber}.png")
        outFile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='draw histos')
    parser.add_argument('--dqm_path', type=str,
            default="/home/jheo/gem-background/")
    parser.add_argument('--threshold', type=int,
            default=500)
    parser.add_argument('--input_path', type=str,
            default="out/out.root")
    parser.add_argument('--out_path', type=str,
            default='histos.root')
    parser.add_argument('--each_chamber', type=bool,
            default=False)
    args = parser.parse_args()

    hot_strips = selectHotStrips(args.dqm_path, threshold=args.threshold)
    h = histos(each_chamber=args.each_chamber)
    draw(args.input_path, hot_strips, h, outfile_name=args.out_path, each_chamber=args.each_chamber)
