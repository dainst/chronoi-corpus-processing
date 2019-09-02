#!/bin/bash

# This script orchestrates all steps taken to produce the corpus results
# in the docker containers setup for the pilot corpus.
# To use this:
#    1. Create an input directory with pdf files
#    2. Create an empty output directory
#    3. Give both path in your .env (copy .env.example)
#    4. Start the containers with docker-compose up
#
#    NOTE: Some manual steps are expected during preprocessing. 

# Preprocess the pdf files
docker exec -it chronoi-pilot python3 preprocessing.py

# create temponym files for heideltime and tell heideltime to recompile itself
docker exec -it chronoi-pilot python3 chronontology_export.py

# rebuild the heideltime jar if any of the temponym files changed
docker exec -it heideltime /srv/app/scripts/build_with_temponyms.sh /srv/output/heideltime_temponym_files

# prepare an output directory for the annotated files
annotated_folder=/srv/output/00X_annotated
docker exec heideltime mkdir -p /srv/output/00X_annotated

# check whether an annotated file exists and if it doesn't, create one using
# the heideltime container
annotate() {
    input_file="$1"
    lang_short="$2"
    language="$3"
    annotated_file="${annotated_folder}/${lang_short}/$(basename -stxt $input_file)xml"
    docker exec heideltime mkdir -p $(dirname "$annotated_file")
    if ! $(docker exec heideltime test -f "$annotated_file"); then
        docker exec heideltime /srv/app/scripts/temponym_annotate.sh "$language" 1970-01-01 "$input_file" "$annotated_file"
    else
        echo "Annotation already present: ${annotated_file}"
    fi
}

# process english input files
for file in $(docker exec heideltime find /srv/output/005_separate_by_language/en -type f)
do
    annotate "$file" "en" "english"
done

# process german input files
for file in $(docker exec heideltime find /srv/output/005_separate_by_language/de -type f)
do
    annotate "$file" "de" "german"
done

# output some basic statistics
docker exec -it chronoi-pilot ./stats_basic.sh
