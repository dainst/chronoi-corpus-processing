#!/usr/bin/env python3

import os
import glob
import shutil

from cleaning import *
from file_scheme import FileScheme
from text_extraction import PdfTextExtractor

input_dir = "/srv/input"

if __name__ == "__main__":
    extractor = PdfTextExtractor(PdfTextExtractor.Strategy.PdfMiner)

    input_files = glob.glob(f"{input_dir}/*.pdf")
    input_files.sort()
    for path in input_files:
        files = FileScheme(path)

        # step 001: text extraction
        out_path = files.get_path_for_extracted_text()
        if not files.file_exists(out_path):
            extractor.extract(path, out_path)

        # step 002: Save a copy for manual correction
        copy_path = files.get_path_for_manual_cleaning()
        done_path = files.get_path_for_manually_cleaned_file()
        if not (files.file_exists(copy_path) or files.file_exists(done_path)):
            os.makedirs(os.path.dirname(copy_path), 0o777, True)
            shutil.copyfile(out_path, copy_path)
