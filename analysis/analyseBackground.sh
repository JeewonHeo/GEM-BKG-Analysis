#!/bin/sh
pwd

python3 filter_hits.py --output_path $1 --output_name $2 --run_number $3 --run_era $4 --input_path $5
