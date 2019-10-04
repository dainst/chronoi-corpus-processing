

# check whether an annotated file exists and if it doesn't, create one using
# the heideltime container with the given variables for language, document
# creation time and an annotated file
annotate() {
    local input_file="$1"
    local dir_language="$2"
    local language="$3"
    local dct="$4"
    local text_type="$5"
    local annotated_file="${folder_annotated}/${dir_language}/$(basename -stxt $input_file)xml"

    docker exec heideltime mkdir -p $(dirname "$annotated_file")
    if ! $(docker exec heideltime test -f "$annotated_file"); then
        docker exec -t heideltime /srv/app/scripts/temponym_annotate.sh "$language" "$dct" "$text_type" "$input_file" "$annotated_file"
    else
        echo "Annotation already present: ${annotated_file}"
    fi
}

# find all files in the directory $1/$2 and hand them to the
# annotate() function together with the language code,
# document creation time and text type
find_and_annotate() {
    local dir_input="$1"
    local dir_language="$2"
    local language_name="$3"
    local dct="$4"
    local text_type="$5"
    
    for file in $(docker exec heideltime find "${dir_input}/${dir_language}" -type f)
    do
        annotate "$file" "$dir_language" "$language_name" "$dct" "$text_type"
    done
}
