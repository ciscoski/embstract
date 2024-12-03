/***********************************************************************************************************************
 * Copyright 2024 Francesco Cervellera
 *
 * SPDX-License-Identifier: Apache-2.0
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * @file config.h
 * @brief Example configuration
 *
 **********************************************************************************************************************/

/* Include Guard */
#ifndef EXPL_GREATINGS_LOCALIZATION_CONFIG_H
#define EXPL_GREATINGS_LOCALIZATION_CONFIG_H

/* C++ Support */
#if defined(__cplusplus)
extern "C"
{
#endif

#if defined(EXPL_GREATINGS_LOCALIZATION_CONFIG_TWEAK)
#include EXPL_GREATINGS_LOCALIZATION_CONFIG_TWEAK
#endif

#if !defined(EXPL_GREATINGS_LOCALIZATION_GREETINGS_MESSAGE)
#define EXPL_GREATINGS_LOCALIZATION_GREETINGS_MESSAGE "Hello World"
#endif

/* C++ Support */
#if defined(__cplusplus)
}
#endif

/* Include Guard */
#endif