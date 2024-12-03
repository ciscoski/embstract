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
#ifndef EXPL_GREATINGS_LOCALIZATION_H
#define EXPL_GREATINGS_LOCALIZATION_H

/* C++ Support */
#if defined(__cplusplus)
extern "C"
{
#endif

/***********************************************************************************************************************
 * System Includes
 **********************************************************************************************************************/

#include <stddef.h>
#include <stdint.h>

/***********************************************************************************************************************
 * Project Includes
 **********************************************************************************************************************/

#include "expl_greatings_localization/config.h"

/***********************************************************************************************************************
 * Types
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Macros
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Function declarations
 **********************************************************************************************************************/

/***********************************************************************************************************************
 * Facade declarations
 **********************************************************************************************************************/

void greetings_message(uint8_t *const message_buffer, size_t message_size);

/* C++ Support */
#if defined(__cplusplus)
}
#endif

/* Include Guard */
#endif