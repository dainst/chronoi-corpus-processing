#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import glob
import langid
import os
import random
import re


from preprocessing import cleaning
from preprocessing.file_scheme import FileScheme
from preprocessing.text_extraction import TextExtractor
from preprocessing.tokenization import sentence_tokenizer


_project_languages = {
    "de": "german",
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "it": "italian",
}


def main(input_dir: str, output_dir: str, args: argparse.Namespace):

    input_files = glob.glob(f"{input_dir}/*")
    input_files.sort()
    for path in input_files:

        scheme = FileScheme(path, output_dir=output_dir)

        scheme.add_step(1, "extracted_texts")
        out_path = scheme.path(1)
        if not scheme.file_exists(out_path):
            extractor = TextExtractor.create_by_file_ext(path)
            extractor.extract(path, out_path)

        scheme.add_step(2, "manual_cleaning")
        copy_path = scheme.todo_path(2)
        done_path = scheme.done_path(2)
        if not (scheme.file_exists(copy_path) or scheme.file_exists(done_path)):
            scheme.copy_file(out_path, copy_path, create_dirs=True)
        if args.skip_manual_cleaning and not scheme.file_exists(done_path):
            scheme.copy_file(out_path, done_path, create_dirs=True)

        scheme.add_step(3, "cleanup_whitespace")
        out_path = scheme.path(3)
        if not scheme.file_exists(out_path):
            done_path = scheme.done_path(2)
            if not scheme.file_exists(done_path):
                print("WARN:", f"No input file at: '{done_path}'. Was this file manually cleaned?")
                continue
            lines = scheme.read_lines(scheme.done_path(2))
            lines = cleaning.cleanup_whitespace(lines)
            scheme.write_lines(out_path, lines, create_dirs=True)

        # detect the document language
        language_code = ""
        if scheme.file_exists(scheme.path(3)):
            content = scheme.read_file(scheme.path(3))
            langid.set_languages(_project_languages.keys())
            language_code, _ = langid.classify(content)

        scheme.add_step(4, "de_hyphenate")
        out_path = scheme.path(4)
        if not scheme.file_exists(out_path):
            lines = scheme.read_lines(scheme.path(3))
            lines = cleaning.remove_end_of_line_hyphens(lines, language_code, args.always_combine_hyphens)
            scheme.write_lines(out_path, lines, create_dirs=True)

        scheme.add_step(5, "tokenize_sententces")
        out_path = scheme.path(5)
        if not scheme.file_exists(out_path):
            content = scheme.read_file(scheme.path(4))
            tokenizer = sentence_tokenizer(_project_languages[language_code])
            sentences = tokenizer.tokenize(content)
            # since no hyphen should exist at this point, we can just cat the lines together
            sentences = map(lambda s: re.sub(r"\s+", " ", s), sentences)
            sentences = map(str.strip, sentences)
            scheme.write_lines(out_path, sentences, create_dirs=True)

        scheme.add_step(6, "escape_xml_chars")
        out_path = scheme.path(6)
        if not scheme.file_exists(out_path):
            content = scheme.read_file(scheme.path(5))
            new_content = cleaning.escape_xml_chars(content)
            scheme.write_file(out_path, new_content, create_dirs=True)

        scheme.add_step(7, "sentence_window")
        out_path = scheme.path(7)
        if args.random_window > 0 and not scheme.file_exists(out_path):
            lines = scheme.read_lines(scheme.path(6))
            if len(lines) > args.random_window:
                begin = random.randrange(0, len(lines) - args.random_window)
                lines = lines[begin:(begin + args.random_window)]
            scheme.write_lines(out_path, lines, create_dirs=True)
        else:
            # reset for the last step
            out_path = scheme.path(6)

        scheme.add_step(42, "separate_by_language")
        path_from_last_step = out_path
        language_dir = os.path.join(scheme.dirname(42), language_code)
        os.makedirs(language_dir, exist_ok=True)
        scheme.copy_file(path_from_last_step, language_dir)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Execute all preprocessing steps over the containers input directory.")
    parser.add_argument("--skip_manual_cleaning", action="store_true",
                        help="If present, skip the manual cleaning step.")
    parser.add_argument("--random_window", type=int, default=0,
                        help="If a random window of n sentences should be extracted from the text set this to n.")
    parser.add_argument("--always_combine_hyphens", action="store_true",
                        help="If a line ends in a hyphen, always combine the hyphenated words (without a spellcheck).")

    main("/srv/input", "/srv/output", parser.parse_args())
