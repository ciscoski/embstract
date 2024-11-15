find_program(TOOLCHAIN_C_COMPILER_PATH "gcc" NO_CACHE REQUIRED)
find_program(TOOLCHAIN_CXX_COMPILER_PATH "g++" NO_CACHE REQUIRED)

set(CMAKE_C_COMPILER TOOLCHAIN_C_COMPILER_PATH)
set(CMAKE_CXX_COMPILER TOOLCHAIN_CXX_COMPILER_PATH)

# Add a command to generate firmware in a provided format
function(target_generate_object TARGET_NAME SUFFIX TYPE)
    message(WARNING "This toolchain does not generate other format.")
endfunction()


set(PCLINT_COMPILER_NAME gcc CACHE STRING "The name of the compiler to be used by pclint.")
set(PCLINT_COMPILER_BIN "${CMAKE_C_COMPILER}" CACHE STRING "Path to the compiler")