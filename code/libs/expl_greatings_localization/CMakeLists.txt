include(embStract)

add_library(expl_greatings_localization STATIC src/expl_greatings_localization.c)
target_include_directories(expl_greatings_localization PUBLIC api)
target_sources(
    expl_greatings_localization
    PUBLIC
        FILE_SET expl_greatings_localization_api
        TYPE HEADERS
        BASE_DIRS api
        FILES api/expl_greatings_localization/expl_greatings_localization.h api/expl_greatings_localization/config.h
)

add_library(expl_greatings_localization._config INTERFACE)
target_link_libraries(expl_greatings_localization PUBLIC expl_greatings_localization._config)
embs_set_config_target(expl_greatings_localization expl_greatings_localization._config)
