/***********************************************************************************************************************
 * Copyright 2024 Francesco Cervellera
 *
 * SPDX-License-Identifier: Apache-2.0
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * @file config.h
 * @brief EmbStract default log config
 *
 **********************************************************************************************************************/

/* Include Guard */
#ifndef EMBS_LOG_CONFIG_H
#define EMBS_LOG_CONFIG_H

/* C++ Support */
#if defined(__cplusplus)
extern "C"
{
#endif

/**
 * @def EMBS_LOG_CONFIG_TWEAK
 *
 * This expression defines the config tweak file.
 */
#if defined(EMBS_LOG_CONFIG_TWEAK)
#include EMBS_LOG_CONFIG_TWEAK
#endif

/**
 * @def EMBS_LOG_LEVEL_DEFAULT
 *
 * This expression determines the default log level.
 */
#if !defined(EMBS_LOG_LEVEL_DEFAULT)
#define EMBS_LOG_LEVEL_DEFAULT EMBS_LOG_LEVEL_INFO
#endif

/**
 * @def EMBS_LOG_ENABLE_IF
 *
 * This expression determines whether or not the statement is enabled and should be passed to the backend.
 */
#if !defined(EMBS_LOG_ENABLE_IF)
#define EMBS_LOG_ENABLE_IF(level, verbosity, module, flags) ((int32_t)(level) >= (int32_t)(verbosity))
#endif // EMBS_LOG_ENABLE_IF

/* C++ Support */
#if defined(__cplusplus)
}
#endif

/* Include Guard */
#endif
