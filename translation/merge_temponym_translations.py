#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv


file_english = "/srv/output/heideltime_temponym_files/en_repattern.txt"

labels_to_files = {
    'idai_vocab': "/srv/output/temponym-translations/translate_en_idai_vocab.txt",
    'dbpedia': "/srv/output/temponym-translations/translate_en_dbpedia.txt",
    'google': "/srv/output/temponym-translations/translate_en_google.txt"
}

target_languages = ['fr', 'it', 'es', 'de']

output_overview = "/srv/output/temponym-translations/translations.csv"

output_heideltime_files = {
    "fr": ("/srv/output/heideltime_temponym_files/fr_auto_repattern.txt", "/srv/output/heideltime_temponym_files/fr_auto_norm.txt"),
    "it": ("/srv/output/heideltime_temponym_files/it_auto_repattern.txt", "/srv/output/heideltime_temponym_files/it_auto_norm.txt"),
    "es": ("/srv/output/heideltime_temponym_files/es_auto_repattern.txt", "/srv/output/heideltime_temponym_files/es_auto_norm.txt")
}

input_normalization_file = "/srv/output/heideltime_temponym_files/en_norm.txt"

# the preference order in which the different translations are used
# first dbpedia, then google, ignore idai.vocab
label_preference = ["dbpedia", "google"]


def file_to_lines(path: str):
    with open(path) as f:
        return f.read().splitlines()


# we want to produce a table
result_headers = []
result_columns = []

# the leftmost result column is the orignial temponyms, so read them
result_headers.append("original")
result_columns.append(file_to_lines(file_english))

# for each label and each interesting language add another result column
for target_lang in target_languages:
    for label, file in labels_to_files.items():
        current_label = f"{target_lang}-{label}"
        result_headers.append(current_label)

        lines = file_to_lines(file)
        column = []

        for i, line in enumerate(lines):
            if "No similar term found" in line:
                column.append("")
            else:
                array_of_pairs = eval(line)
                candidates = [translation for (lang, translation) in array_of_pairs if lang == target_lang]
                item = "||".join(candidates)
                column.append(item)

        result_columns.append(column)

# construct a bunch of result rows
rows = []
for y in range(0, len(result_columns[0])):
    row = [result_columns[x][y] for x in range(0, len(result_columns))]
    # do not use expressions that are exaclty like the original in the first column
    row = [s if (i == 0 or s.strip() != row[0].strip()) else "" for i, s in enumerate(row)]
    rows.append(row)

# print the table as an overview and ensure all strings are properly quoted
with open(output_overview, "w") as csvfile:
    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(result_headers)
    for row in rows:
        writer.writerow(row)

# read in the normalization patterns from the en_norm file
normalization_spans = []
with open(input_normalization_file, "r") as norm_file:
    norm_reader = csv.reader(norm_file)
    for row in norm_reader:
        normalization_spans.append(row[1])

if len(normalization_spans) != len(result_columns[0]):
    print("ERROR: Count of normalizations and translations does not match.")
    exit(1)

# print the repattern and normaliation files for each of the languages
for lang, paths in output_heideltime_files.items():
    repattern_lines = []
    norm_lines = []

    for idx, row in enumerate(rows):

        # Determine a translation
        # use the original english if no other translation is found
        translation = row[0]

        # iterate over the labels of translation types in preferred order
        for preferred_label in label_preference:
            # determine the column position to use by the label name
            label_to_use = f"{lang}-{preferred_label}"
            label_x_pos = result_headers.index(label_to_use)
            candidate = row[label_x_pos]
            if candidate.strip() != "":
                # if multiple candidates are given by the translation only take the first
                translation = candidate.split("||")[0]
                # preferred translation is found so do not test any others
                break

        # Write the translation to the pattern file
        repattern_lines.append(translation + "\n")

        # Write the translation and the normalization to the norm file
        normalization_output = '"%s","%s"\n' % (translation, normalization_spans[idx])
        norm_lines.append(normalization_output)

    # actually write the files
    with open(paths[0], "w") as repattern_file:
        repattern_file.writelines(repattern_lines)
    with open(paths[1], "w") as norm_file:
        norm_file.writelines(norm_lines)
