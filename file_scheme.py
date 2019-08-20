
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

    def __get_todo_path(self, dir, extension):
        return f"{dir}/{self.basename}-TODO.{extension}"

    def get_path_for_extracted_text(self):
        return self.__get_path(self.__DIR_EXTRACTED_TEXTS, "txt")

    def get_path_for_manual_cleaning(self):
        return self.__get_todo_path(self.__DIR_MANUAL_CLEANING, "txt")

    # TODO: Check if these functions are needed any longer

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
