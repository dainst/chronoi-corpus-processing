#!/bin/bash

set -ex

DIR=$(dirname "$0")

input_file="test_lit_extract_input.txt"
pattern_file="test_lit_extract_pattern-file.txt"
extracts_list_file="test_lit_extracts-list.txt"
output_file="test_lit_extract_integrated.xml"

extracts_file="extracts.pickle"
to_timetag_file="patterns_removed.txt"

# Start with a clean slate
for f in "$input_file" "$pattern_file" "$extracts_file" "$extracts_list_file" "$to_timetag_file" "$output_file"; do
  rm -f "/tmp/${f}"
  docker exec chronoi-pilot rm -f "/tmp/${f}"
  docker exec heideltime rm -f "/tmp/${f}"
done

# Extraction of literature expressions should produce the right text
docker cp "${DIR}/${input_file}"   chronoi-pilot:/tmp/
docker cp "${DIR}/${pattern_file}" chronoi-pilot:/tmp/
docker exec -i chronoi-pilot python3 pattern_extract.py extract -f "/tmp/${pattern_file}" "/tmp/${input_file}" "/tmp/${extracts_file}" 1> "/tmp/${to_timetag_file}"
diff "/tmp/${to_timetag_file}" "${DIR}/test_lit_extract_patterns_removed.txt"

# Enumerating the extracts should produce the right output
docker exec -i chronoi-pilot python3 pattern_extract.py enumerate "/tmp/${extracts_file}" 1> "/tmp/${extracts_list_file}"
diff "/tmp/${extracts_list_file}" "${DIR}/${extracts_list_file}"

# Annotate the text file with time expressions
docker cp "/tmp/${to_timetag_file}" "heideltime:/tmp/${to_timetag_file}"
docker exec -i heideltime heideltime -l "english" -dct "2020-01-01" -t "narrative" "/tmp/${to_timetag_file}" 1> "/tmp/annotated.xml"

tail -n+4 "/tmp/annotated.xml" | head -n-3 | sponge "/tmp/annotated.xml"
docker cp "/tmp/annotated.xml" "chronoi-pilot:/tmp/annotated.xml"



# rm /tmp/annotated.xml
docker exec -i chronoi-pilot python3 pattern_extract.py integrate "/tmp/annotated.xml" "/tmp/$extracts_file" 1> "/tmp/${output_file}"







echo "OK: ${0}"
