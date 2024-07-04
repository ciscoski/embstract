#!/usr/bin/env python3
"""Wrapper to run PCLint as pre-commit hook.

This script will
1) Extract the compiler type from the CMake build folder.
2) Generate a pclint project configuration file based on a filtered compile_commands.json.
3) Invoke PCLint to analyze the requested files.

This script assumes the following:
* The cmake project (toolchain file) should specify PCLINT_COMPILER_NAME which should be a compiler name present in the 
  pclint compilers.yaml file.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import mmap
from dataclasses import dataclass
from typing import Pattern, Tuple
import glob
import logging
from pprint import pformat

CMAKE_COMPILE_COMMAND_FILE_NAME = "compile_commands.json"
PCLINT_CONFIG_SCRIPT_RELATIVE_PATH = "config/pclp_config.py"
PCLINT_LINTER_EXECUTABLE = "pclp64"
PCLINT_OUTPUT_PATH = ".pclint"
PCLINT_COMPILER_CONFIG_FILE_NAME = "pclint_compiler_config"
PCLINT_PROJECT_CONFIG_FILE_NAME = "pclint_project_config.lnt"

PCLINT_COMPILER_NAME_REGEX = re.compile(rb"PCLINT_COMPILER_NAME:.*=(.*)")
PCLINT_COMPILER_OPTIONS_REGEX = re.compile(rb"PCLINT_COMPILER_OPTIONS:.*=(.*)")
PCLINT_COMPILER_C_OPTIONS_REGEX = re.compile(rb"PCLINT_COMPILER_C_OPTIONS:.*=(.*)")
PCLINT_COMPILER_CPP_OPTIONS_REGEX = re.compile(rb"PCLINT_COMPILER_CPP_OPTIONS:.*=(.*)")
PCLINT_COMPILER_BIN = re.compile(rb"set\(CMAKE_C_COMPILER \"(.*)\"\)")


@dataclass
class PclingCachedVariable:
    regex: Pattern[bytes]
    required: bool
    value: str | None = None


def abs_dir_path(path: str) -> str:
    if os.path.isdir(path):
        return os.path.abspath(path)
    else:
        raise argparse.ArgumentTypeError("Path is not a direcotry.")


def abs_file_path(path: str) -> str:
    if os.path.isfile(path):
        return os.path.abspath(path)
    else:
        raise argparse.ArgumentParser("Path is not a file")


def extact_compiler_name_from_build(
    build_path: os.PathLike,
) -> dict[str, PclingCachedVariable]:

    logging.debug("Extracting compiler from build")
    pclint_compiler_configs: dict[str, PclingCachedVariable] = {
        "compiler": PclingCachedVariable(PCLINT_COMPILER_NAME_REGEX, True),
        "compiler-options": PclingCachedVariable(PCLINT_COMPILER_OPTIONS_REGEX, False),
        "compiler-c-options": PclingCachedVariable(
            PCLINT_COMPILER_C_OPTIONS_REGEX, False
        ),
        "compiler-cpp-options": PclingCachedVariable(
            PCLINT_COMPILER_CPP_OPTIONS_REGEX, False
        ),
    }

    with open(os.path.join(build_path, "CMakeCache.txt"), "r+") as cache_file:
        data = mmap.mmap(cache_file.fileno(), 0)
        for pclint_compiler_config in pclint_compiler_configs.values():
            match = pclint_compiler_config.regex.search(data)
            if pclint_compiler_config.required is True and match is None:
                raise ValueError(
                    f"Could not find {pclint_compiler_config.regex} in the build cache file. This should be assiegned."
                )
            elif pclint_compiler_config.required is False and match is None:
                pass
            else:
                pclint_compiler_config.value = match.group(1).decode("utf-8").rstrip()

    cmake_C_compiler_def_files = glob.glob(
        f"{build_path}/**/CMakeCCompiler.cmake", recursive=True
    )
    if len(cmake_C_compiler_def_files) != 1:
        raise ValueError(
            "Only one CMakeCCompiler.cmake can exist in the build directory,"
        )

    with open(cmake_C_compiler_def_files[0], "r+") as c_compiler_definition_file:
        data = mmap.mmap(c_compiler_definition_file.fileno(), 0)
        match = PCLINT_COMPILER_BIN.search(data)
        if match is None:
            raise ValueError("Could not find C compiler path.")
        else:
            pclint_compiler_configs["compiler-bin"] = PclingCachedVariable(
                PCLINT_COMPILER_BIN, True, match.group(1).decode("utf-8").rstrip()
            )

    logging.debug(
        "Compiler information extracted from build: \n%s",
        pformat({key: val.value for key, val in pclint_compiler_configs.items()}),
    )

    return pclint_compiler_configs


def build_pclint_compiler_configuration(
    pclint_compiler_configs: dict[str, PclingCachedVariable],
    pclint_output_path: str,
    pcpl_config_path: str,
):
    logging.debug("Compiler configuration")
    pclint_compiler_config_cl = [
        f"--{key}={config.value}"
        for key, config in pclint_compiler_configs.items()
        if config.value is not None
    ]
    output_lint_file = os.path.join(
        pclint_output_path, PCLINT_COMPILER_CONFIG_FILE_NAME + ".lnt"
    )
    output_header_file = os.path.join(
        pclint_output_path, PCLINT_COMPILER_CONFIG_FILE_NAME + ".h"
    )
    subprocess.run(
        [
            "python",
            pcpl_config_path,
            *pclint_compiler_config_cl,
            "--generate-compiler-config",
            f"--config-output-lnt-file={output_lint_file}",
            f"--config-output-header-file={output_header_file}",
        ],
        shell=True,
        check=True,
        stderr=subprocess.DEVNULL,
    )

    logging.debug("Compiler Configuration created in %s", output_lint_file)
    return output_lint_file


def build_pclint_project_configuration(
    project_files: list[str] | None,
    compiler_name: str,
    build_path: str,
    pclint_output_path: str,
    pcpl_config_path: str,
) -> Tuple[str, str | None]:

    logging.debug("Project configuration")
    project_config_file_path = os.path.join(
        pclint_output_path, PCLINT_PROJECT_CONFIG_FILE_NAME
    )
    compile_command_file_path = os.path.join(
        build_path, CMAKE_COMPILE_COMMAND_FILE_NAME
    )

    if project_files is not None:
        temporary_file = True
        # generates a temporary compile_command file because somehow
        # --source-pattern does not work in pclp_config.py
        filter = re.compile("|".join([re.escape(x) for x in project_files]))

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as command_filter_file:
            with open(compile_command_file_path) as compile_command_file:
                compile_commands = json.load(compile_command_file)
                filtered_commands = [
                    s for s in compile_commands if filter.match(s["file"])
                ]
                json.dump(filtered_commands, command_filter_file)
                compile_command_file_path_temp = command_filter_file.name
    else:
        temporary_file = False
        compile_command_file_path_temp = compile_command_file_path

    subprocess.run(
        [
            "python",
            pcpl_config_path,
            f"--compiler={compiler_name}",
            f"--compilation-db={compile_command_file_path_temp}",
            f"--config-output-lnt-file={project_config_file_path}",
            "--generate-project-config",
        ],
        shell=True,
        check=True,
        stderr=subprocess.DEVNULL,
    )

    if project_files is not None:
        os.remove(compile_command_file_path_temp)

    logging.debug("Project Configuration created in %s", project_config_file_path)

    return project_config_file_path


def execute_pclint(pclint_path: str, args: list[str], env: dict):
    pcpl64_path = os.path.abspath(os.path.join(pclint_path, PCLINT_LINTER_EXECUTABLE))
    cmd = [pcpl64_path, *args]
    logging.debug("invoking: \n%s", pformat(cmd))
    r = subprocess.run(cmd, shell=True, env=env)
    return r.returncode


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-f",
        "--files",
        action="append",
        type=abs_file_path,
        help="File paths to analyse.",
    )
    parser.add_argument(
        "--build-path",
        required=True,
        type=abs_dir_path,
        help="Path to a folder containg a compile command database.",
    )

    parser.add_argument(
        "--pclint-path",
        required=False,
        type=abs_dir_path,
        help="Path to PCLint binary directory.",
        default=os.path.dirname(shutil.which("pclp64")),
    )

    parser.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
        default="INFO",
    )

    # parse arguments,
    args, pclp_arguments = parser.parse_known_args()

    # setup logging
    logging.basicConfig(level=getattr(logging, args.log_level))

    # Find path for PCLint config script
    pcpl_config_path = os.path.abspath(
        os.path.join(args.pclint_path, PCLINT_CONFIG_SCRIPT_RELATIVE_PATH)
    )
    if not os.path.isfile(pcpl_config_path):
        raise FileNotFoundError(f"Could not find pcpl_config in {args.pclint_path}")

    # Create PCLint confguration output folder
    pclint_output_path = os.path.join(args.build_path, PCLINT_OUTPUT_PATH)
    if not os.path.exists(pclint_output_path):
        os.mkdir(pclint_output_path)

    # extract compiler configuration
    compiler_configuration = extact_compiler_name_from_build(args.build_path)
    compiler_config_file_path = build_pclint_compiler_configuration(
        compiler_configuration, pclint_output_path, pcpl_config_path
    )

    # extract project configuration
    project_config_file_path = build_pclint_project_configuration(
        args.files,
        compiler_configuration["compiler"].value,
        args.build_path,
        pclint_output_path,
        pcpl_config_path,
    )

    pclint_tooling_path = os.path.dirname(os.path.realpath(__file__))
    pclint_lnt_path = os.path.abspath(os.path.join(args.pclint_path, "lnt"))

    env = os.environ.copy()
    env["PCLINT_LNT_PATH"] = pclint_lnt_path
    env["PCLINT_TOOLING_PATH"] = pclint_tooling_path
    env["PCLINT_COMPILER_FILE_PATH"] = compiler_config_file_path
    env["PCLINT_PROJECT_FILE_PATH"] = project_config_file_path

    logging.debug("Linting")
    exec_return = execute_pclint(args.pclint_path, pclp_arguments, env)

    return exec_return


if __name__ == "__main__":
    sys.exit(main())
