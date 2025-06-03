include_guard(GLOBAL)
include(FetchContent)

# this should be invoked from the top CMakeLists.txt
macro(embs_init target)
    if(${CMAKE_CURRENT_BINARY_DIR} STREQUAL ${CMAKE_CURRENT_SOURCE_DIR})
        message(FATAL_ERROR "Source and build are in the same directory")
    else()
        message(STATUS "Source directory: ${CMAKE_CURRENT_SOURCE_DIR}")
        message(STATUS "Binary directory: ${CMAKE_CURRENT_BINARY_DIR}")
        message(STATUS "CMAKE_SYSTEM_NAME: ${CMAKE_SYSTEM_NAME}")
        message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")
        message(STATUS "CMAKE_TOOLCHAIN_FILE: ${CMAKE_TOOLCHAIN_FILE}")
        message(STATUS "CMAKE_C_COMPILER_ID: ${CMAKE_C_COMPILER_ID}")
        message(STATUS "CMAKE_CXX_COMPILER_ID: ${CMAKE_CXX_COMPILER_ID}")
        message(STATUS "CMAKE_ASM_COMPILER_ID: ${CMAKE_ASM_COMPILER_ID}")
        message(STATUS "CMAKE_SYSROOT: ${CMAKE_SYSROOT}")
    endif()

    set(EMBS_SOURCE_BASE_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
    set(EMBS_SOURCE_EXTERNAL_PATH ${EMBS_SOURCE_BASE_DIRECTORY}/external)
    set(EMBS_SOURCE_LIBS_PATH ${EMBS_SOURCE_BASE_DIRECTORY}/code/libs)
    set(EMBS_SOURCE_APPS_PATH ${EMBS_SOURCE_BASE_DIRECTORY}/code/apps)
    set(EMBS_SOURCE_TARGETS_PATH ${EMBS_SOURCE_BASE_DIRECTORY}/code/targets)

    set(EMBS_BINARY_BASE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})
    set(EMBS_BINARY_EXTERNAL_PATH ${EMBS_BINARY_BASE_DIRECTORY}/external)
    set(EMBS_BINARY_LIBS_PATH ${EMBS_BINARY_BASE_DIRECTORY}/code/libs)
    set(EMBS_BINARY_APPS_PATH ${EMBS_BINARY_BASE_DIRECTORY}/code/apps)
    set(EMBS_BINARY_TARGETS_PATH ${EMBS_BINARY_BASE_DIRECTORY}/code/targets)

    file(
        GLOB_RECURSE sources_list
        CMAKE_CONFIGURE_DEPENDS
        LIST_DIRECTORIES true
        "${EMBS_SOURCE_LIBS_PATH}/*"
        "${EMBS_SOURCE_APPS_PATH}/*"
    )

    # file(GLOB sources_list_nr CMAKE_CONFIGURE_DEPENDS LIST_DIRECTORIES true "${EXTRA_PATH}/*")
    # list(APPEND sources_list ${sources_list_nr})
    foreach(dir ${sources_list})
        if(IS_DIRECTORY ${dir})
            if(EXISTS ${dir}/CMakeLists.txt)
                file(RELATIVE_PATH package_name ${EMBS_SOURCE_LIBS_PATH} ${dir})
                message(STATUS "Processing lib: ${package_name}")

                # doing this to present a common interface to add dependencies for the main target
                FetchContent_Declare(
                    ${package_name}
                    SOURCE_DIR
                    "${dir}"
                    BINARY_DIR
                    "${EMBS_BINARY_LIBS_PATH}/${package_name}"
                    OVERRIDE_FIND_PACKAGE
                )
            endif()
        else()
            continue()
        endif()
    endforeach()

    set(dir "${EMBS_SOURCE_TARGETS_PATH}/${target}")

    if(IS_DIRECTORY ${dir})
        if(EXISTS ${dir}/CMakeLists.txt)
            file(RELATIVE_PATH target_name ${EMBS_SOURCE_TARGETS_PATH} ${dir})
            message(STATUS "Processing target ${target_name}")
            add_subdirectory(${dir})
        endif()
    else()
        message(WARNING "Target ${target} could not be found.")
    endif()
endmacro()

# Facade Helpers
define_property(
    TARGET
    PROPERTY EMBS_FACADE_FRONTEND_TARGET
    BRIEF_DOCS
        "A facade library frontend target name"
)

define_property(
    TARGET
    PROPERTY EMBS_FACADE_BACKEND_TARGET
    BRIEF_DOCS
        "A facade library backend target name"
)

macro(_embs_facade_frontend_name facade_frontend_name facade_name)
    set(${facade_frontend_name} "${facade_name}._frontend")
endmacro()

function(embs_add_facade_library target_name type)
    set(options EXCLUDE_FROM_ALL)
    set(multiValueArgs
        FRONTEND_BASE_DIRS
        FRONTEND_HEADERS
    )

    cmake_parse_arguments(
        args
        "${options}"
        "${oneValueArgs}"
        "${multiValueArgs}"
        ${ARGN}
    )

    _embs_facade_frontend_name(target_frontend_name ${target_name})

    add_library(${target_name} ${type})
    add_library(${target_frontend_name} INTERFACE)

    if(NOT args_FRONTEND_BASE_DIRS)
        set(args_FRONTEND_BASE_DIRS "API")
    endif()

    target_sources(
        ${target_frontend_name}
        INTERFACE
            FILE_SET "frontend_set"
            TYPE HEADERS
            BASE_DIRS ${args_FRONTEND_BASE_DIRS}
    )

    if(args_FRONTEND_HEADERS)
        target_sources(
            ${target_frontend_name}
            INTERFACE
                FILE_SET "frontend_set"
                FILES ${args_FRONTEND_HEADERS}
        )
    endif()

    set_target_properties(
        ${target_name}
        PROPERTIES
            EMBS_FACADE_FRONTEND_TARGET
                ${target_frontend_name}
    )
    target_link_libraries(${target_name} INTERFACE ${target_frontend_name})

    # Variable evaluations are performed immediately for the command to be executed, but evaluations are deferred for
    # the command arguments.
    # see: https://crascit.com/professional-cmake/ 19th version chapter 9.8.3 "Special Cases For Argument Expansion"
    cmake_language(
        EVAL
        CODE
            "cmake_language(
                DEFER
                DIRECTORY ${CMAKE_SOURCE_DIR}
                CALL
                    _embs_check_facade_library_has_backend
                    [[${target_name}]]
            )"
    )
endfunction()

function(embs_set_facade_frontend facade_backend_name facade_name)
    # Check the target_name is a facade library
    get_target_property(
        facade_frontend_name
        ${facade_name}
        EMBS_FACADE_FRONTEND_TARGET
    )

    if(NOT facade_frontend_name)
        message(
            FATAL_ERROR
            "${facade_name} has not been defined as a facade library"
        )
    else()
        target_link_libraries(
            ${facade_backend_name}
            PRIVATE
                ${facade_frontend_name}
        )
    endif()
endfunction()

function(embs_target_link_backend facade_name facade_backend_name)
    set(options)
    set(oneValueArgs)
    set(multiValueArgs)

    cmake_parse_arguments(
        args
        "${options}"
        "${oneValueArgs}"
        "${multiValueArgs}"
        ${ARGN}
    )

    # Check the facade_name is a facade library
    get_target_property(
        is_facade_library
        ${facade_name}
        EMBS_FACADE_FRONTEND_TARGET
    )

    if(NOT is_facade_library)
        message(
            FATAL_ERROR
            "${facade_name} has not been defined as a facade library"
        )
    endif()

    get_target_property(
        backend_target
        ${facade_name}
        EMBS_FACADE_BACKEND_TARGET
    )

    # Check if the faced library has already a defined backend
    if(backend_target)
        message(
            FATAL_ERROR
            "The library ${facade_name} is already associate with the backend ${backend_target}"
        )
    else()
        set_target_properties(
            ${facade_name}
            PROPERTIES
                EMBS_FACADE_BACKEND_TARGET
                    ${facade_backend_name}
        )
    endif()

    # Set direct linking to the top target
    # avoiding to link to intermediate targets
    # see: https://crascit.com/professional-cmake/ 19th version chapter 18.3 "Propagating Up Direct Link Dependencies"
    set(type "$<TARGET_PROPERTY:TYPE>")
    set(head_targets
        EXECUTABLE
        # TODO: do we have to care about other target types ?
        # SHARED_LIBRARY
        # MODULE_LIBRARY
    )
    set(is_head "$<IN_LIST:${type},${head_targets}>")

    set_target_properties(
        ${facade_name}
        PROPERTIES
            INTERFACE_LINK_LIBRARIES_DIRECT
                "$<${is_head}:${facade_backend_name}>"
    )
endfunction()

function(_embs_check_facade_library_has_backend facade_name)
    get_target_property(
        backend_target
        ${facade_name}
        EMBS_FACADE_BACKEND_TARGET
    )

    if(NOT backend_target)
        message(
            FATAL_ERROR
            "The library ${facade_name} has no backend definition"
        )
    endif()
endfunction()

define_property(
    TARGET
    PROPERTY EMBS_CONFIG_TARGET
    BRIEF_DOCS
        "If specified means that the target has defined a target for configuration"
)

function(embs_set_config_target target config_target)
    get_target_property(
        facede_frontend_target
        ${target}
        EMBS_FACADE_FRONTEND_TARGET
    )

    if(facede_frontend_target)
        message(
            FATAL_ERROR
            "${target} is a facade library, the front-end is used as configuration target"
        )
    endif()

    get_target_property(config_target_property ${target} EMBS_CONFIG_TARGET)

    if(config_target_property)
        message(
            FATAL_ERROR
            "${target} already specifies a configuration target"
        )
    endif()

    set_target_properties(
        ${target}
        PROPERTIES
            EMBS_CONFIG_TARGET
                ${config_target}
    )
endfunction()

# Get the configuration target
# if the target is a facade library return the front-end
# if not it return the set target or the target itself if no configuration target is set
macro(embs_get_config_target config_target target)
    get_target_property(
        facede_frontend_target
        ${target}
        EMBS_FACADE_FRONTEND_TARGET
    )

    if(facede_frontend_target)
        set(${config_target} ${facede_frontend_target})
    else()
        get_target_property(config_target_property ${target} EMBS_CONFIG_TARGET)

        if(config_target_property)
            set(${config_target} ${config_target_property})
        else()
            set(${config_target} ${target})
        endif()
    endif()
endmacro()
