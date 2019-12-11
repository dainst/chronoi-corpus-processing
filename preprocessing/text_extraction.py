
import subprocess

import bs4
from enum import Enum
import os
import shutil


class TextExtractionStrategyInterface:

    def extract(self, input_path: str, output_path: str):
        raise NotImplementedError()


# Ghostscript is good at outputting a pdf in a text form like it would appear
# when rendered, the whitespace imitating page borders etc.
class PdfGhostscriptTextExtractionStrategy(TextExtractionStrategyInterface):

    PARAMS = [
        "gs",
        "-sDEVICE=txtwrite",
        "-dNOPAUSE",
        "-dBATCH",
    ]

    def extract(self, input_path, output_path):
        output_file_param = f"-sOutputFile={output_path}"
        params = self.PARAMS + [output_file_param, input_path]
        subprocess.call(params)

# PDFMiner is a PDF extractor with reasonably good text composition
# It is also able to preserve page delimiters.
# PdfMiner has good python bindings, but we call it in a subprocess for
# simplicity.
class PdfMinerTextExtractionStrategy(TextExtractionStrategyInterface):

    def extract(self, input_path, output_path):
        params = ["pdf2txt.py", "-o", output_path, input_path]
        subprocess.call(params)

# MuPDF's mutool command is exceptionally fast and does very good text
# composition.
class PdfMutoolTextExtractionStrategy(TextExtractionStrategyInterface):

    def extract(self, input_path, output_path):
        params = [ "mutool", "convert", "-F", "text", "-o", output_path, input_path]
        subprocess.call(params)


class XMLBeautifulsoupTextExtractionStrategy(TextExtractionStrategyInterface):

    def extract(self, input_path: str, output_path: str):
        with open(input_path, "r") as in_file:
            doc = bs4.BeautifulSoup(in_file, "lxml-xml")
        with open(output_path, "w") as out_file:
            out_file.write(doc.text)


class TextFileCopyStrategy(TextExtractionStrategyInterface):

    def extract(self, input_path: str, output_path: str):
        shutil.copyfile(input_path, output_path)


class TextExtractor:

    class Strategy(Enum):
        PDF_Ghostscript = PdfGhostscriptTextExtractionStrategy
        PDF_PdfMiner = PdfMinerTextExtractionStrategy
        PDF_PdfMutool = PdfMutoolTextExtractionStrategy
        XML_BeautifulSoup = XMLBeautifulsoupTextExtractionStrategy
        TXT_Copy = TextFileCopyStrategy

        def init(self):
            return self.value()

    def __init__(self, strategy: Strategy = Strategy.PDF_PdfMiner):
        self.strategy = strategy.init()

    def extract(self, input_path: str, output_path: str):
        self.__prepare_output_folder_for(output_path)
        self.strategy.extract(input_path, output_path)

    @staticmethod
    def __prepare_output_folder_for(path: str):
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, 0o777, True)

    @classmethod
    def create_by_file_ext(cls, path: str):
        _, ext = os.path.splitext(path)
        if ext in [".pdf", ".PDF"]:
            return cls(cls.Strategy.PDF_PdfMutool)
        elif ext in [".xml", ".XML", ".html", ".HTML", ".htm", ".HTM"]:
            return cls(cls.Strategy.XML_BeautifulSoup)
        elif ext in [".txt", ".TXT"]:
            return cls(cls.Strategy.TXT_Copy)
        else:
            raise ValueError(f"Text extraction not defined for extension: '{ext}'")
