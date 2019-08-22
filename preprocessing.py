#!/usr/bin/env python3

import glob
import os
import shutil

from file_scheme import FileScheme
from text_extraction import PdfTextExtractor

input_dir = "/srv/input"

if __name__ == "__main__":
    extractor = PdfTextExtractor(PdfTextExtractor.Strategy.PdfMiner)

    input_files = glob.glob(f"{input_dir}/*.pdf")
    input_files.sort()
    for path in input_files:
        files = FileScheme(path)

        files.add_step(1, "extracted_texts")
        out_path = files.get_path_for_step(1)
        if not files.file_exists(out_path):
            extractor.extract(path, out_path)

        files.add_step(2, "manual_cleaning")
        copy_path = files.get_todo_path_for_step(2)
        done_path = files.get_done_path_for_step(2)
        if not (files.file_exists(copy_path) or files.file_exists(done_path)):
            os.makedirs(os.path.dirname(copy_path), 0o777, True)
            shutil.copyfile(out_path, copy_path)
