import os
import ROOT  # type: ignore
import uproot
import argparse
import numpy as np
from tqdm import tqdm
from pathlib import Path
from glob import glob
from background import select_hot_strips
ROOT.gROOT.SetBatch(True)


def histos(fill_number):
    h = {}
    labels = r";Instantaneous Luminosity [10^{34}cm^{-2}s^{-1}];Hit rate [ Hz/cm^{2} ]"
    ran = [30, 0, 3]
    if fill_number == 8220: ran = [20, 0, 2]
    for region in [-1, 1]:
        for layer in [1, 2]:
            h[f"{region}_{layer}"] = ROOT.TH2D(f"GE{region}1-L{layer}",
                    f"GE{region}1-L{layer}",
                    36, 0, 36,
                    8, 1, 9)
            for ieta in range(1, 9):
                h[f'{region}_{layer}_{ieta}_odd'] = ROOT.TH1F("", labels, *ran)
                h[f'{region}_{layer}_{ieta}_even'] = ROOT.TH1F("", labels, *ran)
                for chamber in range(1, 37):
                    h[f'{region}_{layer}_{chamber}_{ieta}'] = ROOT.TH1F("", labels, *ran)
    return h


def fill(input_file, hot_strips, bad_chambers, h, chamber_events):
    f = ROOT.TFile(input_file, "r")
    instLumi = f.instLumi
    nEvents = instLumi.GetEntries()
    print(f'{nEvents = }')
    tree = f.rec_hits

    nHits = tree.GetEntries()
    for entry in tqdm(tree, total=nHits):
        lumi = entry.instLumi
        if lumi < 6000 or lumi > 16000: continue  # Fill 8220
        # if lumi < 9000 or lumi > 21000: continue  # Fill 8754
        region = entry.region
        region_str = 'M' if region == -1 else 'P'
        layer = entry.layer
        gem_label = f"GE11-{region_str}-L{layer}"
        chamber = entry.chamber
        if bad_chambers[gem_label][chamber-1]: continue
        scale = entry.scale
        ieta = entry.ieta
        scale = scale / (chamber_events[f"{region_str}_L{layer}"][chamber-1][int(lumi//1000)])  # if good_strip_ratio != 0 else 0 # 17699 -> 17

        h[f"{region}_{layer}"].Fill(chamber, ieta, scale)
        h[f'{region}_{layer}_{chamber}_{ieta}'].Fill(lumi / 10000, scale)
        if chamber % 2 == 0:
            h[f'{region}_{layer}_{ieta}_even'].Fill(lumi / 10000, scale)
        else:
            h[f'{region}_{layer}_{ieta}_odd'].Fill(lumi / 10000, scale)


def draw(h, bad_chambers, outfile_name, fill_number):
    if not os.path.isdir(f'lumipng_{fill_number}'):
        os.mkdir(f'lumipng_{fill_number}')

    colors = [ROOT.kBlack, ROOT.kBlue, ROOT.kRed, ROOT.kGreen, ROOT.kOrange,
            ROOT.kViolet, ROOT.kYellow + 2, ROOT.kCyan + 2]
    out_file = ROOT.TFile.Open(f"{outfile_name}", "RECREATE")
    for region in [-1, 1]:
        region_str = 'M' if region == -1 else 'P'
        for layer in [1, 2]:
            h[f'{region}_{layer}'].SetStats(0)
            out_file.WriteObject(h[f'{region}_{layer}'], f'{region_str}_L{layer}')
            for chamber in range(1, 37):
                leg = ROOT.TLegend(0.2, 0.2, 0.5, 0.5)
                cvs = ROOT.TCanvas('', '', 1600, 1200)
                h[f'{region}_{layer}_{chamber}_8'].Draw('E1')
                for ieta, c in zip(range(1, 9), colors):
                    h[f'{region}_{layer}_{chamber}_{ieta}'].SetStats(0)
                    leg.AddEntry(h[f'{region}_{layer}_{chamber}_{ieta}'],
                            r'i_{#eta} = '+f'{ieta}','le')
                    h[f'{region}_{layer}_{chamber}_{ieta}'].SetMarkerSize(2)
                    h[f'{region}_{layer}_{chamber}_{ieta}'].SetMarkerStyle(22)
                    h[f'{region}_{layer}_{chamber}_{ieta}'].SetMarkerColor(c)
                    h[f'{region}_{layer}_{chamber}_{ieta}'].SetLineColor(c)
                    h[f'{region}_{layer}_{chamber}_{ieta}'].Draw('sameE1')
                    out_file.WriteObject(h[f"{region}_{layer}_{chamber}_{ieta}"],
                            f"h_{region}_{layer}_{chamber}_{ieta}")
                leg.SetFillStyle(0)
                leg.SetBorderSize(0)
                leg.Draw()
                cvs.SaveAs(f"lumipng_{fill_number}/GE11-{region_str}_{layer}_{chamber}.png")
    for chamber in ['even', 'odd']:
        for region in [-1, 1]:
            region_str = 'M' if region == -1 else 'P'
            for layer in [1, 2]:
                leg = ROOT.TLegend(0.2, 0.55, 0.5, 0.85)
                cvs = ROOT.TCanvas('', '', 1600, 1200)
                h[f'{region}_{layer}_8_{chamber}'].Draw('E1')
                inactivated_chamber = sum(bad_chambers[f'GE11-{region_str}-L{layer}'][::2]) if chamber == 'odd' else sum(bad_chambers[f'GE11-{region_str}-L{layer}'][1::2])
                activated_chamber = 18 - inactivated_chamber
                print(activated_chamber)

                for ieta, c in zip(range(1, 9), colors):
                    h[f'{region}_{layer}_{ieta}_{chamber}'].SetStats(0)
                    leg.AddEntry(h[f'{region}_{layer}_{ieta}_{chamber}'],
                            r'i_{#eta} = '+f'{ieta}','le')
                    h[f'{region}_{layer}_{ieta}_{chamber}'].SetMarkerSize(2)
                    h[f'{region}_{layer}_{ieta}_{chamber}'].SetMarkerStyle(22)
                    h[f'{region}_{layer}_{ieta}_{chamber}'].SetMarkerColor(c)
                    h[f'{region}_{layer}_{ieta}_{chamber}'].SetLineColor(c)
                    h[f'{region}_{layer}_{ieta}_{chamber}'].Scale(1 / activated_chamber)
                    h[f'{region}_{layer}_{ieta}_{chamber}'].Draw('sameE1')
                    out_file.WriteObject(h[f"{region}_{layer}_{ieta}_{chamber}"],
                            f"h_{region}_{layer}_{ieta}_{chamber}")
                leg.SetFillStyle(0)
                leg.SetBorderSize(0)
                leg.Draw()
                # cvs.SaveAs(f"bc_lumipng_{fill_number}/GE11-{region_str}_{layer}_{chamber}.png")
    out_file.Close()

if __name__ == "__main__":
    import sys
    file_path = sys.argv[-1]

    run_eras = {
            8149: "Run2022D",
            8220: "Run2022E",
            8456: "Run2022G",
            8754: "Run2023C",
            }

    runs_list = {
            8149: [357802, 357803, 357804, 357805, 357806, 357807, 357808, 357809, 357812, 357813, 357814, 357815],
            8220: [359691, 359693, 359694],
            8456: [362433, 362435, 362437, 362438, 362439],
            8754: [367406, 367413, 367415, 367416],
            }
    fill_number = int(file_path[-4:])
    run_era = run_eras[fill_number]
    runs = runs_list[fill_number]

    # runs = [359691]# , 359693, 359694]
    lumi_events = np.zeros(30)
    tot_avgLumi = 0
    tot_n = 0
    hot_strips = {}
    bad_chambers = {}
    chamber_events = {f"{re}_L{la}": np.zeros((36, 30)) for re in ["M", "P"] for la in [1, 2]}
    for run in runs:
        f = uproot.open(f"{file_path}/out_{run}.root")
        # f = uproot.open(f"test.root")
        instLumi = f['instLumi'].to_numpy()[0]
        for re in ["M", "P"]:
            for la in [1, 2]:
                chamber_events[f"{re}_L{la}"] += instLumi - f[f"bad_chamber_{re}L{la}"].to_numpy()[0]
        hot_strips[run], bad_chambers[run] = select_hot_strips('/hdfs/user/jheo/dqm/', run_number=run, run_era=run_era)

    low_statistics_runs = []
    for key in bad_chambers:
        for layer in bad_chambers[key]:
            print(f"{key}, {layer}, {sum(bad_chambers[key][layer])}")
            if sum(bad_chambers[key][layer]) > 18:
                low_statistics_runs.append(key)
                print(f"removed")

    for key in set(low_statistics_runs):
        bad_chambers.pop(key)

    for i in chamber_events:
        print(i, chamber_events[i].sum(axis=1))
    h = histos(fill_number)
    bad_chamber = {}
    for region_str in ['M', 'P']:
        for layer in [1, 2]:
            gem_label = f"GE11-{region_str}-L{layer}"
            bad_chamber[gem_label] = sum([bad_chambers[run][gem_label] for run in bad_chambers])
    print(f'{" removed chamber ":_^80}')
    for key in bad_chamber:
        print(key, (np.argwhere(bad_chamber[key]>0)+1).reshape(-1))

    for key in bad_chamber:
        bad_chamber[key] = bad_chamber[key].astype(bool).astype(int)
    # bad_chamber["GE11-P-L1"][4] = True
    print(bad_chamber)


    for chamber in ['even', 'odd']:
        for region in [-1, 1]:
            region_str = 'M' if region == -1 else 'P'
            for layer in [1, 2]:
                inactivated_chamber = sum(bad_chamber[f'GE11-{region_str}-L{layer}'][::2]) if chamber == 'odd' else sum(bad_chamber[f'GE11-{region_str}-L{layer}'][1::2])
                activated_chamber = 18 - inactivated_chamber
                print(activated_chamber)


    for run in runs:
        fill(f'{file_path}/out_{run}.root', hot_strips[run], bad_chamber, h, chamber_events)
    # draw(h, bad_chambers[run], 'histos.root', '8220')
    draw(h, bad_chamber, f'{file_path}/histos.root', f'{fill_number}')

