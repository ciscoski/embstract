set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(TRIPLET arm-none-eabi)
set(CMAKE_C_COMPILER ${TRIPLET}-gcc)
set(CMAKE_CXX_COMPILER ${TRIPLET}-g++)
set(CMAKE_ASM_COMPILER ${TRIPLET}-gcc)
set(CMAKE_CROSSCOMPILING true)

set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)


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
    set(target_object_file_path $<TARGET_FILE_DIR:${TARGET_NAME}>/${TARGET_NAME}${SUFFIX})
    add_custom_command(TARGET ${TARGET_NAME} POST_BUILD
        COMMAND ${TRIPLET}-objcopy -O ${TYPE}
        "${CMAKE_CURRENT_BINARY_DIR}/$<TARGET_FILE_NAME:${TARGET_NAME}>" ${target_object_file_path})
    set_property(TARGET ${TARGET_NAME}
                 APPEND
                 PROPERTY ADDITIONAL_CLEAN_FILES ${target_object_file_path})
endfunction()

#Assert if compiler older than required
function(assert_compiler_version)
    if(CMAKE_C_COMPILER_VERSION VERSION_LESS ${GCC_MIN_VERSION})
        message(FATAL_ERROR "arm-none-eabi-gcc version must be ${GCC_MIN_VERSION} or greater. Found version ${CMAKE_C_COMPILER_VERSION}." )
    endif()
endfunction()

co