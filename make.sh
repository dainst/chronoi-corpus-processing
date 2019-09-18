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

# These are the source and target folders
folder_annotated="/srv/output/A01_annotated"
folder_manual_correction="/srv/output/A02_manual_correction"
dir_input="/srv/output/006_separate_by_language"

# Preprocess the pdf files
docker exec -it chronoi-pilot python3 preprocessing.py

# create temponym files for heideltime and tell heideltime to recompile itself
docker exec -it chronoi-pilot python3 chronontology_export.py

# rebuild the heideltime jar if any of the temponym files changed
docker exec -it heideltime /srv/app/scripts/build_with_temponyms.sh /srv/output/heideltime_temponym_files

# prepare an output directory for the annotated files
docker exec heideltime mkdir -p "$folder_annotated"

# check whether an annotated file exists and if it doesn't, create one using
# the heideltime container
annotate() {
    local input_file="$1"
    local dir_language="$2"
    local language="$3"
    local annotated_file="${folder_annotated}/${dir_language}/$(basename -stxt $input_file)xml"
    docker exec heideltime mkdir -p $(dirname "$annotated_file")
    if ! $(docker exec heideltime test -f "$annotated_file"); then
        echo "Annotating (${language}): ${input_file}"
        docker exec heideltime /srv/app/scripts/temponym_annotate.sh "$language" 1970-01-01 "$input_file" "$annotated_file"
    else
        echo "Annotation already present: ${annotated_file}"
    fi
}

# find all files in the directory $1/$2 and hand them to the
# annotate() function together with the language code
find_and_annotate() {
    local dir_input="$1"
    local dir_language="$2"
    local language_name="$3"
    for file in $(docker exec heideltime find "${dir_input}/${dir_language}" -type f)
    do
        annotate "$file" "$dir_language" "$language_name"
    done
}

# annotate english and german input files
find_and_annotate "$dir_input" "en" "english"
find_and_annotate "$dir_input" "de" "german"

# annotate the automatically translated files
find_and_annotate "$dir_input" "fr-auto" "french"
find_and_annotate "$dir_input" "it-auto" "italian"
find_and_annotate "$dir_input" "es-auto" "spanish"

# output some basic statistics
docker exec -it chronoi-pilot ./stats_basic.sh

# copy the annotated folder for manual annotation and copy the dtd in
# docker exec chronoi-pilot mkdir -p "$folder_manual_correction"
# docker exec chronoi-pilot cp -a "${folder_annotated}/." "${folder_manual_correction}/"
# docker exec chronoi-pilot cp resources/TimeML.dtd "$folder_manual_correction"

# make this script's user to the owner of all resources produced here
docker exec chronoi-pilot chown -R "${UID}:${UID}" /srv/output
