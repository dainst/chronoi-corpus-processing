#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import glob
import langid
import os
import re
import shutil
import xml.sax.saxutils

from preprocessing.file_scheme import FileScheme
from preprocessing.text_extraction import TextExtractor
from preprocessing.cleaning import lines_remove_hyphens
from preprocessing.tokenization import sentence_tokenizer


_project_languages = {
    "de": "german",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "it": "italian",
}


def main(input_dir: str, output_dir: str, skip_manual_cleaning=False):

    input_files = glob.glob(f"{input_dir}/*")
    input_files.sort()
    for path in input_files:

        extractor = TextExtractor.create_by_file_ext(path)
        scheme = FileScheme(path, output_dir=output_dir)

        scheme.add_step(1, "extracted_texts")
        out_path = scheme.get_path_for_step(1)
        if not scheme.file_exists(out_path):
            extractor.extract(path, out_path)

        scheme.add_step(2, "manual_cleaning")
        copy_path = scheme.get_todo_path_for_step(2)
        done_path = scheme.get_done_path_for_step(2)
        if not (scheme.file_exists(copy_path) or scheme.file_exists(done_path)):
            os.makedirs(os.path.dirname(copy_path), exist_ok=True)
            shutil.copyfile(out_path, copy_path)
        if skip_manual_cleaning and not scheme.file_exists(done_path):
            shutil.copyfile(out_path, done_path)

        scheme.add_step(3, "cleanup_whitespace")
        out_path = scheme.get_path_for_step(3)
        if not scheme.file_exists(out_path):
            lines = scheme.read_file(scheme.get_done_path_for_step(2)).splitlines()

            # filter out all lines, that are entirely whitespace, then
            # filter the unneccessary whitespace
            lines = [l for l in lines if not re.match(r"^\s*$", l)]
            lines = [l.strip() for l in lines]
            lines = [re.sub(r"\s{2,}", " ", l) for l in lines]
            content = "\n".join(lines)

            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            scheme.write_file(out_path, content)

        # detect the document language
        language_code = ""
        if scheme.file_exists(scheme.get_path_for_step(3)):
            content = scheme.read_file(scheme.get_path_for_step(3))
            langid.set_languages(_project_languages.keys())
            language_code, _ = langid.classify(content)

        scheme.add_step(4, "de_hyphenate")
        out_path = scheme.get_path_for_step(4)
        if not scheme.file_exists(out_path):
            content = scheme.read_file(scheme.get_path_for_step(3))
            lines = content.splitlines()
            for i in range(0, len(lines) - 1):
                l1, l2 = lines_remove_hyphens(lines[i], lines[i + 1], language_code)
                lines[i] = l1
                lines[i+1] = l2

            content = "\n".join(lines)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            scheme.write_file(out_path, content)

        scheme.add_step(5, "tokenize_sententces")
        out_path = scheme.get_path_for_step(5)
        if not scheme.file_exists(out_path):
            content = scheme.read_file(scheme.get_path_for_step(4))

            tokenizer = sentence_tokenizer(_project_languages[language_code])
            sentences = tokenizer.tokenize(content)

            # since no hyphen should exist at this point, we can just cat the lines together
            sentences = map(lambda s: re.sub(r"\s+", " ", s), sentences)
            sentences = map(str.strip, sentences)
            new_content = "\n".join(sentences)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            scheme.write_file(out_path, new_content)

        scheme.add_step(6, "escape_xml_chars")
        out_path = scheme.get_path_for_step(6)
        if not scheme.file_exists(out_path):
            content = scheme.read_file(scheme.get_path_for_step(5))
            new_content = xml.sax.saxutils.escape(content)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            scheme.write_file(out_path, new_content)

        scheme.add_step(7, "separate_by_language")
        path_from_last_step = out_path
        language_dir = os.path.join(scheme.get_dirname_for_step(7), language_code)
        os.makedirs(language_dir, exist_ok=True)
        shutil.copy(path_from_last_step, language_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Execute all preprocessing steps over the containers input directory.")
    parser.add_argument("--skip_manual_cleaning", action="store_true",
                        help="If present, skip the manual cleaning step.")
    args = parser.parse_args()

    main("/srv/input", "/srv/output", args.skip_manual_cleaning)
