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

# translate the english corpus part
docker exec -it chronoi-pilot ./translate_en_corpus.sh "$dir_input"

# translate corpus part (not fully working, an example for now)
# mkdir -p /srv/output/temponym-translations
# while read -r line; do python3 translate_temponym.py "$line"; done < /srv/output/heideltime_temponym_files/en_repattern.txt > /srv/output/temponym-translations/translate_en_idai_vocab.txt

# prepare an output directory for the annotated files
docker exec heideltime mkdir -p "$folder_annotated"

# check whether an annotated file exists and if it doesn't, create one using
# the heideltime container
annotate() {
    input_file="$1"
    lang_short="$2"
    language="$3"
    annotated_file="${folder_annotated}/${lang_short}/$(basename -stxt $input_file)xml"
    docker exec heideltime mkdir -p $(dirname "$annotated_file")
    if ! $(docker exec heideltime test -f "$annotated_file"); then
        echo "Annotating (${language}): ${input_file}"
        docker exec heideltime /srv/app/scripts/temponym_annotate.sh "$language" 1970-01-01 "$input_file" "$annotated_file"
    else
        echo "Annotation already present: ${annotated_file}"
    fi
}

# process english input files
for file in $(docker exec heideltime find "${dir_input}/en" -type f)
do
    annotate "$file" "en" "english"
done

# process german input files
for file in $(docker exec heideltime find "${dir_input}/de" -type f)
do
    annotate "$file" "de" "german"
done

# output some basic statistics
docker exec -it chronoi-pilot ./stats_basic.sh

# copy the annotated folder for manual annotation and copy the dtd in
docker exec chronoi-pilot mkdir -p "$folder_manual_correction"
docker exec chronoi-pilot cp -a "${folder_annotated}/." "${folder_manual_correction}/"
docker exec chronoi-pilot cp resources/TimeML.dtd "$folder_manual_correction"

# make this script's user to the owner of all resources produced here
docker exec chronoi-pilot chown -R "${UID}:${UID}" /srv/output
