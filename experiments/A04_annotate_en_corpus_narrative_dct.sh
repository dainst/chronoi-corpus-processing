#!/usr/bin/env bash

# Require the shared functions used in multiple experiments.
source "$(dirname $0)/util.sh"

dir_input="/srv/output/007_separate_by_language/en"
dir_standard="/srv/output/A02_manual_correction/en"
dir_annotations="/srv/output/A04_annotated_narrative"
dir_eval="/srv/output/A05_annotated_narrative_eval"

# Run the annotations.
annotate "${dir_input}/02_Smith2018.txt"                 "en" "english" 2018-01-01 "narrative" "$dir_annotations"
annotate "${dir_input}/03_Veenhof2018.txt"               "en" "english" 2017-01-01 "narrative" "$dir_annotations"
annotate "${dir_input}/04_Pearce1982.txt"                "en" "english" 1982-06-01 "narrative" "$dir_annotations"
annotate "${dir_input}/05_Pickering1989.txt"             "en" "english" 1989-06-01 "narrative" "$dir_annotations"
annotate "${dir_input}/06_Johnson1977.txt"               "en" "english" 1977-07-01 "narrative" "$dir_annotations"
annotate "${dir_input}/07_HallETAL2004.txt"              "en" "english" 2006-01-01 "narrative" "$dir_annotations"
annotate "${dir_input}/17_AIA-News-107-Winter-1998.txt"  "en" "english" 1998-11-01 "narrative" "$dir_annotations"
annotate "${dir_input}/18_AIA-News-136-Spring-2006A.txt" "en" "english" 2006-04-01 "narrative" "$dir_annotations"

set -x

# Prepare the xml files for evaluation.
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${dir_standard}/*_DONE.xml" "${dir_eval}/bronze"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${dir_annotations}/en/*.xml" "${dir_eval}/system"

# Do the evaluation truncating unneccessary output with grep.
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py "${dir_eval}/bronze" "${dir_eval}/system"

# chown all files created here to the scripts user.
correct_output_files_ownership
