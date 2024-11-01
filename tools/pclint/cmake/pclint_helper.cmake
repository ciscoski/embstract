include_guard()

function(generate_pclint_compiler_config)
    configure_file("${CMAKE_CURRENT_FUNCTION_LIST_DIR}/pclint_compiler_config.json.in" "${CMAKE_BINARY_DIR}/pclint_compiler_config.json" @ONLY)
endfunction()



