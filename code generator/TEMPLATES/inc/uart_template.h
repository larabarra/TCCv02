// --- Handles Declaration ---
{% for uart in uart_interfaces %}
UART_HandleTypeDef huart{{ uart.num }};
{% endfor %}

/* --- Function Prototypes --- */
void MX_UART_Init(void);

/* --- Application-level Functions --- */
HAL_StatusTypeDef UART_Transmit(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size, uint32_t timeout);
HAL_StatusTypeDef UART_Receive(UART_HandleTypeDef *huart, uint8_t *buffer, uint16_t size, uint32_t timeout);


#ifdef __cplusplus
}
#endif


