#!/bin/bash

# Usage: run_good_bad_filter.sh <filename>

filename=$1


 
# bazel sync
# bazel test //src/main/spacex/RF/ATS/spacex Measurement_8979797989.sp2
# gsutil -m mv -r Measurement_8979797989.sp2 gs://spacex/





python3 spacex_2.py  $filename  | tee ${filename}_debug.txt

gsutil -m cp -r ${filename}*  gs://spacex_mq/

