/***********************************************************************************************************************
 * Copyright 2024 Francesco Cervellera
 *
 * SPDX-License-Identifier: Apache-2.0
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * @file options.h
 * @brief EmbStract options
 *
 * This file defines macros used to control the behavior of embs_log statements.
 * File that use embs_log may define these macros BEFORE any header are included to customize embs_log
 *
 * @todo: add example
 **********************************************************************************************************************/

/* Include Guard */
#ifndef EMBS_LOG_OPTIONS_H
#define EMBS_LOG_OPTIONS_H

/* C++ Support */
#if defined(__cplusplus)
extern "C"
{
#endif

#if !defined(EMBS_LOG_MODULE_NAME)
#define EMBS_LOG_MODULE_NAME ""
#endif

#if !defined(EMBS_LOG_LEVEL)
#define EMBS_LOG_LEVEL EMBS_LOG_LEVEL_DEFAULT
#endif

#if !defined(EMBS_LOG_FLAGS)
#define EMBS_LOG_FLAGS (0U)
#endif

/* C++ Support */
#if defined(__cplusplus)
}
#endif

/* Include Guard */
#endif
