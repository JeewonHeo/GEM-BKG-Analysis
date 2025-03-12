#!/bin/sh
pwd
hostname

python3 filter_events.py --output_path $1 --output_name $2 --run_number $3 --fill $4 --run_era $5 --input_path $6
