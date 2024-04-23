#!/usr/bin/env python
"""A wrapper script around run-clang-tidy

This exist moslty because on windows it is a pain
to run script from files in the path.
"""
import shutil
import sys
import subprocess
import os


def main():
    # find the path to run-clang-tidy removing the current venv from the path list
    current_venv_path = os.environ.get("VIRTUAL_ENV")
    env_path = ";".join(
        [
            path
            for path in os.environ["PATH"].split(";")
            if current_venv_path not in path
        ]
    )
    file_path = shutil.which("run-clang-tidy", path=env_path)

    # run it
    subprocess.run([sys.executable, file_path, *sys.argv[1:]])


if __name__ == "__main__":
    main()
