import os

run_eras = {
        8149: "Run2022D",
        8220: "Run2022E",
        8221: "Run2022E",
        8456: "Run2022G",
        8754: "Run2023C",
        9518: "Run2024C",
        9523: "Run2024C",
        9701: "Run2024E",
        10190: "Run2024I",
        10226: "Run2024I",
        }

runs = {
        8149: [357802, 357803, 357804, 357805, 357806, 357807, 357808, 357809, 357812, 357813, 357814, 357815],
        8220: [359691, 359693, 359694],
        8456: [362433, 362435, 362437, 362438, 362439],
        8754: [367406, 367413, 367415, 367416],
        9518: [379420],
        9523: [379454, 379456],
        9701: [381484],
        10190: [386505, 386508, 386509],
        10226: [386924. 396925],
        }

cosmic_runs = {
        8456: [362440],
        8221: [359697],
        8754: [367417],
        }

colliding = True
lumimask_path = "https://cms-service-dqmdc.web.cern.ch/CAF/certification"
lumimask_dict = {
        "Run2022E": f"{lumimask_path}/Collisions22/Cert_Collisions2022_eraE_359022_360331_Muon.json",
        "Run2022G": f"{lumimask_path}/Collisions22/Cert_Collisions2022_eraG_362433_362760_Muon.json",
        "Run2023C": f"{lumimask_path}/Collisions23/Cert_Collisions2023_eraC_367095_368823_Muon.json",
        }

for fill in run_eras:
    if fill != 9701: continue
    for run_number in runs[fill]:
    # for run_number in cosmic_runs[fill]:  # Cosmics
        run_era = run_eras[fill]
        command = f"crab submit -c crabConfig_background.py "
        command += f"General.requestName={run_era}_{run_number}_30Jun2024_BKG_analysis_wolumimask-v1 "
        if colliding:
            command += f"Data.inputDataset=/ZeroBias/{run_era}-v1/RAW "
        else:
            command += f"Data.inputDataset=/Cosmics/{run_era}-v1/RAW "  # 8456 Cosmics
        command += f"Data.runRange={run_number} "
        command += f"Data.outputDatasetTag={fill}_{run_number}_wolumimask-v1 "
        # command += f"Data.lumiMask='{lumimask_dict[run_era]}'"
        print(command)
        os.system(command)
