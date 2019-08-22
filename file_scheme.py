
import os.path


class FileScheme:

    # TODO: Should be an ENV variable / env variables
    output_dir = "/srv/output"
    __DIR_EXTRACTED_TEXTS = f"{output_dir}/001_extracted_texts"
    __DIR_MANUAL_CLEANING = f"{output_dir}/002_manual_cleaning"

    DOCUMENT_STEP_TEMPLATE = "-step%04d.txt"
    PAGE_STEP_TEMPLATE = "-page%04d-step%04d.txt"
    FIRST_STEP_TEMPLATE = "-page%04d-step0000.txt"

    input_path = ""
    basename = ""
    output_basepath = ""

    def __init__(self, path: str):
        self.input_path = path
        (basepath, _) = os.path.splitext(path)
        self.basename = os.path.basename(basepath)
        self.output_basepath = f"{self.output_dir}/{self.basename}"

    @staticmethod
    def __write_file(file_path, content):
        # assert not(os.path.isfile(file_path)), f"File already exists: {file_path}"
        with open(file_path, 'w') as f:
            f.write(content)

    def __get_path(self, dir, extension):
        return f"{dir}/{self.basename}.{extension}"

    def __get_path_with_instruction_in_filename(self, dir: str, instruction: str, extension: str):
        return f"{dir}/{self.basename}-{instruction}.{extension}"

    def get_path_for_extracted_text(self):
        return self.__get_path(self.__DIR_EXTRACTED_TEXTS, "txt")

    def get_path_for_manual_cleaning(self):
        return self.__get_path_with_instruction_in_filename(self.__DIR_MANUAL_CLEANING, "TODO", "txt")

    def get_path_for_manually_cleaned_file(self):
        return self.__get_path_with_instruction_in_filename(self.__DIR_MANUAL_CLEANING, "DONE", "txt")

    @staticmethod
    def file_exists(path: str) -> bool:
        return os.path.isfile(path)