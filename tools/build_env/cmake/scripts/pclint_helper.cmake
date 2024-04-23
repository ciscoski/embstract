include_guard()
function(pclint_compiler_config compiler_name)
    set(_options)
    set(_one_value_args)
    set(multi_value_args OPTIONS C_OPTIONS CPP_OPTIONS)
    cmake_parse_arguments(args "${_options}" "${_one_value_args}"
                          "${multi_value_args}" ${ARGN} )

    set(PCLINT_COMPILER_NAME ${compiler_name} CACHE STRING "The name of the compiler to be used by pclint.")
    set(PCLINT_COMPILER_OPTIONS ${args_OPTIONS} CACHE STRING "The name of the compiler to be used by pclint.")
    set(PCLINT_COMPILER_C_OPTIONS ${args_C_OPTIONS} CACHE STRING "The name of the compiler to be used by pclint.")
    set(PCLINT_COMPILER_CPP_OPTIONS ${args_CPP_OPTIONS} CACHE STRING "The name of the compiler to be used by pclint.")
endfunction()