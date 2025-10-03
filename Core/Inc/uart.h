#ifndef __UART_H
#define __UART_H

#include "stm32g4xx_hal.h"

#ifdef __cplusplus
 extern "C" {
#endif

// --- Declaração dos Handles e Protótipos ---

extern UART_HandleTypeDef huart1;
void MX_UART1_Init(void);

extern UART_HandleTypeDef huart3;
void MX_UART3_Init(void);


// Protótipos das funções de baixo nível do CubeMX (externas)
void HAL_UART_MspInit(UART_HandleTypeDef* huart);
void HAL_UART_MspDeInit(UART_HandleTypeDef* huart);

#ifdef __cplusplus
}
#endif

#endif /* __UART_H */