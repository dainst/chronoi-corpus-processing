#!/usr/bin/env bash

# Require the shared functions used in multiple experiments.
# shellcheck source=./util.sh
source "$(dirname "$0")/util.sh"

tagged_dir="/srv/output/A06_tagging"
work_dir="/srv/output/A09_eval_tagged"
input_dir="${work_dir}/input"
bronze_dir="${work_dir}/bronze"
system_dir="${work_dir}/system"
system_no_temponyms_dir="${work_dir}/system_no_temponyms"
system_temponyms_dir="${work_dir}/system_only_temponyms"
bronze_temponyms_dir="${work_dir}/bronze_only_temponyms"

docker exec -it chronoi-pilot mkdir -p "$work_dir" "$input_dir" "$bronze_dir" "$system_dir" "$system_no_temponyms_dir"

# from the annotated corpus texts extract only the necessary timex3-tags, this forms the
# "bronze"-standard
for lang in "fr" "it" "es" "de"
do
  docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --a06tagged "${tagged_dir}/${lang}/*.xml" "$bronze_dir"
done

# remove all xml-tags from the bronze xmls to use the plain text as input for the tagger
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --text-only "${bronze_dir}/*.xml" "$input_dir"

# insert newlines in the bronze directory so that it will match the system output
# docker exec -it chronoi-pilot bash -c "sed -i 's|<TimeML|\n<TimeML|g' ${bronze_dir}/*.xml"
docker exec -it chronoi-pilot bash -c "sed -i 's|<TEXT>\([^\n]\)|<TEXT>\n\1|g' ${bronze_dir}/*.xml"
docker exec -it chronoi-pilot bash -c "sed -i 's|\(.\)</TEXT>|\1\n</TEXT>|g' ${bronze_dir}/*.xml"

# make a single evaluation for each language
french_texts="23_GawlikowskiAsad1997.xml 24_Gsell1952.xml 28_Hatt1967.xml 32_Hari1979.xml 46_Allard2017.xml 47_Malleret1959.xml 48_VerrandVidal2004.xml 49_VandenBerghe1980.xml 50_Flament2012.xml 51_KazanskiPerin1988.xml"
german_texts="01_Funke2019.xml 08_ReindelETAL2017.xml 10_WagnerETAL2018.xml 11_WagnerETAL2017.xml 12_Reinecke2018.xml 14_Gnirs1919.xml 15_Wilhelm1898.xml 16_Heberdey1905.xml 19_Berisha2012.xml 30_Andreae1985.xml"
italian_texts="21_Egloff1996.xml 25_Guidotti1978.xml 27_Mele1881.xml 31_Roccati1969.xml 40_Donadoni1951.xml 41_Ciampoltrini1984.xml 42_AdamoCappuccino2014.xml 43_deVillard1948.xml 44_Furlani1936.xml 45_Cecconi2019.xml"
spanish_texts="22_AlonsoGuardo2019.xml 26_Clemente2003.xml 29_Yubero1998.xml 33_Galan1971.xml 34_Moreno1982.xml 35_RavinesSanchez1968.xml 36_Zamora2003.xml 37_RomanJackson1998.xml 38_Valverde2007.xml 39_CruzETAL2010.xml"

# for fname in $italian_texts
# do
#     docker exec -it chronoi-pilot rm -v "${system_dir}/${fname}"
# done

# do the annotations
# annotate "${input_dir}/01_Funke2019.txt"           "" german  2019-01-01 narrative "$system_dir"
# annotate "${input_dir}/08_ReindelETAL2017.txt"     "" german  2017-01-01 narrative "$system_dir"
# annotate "${input_dir}/10_WagnerETAL2018.txt"      "" german  2018-01-01 narrative "$system_dir"
# annotate "${input_dir}/11_WagnerETAL2017.txt"      "" german  2017-01-01 narrative "$system_dir"
# annotate "${input_dir}/12_Reinecke2018.txt"        "" german  2018-01-01 narrative "$system_dir"
# annotate "${input_dir}/14_Gnirs1919.txt"           "" german  1919-01-01 narrative "$system_dir"
# annotate "${input_dir}/15_Wilhelm1898.txt"         "" german  1898-01-01 narrative "$system_dir"
# annotate "${input_dir}/16_Heberdey1905.txt"        "" german  1905-01-01 narrative "$system_dir"
# annotate "${input_dir}/19_Berisha2012.txt"         "" german  2012-01-01 narrative "$system_dir"
# annotate "${input_dir}/21_Egloff1996.txt"          "" italian 1994-01-01 narrative "$system_dir"
# annotate "${input_dir}/22_AlonsoGuardo2019.txt"    "" spanish 2019-01-01 narrative "$system_dir"
# annotate "${input_dir}/23_GawlikowskiAsad1997.txt" "" french  1997-01-01 narrative "$system_dir"
# annotate "${input_dir}/24_Gsell1952.txt"           "" french  1952-01-01 narrative "$system_dir"
# annotate "${input_dir}/25_Guidotti1978.txt"        "" italian 1978-01-01 narrative "$system_dir"
# annotate "${input_dir}/26_Clemente2003.txt"        "" spanish 2003-01-01 narrative "$system_dir"
# annotate "${input_dir}/27_Mele1881.txt"            "" italian 1881-01-01 narrative "$system_dir"
# annotate "${input_dir}/28_Hatt1967.txt"            "" french  1967-01-01 narrative "$system_dir"
# annotate "${input_dir}/29_Yubero1998.txt"          "" spanish 1998-01-01 narrative "$system_dir"
# annotate "${input_dir}/30_Andreae1985.txt"         "" german  1985-01-01 narrative "$system_dir"
# annotate "${input_dir}/31_Roccati1969.txt"         "" italian 1969-01-01 narrative "$system_dir"
# annotate "${input_dir}/32_Hari1979.txt"            "" french  1979-01-01 narrative "$system_dir"
# annotate "${input_dir}/33_Galan1971.txt"           "" spanish 1971-01-01 narrative "$system_dir"
# annotate "${input_dir}/34_Moreno1982.txt"          "" spanish 1982-01-01 narrative "$system_dir"
# annotate "${input_dir}/35_RavinesSanchez1968.txt"  "" spanish 1968-01-01 narrative "$system_dir"
# annotate "${input_dir}/36_Zamora2003.txt"          "" spanish 2003-01-01 narrative "$system_dir"
# annotate "${input_dir}/37_RomanJackson1998.txt"    "" spanish 1998-01-01 narrative "$system_dir"
# annotate "${input_dir}/38_Valverde2007.txt"        "" spanish 2007-01-01 narrative "$system_dir"
# annotate "${input_dir}/39_CruzETAL2010.txt"        "" spanish 2010-01-01 narrative "$system_dir"
# annotate "${input_dir}/40_Donadoni1951.txt"        "" italian 1951-01-01 narrative "$system_dir"
# annotate "${input_dir}/41_Ciampoltrini1984.txt"    "" italian 1984-01-01 narrative "$system_dir"
# annotate "${input_dir}/42_AdamoCappuccino2014.txt" "" italian 2014-01-01 narrative "$system_dir"
# annotate "${input_dir}/43_deVillard1948.txt"       "" italian 1948-01-01 narrative "$system_dir"
# annotate "${input_dir}/44_Furlani1936.txt"         "" italian 1936-01-01 narrative "$system_dir"
# annotate "${input_dir}/45_Cecconi2019.txt"         "" italian 2019-01-01 narrative "$system_dir"
# annotate "${input_dir}/46_Allard2017.txt"          "" french  2017-01-01 narrative "$system_dir"
# annotate "${input_dir}/47_Malleret1959.txt"        "" french  1959-01-01 narrative "$system_dir"
# annotate "${input_dir}/48_VerrandVidal2004.txt"    "" french  2004-01-01 narrative "$system_dir"
# annotate "${input_dir}/49_VandenBerghe1980.txt"    "" french  1980-01-01 narrative "$system_dir"
# annotate "${input_dir}/50_Flament2012.txt"         "" french  2012-01-01 narrative "$system_dir"
# annotate "${input_dir}/51_KazanskiPerin1988.txt"   "" french  1988-01-01 narrative "$system_dir"

# remove temponyms from the system output by doing a standard preparation
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${system_dir}/*.xml" "$system_no_temponyms_dir"

# do the evaluation
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --print-short-info "$bronze_dir" "$system_no_temponyms_dir"

eval_language() {
    echo "EVAL $1"
    local dir="/tmp/lang_$1"
    local src_system="$2"
    local src_bronze="$3"
    docker exec -it chronoi-pilot mkdir -p "$dir"
    docker exec -it chronoi-pilot rm -rf "${dir}/*"

    shift 3
    for fname in "$@"; do
        docker exec -t chronoi-pilot cp "${src_system}/${fname}" "${dir}/"
    done
    docker exec -t chronoi-pilot python postprocessing/evaluate_line_by_line.py --print-short-info "$src_bronze" "$dir"
}
eval_language "french" "$system_no_temponyms_dir" "$bronze_dir" $french_texts
eval_language "german" "$system_no_temponyms_dir" "$bronze_dir" $german_texts
eval_language "italian" "$system_no_temponyms_dir" "$bronze_dir" $italian_texts
eval_language "spanish" "$system_no_temponyms_dir" "$bronze_dir" $spanish_texts

# redo the general evaluation, but collect output in a csv table and print output about the different evaluation decisions
eval_csv="${work_dir}/eval.csv"
docker exec -i chronoi-pilot bash -c "postprocessing/evaluate_line_by_line.py --print_results_csv ${bronze_dir} ${system_no_temponyms_dir} > ${eval_csv}"
docker exec -it chronoi-pilot bash postprocessing/describe_eval_decisions.sh "$eval_csv"


# echo "LITERATURE REFERENCES"
# docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --only_with_attr="literature-time:true" "${bronze_dir}" "${system_no_temponyms_dir}"
# echo "NO LITERATURE REFERENCES"
# docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --disregard_with_attr="literature-time:true" "${bronze_dir}" "${system_no_temponyms_dir}"

# echo "CONTEXT: TOPICAL"
# docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --disregard_with_attr="temporal-context:exploration" "${bronze_dir}" "${system_no_temponyms_dir}"
# echo "CONTEXT: EXPLORATION"
# docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --disregard_with_attr="temporal-context:topic" "${bronze_dir}" "${system_no_temponyms_dir}"



# ENGLISH TEXTS
english_texts="02_Smith2018.xml 03_Veenhof2018.xml 04_Pearce1982.xml 05_Pickering1989.xml 06_Johnson1977.xml 07_HallETAL2004.xml 09_Bermann1997.xml 17_AIA-News-107-Winter-1998.xml 18_AIA-News-136-Spring-2006A.xml"
bronze_en_dir="${work_dir}/en_bronze"
system_en_dir="${work_dir}/en_system"
input_en_dir="${work_dir}/en_input"
system_en_no_temponyms_dir="${work_dir}/en_system_no_temponyms"
docker exec -it chronoi-pilot mkdir -p "$bronze_en_dir" "$system_en_dir" "$input_en_dir" "$system_en_no_temponyms_dir"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --a06tagged "${tagged_dir}/en/*.xml" "$bronze_en_dir"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --text-only "${bronze_en_dir}/*.xml" "$input_en_dir"
annotate "${input_en_dir}/02_Smith2018.txt"                 "" english 2018-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/03_Veenhof2018.txt"               "" english 2017-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/04_Pearce1982.txt"                "" english 1982-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/05_Pickering1989.txt"             "" english 1989-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/06_Johnson1977.txt"               "" english 1977-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/07_HallETAL2004.txt"              "" english 2004-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/09_Bermann1997.txt"               "" english 1997-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/17_AIA-News-107-Winter-1998.txt"  "" english 1998-01-01 narrative "$system_en_dir"
annotate "${input_en_dir}/18_AIA-News-136-Spring-2006A.txt" "" english 2006-01-01 narrative "$system_en_dir"
docker exec -it chronoi-pilot bash -c "sed -i 's|<TimeML><TEXT>\([^\n]\)|<TimeML><TEXT>\n\1|g' ${bronze_en_dir}/*.xml"
docker exec -it chronoi-pilot bash -c "sed -i 's/.*<TimeML><TEXT>$/<TimeML><TEXT>/g' ${bronze_en_dir}/*.xml"
echo "EVAL en"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct "${system_en_dir}/*.xml" "$system_en_no_temponyms_dir"
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --print-short-info "$bronze_en_dir" "$system_en_no_temponyms_dir"


# TEMPONYM EVALUATION
docker exec -it chronoi-pilot bash -c "rm ${bronze_temponyms_dir}/*.xml"

# prepare multilanguage corpus texts
for lang in "fr" "it" "es" "de"
do
  docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --a06tagged --only-temponyms "${tagged_dir}/${lang}/*.xml" "$bronze_temponyms_dir"
done
docker exec -it chronoi-pilot bash -c "sed -i 's|<TEXT>\([^\n]\)|<TEXT>\n\1|g' ${bronze_temponyms_dir}/*.xml"
docker exec -it chronoi-pilot bash -c "sed -i 's|\(.\)</TEXT>|\1\n</TEXT>|g' ${bronze_temponyms_dir}/*.xml"

# prepare english pilot corpus texts
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --a06tagged --only-temponyms "${tagged_dir}/en/*.xml" "$bronze_temponyms_dir"
docker exec -it chronoi-pilot bash -c "sed -i 's|<TimeML><TEXT>\([^\n]\)|<TimeML><TEXT>\n\1|g' ${bronze_temponyms_dir}/*.xml"
docker exec -it chronoi-pilot bash -c "sed -i 's/.*<TimeML><TEXT>$/<TimeML><TEXT>/g' ${bronze_temponyms_dir}/*.xml"

# evaluate all together
echo "EVAL temponyms general"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct --only-temponyms "${system_dir}/*.xml" "$system_temponyms_dir"
docker exec -it chronoi-pilot python3 postprocessing/prepare_tempeval.py --no-fake-dct --only-temponyms "${system_en_dir}/*.xml" "$system_temponyms_dir"
docker exec -it chronoi-pilot python postprocessing/evaluate_line_by_line.py --print-short-info "$bronze_temponyms_dir" "$system_temponyms_dir"
eval_language "english_temponyms" "$system_temponyms_dir" "$bronze_temponyms_dir" $english_texts
eval_language "german_temponyms" "$system_temponyms_dir" "$bronze_temponyms_dir" $german_texts
eval_language "french_temponyms" "$system_temponyms_dir" "$bronze_temponyms_dir" $french_texts
eval_language "italian_temponyms" "$system_temponyms_dir" "$bronze_temponyms_dir" $italian_texts
eval_language "spanish_temponyms" "$system_temponyms_dir" "$bronze_temponyms_dir" $spanish_texts


# chown all files created here to the scripts user.
correct_output_files_ownership
