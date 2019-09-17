#!/bin/bash

# read the relevant directories from the command line
dir_temponym_files="${1}"
dir_heideltime_app=/srv/app/heideltime
config_file=/srv/app/config.props

# a checksum file will be put in the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
checksum_path="${DIR}/.temponym-files-checksum"

# replace pipe chars in the automatically created patterns as they confuse heideltime
sed -i 's/\s*|//g' "$1"/*auto*

# check if the checksum changed since this was last executed
if md5sum --check "$checksum_path" --status
then
    echo "No changed files. Not rebuilding Heideltime."
    exit 0
fi

echo "Files changed. Rebuilding Heideltime."

# Fail before the new checksum is written if anything goes wrong here from here on
set -e

# copy the temponym resource files
cp_resource() {
    cp "${1}" "${dir_heideltime_app}/resources/${2}/${3}/resources_${3}_${4}TemponymChronontology.txt"
}

# copy the primary resource files extracted from chronontology
cp_resource "${dir_temponym_files}/de_repattern.txt" "german"  "repattern" "re"
cp_resource "${dir_temponym_files}/en_repattern.txt" "english" "repattern" "re"
cp_resource "${dir_temponym_files}/de_norm.txt" "german"  "normalization" "norm"
cp_resource "${dir_temponym_files}/en_norm.txt" "english" "normalization" "norm"

# copy the resource files that were automatically translated from the chronontology export
cp_resource "${dir_temponym_files}/es_auto_repattern.txt" "spanish" "repattern" "re"
cp_resource "${dir_temponym_files}/fr_auto_repattern.txt" "french"  "repattern" "re"
cp_resource "${dir_temponym_files}/it_auto_repattern.txt" "italian" "repattern" "re"
cp_resource "${dir_temponym_files}/es_auto_norm.txt" "spanish" "normalization" "norm"
cp_resource "${dir_temponym_files}/fr_auto_norm.txt" "french"  "normalization" "norm"
cp_resource "${dir_temponym_files}/it_auto_norm.txt" "italian" "normalization" "norm"

# put temponym rules into place (same rule for both languages)
write_rule_if_not_exists() {
    local rule='RULENAME="temponym_chronontology_1",EXTRACTION="%reTemponymChronontology",NORM_VALUE="%normTemponymChronontology(group(1))"'
    local file=${1}
    grep -q "temponym_chronontology_1" "$file" || echo "$rule" >> "$file"
}

# write rules to include the temponym files for the chronontology export
write_rule_if_not_exists "${dir_heideltime_app}/resources/english/rules/resources_rules_temponymrules.txt"
write_rule_if_not_exists "${dir_heideltime_app}/resources/german/rules/resources_rules_temponymrules.txt"

# write rules to include the temponym files automatically translated from the chronontology export
write_rule_if_not_exists "${dir_heideltime_app}/resources/spanish/rules/resources_rules_temponymrules.txt"
write_rule_if_not_exists "${dir_heideltime_app}/resources/french/rules/resources_rules_temponymrules.txt"
write_rule_if_not_exists "${dir_heideltime_app}/resources/italian/rules/resources_rules_temponymrules.txt"

# run the maven build
mvn -f "${dir_heideltime_app}/pom.xml" clean package

# enable temponyms in the config
sed -i 's|^considerTemponym =.*$|considerTemponym = true|g' "$config_file"

# create a new checksum
md5sum "$dir_temponym_files"/*.txt > "$checksum_path"
