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

    def move(self, src: str, dst: str):
        shutil.move(
            os.path.expanduser(src),
            os.path.expanduser(dst),
        )
        return f"Moved {src} -> {dst}"
