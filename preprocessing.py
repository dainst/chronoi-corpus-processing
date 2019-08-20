#!/usr/bin/env python3

import nltk
import subprocess
import time
import os

from cleaning import *

input_dir = "/srv/input"

ghostscript_params = [
    "gs",
    "-sDEVICE=txtwrite",
    "-dNOPAUSE",
    "-dBATCH",
]


class FileScheme:
    DOCUMENT_STEP_TEMPLATE = "-step%04d.txt"
    PAGE_STEP_TEMPLATE = "-page%04d-step%04d.txt"
    FIRST_STEP_TEMPLATE = "-page%04d-step0000.txt"

    input_path = ""
    basename = ""
    output_dir = "/srv/output"
    output_basepath = ""

    def __init__(self, path):
        self.input_path = path
        (basepath, _) = os.path.splitext(path)
        self.basename = os.path.basename(basepath)
        self.output_basepath = f"{self.output_dir}/{self.basename}"

    def build_output_file_template(self):
        return self.output_basepath + self.FIRST_STEP_TEMPLATE

    def get_file_for_page_and_step(self, page_no, step_no):
        template = self.output_basepath + self.PAGE_STEP_TEMPLATE
        return template % (page_no, step_no)

    def get_file_for_document_and_step(self, step_no):
        template = self.output_basepath + self.DOCUMENT_STEP_TEMPLATE
        return template % step_no

    def read_page_file(self, page_no, step_no):
        file_path = self.get_file_for_page_and_step(page_no, step_no)
        # assert (os.path.isfile(file_path)), f"File does not exist: {file_path}"
        with open(file_path, 'r') as f:
            return f.read()

    def write_page_file(self, page_no, step_no, content):
        file_path = self.get_file_for_page_and_step(page_no, step_no)
        self.__write_file(file_path, content)

    def write_document_file(self, step_no, content):
        file_path = self.get_file_for_document_and_step(step_no)
        self.__write_file(file_path, content)

    @staticmethod
    def __write_file(file_path, content):
        # assert not(os.path.isfile(file_path)), f"File already exists: {file_path}"
        with open(file_path, 'w') as f:
            f.write(content)


class Page:
    page_no = 0
    current_step = 0
    file_scheme = None

    def __init__(self, file_scheme, page_no, step_no=0):
        self.file_scheme = file_scheme
        self.page_no = page_no
        self.current_step = step_no

    def get_text(self):
        return self.file_scheme.read_page_file(self.page_no, self.current_step)

    def get_lines(self):
        return self.get_text().splitlines()

    def save_result(self, result):
        # the only place where the step number is incremented should be here,
        # right before a new result is saved
        self.current_step += 1
        self.file_scheme.write_page_file(self.page_no, self.current_step, result)

    def apply_to_text(self, callback):
        new_text = callback(self.get_text())
        self.save_result(new_text)

    def apply_to_lines(self, callback):
        lines = [callback(l) for l in self.get_lines()]
        new_text = "\n".join(lines)
        self.save_result(new_text)


class PdfDocument:
    max_page = 66
    file_scheme = None
    current_step = 0

    def __init__(self, path):
        assert os.path.isfile(path) and os.access(path, os.R_OK), \
            f"File is not present or not readable: {path}"
        self.file_scheme = FileScheme(path)

    def convert_pages_to_text(self):
        # ghostscript directly accepts a printf-like template with "%d" in it
        output_file_param = "-sOutputFile=%s" % self.file_scheme.build_output_file_template()
        params = ghostscript_params + [output_file_param, self.file_scheme.input_path]
        subprocess.call(params)
        return

    def __iter_pages(self):
        for page_no in range(1, self.max_page + 1):
            # DONTCOMMIT
            # if (page_no != 3 and page_no != 4):
            #     continue

            page = Page(self.file_scheme, page_no, self.current_step)
            yield page

    def __increment_step_no(self):
        self.current_step += 1

    def apply_to_page_texts(self, callback):
        """
        Do a new conversion step by executing the callback on the page
        text. Increments the step no by 1 and saves a new file with the
        changed page text.
        """
        for page in self.__iter_pages():
            page.apply_to_text(callback)
        self.__increment_step_no()

    def apply_to_page_lines(self, callback):
        """
        Do a new conversion step by executing the callback on each line
        of the page text. Increments the step no by 1 and saves a new file
        with the changed page text.
        """
        for page in self.__iter_pages():
            page.apply_to_lines(callback)
        self.__increment_step_no()

    def combine_pages(self):
        text = "\f".join([p.get_text() for p in self.__iter_pages()])
        self.file_scheme.write_document_file(self.current_step, text)
        self.__increment_step_no()


if __name__ == "__main__":
    doc = PdfDocument(input_dir + "/01_Funke2019.pdf")
    print(doc.file_scheme.input_path)
    print(doc.file_scheme.basename)
    print(doc.file_scheme.output_dir)
    print(doc.file_scheme.output_basepath)

    doc.convert_pages_to_text()

    doc.apply_to_page_texts(page_remove_first_line)
    doc.apply_to_page_lines(line_delete_text_surrounded_by_whitespace_left)
    doc.apply_to_page_lines(lambda l: line_delete_if_whitespace_exceeds(l, 0.85))
    doc.apply_to_page_lines(lambda l: l.strip())
    doc.apply_to_page_texts(lambda p: "\n".join([line for line in p.splitlines() if line != ""]))
    doc.apply_to_page_lines(line_delete_text_surrounded_by_whitespace_right)

    doc.combine_pages()
