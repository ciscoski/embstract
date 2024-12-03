include(embStract)

add_library(embs_log_stdlib STATIC src/embs_log_stdlib.c)
target_include_directories(embs_log_stdlib PUBLIC api)

embs_set_facade_frontend(embs_log_stdlib embs_log)
