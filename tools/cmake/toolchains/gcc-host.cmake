find_program(TOOLCHAIN_C_COMPILER_PATH "gcc" NO_CACHE REQUIRED)
find_program(TOOLCHAIN_CXX_COMPILER_PATH "g++" NO_CACHE REQUIRED)

set(CMAKE_C_COMPILER "${TOOLCHAIN_C_COMPILER_PATH}" CACHE "STRING" "c")
set(CMAKE_ASM_COMPILER "${CMAKE_C_COMPILER}" CACHE "STRING" "C")
set(CMAKE_CXX_COMPILER "${TOOLCHAIN_CXX_COMPILER_PATH}" CACHE "STRING" "c")

execute_process(
    COMMAND
        ${CMAKE_C_COMPILER} -print-sysroot
    OUTPUT_VARIABLE CMAKE_SYSROOT
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
cmake_path(SET CMAKE_SYSROOT NORMALIZE ${CMAKE_SYSROOT})

# Add a command to generate firmware in a provided format
function(target_generate_object TARGET_NAME SUFFIX TYPE)
    message(WARNING "This toolchain does not generate other format.")
endfunction()

# pclint
set(PCLINT_COMPILER_NAME
    gcc
    CACHE STRING
    "The name of the compiler to be used by pclint."
)
set(PCLINT_COMPILER_BIN
    "${CMAKE_C_COMPILER}"
    CACHE STRING
    "Path to the compiler"
)

# compile options
add_compile_options(
    # rabase macro __FILE__ expansion relative to the codebase
    "$<$<COMPILE_LANGUAGE:C,CXX>:-fmacro-prefix-map=${CMAKE_CURRENT_SOURCE_DIR}=.>"
)
