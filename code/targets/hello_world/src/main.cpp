#include <iostream>

#include <embs_log/levels.h>

#define EMBS_LOG_MODULE_NAME "ciscoski"
#define EMBS_LOG_LEVEL       EMBS_LOG_LEVEL_DEBUG

#include <embs_log/log.h>
#include <expl_greatings_localization/expl_greatings_localization.h>

auto main() -> int
{
    uint8_t greetings[50];
    greetings_message(greetings, sizeof(greetings));
    EMBS_LOG_INFO("%s %d", greetings, 10);
    EMBS_LOG_DEBUG("%s %d", EXPL_GREATINGS_LOCALIZATION_GREETINGS_MESSAGE, 11);
    return 0;
}
