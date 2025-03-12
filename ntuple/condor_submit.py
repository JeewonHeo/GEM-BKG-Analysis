import os
import yaml
from glob import glob


def submit_fill(fill_number):
    with open("/users/jheo/GEM-BKG-Analysis/analysis/txt/fill_info.yaml") as f:
        fill_info = yaml.load(f, Loader=yaml.CLoader)
    
    run_era = fill_info['run_era'][fill_number]
    run_lst = fill_info['run_lst'][fill_number]
    # print(run_era, run_lst)
    
    jds = "common2gem.jds"
    base_path = "/hdfs/store/user/jheo/ZeroBias/"
    
    for run_number in run_lst:
        batch_name = f"com2gem-ntuple-{run_era}-Fill{fill_number}-Run{run_number}"
        file_paths = glob(f"{base_path}/{fill_number}_{run_number}_muntuple-v1/*/*/*.root")
        output_path = f"/users/jheo/GEM-BKG-Analysis/ntuple/gem_ntuple/fill_{fill_number}/{run_number}"
        if not os.path.isdir(output_path) :
            os.makedirs(output_path)
        if not os.path.isdir("condor/log") :
            os.makedirs("condor/log")
            os.makedirs("condor/error")
            os.makedirs("condor/output")
        for input_path in file_paths:
            file_name = input_path.split('/')[-1]
            condor_command = f'condor_submit {jds} -batch-name "{batch_name}" --append "arguments = {output_path} {file_name} {input_path}" -append "log = condor/log/{file_name} " -append "output = condor/output/{file_name}" -append " error = condor/error/{file_name} "'
            print(condor_command)
            os.system(condor_command)

def submit_filter(fill_number):
    with open("/users/jheo/GEM-BKG-Analysis/analysis/txt/fill_info.yaml") as f:
        fill_info = yaml.load(f, Loader=yaml.CLoader)
    
    run_era = fill_info['run_era'][fill_number]
    run_lst = fill_info['run_lst'][fill_number]
    
    jds = "filter_events.jds"
    base_path = "/users/jheo/GEM-BKG-Analysis/ntuple/gem_ntuple"
    
    for run_number in run_lst:
        batch_name = f"filter_events-{run_era}-Fill{fill_number}-Run{run_number}"
        # file_paths = glob(f"{base_path}/{fill_number}_{run_number}-2024-v2_wlumimask/*/*/histo*.root")
        # file_paths = glob(f"{base_path}/{fill_number}_{run_number}-v1/*/*/histo*.root")
        file_paths = glob(f"{base_path}/fill_{fill_number}/{run_number}/*.root")
        output_path = f"/users/jheo/GEM-BKG-Analysis/ntuple/results/fill_{fill_number}/{run_number}"
        if not os.path.isdir(output_path) :
            os.makedirs(output_path)
        if not os.path.isdir("results/condor/log") :
            os.makedirs("results/condor/log")
            os.makedirs("results/condor/error")
            os.makedirs("results/condor/output")
        for path in file_paths:
            file_name = path.split('/')[-1]
            condor_command = f'condor_submit {jds} -batch-name "{batch_name}" --append "arguments = {output_path} {file_name} {run_number} {fill_number} {run_era} {path}" -append "log = results/condor/log/{file_name} " -append "output = results/condor/output/{file_name}" -append " error = results/condor/error/{file_name} "'
            print(condor_command)
            os.system(condor_command)




if __name__=='__main__':
    # for fill_number in [8220, 8456, 8754, 9606, 9573, 9877, 10190, 10226]:
    for fill_number in [9606]:
        # submit_fill(fill_number)
        submit_filter(fill_number)
