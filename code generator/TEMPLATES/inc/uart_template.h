#ifndef __UART_H
#define __UART_H

#include "stm32g4xx_hal.h"

#ifdef __cplusplus
 extern "C" {
#endif

// --- Declaração dos Handles e Protótipos ---
{% for uart in uart_interfaces %}
extern UART_HandleTypeDef huart{{ uart.num }};
void MX_UART{{ uart.num }}_Init(void);
{% endfor %}

// Protótipos das funções de baixo nível do CubeMX (externas)
void HAL_UART_MspInit(UART_HandleTypeDef* huart);
void HAL_UART_MspDeInit(UART_HandleTypeDef* huart);

#ifdef __cplusplus
}
#endif

#endif /* __UART_H */