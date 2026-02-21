import glob
import os
import shutil
from tools.base import Tool


class FileOps(Tool):
    name = "FileOps"

    def scan(self, path: str):
        return os.listdir(os.path.expanduser(path))

    def mkdir(self, path: str):
        os.makedirs(os.path.expanduser(path), exist_ok=True)
        return f"Directory created: {path}"

    def move(self, source: str, destination: str):
        src_pattern = os.path.expanduser(source)
        dst = os.path.expanduser(destination)

        for path in glob.glob(src_pattern):
            shutil.move(path, dst)
        return f"Moved files matching {source} -> {destination}"
    
    def write_file(self, path: str, content: str):
        full = os.path.expanduser(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content)
        return f"File written: {path}"


    def touch(self, path: str):
        full = os.path.expanduser(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "a").close()
        return f"File created: {path}"