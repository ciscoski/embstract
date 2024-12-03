include(embStract)

embs_add_facade_library(
    embs_log
    INTERFACE
    FRONTEND_HEADERS
        api/embs_log/config.h
        api/embs_log/levels.h
        api/embs_log/log.h
        api/embs_log/options.h
)
