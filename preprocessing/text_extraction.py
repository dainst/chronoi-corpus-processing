
import subprocess

from enum import Enum
import os


class PdfTextExtractionStrategyInterface:

    def extract(self, input_path: str, output_path: str):
        raise NotImplementedError()


class PdfTextExtractor:

    class Strategy(Enum):
        Ghostscript = 0
        PdfMiner =1

    strategy: PdfTextExtractionStrategyInterface

    def __init__(self, strategy: Strategy = Strategy.Ghostscript):
        if strategy == self.Strategy.Ghostscript:
            self.strategy = PdfGhostscriptTextExtractionStrategy()
        elif strategy == self.Strategy.PdfMiner:
            self.strategy = PdfMinerTextExtractionStrategy()

    def extract(self, input_path: str, output_path: str):
        self.__prepare_output_folder_for(output_path)
        self.strategy.extract(input_path, output_path)

    @staticmethod
    def __prepare_output_folder_for(path: str):
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, 0o777, True)


class PdfGhostscriptTextExtractionStrategy(PdfTextExtractionStrategyInterface):

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


class PdfMinerTextExtractionStrategy(PdfTextExtractionStrategyInterface):

    def extract(self, input_path, output_path):
        params = ["pdf2txt.py", "-o", output_path, input_path]
        subprocess.call(params)
