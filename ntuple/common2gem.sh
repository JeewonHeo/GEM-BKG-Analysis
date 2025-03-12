#!/bin/sh
pwd
hostname

python3 common2gem.py --output_path $1 --output_name $2 --input_path $3
