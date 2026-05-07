import os
import subprocess
from config import WORKSPACE


class ToolManager:

    @staticmethod
    def read_file(path):
        full_path = os.path.join(WORKSPACE, path)

        if not os.path.exists(full_path):
            return "文件不存在"

        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_file(path, content):
        full_path = os.path.join(WORKSPACE, path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"文件已写入: {path}"

    @staticmethod
    def list_files():
        result = []

        for root, dirs, files in os.walk(WORKSPACE):
            for file in files:
                result.append(os.path.join(root, file))

        return "\n".join(result)

    @staticmethod
    def run_command(command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=WORKSPACE,
                timeout=30
            )

            return result.stdout + "\n" + result.stderr

        except Exception as e:
            return str(e)
