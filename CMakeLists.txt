cmake_minimum_required(VERSION 3.30)

project(
    embstract
    DESCRIPTION "embstract"
    LANGUAGES
        C
        CXX
        ASM
    VERSION 0.0.0
)

set(CMAKE_MESSAGE_CONTEXT_SHOW TRUE)
set(CMAKE_COLOR_DIAGNOSTICS TRUE)
list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/tools/cmake/modules)

include(embStract)

# TODO: provide guidance on TARGET
embs_init(${TARGET})

# PCLint Compiler Configuration
set(PCLINT_HELPER_SCRIPT_PATH ${CMAKE_CURRENT_SOURCE_DIR}/tools/pclint/cmake)
include(${PCLINT_HELPER_SCRIPT_PATH}/pclint_helper.cmake)
generate_pclint_compiler_config()
