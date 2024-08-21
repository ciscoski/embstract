set(CMAKE_C_COMPILER gcc)
set(CMAKE_CXX_COMPILER g++)
set(CMAKE_ASM_COMPILER gcc)

function(target_generate_mapfile TARGET_NAME GENERATE)
if(${GENERATE})
    set(target_map_file_path "$<TARGET_FILE_DIR:${TARGET_NAME}>/${TARGET_NAME}.map")
    target_link_options(${TARGET_NAME} PUBLIC -Xlinker -Map=${target_map_file_path})
    set_property(TARGET ${TARGET_NAME}
        APPEND
        PROPERTY ADDITIONAL_CLEAN_FILES ${target_map_file_path})
endif()
endfunction()

# Add a command to generate firmware in a provided format
function(target_generate_object TARGET_NAME SUFFIX TYPE)
    message(WARNING "This toolchain does not generate other format.")
endfunction()

#Assert if compiler older than required
function(assert_compiler_version)
    if(CMAKE_C_COMPILER_VERSION VERSION_LESS ${GCC_MIN_VERSION})
        message(FATAL_ERROR "arm-none-eabi-gcc version must be ${GCC_MIN_VERSION} or greater. Found version ${CMAKE_C_COMPILER_VERSION}." )
    endif()
endfunction()

set(PCLINT_COMPILER_NAME gcc CACHE STRING "The name of the compiler to be used by pclint.")

set(PCLINT_COMPILER_BIN "${CMAKE_C_COMPILER}" CACHE STRING "Path to the compiler")