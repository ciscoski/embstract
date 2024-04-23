# Folder structure

This project uses a folder structure inspired by (The Pitchfork Layout)[https://github.com/vector-of-bool/pitchfork].
The changes in place are mostly to adapt to embedded projects.

## build/

A special directory that should not be considered part of the source of the project.
Used for storing ephemeral build results, must not be checked into source control.
If using source control, must be ignored using source control ignore-lists.

## code

### libs/

The `libs/` directory is a [submodule root](#submodules).

All the submodules in the `libs/` directory constitute the embedded `platform` onto which the application will execute.
This can contain:

* vendor SDK abstractions
* BSP definitions
* device drivers
* utilities (circular buffers, debugging functionalities, linked list, PID implementation etc)

### apps/

The `libs/` directory is a [submodule root](#submodules).
Each subfolder in the `apps/` directory defines an `application` which will run on one or more `targets`.

The `application` can use one or more modules defined in the `platform` (`libs/`).
It should use only the public API offered by the `platform`, the user should avoid referencing their implementation.

### targets/

The `targets/` folder contains the definition of executables `targets`.

Each `target` is defined as:

* a permutation of multiple `libs/` submodules implementation
* `external/` submodules
* one `application`.

For example, a target can define an `application` that can run on a Cortex-M-based architecture meanwhile another target can define the same `application` running on a Windows machine.

A `target` has the responsibility of all the compatible toolchains and respective parameters for each library and application.

!!! Note 
    A `target` without an application can exist, this is usually used for testing or to sandbox development experimentation.

## docs/

This directory is not required.

The `docs/` directory is designated to contain project documentation. The documentation process, tools, and layout is not prescribed by this document.

## external/

This directory is not required.

The `external/` directory is reserved for embedding external projects.
Each embedded project should occupy a single subdirectory of `external/`.

This directory may be automatically populated, either partially or completely, by tools (eg. git submodules, subtree) as part of a build process.

!!! Note
    For medical device projects which follow [IEC 62304](https://en.wikipedia.org/wiki/IEC_62304) extra can be used to contain SOUP.
    The content of each external module should not be changed from within the project.

## tools/

This directory is not required.

The tools/ directory is designated for holding extra scripts and tools related to developing and contributing to the project. For example, turn-key build scripts, linting scripts, code-generation scripts, test scripts, or other tools that may be useful to a project development.

The contents of this directory should not be relevant to a project consumer.

## Library Source Layout

A library source tree refers to the layout of source code files that comprise a single library, which is a collection of code that is exposed to the library’s consumer.

The pitchfork layout supports two different methods of placing headers in a single library: separate and merged.

This project uses `Separate Header Placement` where the public APIs are located in the `api/` folder.

## Submodules

A submodule is represented as a subdirectory of the project which may contain the following directories:

* `src/` for submodule sources
* `api/` for submodule includes
* `tests/` for submodule tests
* `data/` for submodule data
* `examples/` for examples
* `docs/` for submodule documentation


