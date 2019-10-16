
import os.path
import shutil


class FileScheme:

    def __init__(self, path: str, output_dir="/srv/output"):
        self.steps = {
            # 1 => "extract_texts,
            # 2 => "manual_cleaning",
            # ...
        }
        self.input_path = path
        (basepath, _) = os.path.splitext(path)
        self.basename = os.path.basename(basepath)
        self.output_dir = output_dir

    def add_step(self, step: int, step_name: str):
        if step in self.steps.keys():
            raise Exception("Step number already exists")
        else:
            self.steps[step] = step_name

    def __path(self, directory: str, extension):
        return f"{directory}/{self.basename}.{extension}"

    def __path_with_instruction(self, directory: str, instruction: str, extension: str):
        return f"{directory}/{self.basename}-{instruction}.{extension}"

    def dirname(self, step: int):
        number_str = "%03d" % step
        folder_name = f"{number_str}_{self.steps[step]}"
        return os.path.join(self.output_dir, folder_name)

    def path(self, step: int) -> str:
        return self.__path(self.dirname(step), "txt")

    def todo_path(self, step: int) -> str:
        return self.__path_with_instruction(self.dirname(step), "TODO", "txt")

    def done_path(self, step: int) -> str:
        return self.__path_with_instruction(self.dirname(step), "DONE", "txt")

    @staticmethod
    def read_file(path: str) -> str:
        with open(path, 'r') as file:
            return file.read()

    @classmethod
    def read_lines(cls, path: str) -> [str]:
        return cls.read_file(path).splitlines()

    @staticmethod
    def write_file(file_path, content, create_dirs=False):
        assert not(os.path.isfile(file_path)), f"File already exists: {file_path}"
        if create_dirs:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)

    @classmethod
    def write_lines(cls, path, lines: [str], create_dirs=False):
        return cls.write_file(path, "\n".join(lines), create_dirs)

    @staticmethod
    def copy_file(src, dst, create_dirs=False):
        if create_dirs:
            dir = dst if os.path.isdir(dst) else os.path.dirname(dst)
            os.makedirs(dir, exist_ok=True)
        shutil.copy(src, dst)

    @staticmethod
    def file_exists(path: str) -> bool:
        return os.path.isfile(path)
