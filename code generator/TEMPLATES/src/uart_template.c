#include "uart.h"

// --- Handles Declaration ---
{% for uart in uart_interfaces %}
UART_HandleTypeDef huart{{ uart.num }};
{% endfor %}

// --- MX_UART_Init Function ---
void MX_UART_Init(void)
{
{% for uart in uart_interfaces %}
    /* {{ uart.interface }} */
    __HAL_RCC_{{ uart.interface }}_CLK_ENABLE();  // clock do PERIFÉRICO

    huart{{ uart.num }}.Instance        = {{ uart.interface }};
    huart{{ uart.num }}.Init.BaudRate   = {{ uart.baud_rate }};
    huart{{ uart.num }}.Init.WordLength = {{ uart.word_length }};
    huart{{ uart.num }}.Init.StopBits   = {{ uart.stop_bits }};
    huart{{ uart.num }}.Init.Parity     = {{ uart.parity }};
    huart{{ uart.num }}.Init.Mode       = {{ uart.mode }};
    huart{{ uart.num }}.Init.HwFlowCtl  = {{ uart.hw_flow_ctl }};
    huart{{ uart.num }}.Init.OverSampling = {{ uart.oversampling }};

    if (HAL_UART_Init(&huart{{ uart.num }}) != HAL_OK)
    {
        Error_Handler();
    }
{% endfor %}
}

/* MSP: NÃO configurar GPIO aqui (pinmux e __HAL_RCC_GPIOx_CLK_ENABLE ficam no gpio.c) */
void HAL_UART_MspInit(UART_HandleTypeDef* uartHandle)
{
    (void)uartHandle;
    /* Intencionalmente vazio. Se quiser NVIC/DMA, configure aqui. */
}

/*
 * ----------------------------------------------------------------
 * --- Application-level Transmit/Receive Functions ---
 * ----------------------------------------------------------------
 */
HAL_StatusTypeDef UART_Transmit(UART_HandleTypeDef *huart, uint8_t *data, uint16_t size, uint32_t timeout)
{
    {% for uart in uart_interfaces %}
    if (huart->Instance == {{ uart.interface }})
    {
        {% if uart.transferMode == 'POLLING' %}
        return HAL_UART_Transmit(huart, data, size, timeout);
        {% elif uart.transferMode == 'INTERRUPT' %}
        return HAL_UART_Transmit_IT(huart, data, size);
        {% elif uart.transferMode == 'DMA' %}
        return HAL_UART_Transmit_DMA(huart, data, size);
        {% else %}
        return HAL_UART_Transmit(huart, data, size, timeout);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}

HAL_StatusTypeDef UART_Receive(UART_HandleTypeDef *huart, uint8_t *buffer, uint16_t size, uint32_t timeout)
{
    {% for uart in uart_interfaces %}
    if (huart->Instance == {{ uart.interface }})
    {
        {% if uart.transferMode == 'POLLING' %}
        return HAL_UART_Receive(huart, buffer, size, timeout);
        {% elif uart.transferMode == 'INTERRUPT' %}
        return HAL_UART_Receive_IT(huart, buffer, size);
        {% elif uart.transferMode == 'DMA' %}
        return HAL_UART_Receive_DMA(huart, buffer, size);
        {% else %}
        return HAL_UART_Receive(huart, buffer, size, timeout);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}
