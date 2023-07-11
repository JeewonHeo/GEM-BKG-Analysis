import os, sys
from glob import glob


fill = int(sys.argv[-1])
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
        8221: [359697],
        # 8456: [362433, 362435, 362437, 362438, 362439],
        8456: [362433, 362437, 362438, 362439],  # With Lumimask
        8754: [367406, 367413, 367415, 367416],
        }

run_era = run_eras[fill]
runs = runs[fill]

jds = "run_background.jds"
# base_path = "/store/user/jheo/ZeroBias/"
base_path = "/store/scratch/jheo/ZeroBias/"

# fill = 8754
for run_number in runs:
    batch_name = f"Run3_Background_{run_era}_Fill{fill}_{run_number}"
    file_paths = glob(f"{base_path}/{fill}_{run_number}-v1/*/*/histo*.root")
    output_path = f"/pad/jheo/GEM-BKG-Analysis/analysis/results/fill_{fill}/{run_number}"
    # output_path = f"/home/jheo/gem-background/git/jheo/gem-background/cmssw/flower/fill_{fill}/off/{run_number}"
    if not os.path.isdir(output_path) :
        os.makedirs(output_path)
    if not os.path.isdir("results/condor/log") :
        os.makedirs("results/condor/log")
        os.makedirs("results/condor/error")
        os.makedirs("results/condor/output")
    for path in file_paths:
        file_name = path.split('/')[-1]
        condor_command = f'condor_submit {jds} -batch-name "{batch_name}" --append "arguments = {output_path} {file_name} {run_number} {run_era} {path}" -append "log = results/condor/log/{file_name} " -append "output = results/condor/output/{file_name}" -append " error = results/condor/error/{file_name} "'
        os.system(condor_command)
