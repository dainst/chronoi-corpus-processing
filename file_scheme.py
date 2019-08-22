
import os.path


class FileScheme:

    # TODO: Should be an ENV variable / env variables
    output_dir = "/srv/output"

    input_path = ""
    basename = ""
    output_basepath = ""

    def __init__(self, path: str):
        self.steps = {
            # 1 => "extract_texts,
            # 2 => "manual_cleaning",
            # ...
        }
        self.input_path = path
        (basepath, _) = os.path.splitext(path)
        self.basename = os.path.basename(basepath)
        self.output_basepath = f"{self.output_dir}/{self.basename}"

    def add_step(self, step_no: int, step_name: str):
        if step_no in self.steps.keys():
            raise Exception("Step number already exists")
        else:
            self.steps[step_no] = step_name

    @staticmethod
    def __write_file(file_path, content):
        # assert not(os.path.isfile(file_path)), f"File already exists: {file_path}"
        with open(file_path, 'w') as f:
            f.write(content)

    def __get_path(self, directory: str, extension):
        return f"{directory}/{self.basename}.{extension}"

    def __get_path_with_instruction_in_filename(self, directory: str, instruction: str, extension: str):
        return f"{directory}/{self.basename}-{instruction}.{extension}"

    def __get_dirname_for_step(self, step_no: int):
        number_str = "%03d" % step_no
        folder_name = f"{number_str}_{self.steps[step_no]}"
        return os.path.join(self.output_dir, folder_name)

    def get_path_for_step(self, step_no: int) -> str:
        return self.__get_path(self.__get_dirname_for_step(step_no), "txt")

    def get_todo_path_for_step(self, step_no: int) -> str:
        return self.__get_path_with_instruction_in_filename(self.__get_dirname_for_step(step_no), "TODO", "txt")

    def get_done_path_for_step(self, step_no: int) -> str:
        return self.__get_path_with_instruction_in_filename(self.__get_dirname_for_step(step_no), "DONE", "txt")

    @staticmethod
    def file_exists(path: str) -> bool:
        return os.path.isfile(path)
