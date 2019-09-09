#!/bin/bash

# Call heideltime with the given parameters. This is mainly a help
# to start annotation within the Docker container without having
# to redirect output back to the host via '>'.

language="${1}"
dct="${2}"
input_file="${3}"
output_file="${4}"

heideltime -l "$language" -it -t scientific -dct "$dct" "$input_file" > "$output_file"
