import os

run_eras = {
        8149: "Run2022D",
        8220: "Run2022E",
        8221: "Run2022E",
        8456: "Run2022G",
        8754: "Run2023C",
        }

runs = {
        8149: [357802, 357803, 357804, 357805, 357806, 357807, 357808, 357809, 357812, 357813, 357814, 357815],
        8220: [359691, 359693, 359694],
        8456: [362433, 362435, 362437, 362438, 362439],
        8754: [367406, 367413, 367415, 367416],
        }

cosmic_runs = {
        8456: [362440],
        8221: [359697],
        8754: [367417]
        }

colliding = True

for fill in run_eras:
    if fill != 8754: continue
    for run_number in runs[fill]:
    # for run_number in cosmic_runs[fill]:  # Cosmics
        # if run_number != 367416: continue
        run_era = run_eras[fill]
        command = f"crab submit -c crabConfig_background.py "
        command += f"General.requestName={run_era}_{run_number}_Jul2023_BKG_analysis "
        if colliding:
            command += f"Data.inputDataset=/ZeroBias/{run_era}-v1/RAW "
        else:
            command += f"Data.inputDataset=/Cosmics/{run_era}-v1/RAW "  # 8456 Cosmics
        command += f"Data.runRange={run_number} "
        command += f"Data.outputDatasetTag={fill}_{run_number}-v1 "
        print(command)
        os.system(command)