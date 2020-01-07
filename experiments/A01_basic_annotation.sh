#!/usr/bin/env bash

# This script orchestrates all steps taken to produce the corpus results
# in the docker containers setup for the pilot corpus.
# To use this:
#    1. Create an input directory with pdf files
#    2. Create an empty output directory
#    3. Give both path in your .env (copy .env.example)
#    4. Start the containers with docker-compose up
#
#    NOTE: Some manual steps are expected during preprocessing. 

# make the utility funcitons available
source "$(dirname $0)/util.sh"

# These are the source and target folders
folder_annotated="/srv/output/A01_annotated"
folder_manual_correction="/srv/output/A02_manual_correction"
dir_input="/srv/output/042_separate_by_language"

# Preprocess the pdf files
docker exec -it chronoi-pilot python3 preprocessing.py

# create temponym files for heideltime
docker exec -it chronoi-pilot python3 heideltime/chronontology_temponyms_export.py

# rebuild the heideltime jar if any of the temponym files changed
docker exec -it heideltime /srv/app/scripts/build_with_temponyms.sh /srv/output/heideltime_temponym_files

# prepare an output directory for the annotated files
docker exec heideltime mkdir -p "$folder_annotated"

# annotate english and german input files
find_and_annotate "$dir_input" "en" "english" "1970-01-01" "scientific" "$folder_annotated"
find_and_annotate "$dir_input" "de" "german" "1970-01-01" "scientific" "$folder_annotated"

# annotate the automatically translated files
find_and_annotate "$dir_input" "fr-auto" "french" "1970-01-01" "scientific" "$folder_annotated"
find_and_annotate "$dir_input" "it-auto" "italian" "1970-01-01" "scientific" "$folder_annotated"
find_and_annotate "$dir_input" "es-auto" "spanish" "1970-01-01" "scientific" "$folder_annotated"

# output some basic statistics
docker exec -it chronoi-pilot ./postprocessing/stats_basic.sh

# copy the annotated folder for manual annotation and copy the dtd in
# docker exec chronoi-pilot mkdir -p "$folder_manual_correction"
# docker exec chronoi-pilot cp -a "${folder_annotated}/." "${folder_manual_correction}/"
# docker exec chronoi-pilot cp resources/TimeML.dtd "$folder_manual_correction"

correct_output_files_ownership
