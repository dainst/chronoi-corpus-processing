#!/bin/bash

language="${1}"
dct="${2}"
input_file="${3}"
output_file="${4}"

heideltime -l "$language" -it -t scientific -dct "$dct" "$input_file" > "$output_file"
