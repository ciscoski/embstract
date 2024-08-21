cmake_minimum_required(VERSION 3.25)

project(embstracto
        DESCRIPTION "embstracto"
        LANGUAGES C CXX ASM
        VERSION 0.0.0)

set(CMAKE_SCRIPTS_PATH ${CMAKE_CURRENT_SOURCE_DIR}/tools/cmake/scripts)
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/tools/cmake/modules)

if (${CMAKE_BINARY_DIR} STREQUAL ${CMAKE_SOURCE_DIR})
    message(FATAL_ERROR "Source and build are in the same directory")
else()
    message(STATUS "CMAKE_SYSTEM_NAME: ${CMAKE_SYSTEM_NAME}")
    message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")
    message(STATUS "CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")
    message(STATUS "CMAKE_C_COMPILER_ID: ${CMAKE_C_COMPILER_ID}")
    message(STATUS "Source directory: ${CMAKE_SOURCE_DIR}")
    message(STATUS "Binary directory: ${CMAKE_BINARY_DIR}")
endif()

execute_process(COMMAND  "python" "${CMAKE_SOURCE_DIR}/x.py" "${CMAKE_BINARY_DIR}")

cmake_language(DEFER CALL execute_process COMMAND  "python" "${CMAKE_SOURCE_DIR}/x.py" "${CMAKE_BINARY_DIR}")
cmake_language(DEFER ID_VAR id CALL message "Canceled Message")
cmake_language(DEFER CANCEL_CALL ${id})
message("Immediate Message")
set(deferred_message "Deferred Message")

include(${CMAKE_SCRIPTS_PATH}/build_options.cmake)

set(CMAKE_CXX_STANDARD_REQUIRED 17)

set(EXTERNAL_PATH ${CMAKE_CURRENT_SOURCE_DIR}/external)
set(LIBS_PATH ${CMAKE_CURRENT_SOURCE_DIR}/code/libs)
set(APPS_PATH ${CMAKE_CURRENT_SOURCE_DIR}/code/apps)
set(TARGETS_PATH ${CMAKE_CURRENT_SOURCE_DIR}/code/targets)

file(GLOB_RECURSE sources_list CMAKE_CONFIGURE_DEPENDS LIST_DIRECTORIES true "${LIBS_PATH}/*" "${APPS_PATH}/*")
file(GLOB sources_list_nr CMAKE_CONFIGURE_DEPENDS LIST_DIRECTORIES true "${EXTERNAL_PATH}/*")
list(APPEND sources_list ${sources_list_nr})
foreach(dir ${sources_list})
    IF(IS_DIRECTORY ${dir})
        IF(EXISTS ${dir}/CMakeLists.txt)
            file(RELATIVE_PATH rel_dir ${CMAKE_SOURCE_DIR} ${dir})
            message(STATUS "Processing ${rel_dir}")
            add_subdirectory(${dir} EXCLUDE_FROM_ALL)
        ENDIF()
    ELSE()
        CONTINUE()
    ENDIF()
endforeach()

set(dir "${TARGETS_PATH}/${TARGET}" )
IF(IS_DIRECTORY ${dir})
    IF(EXISTS ${dir}/CMakeLists.txt)
        file(RELATIVE_PATH rel_dir ${CMAKE_SOURCE_DIR} ${dir})
        message(STATUS "Processing ${rel_dir}")
        add_subdirectory(${dir})
    ENDIF()
ELSE()
    message(WARNING "Target ${TARGET} could not be found.")
ENDIF()