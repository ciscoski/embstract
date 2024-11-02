# clang-format

A tool to format C/C++/Java/JavaScript/JSON/Objective-C/Protobuf/C# code.

## run-clang-format

A wrapper script around clang-format, suitable for linting multiple files
and to use for continuous integration.

This is an alternative API for the clang-format command line.
It runs over multiple files and directories in parallel.
A diff output is produced and a sensible exit code is returned.

## Additional Resources

* Clang-format documentation: [https://clang.llvm.org/docs/ClangFormat.html](https://clang.llvm.org/docs/ClangFormat.html)
* run-clang-format documentation [https://github.com/Sarcasm/run-clang-format](https://github.com/Sarcasm/run-clang-format)
