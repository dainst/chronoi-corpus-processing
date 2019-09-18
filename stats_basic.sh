#!/bin/bash

text_dir=/srv/output/A01_annotated

for lang_dir in en de fr-auto it-auto es-auto
do
    lang_dir_path="${text_dir}/${lang_dir}"

    echo "Temponyms per file, ${lang_dir}:"
    grep -Iric 'type="TEMPONYM"' "$lang_dir_path"

    echo "Temponym counts, ${lang_dir}:"
    grep -Inrio 'type="TEMPONYM"[^>]*[^<]*' "$lang_dir_path" | grep -o '[^>]*$' | sort | uniq -c | sort -nr
done

for lang_dir in en de fr-auto it-auto es-auto
do
    lang_dir_path="${text_dir}/${lang_dir}"

    total_count=$(grep -Iri 'type="TEMPONYM"' "$lang_dir_path" | wc -l)
    unique_count=$(grep -Inrio 'type="TEMPONYM"[^>]*[^<]*' "$lang_dir_path" | grep -o '[^>]*$' | sort | uniq | wc -l)

    echo "${lang_dir}: ${total_count} total, ${unique_count} unique"
done
