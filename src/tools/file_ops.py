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