
// --- Handles Declaration ---
#include "main.h"

#include <stdint.h>

UART_HandleTypeDef huart1;

/* --- Application-level Functions --- */
HAL_StatusTypeDef UART_Transmit(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef UART_Receive(UART_HandleTypeDef *huart, uint8_t *buffer, uint16_t size, uint32_t timeout);

/* --- Function Prototypes --- */
void MX_UART_Init(void);




#ifdef __cplusplus
#endif /* __UART_H__ */
