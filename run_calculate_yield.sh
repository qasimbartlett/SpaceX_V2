#!/bin/bash

# When bazel is used:
# bazel sync
# bazel test //src/main/spacex/RF/ATS/spacex 

python3 spacex.py  | tee all_files_debug

# gsutil -m cp -r Measurement* gs://spacex_mq/
# gsutil -m cp -r all_files_debug gs://spacex_mq/

