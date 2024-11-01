#!/usr/bin/env python3
"""
Wrapper to run PCLint for development purposes.

This script will:
1) Extract the compiler configuration from a build rendered JSON file `pclint_compiler_config.json`
2) Generate a PCLint project configuration file based on `compile_commands.json`.
3) Invoke PCLint to analyze the requested files.

The script can be run in one shot mode and in watch mode.
"""

import json
import logging
import os
import shutil
import subprocess
import time
from collections import defaultdict
from pprint import pformat
from threading import Event


import click
from jsonschema import validate as JSONvalidate
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer as WatchdogObserver
from watchdog.observers.api import BaseObserver

# CONSTANTS

BUILD_COMPILE_COMMANDS_FILE_NAME = "compile_commands.json"
BUILD_GENERATED_COMPILER_CONFIG_JSON_FILE_NAME = "pclint_compiler_config.json"
BUILD_GENERATED_COMPILER_CONFIG_JSON_SCHEMA_FILE_NAME = "pclint_compiler_config.schema.json"

PCLINT_CONFIG_SCRIPT_RELATIVE_PATH = "config/pclp_config.py"
PCLINT_COMPILER_CONFIG_FILE_NAME = "pclint_compiler_config"
PCLINT_LINTER_EXECUTABLE = "pclp64"
PCLINT_OUTPUT_PATH = ".pclint"
PCLINT_PROJECT_CONFIG_FILE_NAME = "pclint_project_config.lnt"


class ProjectFilesEventHandler(PatternMatchingEventHandler):
    """
    Handles file system events related to project files. Triggers an event when a file is modified.
    """

    def __init__(
        self,
        *,
        event: Event,
        patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self.event = event

    def on_modified(self, event):
        logging.debug("%s", event)
        self.event.set()

    @classmethod
    def schedule(cls, observer: BaseObserver, event: Event, compile_command_file_path: os.PathLike) -> None:
        """
        Schedules the event handler for the specified files in the compile command database.

        :param observer: The observer to which the handler should be attached.
        :param event: The event to trigger
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
            event_handler = cls(event=event, patterns=patterns, ignore_directories=True)
            observer.schedule(event_handler, folder_path)


class BuildFilesEventHandler(PatternMatchingEventHandler):
    """
    Handles file system events related to build path files. Triggers an event when build-related files are created, modified, or deleted.
    """

    def __init__(
        self,
        *,
        event: Event,
        build_path: os.PathLike,
        patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
    ):
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )

        self.build_path = build_path
        self.event = event

    def _check_if_ready(self) -> bool:
        """
        Checks if the necessary build files are present.

        :return: True if all required files are present, False otherwise.
        """
        compile_command_exists = os.path.exists(os.path.join(self.build_path, BUILD_COMPILE_COMMANDS_FILE_NAME))
        compiler_configuration_exists = os.path.exists(
            os.path.join(self.build_path, BUILD_GENERATED_COMPILER_CONFIG_JSON_FILE_NAME)
        )
        return compile_command_exists and compiler_configuration_exists

    def on_deleted(self, event: FileSystemEvent) -> None:
        logging.debug("%s", event)
        return super().on_deleted(event)

    def on_created(self, event: FileSystemEvent) -> None:
        logging.debug("%s", event)
        if self._check_if_ready():
            self.event.set()

    def on_modified(self, event: FileSystemEvent) -> None:
        logging.debug("%s", event)
        if self._check_if_ready():
            self.event.set()

    @classmethod
    def schedule(cls, observer: BaseObserver, event: Event, build_path: os.PathLike) -> None:
        """
        Schedules the event handler for build-related files.

        :param observer: The observer to which the handler should be attached.
        :param event: The event to trigger
        :param build_path: Path to the build directory.
        """
        event_handler = cls(
            event=event,
            build_path=build_path,
            patterns=[BUILD_COMPILE_COMMANDS_FILE_NAME, BUILD_GENERATED_COMPILER_CONFIG_JSON_FILE_NAME],
            ignore_directories=True,
        )
        observer.schedule(event_handler, build_path)


class RunPCLint:
    def __init__(
        self,
        pclint_output_path: os.PathLike,
        pcpl_config_path: os.PathLike,
        build_path: os.PathLike,
        pclint_path: os.path,
    ):
        self.pclint_output_path = pclint_output_path
        self.pcpl_config_path = pcpl_config_path
        self.build_path = build_path
        self.pclint_path = pclint_path

    def extract_and_validate_compiler_configuration_from_build(self) -> dict[str, str]:
        # open schema
        compiler_config_schema_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), BUILD_GENERATED_COMPILER_CONFIG_JSON_SCHEMA_FILE_NAME
        )
        with open(compiler_config_schema_file_path, "r") as compiler_config_schema_file:
            compiler_configuration_schema = json.load(compiler_config_schema_file)

        # open configuration
        compiler_config_file_path = os.path.join(self.build_path, BUILD_GENERATED_COMPILER_CONFIG_JSON_FILE_NAME)
        with open(compiler_config_file_path, "r") as pclint_compiler_config_file:
            compiler_configuration: dict = json.load(pclint_compiler_config_file)

        # validate configuration
        JSONvalidate(compiler_configuration, compiler_configuration_schema)

        return compiler_configuration

    def build_pclint_compiler_configuration(
        self,
        compiler_configuration: dict[str, str],
    ) -> str:
        logging.debug("Compiler configuration")
        pclint_compiler_config_cl = [f"--{key}={value}" for key, value in compiler_configuration.items() if value != ""]
        output_lint_file = os.path.join(self.pclint_output_path, PCLINT_COMPILER_CONFIG_FILE_NAME + ".lnt")
        output_header_file = os.path.join(self.pclint_output_path, PCLINT_COMPILER_CONFIG_FILE_NAME + ".h")
        subprocess.run(
            [
                "python",
                self.pcpl_config_path,
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
        self,
        compiler_configuration: dict[str, str],
    ) -> str:
        logging.debug("Project configuration")
        compiler = compiler_configuration["compiler"]
        project_config_file_path = os.path.join(self.pclint_output_path, PCLINT_PROJECT_CONFIG_FILE_NAME)
        compile_command_file_path = os.path.join(self.build_path, BUILD_COMPILE_COMMANDS_FILE_NAME)

        subprocess.run(
            [
                "python",
                self.pcpl_config_path,
                f"--compiler={compiler}",
                f"--compilation-db={compile_command_file_path}",
                f"--config-output-lnt-file={project_config_file_path}",
                "--generate-project-config",
            ],
            shell=True,
            check=True,
            stderr=subprocess.DEVNULL,
        )

        logging.debug("Project Configuration created in %s", project_config_file_path)

        return project_config_file_path

    def prepare_pclint_execution_enviornment(self) -> dict[str, str]:
        # extract compiler configuration
        compiler_configuration = self.extract_and_validate_compiler_configuration_from_build()

        # build pclint compiler configuration
        compiler_config_file_path = self.build_pclint_compiler_configuration(compiler_configuration)

        # extract project configuration
        project_config_file_path = self.build_pclint_project_configuration(compiler_configuration)

        pclint_lnt_path = os.path.abspath(os.path.join(self.pclint_path, "lnt"))
        pclint_tooling_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config")

        env = os.environ.copy()
        env["PCLINT_COMPILER_FILE_PATH"] = compiler_config_file_path
        env["PCLINT_PROJECT_FILE_PATH"] = project_config_file_path
        env["PCLINT_LNT_PATH"] = pclint_lnt_path
        env["PCLINT_TOOLING_PATH"] = pclint_tooling_path

        return env

    def execute_pclint(
        self,
        args: list[str],
        env: dict[str, str],
    ) -> int:
        logging.debug("Running PCLint")
        pcpl64_path = os.path.abspath(os.path.join(self.pclint_path, PCLINT_LINTER_EXECUTABLE))
        cmd = [pcpl64_path, *args]
        logging.debug("invoking: \n%s", pformat(cmd))
        r = subprocess.run(cmd, shell=True, env=env)
        return r.returncode

    def lint(
        self,
        pclint_args: list[str],
    ) -> int:
        env = self.prepare_pclint_execution_enviornment()
        exec_return = self.execute_pclint(pclint_args, env)
        return exec_return

    def watch(
        self,
        throttle: int,
        pclint_args: list[str],
    ) -> int:

        project_files_changed_event = Event()
        build_files_changed_event = Event()

        ret_val: int = 0
        compile_command_file_path = os.path.join(self.build_path, BUILD_COMPILE_COMMANDS_FILE_NAME)

        # clear file change events
        project_files_changed_event.clear()
        build_files_changed_event.set()

        # Start the File Watchdog
        watchdog_observer = WatchdogObserver()
        watchdog_observer.start()

        try:
            while True:
                if build_files_changed_event.is_set():
                    build_files_changed_event.clear()

                    env = self.prepare_pclint_execution_enviornment()

                    # remove all listener
                    watchdog_observer.unschedule_all()

                    BuildFilesEventHandler.schedule(watchdog_observer, build_files_changed_event, self.build_path)
                    ProjectFilesEventHandler.schedule(
                        watchdog_observer, project_files_changed_event, compile_command_file_path
                    )

                    project_files_changed_event.set()

                elif project_files_changed_event.is_set():
                    click.echo("File change detected: starting linting")
                    project_files_changed_event.clear()
                    self.execute_pclint(pclint_args, env)
                    click.echo("File change detected: end linting")

                time.sleep(throttle)
        except KeyboardInterrupt:
            logging.info("Interrupted by Keyboard interrupt")
        except Exception as exception:
            logging.exception(exception)
            ret_val = 1
        finally:
            watchdog_observer.stop()

        watchdog_observer.join()
        return ret_val


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
def cli(ctx: click.Context, log_level: str, pclint_path: os.PathLike, build_path: os.PathLike):
    # setup logging
    logging.basicConfig(level=getattr(logging, log_level))

    # Find path for PCLint config script
    pcpl_config_path = os.path.abspath(os.path.join(pclint_path, PCLINT_CONFIG_SCRIPT_RELATIVE_PATH))
    if not os.path.isfile(pcpl_config_path):
        raise FileNotFoundError(f"Could not find pcpl_config.py in {pclint_path}")

    # Create PCLint confguration output folder
    pclint_output_path = os.path.join(build_path, PCLINT_OUTPUT_PATH)
    if not os.path.exists(pclint_output_path):
        os.mkdir(pclint_output_path)

    ctx.obj = RunPCLint(pclint_output_path, pcpl_config_path, build_path, pclint_path)


@cli.command(name="watch")
@click.option(
    "--throttle",
    type=float,
    default=1,
    help="Time (in seconds) to wait between file change event and linting execution",
)
@click.argument("pclint_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def cli_watch(ctx: click.Context, throttle: float, pclint_args: list[str]) -> int:
    """
    Watch the project files and run the linter everytime a file changes.
    """
    if not isinstance(ctx.obj, RunPCLint):
        raise TypeError("The conect object is not an instance of RunPCLint")
    return ctx.obj.watch(throttle, pclint_args)


@cli.command(name="lint")
@click.pass_context
@click.argument("pclint_args", nargs=-1, type=click.UNPROCESSED)
def cli_lint(ctx: click.Context, pclint_args: list[str]) -> int:
    """
    Lint the project.
    """
    if not isinstance(ctx.obj, RunPCLint):
        raise TypeError("The conect object is not an instance of RunPCLint")
    return ctx.obj.lint(pclint_args)


if __name__ == "__main__":
    cli()
