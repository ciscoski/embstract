# Tools

## Install

Steps

* Create a virtual environment
* Install using `pip install -e D:\Dev\embstracto\tools\python\`

## Linting

### clang-tidy

This document outlines the execution methods for `clang-tidy`, a tool that performs static analysis of C++ code to 
identify potential bugs and enforce coding style guidelines.

The `clang-tidy` configuration is contained in the `clang-tidy.yaml` located in `tools/linting/clang` folder.

#### Requirements

* clang >= 16.0

####  Leveraging a Compilation Database

When using a preset which inherits `Release` or `Debug` a compilation database is generated during the configuration process.
This database stores information about the compiler flags used for each source file. 
Utilizing this database is the recommended approach for linting with `clang-tidy`.

##### Linting all the code for a target:

```bash
run-clang-tidy -config-file ./tools/linting/clang/clang-tidy.yaml -p [target_build_path] [other-options]
```

- `[target_build_path]`: Path to target build path which contains the compilation database
- `[other-options]`: (Optional) Flags to configure `run-clang-tidy` ( run `run-clang-tidy --help` for a full list )

##### Linting selected files used for a target

```bash
clang-tidy -config-file ./tools/linting/clang/clang-tidy.yaml -p [target_build_path] [other-options] <source0> [... <sourceN>]
```

- `[target_build_path]`: Path to target build path which contains the compilation database
- `<source0> [... <sourceN>]`: Path to source code to analyze (there can be multiple)

####  Manual Execution (Without Compilation Database)

!!! warning
    This method is less common but can be useful for smaller projects or testing purposes.
    It requires manually providing the compiler flags used for your project.

```bash
clang-tidy -config-file ./tools/linting/clang/clang-tidy.yaml <compiler_flags> [options] <source0> [... <sourceN>]
```

Run the following command, replacing `<clang-tidy-path>` with the path to your `clang-tidy` executable, `<compiler_flags>` with the actual flags, and `<source_files>` with the list of source files to analyze:

- `<compiler_flags>`: Flags used by your compiler (e.g., -I<include_dir>)
- `[options]`: (Optional) Flags to configure Clang-Tidy (e.g., `--checks` to specify checks to run)
- `<source0> [... <sourceN>]`: List of source files to analyze

!!! Note
    When using the manual execution method, ensure the provided compiler flags accurately reflect those used during compilation to achieve optimal analysis results.

####  Additional Resources

For further details and advanced configurations, refer to the following resources:

* Clang-Tidy documentation: [https://clang.llvm.org/extra/clang-tidy/](https://clang.llvm.org/extra/clang-tidy/)
* Clang-Tidy naming convention documentation: [https://releases.llvm.org/17.0.1/tools/clang/tools/extra/docs/clang-tidy/checks/readability/identifier-naming.html](https://releases.llvm.org/17.0.1/tools/clang/tools/extra/docs/clang-tidy/checks/readability/identifier-naming.html)

### PCLint

This section outlines the execution methods for `pclint`, a tool that performs static analysis of C code to identify potential bugs and enforce coding guidelines.

The `pclint` configuration files are located in the `tools/linting/pclint` folder.

#### Requirements

* PCLintPlus >= 2.0

#### Leveraging a Compilation Database

As for [`clang-tidy`](#leveraging-a-compilation-database), the compilation database generated from CMake is the recommended approach for linting with `pclint`.

##### Linting all the code for a target
```shell
run-pclint --build-path [target_build_path] --pclint-pre-args std.lnt [other-options]
```

- `[target_build_path]`: Path to target build path which contains the compilation database
- `[other-options]`: (Optional) Flags to configure `run-pclint` (run `run-pclint --help` for a full list)