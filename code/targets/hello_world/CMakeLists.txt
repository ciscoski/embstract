include(embStract)

add_executable(hello_world src/main.cpp)
target_compile_features(hello_world PUBLIC cxx_std_11)

# Include modules
find_package(embs_log)
find_package(embs_log_stdlib)
find_package(expl_greatings_localization)

# Facade Configuration
embs_target_link_backend(embs_log embs_log_stdlib)

embs_get_config_target(embs_log_config embs_log)
target_include_directories(${embs_log_config} INTERFACE config)
target_compile_definitions(
    ${embs_log_config}
    INTERFACE
        EMBS_LOG_CONFIG_TWEAK="my_config.h"
)

embs_get_config_target(expl_greatings_localization_config expl_greatings_localization)
target_compile_definitions(
    ${expl_greatings_localization_config}
    INTERFACE
        EXPL_GREATINGS_LOCALIZATION_GREETINGS_MESSAGE="Ciao Mondo"
)
target_include_directories(expl_greatings_localization INTERFACE config)

target_link_libraries(hello_world PRIVATE expl_greatings_localization)
target_link_libraries(hello_world PRIVATE embs_log)
