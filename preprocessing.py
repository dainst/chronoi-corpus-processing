#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import langid
import os
import re
import shutil

from file_scheme import FileScheme
from text_extraction import PdfTextExtractor
from cleaning import lines_remove_hyphens
from tokenization import sentence_tokenizer

input_dir = "/srv/input"

if __name__ == "__main__":
    extractor = PdfTextExtractor(PdfTextExtractor.Strategy.PdfMiner)

    input_files = glob.glob(f"{input_dir}/*.pdf")
    input_files.sort()
    for path in input_files:

        scheme = FileScheme(path)

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

        scheme.add_step(3, "cleanup_whitespace")
        out_path = scheme.get_path_for_step(3)
        if not scheme.file_exists(out_path):
            lines = scheme.read_file(scheme.get_done_path_for_step(2)).splitlines()

            lines = [l.strip() for l in lines]
            lines = [re.sub(r"\s{2,}", " ", l) for l in lines]
            content = "\n".join(lines)

            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            scheme.write_file(out_path, content)

        # detect the document language
        language_code = ""
        languages = {"en": "english", "de": "german"}
        if scheme.file_exists(scheme.get_path_for_step(3)):
            content = scheme.read_file(scheme.get_path_for_step(3))
            langid.set_languages(languages.keys())
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

            tokenizer = sentence_tokenizer(languages[language_code])
            sentences = tokenizer.tokenize(content)

            # since no hyphen should exist at this point, we can just cat the lines together
            sentences = map(lambda s: re.sub("\s+", " ", s), sentences)
            sentences = map(str.strip, sentences)
            new_content = "\n".join(sentences)
            os.makedirs(os.path.dirname((out_path)), exist_ok=True)
            scheme.write_file(out_path, new_content)

        scheme.add_step(6, "separate_by_language")
        path_from_last_step = out_path
        language_dir = os.path.join(scheme.get_dirname_for_step(6), language_code)
        os.makedirs(language_dir, exist_ok=True)
        shutil.copy(path_from_last_step, language_dir)
