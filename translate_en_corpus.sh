#!/bin/bash

# Translate some files using mkTranslate
# https://github.com/mythkiven/mkTranslate

corpus_dir=${1}

target_languages="fr es it de"

for input_file in $(find "${corpus_dir}/en" -type f -name "*.txt" ); do
    file_name=$(basename $input_file)
    dir_name=$(dirname $input_file)

    # iterate over each target languag
    for lang in $target_languages; do
        expected_lang_dir="${corpus_dir}/${lang}-auto"
        expected_final_path="${expected_lang_dir}/${file_name}"

        # this is the way that mkTranslation outputs translation files at first
        expected_translation_path="${dir_name}/translate_${lang}_by_google_${file_name}"

        # check if a translation is present or else do it now
        if [ -f $expected_final_path ]; then
            echo "Translation exists at: ${expected_final_path}"
        else
            mkdir -p "$expected_lang_dir"
            translate -c 'google' -d "$lang" -p "$input_file"
            mv "$expected_translation_path" "$expected_final_path"
        fi
    done
done

