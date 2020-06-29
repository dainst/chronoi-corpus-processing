#!/bin/bash

# Given a csv file which is a human-corrected temponym translation table
# and a language code (en, fr, it, es, de), this constructs
# heideltime normalization files in our custom format from that table.
# It needs the python package "csvkit".
# The csv file should best be constructed with quoted strings
# To re-generate all necessary pattern and normalization files, you can e.g. do:
#
# mkdir -p /tmp/temponyms
# for lang in de en es fr it; do
#   ./format_resource_files_from_temponym_translations.sh ./resources/temponym_translations.csv $lang > "/tmp/temponyms/${lang}_norm.txt"
#   ./format_resource_files_from_temponym_translations.sh ./resources/temponym_translations.csv $lang -pattern > "/tmp/temponyms/${lang}_repattern.txt"
# done


if ! which csvsql > /dev/null; then
    echo "Please install csvkit, e.g.: pip install csvkit"
    exit
fi

in_file="$1"
lang="$2"
tablename="$(basename -s.csv $in_file)"

condition="
    (
        SUBSTR(${lang}_vote, 1, 1) = 'U'
    ) OR (
        (SUBSTR(${lang}_vote, 1, 1) = '' OR SUBSTR(${lang}_vote, 1, 1) IS NULL)
        AND SUBSTR(vote_general, 1, 1) = 'U'
    )
"

query_pattern="
    SELECT
        ${lang}_name as pattern
    FROM ${tablename}
    WHERE ${condition}
"

query_norm="
    SELECT
        ${lang}_name as pattern,
        printf(
            '[%+05d, %+05d, %+05d, %+05d],[''%s'']',
            earliest_begin, latest_begin, earliest_end, latest_end, link_chronontology
        ) as norm
    FROM ${tablename}
    WHERE ${condition}
"


if [[ $3 == "-pattern" ]]
then
    query="$query_pattern"
    quote_level=0
else
    query="$query_norm"
    quote_level=1
fi

csvsql --query "$query" "$in_file" \
    | csvformat --out-quoting=$quote_level \
    | tail -n +2
