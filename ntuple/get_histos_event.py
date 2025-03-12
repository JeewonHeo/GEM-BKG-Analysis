import os
import ROOT  # type: ignore
import uproot
import numpy as np
from tqdm import tqdm
from background import select_hot_strips_with_analyzed
ROOT.gROOT.SetBatch(True)


def histos(fill_number):
    h = {}
    labels = r";Instantaneous Luminosity [10^{34}cm^{-2}s^{-1}];Hit rate [ Hz/cm^{2} ]"
    ran = [30, 0, 3]
    ran = [60, 0, 3]
    if fill_number == 8220: ran = [40, 0, 2]
    if fill_number == 9518: ran = [15, 0, 1.5]
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
                    h[f'{region}_{layer}_{chamber}'] = ROOT.TH1F("", labels, *ran)
    return h


def fill(input_file, hot_strips, bad_chambers, h, chamber_events, fill_number):
    f = ROOT.TFile(input_file, "r")
    instLumi = f.instLumi
    n_events = instLumi.GetEntries()
    print(f'{n_events = }')
    tree = f.rec_hits

    nHits = tree.GetEntries()
    for entry in tqdm(tree, total=nHits):
        lumi = entry.instLumi
        if fill_number == 8220:
            if lumi < 6000 or lumi > 16000: continue  
        elif fill_number == 8456:
            if (lumi < 11000 or lumi > 19000) and (lumi < 21000 or lumi > 26000): continue  
        elif fill_number == 8754:
            if lumi < 9000 or lumi > 21000: continue  
        elif fill_number == 9518:
            if lumi < 1000 or lumi > 11000: continue  
        elif fill_number == 9523:
            if lumi < 1000 or lumi > 12000: continue  
        elif fill_number == 9573:
            if lumi < 10000 or lumi > 21000: continue  
        elif fill_number == 9696:
            if lumi < 12000 or lumi > 21000: continue  
        elif fill_number == 9701:
            if lumi < 16000 or lumi > 22000: continue  
        elif fill_number == 9877:
            if lumi < 10000 or lumi > 21000: continue  
        elif fill_number == 9606:
            if lumi < 10000 or lumi > 21000: continue  
        elif fill_number == 10190:
            if lumi < 14000 or lumi > 21000: continue  
        elif fill_number == 10226:
            if lumi < 14000 or lumi > 21000: continue  
        else: 
            print('no info.')
            print(f"{fill_number = }")
            exit()
        vec_lst = [entry.region, entry.layer, entry.chamber, entry.scale,
                   entry.scale_chamber, entry.ieta]
        for vec in zip(*vec_lst):
            region, layer, chamber, scale, scale_chamber, ieta = vec
            region_str = 'M' if region == -1 else 'P'
            gem_label = f"GE11-{region_str}-L{layer}"
            scale = scale / (chamber_events[f"{region_str}_L{layer}"][chamber-1][int(lumi//500)])  # if good_strip_ratio != 0 else 0 # 17699 -> 17
            scale_chamber = scale_chamber / (chamber_events[f"{region_str}_L{layer}"][chamber-1][int(lumi//500)])  # if good_strip_ratio != 0 else 0 # 17699 -> 17
            if bad_chambers[gem_label][chamber-1]: continue
            h[f"{region}_{layer}"].Fill(chamber, ieta, scale)
            h[f'{region}_{layer}_{chamber}'].Fill(lumi / 10000, scale_chamber)
            h[f'{region}_{layer}_{chamber}_{ieta}'].Fill(lumi / 10000, scale)
            if chamber % 2 == 0:
                h[f'{region}_{layer}_{ieta}_even'].Fill(lumi / 10000, scale)
            else:
                h[f'{region}_{layer}_{ieta}_odd'].Fill(lumi / 10000, scale)


def draw(h, bad_chambers, file_path, fill_number):
    if not os.path.isdir(f'{file_path}/lumipng_{fill_number}'):
        os.makedirs(f'{file_path}/lumipng_{fill_number}')

    colors = [ROOT.kBlack, ROOT.kBlue, ROOT.kRed, ROOT.kGreen, ROOT.kOrange,
            ROOT.kViolet, ROOT.kYellow + 2, ROOT.kCyan + 2]
    # out_file = ROOT.TFile.Open(f"{file_path}/histos.root", "RECREATE")
    out_file = ROOT.TFile.Open(f"{file_path}/histos_noeffcut.root", "RECREATE")
    for region in [-1, 1]:
        region_str = 'M' if region == -1 else 'P'
        for layer in [1, 2]:
            h[f'{region}_{layer}'].SetStats(0)
            out_file.WriteObject(h[f'{region}_{layer}'], f'{region_str}_L{layer}')
            for chamber in range(1, 37):
                out_file.WriteObject(h[f"{region}_{layer}_{chamber}"],
                            f"h_{region}_{layer}_{chamber}")
                # leg = ROOT.TLegend(0.2, 0.2, 0.5, 0.5)
                leg = ROOT.TLegend(0.2, 0.55, 0.5, 0.85)
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
                cvs.SaveAs(f"{file_path}/lumipng_{fill_number}/GE11-{region_str}_{layer}_{chamber}.png")
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
    import yaml
    file_path = sys.argv[-2]
    fill_number = int(sys.argv[-1])

    with open("/users/jheo/GEM-BKG-Analysis/analysis/txt/fill_info.yaml") as f:
        fill_info = yaml.load(f, Loader=yaml.CLoader)
    run_lst = fill_info['run_lst'][fill_number]
    run_era = fill_info['run_era'][fill_number]

    lumi_events = np.zeros(30)
    tot_avgLumi = 0
    tot_n = 0
    hot_strips = {}
    bad_chambers = {}
    chamber_events = {f"{re}_L{la}": np.zeros((36, 60)) for re in ["M", "P"] for la in [1, 2]}
    for run in run_lst:
        f = uproot.open(f"{file_path}/out_{run}.root")
        # f = uproot.open(f"test.root")
        instLumi = f['instLumi'].to_numpy()[0]
        for re in ["M", "P"]:
            for la in [1, 2]:
                chamber_events[f"{re}_L{la}"] += instLumi - f[f"bad_chamber_{re}L{la}"].to_numpy()[0]
        # hot_strips[run], bad_chambers[run] = select_hot_strips('/hdfs/user/jheo/dqm/', run_number=run, run_era=run_era)
        # hot_strips[run], bad_chambers[run] = select_hot_strips_with_analyzed('/hdfs/user/jheo/dqm/', '/store/user/jheo/ZeroBias/', run_number=run, fill=fill_number, run_era=run_era)
        hot_strips[run], bad_chambers[run] = select_hot_strips_with_analyzed('/hdfs/user/jheo/dqm/', '/users/jheo/GEM-BKG-Analysis/ntuple/gem_ntuple', run_number=run, fill=fill_number, run_era=run_era)
        # hot_strips, bad_chambers = select_hot_strips_with_analyzed(args.dqm_path, '/users/jheo/GEM-BKG-Analysis/ntuple/gem_ntuple', args.run_number, args.fill, args.run_era)
        print(hot_strips[run])

    low_statistics_run_lst = []
    for key in bad_chambers:
        for layer in bad_chambers[key]:
            print(f"{key}, {layer}, {sum(bad_chambers[key][layer])}")
            if sum(bad_chambers[key][layer]) > 18:
                low_statistics_run_lst.append(key)
                print(f"removed")

    for key in set(low_statistics_run_lst):
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
    if fill_number == 8220:
        bad_chamber["GE11-M-L1"][9] = True
        bad_chamber["GE11-M-L1"][21] = True
        bad_chamber["GE11-P-L1"][25] = True
    elif fill_number == 8456:
        bad_chamber["GE11-M-L1"][0] = True
        bad_chamber["GE11-P-L1"][4] = True
        bad_chamber["GE11-P-L1"][26] = True
        bad_chamber["GE11-P-L1"][30] = True
        bad_chamber["GE11-P-L1"][32] = True
        bad_chamber["GE11-P-L2"][9] = True
        bad_chamber["GE11-P-L2"][26] = True
    elif fill_number == 8754:
        bad_chamber["GE11-M-L1"][11] = True
        bad_chamber["GE11-M-L1"][13] = True
        bad_chamber["GE11-M-L1"][21] = True
        bad_chamber["GE11-M-L2"][17] = True
        bad_chamber["GE11-M-L2"][31] = True
        bad_chamber["GE11-P-L1"][4] = True
        bad_chamber["GE11-P-L1"][25] = True
        bad_chamber["GE11-P-L2"][1] = True
    elif fill_number == 9573:
        bad_chamber["GE11-M-L1"][21] = True
        bad_chamber["GE11-M-L2"][31] = True
        bad_chamber["GE11-P-L1"][4] = True
    elif fill_number == 9606:
        bad_chamber["GE11-M-L1"][21] = True
        bad_chamber["GE11-M-L2"][10] = True
        bad_chamber["GE11-M-L2"][31] = True
        bad_chamber["GE11-P-L1"][4] = True
        bad_chamber["GE11-P-L2"][20] = True
        bad_chamber["GE11-P-L2"][27] = True
    elif fill_number == 9877:
        bad_chamber["GE11-M-L1"][21] = True
        bad_chamber["GE11-M-L2"][0] = True
        bad_chamber["GE11-M-L2"][6] = True
        bad_chamber["GE11-M-L2"][31] = True
        bad_chamber["GE11-P-L2"][27] = True

    effcut_wp = 90
    effcut_wp = 0
    try:
        import json
        
        with open("txt/efficiency.json", "r") as f:
            eff_dict = json.load(f)
        eff_dict = eff_dict[f"Fill_{fill_number}"]
        
        bad_eff_chamber_dict = {}
        for region in ["M", "P"]:
            for layer in [1, 2]:
                eff_key = f"{region}L{layer}"
                save_key = f"GE11-{region}-L{layer}"
                # for i in range(1, 37):
                #     print(eff_dict[eff_key].get(f"{i}"))

                bad_eff_chamber_dict[save_key] = np.array([eff_dict[eff_key][f"{i}"][0] if eff_dict[eff_key].get(f"{i}") is not None else 0
                                              for i in range(1, 37)]) < effcut_wp
                bad_eff_chamber_dict[save_key] = bad_eff_chamber_dict[save_key].astype(int)
    except:
        with open(f"/users/jheo/GEM-BKG-Analysis/analysis/txt/dqm_eff_{fill_number}.yaml", "r") as f:
            eff_dct_run = yaml.load(f, Loader=yaml.CLoader)
        bad_eff_chamber_dict = {}
        for run in run_lst:
            eff_dict = eff_dct_run[run]
            bad_eff_chamber_dict[run] = {}
            for region in ["M", "P"]:
                for layer in [1, 2]:
                    eff_key = f"{region}-L{layer}"
                    save_key = f"GE11-{region}-L{layer}"
                    bad_eff_chamber_dict[run][save_key] = np.array([eff_dict[eff_key][i] for i in range(1, 37)])*100 < effcut_wp
                    bad_eff_chamber_dict[run][save_key] = bad_eff_chamber_dict[run][save_key].astype(int)

        for i in bad_chamber:
            for run in run_lst:
                bad_chamber[i] += bad_eff_chamber_dict[run][i]

    for key in bad_chamber:
        bad_chamber[key] = bad_chamber[key].astype(bool).astype(int)
    print(bad_chamber)
    # print(bad_eff_chamber_dict)
 
    # for i in bad_chamber:
    #     bad_chamber[i] += bad_eff_chamber_dict[i]
    # for key in bad_chamber:
    #     bad_chamber[key] = bad_chamber[key].astype(bool).astype(int)
    # print(bad_chamber)
    # print(bad_eff_chamber_dict)
    # exit()
    
    
   #  avg_eff = {}
   #  for region in ["M", "P"]:
   #      for layer in [1, 2]:
   #          eff_key = f"{region}-L{layer}"
   #          avg_eff[eff_key] = np.zeros(36)

   #  for run in run_lst:
   #      eff_dict = eff_dct_run[run]
   #      for region in ["M", "P"]:
   #          for layer in [1, 2]:
   #              eff_key = f"{region}-L{layer}"
   #              avg_eff[eff_key] += np.array([eff_dict[eff_key][i] for i in range(1, 37)])*100

   #  for region in ["M", "P"]:
   #      for layer in [1, 2]:
   #          eff_key = f"{region}-L{layer}"
   #          avg_eff[eff_key] /= len(run_lst)


   # eff_dict = avg_eff

#
    n_active = 0
    for chamber in ['even', 'odd']:
        for region in [-1, 1]:
            region_str = 'M' if region == -1 else 'P'
            for layer in [1, 2]:
                inactivated_chamber = sum(bad_chamber[f'GE11-{region_str}-L{layer}'][::2]) if chamber == 'odd' else sum(bad_chamber[f'GE11-{region_str}-L{layer}'][1::2])
                activated_chamber = 18 - inactivated_chamber
                print(activated_chamber)
                n_active += activated_chamber
    print(f"{n_active = }")


    for run in run_lst:
        fill(f'{file_path}/out_{run}.root', hot_strips[run], bad_chamber, h, chamber_events, fill_number)
    draw(h, bad_chamber, file_path, f'{fill_number}')

