import uproot
import numpy as np
from glob import glob


def select_hot_strips(dqm_path, run_number=359691, run_era="Run2022E", threshold_ratio=0.001):
    try:
        dqm_file = glob(f"{dqm_path}/DQM_V*_R000{run_number}__ZeroBias__{run_era}-*__DQMIO.root")[0]
        print(f"run {run_number}: Colliding run")
    except:
        dqm_file = glob(f"{dqm_path}/DQM_V*_R000{run_number}__Cosmics__{run_era}-*__DQMIO.root")[0]
        print(f"run {run_number}: Cosmics run")
    print(f"Open {dqm_file}")
    dqm = uproot.open(dqm_file)
    nEvents = dqm[f"DQMData/Run {run_number}/DQM/Run summary/TimerService/event allocated"].to_pyroot().GetEntries()
    threshold = nEvents * threshold_ratio
    digis = dqm[f"DQMData/Run {run_number}/GEM/Run summary/Digis"]
    eventInfo = dqm[f"DQMData/Run {run_number}/GEM/Run summary/EventInfo"]
    regions = [-1, 1]
    layers = [1, 2]
    hot_strips = {}
    bad_chambers = {}
    for region in regions:
        region_str = 'M' if region == -1 else 'P'
        for layer in layers:
            gem_label = f"GE11-{region_str}-L{layer}"
            occs = digis[f"occupancy_{gem_label}"]
            inactive_channels = eventInfo[f"inactive_frac_chamber_{gem_label}"]
            bad_chambers[gem_label] = inactive_channels.to_numpy()[0] > 1 / 3
            for chamber in range(1, 37):
                gem_chamber_label = f"{gem_label}-{chamber}"
                LS = "L" if chamber % 2 == 0 else "S"
                chamber = "0" + str(chamber) if chamber < 10 else chamber
                occ_label = f"occ_GE11-{region_str}-{chamber}L{layer}-{LS}"
                occ = occs[occ_label].to_numpy()[0].T  # [ieta, strip]
                hot_in_chamber = np.argwhere((occ > threshold))  # + (occ == 0))
                hot_strips[gem_chamber_label] = {}
                for ieta in range(0, 8):
                    hot_strips[gem_chamber_label][ieta+1] = list(hot_in_chamber[hot_in_chamber[:, 0]==ieta][:,1])
    return hot_strips, bad_chambers


def select_hot_strips_with_analyzed(dqm_path, file_path, run_number=359691, fill=8754, run_era="Run2022E", threshold_ratio=0.001):
    print(f"{dqm_path}/DQM_V*_R000{run_number}__ZeroBias__{run_era}-*__DQMIO.root")
    try:
        dqm_file = glob(f"{dqm_path}/DQM_V*_R000{run_number}__ZeroBias__{run_era}-*__DQMIO.root")[0]
        print(f"run {run_number}: Colliding run")
    except:
        dqm_file = glob(f"{dqm_path}/DQM_V*_R000{run_number}__Cosmics__{run_era}-*__DQMIO.root")[0]
        print(f"run {run_number}: Cosmics run")
    print(f"Open {dqm_file}")
    dqm = uproot.open(dqm_file)
    file_name = f"{file_path}/fill_{fill}/histo_{fill}_{run_number}.root"
    analyzed_file = uproot.open(file_name)
    # nEvents = dqm[f"DQMData/Run {run_number}/DQM/Run summary/TimerService/event allocated"].to_pyroot().GetEntries()
    gem_bkg = analyzed_file#['gemBackground']

    nEvents = len(gem_bkg['rec_hits/event'].array())
    threshold = nEvents * threshold_ratio
    # digis = dqm[f"DQMData/Run {run_number}/GEM/Run summary/Digis"]
    eventInfo = dqm[f"DQMData/Run {run_number}/GEM/Run summary/EventInfo"]
    regions = [-1, 1]
    layers = [1, 2]
    hot_strips = {}
    bad_chambers = {}
    for region in regions:
        region_str = 'M' if region == -1 else 'P'
        for layer in layers:
            gem_label = f"GE11-{region_str}-L{layer}"
            # occs = digis[f"occupancy_{gem_label}"]
            inactive_channels = eventInfo[f"inactive_frac_chamber_{gem_label}"]
            bad_chambers[gem_label] = inactive_channels.to_numpy()[0] > 1 / 3
            for chamber in range(1, 37):
                gem_chamber_label = f"{gem_label}-{chamber}"
                LS = "L" if chamber % 2 == 0 else "S"
                # chamber = "0" + str(chamber) if chamber < 10 else chamber
                occ_label = f"occ_GE11-{region_str}-{chamber}L{layer}-{LS}"
                occ = gem_bkg[occ_label].to_numpy()[0].T  # [ieta, strip]
                hot_in_chamber = np.argwhere((occ > threshold))  # + (occ == 0))
                hot_strips[gem_chamber_label] = {}
                for ieta in range(0, 8):
                    hot_strips[gem_chamber_label][ieta+1] = list(hot_in_chamber[hot_in_chamber[:, 0]==ieta][:,1])
    return hot_strips, bad_chambers


def fit_occ(ieta_strips):
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from scipy.special import factorial
    from scipy.stats import norm

    mu = ieta_strips.mean()
    std = ieta_strips.std()
    # ran = [100, 0, 0.005]
    max_val = int(mu+std)
    ran = [max_val, 0, max_val]
    entries, bin_edges, patches = plt.hist(ieta_strips,
                                           density=True,
                                           bins=ran[0],
                                           range=(ran[1:]),
                                           histtype='step')

    # calculate bin centers
    bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])


    def fit_function(x, mu, std):
        '''poisson function, parameter lamb is the fit parameter'''
        return norm.pdf(x, loc=mu, scale=std)

    # fit with curve_fit
    parameters, cov_matrix = curve_fit(fit_function, bin_centers, entries)
    return parameters


def select_hot_strips_fit(dqm_path, run_number=359691, run_era="Run2022E", threshold_ratio=0.001):
    try:
        dqm_file = glob(f"{dqm_path}/DQM_V*_R000{run_number}__ZeroBias__{run_era}-*__DQMIO.root")[0]
        print(f"run {run_number}: Colliding run")
    except:
        dqm_file = glob(f"{dqm_path}/DQM_V*_R000{run_number}__Cosmics__{run_era}-*__DQMIO.root")[0]
        print(f"run {run_number}: Cosmics run")
    print(f"Open {dqm_file}")
    dqm = uproot.open(dqm_file)
    nEvents = dqm[f"DQMData/Run {run_number}/DQM/Run summary/TimerService/event allocated"].to_pyroot().GetEntries()
    digis = dqm[f"DQMData/Run {run_number}/GEM/Run summary/Digis"]
    eventInfo = dqm[f"DQMData/Run {run_number}/GEM/Run summary/EventInfo"]
    regions = [-1, 1]
    layers = [1, 2]
    hot_strips = {}
    bad_chambers = {}
    ieta_strips = []
    for region in regions:
        region_str = 'M' if region == -1 else 'P'
        for layer in layers:
            gem_label = f"GE11-{region_str}-L{layer}"
            occs = digis[f"occupancy_{gem_label}"]
            for chamber in range(1, 37):
                gem_chamber_label = f"{gem_label}-{chamber}"
                LS = "L" if chamber % 2 == 0 else "S"
                chamber = "0" + str(chamber) if chamber < 10 else chamber
                occ_label = f"occ_GE11-{region_str}-{chamber}L{layer}-{LS}"
                occ = occs[occ_label].to_numpy()[0].T  # [ieta, strip]
                ieta_strips.append(occ)
    ieta_strips = np.array(ieta_strips).reshape(-1)
    ieta_strips = ieta_strips[ieta_strips != 0]
    mu, std = fit_occ(ieta_strips)
    threshold = mu + 3*std
    for region in regions:
        region_str = 'M' if region == -1 else 'P'
        for layer in layers:
            gem_label = f"GE11-{region_str}-L{layer}"
            occs = digis[f"occupancy_{gem_label}"]
            inactive_channels = eventInfo[f"inactive_frac_chamber_{gem_label}"]
            bad_chambers[gem_label] = inactive_channels.to_numpy()[0] > 1 / 3
            for chamber in range(1, 37):
                gem_chamber_label = f"{gem_label}-{chamber}"
                LS = "L" if chamber % 2 == 0 else "S"
                chamber = "0" + str(chamber) if chamber < 10 else chamber
                occ_label = f"occ_GE11-{region_str}-{chamber}L{layer}-{LS}"
                occ = occs[occ_label].to_numpy()[0].T  # [ieta, strip]
                hot_in_chamber = np.argwhere((occ > threshold))  # + (occ == 0))
                hot_strips[gem_chamber_label] = {}
                for ieta in range(0, 8):
                    hot_strips[gem_chamber_label][ieta+1] = list(hot_in_chamber[hot_in_chamber[:, 0]==ieta][:,1])
    return hot_strips, bad_chambers
