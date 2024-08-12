#!/usr/bin/env python3
"""
Wrapper to run PCLint as a pre-commit hook.

This script will:
1) Extract the compiler type from the CMake build folder.
2) Generate a PCLint project configuration file based on a filtered `compile_commands.json`.
3) Invoke PCLint to analyze the requested files.

This script assumes the following:
* The CMake project (toolchain file) should specify `PCLINT_COMPILER_NAME`, which should be a compiler name present in the 
  PCLint `compilers.yaml` file.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import mmap
from dataclasses import dataclass
from typing import Pattern, Tuple
import glob
import logging
from pprint import pformat
import click
import time
from collections import defaultdict
from watchdog.observers import Observer as WatchdogObserver
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from threading import Event

CMAKE_COMPILE_COMMAND_FILE_NAME = "compile_commands.json"
CMAKE_CACHE_FILE_NAME = "CMakeCache.txt"
CMAKE_COMPILER_CACHE_FILE_NAME = "CMakeCCompiler.cmake"

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

event_file_changed = Event()
build_files_changed = Event()


class ProjectEventHandler(PatternMatchingEventHandler):
    """
    Handles file system events related to project files. Triggers an event when a file is modified.
    """

    def on_modified(self, event):
        logging.debug("%s", event)
        event_file_changed.set()

    @classmethod
    def schedule(cls, observer: BaseObserver, compile_command_file_path: os.PathLike) -> None:
        """
        Schedules the event handler for the specified files in the compile command database.

        :param observer: The observer to which the handler should be attached.
        :param compile_command_file_path: Path to the `compile_commands.json` file.
        """
        with open(compile_command_file_path, "r") as compile_command_file:
            compile_command_data = json.load(compile_command_file)
            list_of_files = [item["file"] for item in compile_command_data]

        collection = defaultdict(list)
        for file in list_of_files:
            folder_path, file_name = os.path.split(file)
            collection[folder_path].append(file_name)

        logging.debug("Scheduling the following files\n%s", pformat(dict(collection)))

        for folder_path, patterns in collection.items():
            observer.schedule(cls(patterns, ignore_directories=True), folder_path)


class BuildPathEventHandler(PatternMatchingEventHandler):
    """
    Handles file system events related to build path files. Triggers an event when build-related files are created, modified, or deleted.
    """

    def __init__(self, build_path: os.PathLike):
        super().__init__(
            patterns=[CMAKE_COMPILE_COMMAND_FILE_NAME, CMAKE_CACHE_FILE_NAME, CMAKE_COMPILER_CACHE_FILE_NAME],
        )
        self.build_path = build_path

    def _check_if_ready(self) -> bool:
        """
        Checks if the necessary build files are present.

        :return: True if all required files are present, False otherwise.
        """
        compile_command_exists = os.path.exists(os.path.join(self.build_path, CMAKE_COMPILE_COMMAND_FILE_NAME))
        cache_file_exists = os.path.exists(os.path.join(self.build_path, CMAKE_CACHE_FILE_NAME))
        compiler_cache_file_exists = (
            True
            if len(glob.glob(f"{self.build_path}/**/{CMAKE_COMPILER_CACHE_FILE_NAME}", recursive=True)) > 0
            else False
        )
        return compile_command_exists and cache_file_exists and compiler_cache_file_exists

    def on_deleted(self, event: FileSystemEvent) -> None:
        logging.debug("%s", event)
        return super().on_deleted(event)

    def on_created(self, event: FileSystemEvent) -> None:
        logging.debug("%s", event)
        if self._check_if_ready():
            build_files_changed.set()

    def on_modified(self, event: FileSystemEvent) -> None:
        logging.debug("%s", event)
        if self._check_if_ready():
            build_files_changed.set()

    @classmethod
    def schedule(cls, observer: BaseObserver, build_path: os.PathLike) -> None:
        """
        Schedules the event handler for build-related files.

        :param observer: The observer to which the handler should be attached.
        :param build_path: Path to the build directory.
        """
        event_handler = cls(build_path)
        observer.schedule(event_handler, build_path, recursive=True)


@dataclass
class PclingCachedVariable:
    """
    Dataclass to store PCLint cached variables.
    """

    regex: Pattern[bytes]
    required: bool
    value: str | None = None


def extract_compiler_name_from_build(build_path: os.PathLike) -> dict[str, PclingCachedVariable]:
    """
    Extracts the compiler name and related configuration from the CMake cache files.

    :param build_path: Path to the build directory.
    :return: Dictionary containing the compiler configuration variables.
    :raises ValueError: If required configuration variables are not found.
    """
    logging.debug("Extracting compiler from build")
    pclint_compiler_configs: dict[str, PclingCachedVariable] = {
        "compiler": PclingCachedVariable(PCLINT_COMPILER_NAME_REGEX, True),
        "compiler-options": PclingCachedVariable(PCLINT_COMPILER_OPTIONS_REGEX, False),
        "compiler-c-options": PclingCachedVariable(PCLINT_COMPILER_C_OPTIONS_REGEX, False),
        "compiler-cpp-options": PclingCachedVariable(PCLINT_COMPILER_CPP_OPTIONS_REGEX, False),
    }

    with open(os.path.join(build_path, CMAKE_CACHE_FILE_NAME), "r+") as cache_file:
        data = mmap.mmap(cache_file.fileno(), 0)
        for pclint_compiler_config in pclint_compiler_configs.values():
            match = pclint_compiler_config.regex.search(data)
            if pclint_compiler_config.required is True and match is None:
                raise ValueError(
                    f"Could not find {pclint_compiler_config.regex} in the build cache file. This should be assigned."
                )
            elif pclint_compiler_config.required is False and match is None:
                pass
            else:
                pclint_compiler_config.value = match.group(1).decode("utf-8").rstrip()

    cmake_C_compiler_def_files = glob.glob(f"{build_path}/**/{CMAKE_COMPILER_CACHE_FILE_NAME}", recursive=True)
    if len(cmake_C_compiler_def_files) != 1:
        raise ValueError(f"Only one {CMAKE_COMPILER_CACHE_FILE_NAME} can exist in the build directory,")

    with open(cmake_C_compiler_def_files[0], "r+") as c_compiler_definition_file:
        data = mmap.mmap(c_compiler_definition_file.fileno(), 0)
        match = PCLINT_COMPILER_BIN.search(data)
        if match is None:
            raise ValueError("Could not find C compiler path.")
        else:
            pclint_compiler_configs["compiler-bin"] = PclingCachedVariable(
                PCLINT_COMPILER_BIN,
                True,
                match.group(1).decode("utf-8").rstrip(),
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
) -> str:
    """
    Builds the PCLint compiler configuration file.

    :param pclint_compiler_configs: Dictionary containing compiler configuration variables.
    :param pclint_output_path: Path to store the PCLint output.
    :param pcpl_config_path: Path to the PCLint configuration script.
    :return: Path to the generated PCLint compiler configuration file.
    """
    logging.debug("Compiler configuration")
    pclint_compiler_config_cl = [
        f"--{key}={config.value}" for key, config in pclint_compiler_configs.items() if config.value is not None
    ]
    output_lint_file = os.path.join(pclint_output_path, PCLINT_COMPILER_CONFIG_FILE_NAME + ".lnt")
    output_header_file = os.path.join(pclint_output_path, PCLINT_COMPILER_CONFIG_FILE_NAME + ".h")
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
    """
    Builds the PCLint project configuration file.

    :param project_files: List of project files to include in the configuration.
    :param compiler_name: Name of the compiler.
    :param build_path: Path to the build directory.
    :param pclint_output_path: Path to store the PCLint output.
    :param pcpl_config_path: Path to the PCLint configuration script.
    :return: Tuple containing the path to the generated project configuration file and the compiler options.
    """
    logging.debug("Project configuration")
    project_config_file_path = os.path.join(pclint_output_path, PCLINT_PROJECT_CONFIG_FILE_NAME)
    compile_command_file_path = os.path.join(build_path, CMAKE_COMPILE_COMMAND_FILE_NAME)

    if project_files is not None:
        temporary_file = True
        # generates a temporary compile_command file because somehow
        # --source-pattern does not work in pclp_config.py
        filter = re.compile("|".join([re.escape(x) for x in project_files]))

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as command_filter_file:
            with open(compile_command_file_path) as compile_command_file:
                compile_commands = json.load(compile_command_file)
                filtered_commands = [s for s in compile_commands if filter.match(s["file"])]
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


def execute_pclint(pclint_path: str, args: list[str], env: dict[str, str]) -> int:
    """
    Executes the PCLint linter with the specified arguments and environment.

    :param pclint_path: Path to the PCLint executable.
    :param args: List of arguments to pass to PCLint.
    :param env: Environment variables for the PCLint execution.
    :return: Exit code from the PCLint process.
    """
    logging.debug("Running PCLint")
    pcpl64_path = os.path.abspath(os.path.join(pclint_path, PCLINT_LINTER_EXECUTABLE))
    cmd = [pcpl64_path, *args]
    logging.debug("invoking: \n%s", pformat(cmd))
    r = subprocess.run(cmd, shell=True, env=env)
    return r.returncode


@click.group()
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="INFO",
    help="Set the logging level",
)
@click.option(
    "--pclint-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    default=os.path.dirname(shutil.which("pclp64")),
    help="Path to PCLint binary directory.",
)
@click.option(
    "--build-path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="Path to a folder containg a compile command database",
)
@click.pass_context
def cli(ctx, log_level, pclint_path, build_path):
    """
    Main command group for setting up and managing PCLint configurations.
    """
    ctx.ensure_object(dict)

    # setup logging
    logging.basicConfig(level=getattr(logging, log_level))

    # Find path for PCLint config script
    pcpl_config_path = os.path.abspath(os.path.join(pclint_path, PCLINT_CONFIG_SCRIPT_RELATIVE_PATH))
    if not os.path.isfile(pcpl_config_path):
        raise FileNotFoundError(f"Could not find pcpl_config in {pclint_path}")

    # Create PCLint confguration output folder
    pclint_output_path = os.path.join(build_path, PCLINT_OUTPUT_PATH)
    if not os.path.exists(pclint_output_path):
        os.mkdir(pclint_output_path)

    ctx.obj["pclint_output_path"] = pclint_output_path
    ctx.obj["pcpl_config_path"] = pcpl_config_path
    ctx.obj["build_path"] = build_path
    ctx.obj["pclint_path"] = pclint_path


@cli.command()
@click.option(
    "--throttle",
    type=float,
    default=1,
    help="Time (in seconds) to wait between file change event and linting execution",
)
@click.option(
    "--restart-on-change",
    type=bool,
    default=False,
    help="If a file changes while the linter is running the process is stopped and restarted",
)
@click.argument("pclint_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def watch(ctx, throttle, restart_on_change, pclint_args):
    """
    Command to watch for file changes and run PCLint accordingly.

    :param build_path: Path to the build directory.
    """
    pclint_output_path = ctx.obj["pclint_output_path"]
    pcpl_config_path = ctx.obj["pcpl_config_path"]
    build_path = ctx.obj["build_path"]
    pclint_path = ctx.obj["pclint_path"]

    compile_command_file_path = os.path.join(build_path, CMAKE_COMPILE_COMMAND_FILE_NAME)

    # clear file change events
    event_file_changed.clear()
    build_files_changed.set()

    # Start the File Watchdog
    watchdog_observer = WatchdogObserver()
    watchdog_observer.start()

    # Schedule an Handler for the CMake configured files
    BuildPathEventHandler.schedule(watchdog_observer, build_path)

    try:
        while True:
            if build_files_changed.is_set():
                build_files_changed.clear()

                # extract compiler configuration
                compiler_configuration = extract_compiler_name_from_build(build_path)
                compiler_config_file_path = build_pclint_compiler_configuration(
                    compiler_configuration, pclint_output_path, pcpl_config_path
                )

                # extract project configuration
                project_config_file_path = build_pclint_project_configuration(
                    [],
                    compiler_configuration["compiler"].value,
                    build_path,
                    pclint_output_path,
                    pcpl_config_path,
                )

                # prepare enviornment
                pclint_tooling_path = os.path.dirname(os.path.realpath(__file__))
                pclint_lnt_path = os.path.abspath(os.path.join(pclint_path, "lnt"))

                env = os.environ.copy()
                env["PCLINT_LNT_PATH"] = pclint_lnt_path
                env["PCLINT_TOOLING_PATH"] = pclint_tooling_path
                env["PCLINT_COMPILER_FILE_PATH"] = compiler_config_file_path
                env["PCLINT_PROJECT_FILE_PATH"] = project_config_file_path

                # remove all listener
                watchdog_observer.unschedule_all()

                BuildPathEventHandler.schedule(watchdog_observer, build_path)
                ProjectEventHandler.schedule(watchdog_observer, compile_command_file_path)

                event_file_changed.set()

            elif event_file_changed.is_set():
                click.echo("File change detected: starting linting")
                event_file_changed.clear()
                execute_pclint(pclint_path, pclint_args, env)
                click.echo("File change detected: end linting")

            time.sleep(throttle)
    except KeyboardInterrupt:
        logging.info("Interrupted by Keyboard interrupt")
    except Exception as exception:
        logging.warning(exception)
    finally:
        watchdog_observer.stop()
    watchdog_observer.join()


@cli.command()
@click.pass_context
@click.argument("pclint_args", nargs=-1, type=click.UNPROCESSED)
def lint(ctx, pclint_args):
    """
    Command to run PCLint on the specified files.

    :param files: List of files to analyze with PCLint.
    :param build_path: Path to the build directory.
    """
    pclint_output_path = ctx.obj["pclint_output_path"]
    pcpl_config_path = ctx.obj["pcpl_config_path"]
    build_path = ctx.obj["build_path"]
    pclint_path = ctx.obj["pclint_path"]

    # extract compiler configuration
    compiler_configuration = extract_compiler_name_from_build(build_path)
    compiler_config_file_path = build_pclint_compiler_configuration(
        compiler_configuration, pclint_output_path, pcpl_config_path
    )

    # extract project configuration
    project_config_file_path = build_pclint_project_configuration(
        [],
        compiler_configuration["compiler"].value,
        build_path,
        pclint_output_path,
        pcpl_config_path,
    )

    pclint_tooling_path = os.path.dirname(os.path.realpath(__file__))
    pclint_lnt_path = os.path.abspath(os.path.join(pclint_path, "lnt"))

    env = os.environ.copy()
    env["PCLINT_LNT_PATH"] = pclint_lnt_path
    env["PCLINT_TOOLING_PATH"] = pclint_tooling_path
    env["PCLINT_COMPILER_FILE_PATH"] = compiler_config_file_path
    env["PCLINT_PROJECT_FILE_PATH"] = project_config_file_path

    exec_return = execute_pclint(pclint_path, pclint_args, env)
    return exec_return


if __name__ == "__main__":
    cli(obj={})
