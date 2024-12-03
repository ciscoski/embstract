/***********************************************************************************************************************
 * Copyright 2024 Francesco Cervellera
 *
 * SPDX-License-Identifier: Apache-2.0
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * @file
 * @brief Log library
 *
 **********************************************************************************************************************/

/* Include Guard */
#ifndef EMBS_LOG_H
#define EMBS_LOG_H

/* C++ Support */
#if defined(__cplusplus)
extern "C"
{
#endif

/***********************************************************************************************************************
 * System Includes
 **********************************************************************************************************************/

#include <stddef.h>

/***********************************************************************************************************************
 * Project Includes
 **********************************************************************************************************************/

#include "embs_log/config.h"
#include "embs_log/levels.h"
#include "embs_log/options.h"

#include "embs_log_backend/log_backend.h"

/***********************************************************************************************************************
 * Types
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Macros
 **********************************************************************************************************************/

#define EMBS_LOG(level, verbosity, module, flags, /* format string and arguments */...)                                \
    do                                                                                                                 \
    {                                                                                                                  \
        if (EMBS_LOG_ENABLE_IF(level, verbosity, module, flags))                                                       \
        {                                                                                                              \
            EMBS_LOG_HANDLE_LOG(level, module, flags, __VA_ARGS__);                                                    \
        }                                                                                                              \
    } while (0)

#ifndef EMBS_LOG_DEBUG
#define EMBS_LOG_DEBUG(...)                                                                                            \
    EMBS_LOG(EMBS_LOG_LEVEL_DEBUG, EMBS_LOG_LEVEL, EMBS_LOG_MODULE_NAME, EMBS_LOG_FLAGS, __VA_ARGS__)
#endif // EMBS_LOG_DEBUG

#ifndef EMBS_LOG_INFO
#define EMBS_LOG_INFO(...)                                                                                             \
    EMBS_LOG(EMBS_LOG_LEVEL_INFO, EMBS_LOG_LEVEL, EMBS_LOG_MODULE_NAME, EMBS_LOG_FLAGS, __VA_ARGS__)
#endif // EMBS_LOG_INFO

#ifndef EMBS_LOG_WARN
#define EMBS_LOG_WARN(...)                                                                                             \
    EMBS_LOG(EMBS_LOG_LEVEL_WARN, EMBS_LOG_LEVEL, EMBS_LOG_MODULE_NAME, EMBS_LOG_FLAGS, __VA_ARGS__)
#endif // EMBS_LOG_WARN

#ifndef EMBS_LOG_ERROR
#define EMBS_LOG_ERROR(...)                                                                                            \
    EMBS_LOG(EMBS_LOG_LEVEL_ERROR, EMBS_LOG_LEVEL, EMBS_LOG_MODULE_NAME, EMBS_LOG_FLAGS, __VA_ARGS__)
#endif // EMBS_LOG_ERROR

#ifndef EMBS_LOG_CRITICAL
#define EMBS_LOG_CRITICAL(...)                                                                                         \
    EMBS_LOG(EMBS_LOG_LEVEL_CRITICAL, EMBS_LOG_LEVEL, EMBS_LOG_MODULE_NAME, EMBS_LOG_FLAGS, __VA_ARGS__)
#endif // EMBS_LOG_CRITICAL

/***********************************************************************************************************************
 * Function declarations
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Facade declarations
 **********************************************************************************************************************/

/* C++ Support */
#if defined(__cplusplus)
}
#endif

/* Include Guard */
#endif
