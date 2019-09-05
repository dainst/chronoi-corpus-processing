#!/bin/bash

text_dir=/srv/output/A01_annotated
dir_english="${text_dir}/en"
dir_german="${text_dir}/de"

echo "Temponyms per file, english:"
grep -Iric 'type="TEMPONYM"' "$dir_english"

echo "Temponyms per file, german:"
grep -Iric 'type="TEMPONYM"' "$dir_german"

echo "Temponym counts, english:"
grep -Inrio 'type="TEMPONYM"[^>]*[^<]*' "$dir_english" | grep -o '[^>]*$' | sort | uniq -c | sort -nr

echo "Temponym counts, german:"
grep -Inrio 'type="TEMPONYM"[^>]*[^<]*' "$dir_german" | grep -o '[^>]*$' | sort | uniq -c | sort -nr

total_english=$(grep -Iri 'type="TEMPONYM"' "$dir_english" | wc -l)
total_german=$(grep -Iri 'type="TEMPONYM"' "$dir_german" | wc -l)
unique_english=$(grep -Inrio 'type="TEMPONYM"[^>]*[^<]*' "$dir_english" | grep -o '[^>]*$' | sort | uniq | wc -l)
unique_german=$(grep -Inrio 'type="TEMPONYM"[^>]*[^<]*' "$dir_german" | grep -o '[^>]*$' | sort | uniq | wc -l)
echo "english: ${total_english} total, ${unique_english} unique"
echo "german: ${total_german} total, ${unique_german} unique"
