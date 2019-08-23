#!/usr/bin/env python3

import glob
import langid
import os
import re
import shutil

from file_scheme import FileScheme
from text_extraction import PdfTextExtractor
from cleaning import lines_remove_hyphens

input_dir = "/srv/input"

if __name__ == "__main__":
    extractor = PdfTextExtractor(PdfTextExtractor.Strategy.PdfMiner)

    input_files = glob.glob(f"{input_dir}/*.pdf")
    input_files.sort()
    for path in input_files:

        # DONTCOMMIT
        # if "07_" not in path:
        #     continue

        scheme = FileScheme(path)

        scheme.add_step(1, "extracted_texts")
        out_path = scheme.get_path_for_step(1)
        if not scheme.file_exists(out_path):
            extractor.extract(path, out_path)

        scheme.add_step(2, "manual_cleaning")
        copy_path = scheme.get_todo_path_for_step(2)
        done_path = scheme.get_done_path_for_step(2)
        if not (scheme.file_exists(copy_path) or scheme.file_exists(done_path)):
            os.makedirs(os.path.dirname(copy_path), 0o777, True)
            shutil.copyfile(out_path, copy_path)

        scheme.add_step(3, "cleanup_whitespace")
        out_path = scheme.get_path_for_step(3)
        if not scheme.file_exists(out_path):
            lines = scheme.read_file(scheme.get_done_path_for_step(2)).splitlines()

            lines = [l.strip() for l in lines]
            lines = [re.sub(r"\s{2,}", " ", l) for l in lines]
            content = "\n".join(lines)

            os.makedirs(os.path.dirname(out_path), 0o777, True)
            scheme.write_file(out_path, content)

        scheme.add_step(4, "de_hyphenate")
        out_path = scheme.get_path_for_step(4)
        if True: #not scheme.file_exists(out_path):
            content = scheme.read_file(scheme.get_path_for_step(3))

            languages = {"en": "english", "de": "german"}
            langid.set_languages(languages.keys())
            language_code, _ = langid.classify(content)

            lines = content.splitlines()
            for i in range(0, len(lines) - 1):
                l1, l2 = lines_remove_hyphens(lines[i], lines[i + 1], language_code)
                lines[i] = l1
                lines[i+1] = l2

            content = "\n".join(lines)
            os.makedirs(os.path.dirname(out_path), 0o777, True)
            scheme.write_file(out_path, content)

