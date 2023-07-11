import ROOT
import numpy as np
from array import array
from tqdm import tqdm
from background import select_hot_strips


def fill_hits(input_file, hits, bad_chambers):
    f = ROOT.TFile.Open(input_file)
    tree = f.rec_hits
    nHits = tree.GetEntries()
    for entry in tqdm(tree, total=nHits):
        if entry.ieta != 8: continue
        # if entry.region != -1: continue
        # if entry.layer != 1: continue
        # if entry.chamber != 21: continue
        region = entry.region
        region_str = 'M' if region == -1 else 'P'
        layer = entry.layer
        gem_label = f"GE11-{region_str}-L{layer}"
        chamber = entry.chamber
        if bad_chambers[gem_label][chamber-1]: continue
        t = entry.eventTime
        event = entry.event
        scale = entry.scale
        try:
            hits['hit'][t].append(scale)
            hits['event'][t].append(event)
        except:
            hits['hit'][t] = [scale]
            hits['event'][t] = [event]
            hits['lumi'][t] = entry.instLumi

    return hits

if __name__ == '__main__':
    import sys
    fill_path = sys.argv[-1]
    bad_chamber_runs = {}
    fill = int(fill_path[-4:])
    run_eras = {
        8149: "Run2022D",
        8220: "Run2022E",
        8456: "Run2022G",
        8754: "Run2023C",
        }

    runs = {
        8149: [357802, 357803, 357804, 357805, 357806, 357807, 357808, 357809, 357812, 357813, 357814, 357815],
        8220: [359691, 359693, 359694],
        # 8456: [362433, 362435, 362437, 362438, 362439, 362440],
        8456: [362433, 362437, 362438, 362439, 362440],
        8754: [367406, 367413, 367415, 367416],
        }


    # runs = [359691, 359693, 359694]
    run_lst = runs[fill]
    for run in run_lst:
        _, bad_chamber_runs[run] = select_hot_strips('/hdfs/user/jheo/dqm/', run_number=run, run_era=run_eras[fill])

    # bad_chamber = {}
    # for region_str in ['M', 'P']:
    #     for layer in [1, 2]:
    #         gem_label = f"GE11-{region_str}-L{layer}"
    #         bad_chamber[gem_label] = sum([bad_chamber_runs[run][gem_label] for run in run_lst])
    # print(f'{" removed chamber ":_^80}')
    # bad_chamber_mult = 0
    # for key in bad_chamber:
    #     print(key, (np.argwhere(bad_chamber[key]>0)+1).reshape(-1))
    #     bad_chamber_mult += sum(np.array(bad_chamber[key]>0).reshape(-1))

    # for key in bad_chamber:
    #     bad_chamber[key] = bad_chamber[key].astype(bool).astype(int)

    # print(f"{bad_chamber = }")
    # print(f"{bad_chamber_mult = }")
    low_statistics_runs = []
    for key in bad_chamber_runs:
        for layer in bad_chamber_runs[key]:
            print(f"{key}, {layer}, {sum(bad_chamber_runs[key][layer])}")
            if sum(bad_chamber_runs[key][layer]) > 18:
                low_statistics_runs.append(key)
                print(f"removed")

    for key in set(low_statistics_runs):
        bad_chamber_runs.pop(key)
     #bad_chamber_runs.pop(362440)


    bad_chamber = {}
    for region_str in ['M', 'P']:
        for layer in [1, 2]:
            gem_label = f"GE11-{region_str}-L{layer}"
            bad_chamber[gem_label] = sum([bad_chamber_runs[run][gem_label] for run in bad_chamber_runs])
    print(f'{" removed chamber ":_^80}')
    for key in bad_chamber:
        print(key, (np.argwhere(bad_chamber[key]>0)+1).reshape(-1))

    for key in bad_chamber:
        bad_chamber[key] = bad_chamber[key].astype(bool).astype(int)
    print(bad_chamber)

    bad_chamber_mult = 0
    for key in bad_chamber:
        print(key, (np.argwhere(bad_chamber[key]>0)+1).reshape(-1))
        bad_chamber_mult += sum(np.array(bad_chamber[key]>0).reshape(-1))
    print(f"{bad_chamber_mult = }")
    hits = {
            "hit": {},
            "lumi": {},
            "event": {},
            }

    # run_lst = [359691, 359693, 359694, 359696, 359697]
    # run_lst = [359697]
    # run_lst = [367406, 367413, 367415, 367416]# , 367417]
    for run in run_lst:
        hits = fill_hits(f'{fill_path}/out_{run}.root', hits, bad_chamber)

    np.save(f'{fill_path}/hit_time_ieta8.npy', hits)

