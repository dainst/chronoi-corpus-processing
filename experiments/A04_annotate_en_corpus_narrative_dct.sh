#!/usr/bin/env bash

# Require the shared functions used in multiple experiments.
source "$(dirname $0)/util.sh"

#input direcories
dir_input="/srv/output/042_separate_by_language/en"
dir_standard="/srv/output/A02_manual_correction/en"

# output directories
dir_annotations="/srv/output/A04_annotated_narrative"
dir_eval="/srv/output/A05_annotated_narrative_eval"

# rebuild the temponyms and heideltime jar if any of the temponym files changed
# docker exec -it chronoi-pilot python3 heideltime/chronontology_temponyms_export.py
docker exec -it heideltime /srv/app/scripts/build_with_temponyms.sh /srv/output/heideltime_temponym_files

# Run the annotations.
annotate "${dir_input}/02_Smith2018.txt"                 "en" "english" 2018-01-01 "narrative" "$dir_annotations"
annotate "${dir_input}/03_Veenhof2018.txt"               "en" "english" 2017-01-01 "narrative" "$dir_annotations"
annotate "${dir_input}/04_Pearce1982.txt"                "en" "english" 1982-06-01 "narrative" "$dir_annotations"
annotate "${dir_input}/05_Pickering1989.txt"             "en" "english" 1989-06-01 "narrative" "$dir_annotations"
annotate "${dir_input}/06_Johnson1977.txt"               "en" "english" 1977-07-01 "narrative" "$dir_annotations"
annotate "${dir_input}/07_HallETAL2004.txt"              "en" "english" 2006-01-01 "narrative" "$dir_annotations"
annotate "${dir_input}/17_AIA-News-107-Winter-1998.txt"  "en" "english" 1998-11-01 "narrative" "$dir_annotations"
annotate "${dir_input}/18_AIA-News-136-Spring-2006A.txt" "en" "english" 2006-04-01 "narrative" "$dir_annotations"

# Prepare the xml files for evaluation.
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct --keep-attr "literature-time" "${dir_standard}/*_DONE.xml" "${dir_eval}/bronze"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${dir_annotations}/en/*.xml" "${dir_eval}/system"

# Evaluate and print some basic information
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py "${dir_eval}/bronze" "${dir_eval}/system"

# Redo the evaluation, collecting detailed information in a csv file
eval_csv="${dir_eval}/eval.csv"
docker exec -i chronoi-pilot bash -c "postprocessing/evaluate_line_by_line.py --print_results_csv ${dir_eval}/bronze ${dir_eval}/system > ${eval_csv}"

# print the text occurences with context for some of the different evaluation decisions
docker exec -it chronoi-pilot bash postprocessing/describe_eval_decisions.sh "$eval_csv"

# Redo the evaluation again, but this this time only for or without literature references
echo "LITERATURE REFERENCES"
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --only_with_attr="literature-time:true" "${dir_eval}/bronze" "${dir_eval}/system"
echo "NO LITERATURE REFERENCES"
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --disregard_with_attr="literature-time:true" "${dir_eval}/bronze" "${dir_eval}/system"

# print distribution plots for the tokens found in the texts
plots_folder="${dir_eval}/distribution-timex"
plots_folder_lit="${dir_eval}/distribution-timex-lit"
plots_folder_nonlit="${dir_eval}/distribution-timex-nonlit"

num_bins=10
docker exec -it chronoi-pilot bash postprocessing/plot_distributions.sh "$dir_annotations" "$eval_csv" "$num_bins" "$plots_folder"

num_bins=5
docker exec -it chronoi-pilot bash postprocessing/plot_distributions.sh "$dir_annotations" "$eval_csv" "$num_bins" "$plots_folder_lit" "tag1_attr_literature_time = True"
docker exec -it chronoi-pilot bash postprocessing/plot_distributions.sh "$dir_annotations" "$eval_csv" "$num_bins" "$plots_folder_nonlit" "tag1_attr_literature_time is null"


# Prepare the xml files again, but this time for the temponym evaluation
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct --only-temponyms --keep-attr "literature-time" "${dir_standard}/*_DONE.xml" "${dir_eval}/bronze-temponyms"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct --only-temponyms "${dir_annotations}/en/*.xml" "${dir_eval}/system-temponyms"

# Evaluate the temponyms
echo "TEMPONYM PERFORMANCE"
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py "${dir_eval}/bronze-temponyms" "${dir_eval}/system-temponyms"

# Evaluate the temponyms again, record decisions and print the distribution plots
eval_temponyms_csv="${dir_eval}/eval_temponyms.csv"
docker exec -i chronoi-pilot bash -c "postprocessing/evaluate_line_by_line.py --print_results_csv ${dir_eval}/bronze-temponyms ${dir_eval}/system-temponyms > ${eval_temponyms_csv}"
docker exec -it chronoi-pilot bash postprocessing/plot_distributions.sh "$dir_annotations" "$eval_temponyms_csv" 10 "${dir_eval}/distribution-temponyms"

# chown all files created here to the scripts user.
correct_output_files_ownership
