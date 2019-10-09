#!/bin/bash

dir_bronze="/srv/output/A02_manual_correction/"
dir_system="/srv/output/A01_annotated"
dir_eval=/srv/output/A03_test_evaluation

# Prepare the xml files from A01 for evaluation.
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py "${dir_bronze}/en/*_DONE.xml" "${dir_eval}/bronze"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py "${dir_system}/en/*.xml" "${dir_eval}/system"

# Remove the file that is not present as an annotation correction
docker exec -it chronoi-pilot rm "${dir_eval}/system/09_Bermann1997.xml"

# Do the evaluation truncating unneccessary output with grep.
docker exec tempeval3 python TE3-evaluation.py "${dir_eval}/bronze" "${dir_eval}/system" 0.5 | grep -v "\.\.\.$"

# Prepare for and run our own evaluation to compare it with the tempeval3
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${dir_bronze}/en/*_DONE.xml" "${dir_eval}/bronze2"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${dir_system}/en/*.xml" "${dir_eval}/system2"
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py "${dir_eval}/bronze2" "${dir_eval}/system2"

# chown all files created here to the scripts user.
source "$(dirname $0)/util.sh"
correct_output_files_ownership
