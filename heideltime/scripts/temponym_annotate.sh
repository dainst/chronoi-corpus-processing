#!/bin/bash

# Call heideltime with the given parameters. This is mainly a help
# to start annotation within the Docker container without having
# to redirect output back to the host via '>'.

language="${1}"
dct="${2}"
text_type="${3}"
input_file="${4}"
output_file="${5}"

set -x
heideltime -l "$language" -t "$text_type" -dct "$dct" "$input_file" > "$output_file"
