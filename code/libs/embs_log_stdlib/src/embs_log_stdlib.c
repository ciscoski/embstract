/***********************************************************************************************************************
 * Copyright 2024 Francesco Cervellera
 *
 * SPDX-License-Identifier: Apache-2.0
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * @file
 * @brief A simple log backend that uses standard library printf
 *
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * System Includes
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Project Includes
 **********************************************************************************************************************/

/* Implements */
#include "embs_log_stdlib/log_stdlib.h"

/* Requires */
#include "embs_log/levels.h"

#include <stdio.h>

/***********************************************************************************************************************
 * Private Macros
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Private Types
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Private Variables
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Private Function Declarations
 **********************************************************************************************************************/

const char *embs_log_stdlib_level_name(embs_log_level_t level);

/***********************************************************************************************************************
 * Public Function Definitions
 **********************************************************************************************************************/
void embs_log_stdlib(embs_log_level_t level, uint32_t flags, const char *const module_name, const char *const file_name,
                     int line_number, const char *const function_name, const char *const message, ...)
{
    char formatted_string[200] = {0};

    va_list args;
    int stdlib_result;
    va_start(args, message);
    stdlib_result = vsnprintf_s(formatted_string, sizeof(formatted_string), sizeof(formatted_string), message, args);
    va_end(args);

    if (stdlib_result >= 0)
    {
        const char *const level_name = embs_log_stdlib_level_name(level);

        (void)printf("%s [%s %s %s:%d] : %s\n", level_name, module_name, function_name, file_name, line_number,
                     formatted_string);
    }
    else
    {
        // TODO: assert
    }
}
/***********************************************************************************************************************
 * Private Function Definitions
 **********************************************************************************************************************/

const char *embs_log_stdlib_level_name(embs_log_level_t level)
{
    const char *level_name;
    switch (level)
    {
    case EMBS_LOG_LEVEL_DEBUG:
        level_name = "DEBUG";
        break;
    case EMBS_LOG_LEVEL_INFO:
        level_name = "INFO";
        break;
    case EMBS_LOG_LEVEL_WARN:
        level_name = "WARNING";
        break;
    case EMBS_LOG_LEVEL_ERROR:
        level_name = "ERROR";
        break;
    case EMBS_LOG_LEVEL_CRITICAL:
        level_name = "CRITICAL";
        break;

    default:
        level_name = "";
        break;
    }
    return level_name;
}