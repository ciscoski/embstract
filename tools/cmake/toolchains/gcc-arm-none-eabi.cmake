set(CMAKE_CROSSCOMPILING true)
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# find the fully qualified path to the tool chain
set(TOOLCHAIN_PREFIX arm-none-eabi-)
find_program(
    TOOLCHAIN_C_COMPILER_PATH
    "${TOOLCHAIN_PREFIX}gcc"
    NO_CACHE
    REQUIRED
)
find_program(
    TOOLCHAIN_CXX_COMPILER_PATH
    "${TOOLCHAIN_PREFIX}g++"
    NO_CACHE
    REQUIRED
)
find_program(
    TOOLCHAIN_ASM_COMPILER_PATH
    "${TOOLCHAIN_PREFIX}gcc"
    NO_CACHE
    REQUIRED
)

set(CMAKE_C_COMPILER ${TOOLCHAIN_C_COMPILER_PATH})
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_CXX_COMPILER_PATH})
set(CMAKE_ASM_COMPILER ${TOOLCHAIN_ASM_COMPILER_PATH})

execute_process(
    COMMAND
        ${CMAKE_C_COMPILER} -print-sysroot
    OUTPUT_VARIABLE CMAKE_SYSROOT
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
cmake_path(SET CMAKE_SYSROOT NORMALIZE ${CMAKE_SYSROOT})

# Add a command to generate firmware in a provided format
function(target_generate_object TARGET_NAME SUFFIX TYPE)
    set(target_object_file_path
        $<TARGET_FILE_DIR:${TARGET_NAME}>/${TARGET_NAME}${SUFFIX}
    )
    add_custom_command(
        TARGET ${TARGET_NAME}
        POST_BUILD
        COMMAND
            ${CMAKE_OBJCOPY} -O ${TYPE}
            "${CMAKE_CURRENT_BINARY_DIR}/$<TARGET_FILE_NAME:${TARGET_NAME}>"
            ${target_object_file_path}
    )
    set_property(
        TARGET
            ${TARGET_NAME}
        APPEND
        PROPERTY
            ADDITIONAL_CLEAN_FILES
                ${target_object_file_path}
    )
endfunction()

# pclint settings
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
