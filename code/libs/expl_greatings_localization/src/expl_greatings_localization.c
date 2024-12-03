
#include "expl_greatings_localization/expl_greatings_localization.h"
#include "expl_greatings_localization/config.h"
#include <assert.h>
#include <string.h>

void greetings_message(uint8_t *const message_buffer, size_t message_size)
{
    assert(message_buffer != NULL);
    strncpy(message_buffer, EXPL_GREATINGS_LOCALIZATION_GREETINGS_MESSAGE, message_size - 1);
}