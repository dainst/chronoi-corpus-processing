#!/usr/bin/env bash

set -ex

# TODO: Remove and dockerize commands
CHRONOI_HOME=/home/david/Projekte/chronoi

tagged_dir="/srv/output/A06_tagging"

work_dir="/srv/output/A10_ml_tagged"
bronze_dir="${work_dir}/bronze"

docker exec -it chronoi-pilot mkdir -p "$work_dir" "$bronze_dir"

for lang in "fr" "it" "es" "de" "en"
do
  out_dir="${bronze_dir}/${lang}"
  docker exec -it chronoi-pilot mkdir -p "$out_dir"
  
  # prepare input texts to only contain sections of the text in the annotation window
  docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --annotation-window "${tagged_dir}/${lang}/*.xml" "$out_dir"

  # prepare a table of the input texts words enriched with pos-tags
  csv="${CHRONOI_HOME}/pilotkorpus/out/A10_ml_tagged/${lang}.csv"
  $CHRONOI_HOME/pilotkorpus-code/postprocessing/docs_to_sentences_table.py "${CHRONOI_HOME}/pilotkorpus/out/A10_ml_tagged/bronze/${lang}" > "$csv"

  # prepare a table with the literature tags only
  csv="${CHRONOI_HOME}/pilotkorpus/out/A10_ml_tagged/${lang}-lit.csv"
  $CHRONOI_HOME/pilotkorpus-code/postprocessing/docs_to_sentences_table.py --literature "${CHRONOI_HOME}/pilotkorpus/out/A10_ml_tagged/bronze/${lang}" > "$csv"
done

# Remove the "B-" and "I-"prefixes from NER-tags
# for f in en es de fr it; do sed  's/[BI]-\([^,]*$\)/\1/' "$f".csv > "$f"-single-vals.csv ; done

# prepare an english corpus keeping only the "timex3" tags and not restricting the content
# to the <annotation-window/>
out_dir="${bronze_dir}/en-timex"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --a06tagged-no-window "${tagged_dir}/en/*.xml" "$out_dir"
csv="${CHRONOI_HOME}/pilotkorpus/out/A10_ml_tagged/en-timex.csv"
$CHRONOI_HOME/pilotkorpus-code/postprocessing/docs_to_sentences_table.py "${CHRONOI_HOME}/pilotkorpus/out/A10_ml_tagged/bronze/en-timex" > "$csv"

# Example evaluation using the machine learning container
# cp $CHRONOI_HOME/pilotkorpus/out/A10_ml_tagged/*.csv ~/Downloads/entity-annotated-corpus
# docker rm -f testdl && docker run -d --name testdl -v ~/Downloads/entity-annotated-corpus:/srv/data -v ~/Projekte/chronoi/pilotkorpus-code/learning:/scripts chronoi/testdl
# docker exec -it testdl python3 test_ner_ml.py /srv/data/it.csv

