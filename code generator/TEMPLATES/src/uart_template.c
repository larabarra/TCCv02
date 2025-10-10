#include "uart.h"



// --- MX_UART_Init Function ---
void MX_UART_Init(void)
{
{% for uart in uart_interfaces %}
    huart{{ uart.num }}.Instance = {{ uart.interface }};
    huart{{ uart.num }}.Init.BaudRate = {{ uart.baud_rate }};
    huart{{ uart.num }}.Init.WordLength = {{ uart.word_length }};
    huart{{ uart.num }}.Init.StopBits = {{ uart.stop_bits }};
    huart{{ uart.num }}.Init.Parity = {{ uart.parity }};
    huart{{ uart.num }}.Init.Mode = {{ uart.mode }};
    huart{{ uart.num }}.Init.HwFlowCtl = {{ uart.hw_flow_ctl }};
    huart{{ uart.num }}.Init.OverSampling = {{ uart.oversampling }};
    if (HAL_UART_Init(&huart{{ uart.num }}) != HAL_OK)
    {
        Error_Handler();
    }
{% endfor %}
}

// --- HAL_UART_MspInit (Low-Level Pin Configuration) ---
void HAL_UART_MspInit(UART_HandleTypeDef* uartHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
{% for uart in uart_interfaces %}
    if(uartHandle->Instance=={{ uart.interface }})
    {
        /* Peripheral clock enable */
        __HAL_RCC_{{ uart.interface }}_CLK_ENABLE();

        /* GPIO Clocks Enable */
        {% if uart.tx_pin %}__HAL_RCC_{{ uart.tx_pin.port }}_CLK_ENABLE();{% endif %}
        {% if uart.rx_pin and (not uart.tx_pin or uart.rx_pin.port != uart.tx_pin.port) %}__HAL_RCC_{{ uart.rx_pin.port }}_CLK_ENABLE();{% endif %}

        /**{{ uart.interface }} GPIO Configuration
        {% if uart.tx_pin %}P{{ uart.tx_pin.port[4:] }}{{ uart.tx_pin.pin }}     ------> {{ uart.interface }}_TX
        {% endif %}{% if uart.rx_pin %}P{{ uart.rx_pin.port[4:] }}{{ uart.rx_pin.pin }}     ------> {{ uart.interface }}_RX
        {% endif %}*/
        
        {% if uart.tx_pin %}
        /*Configure GPIO pin : {{ uart.tx_pin.port[4:] }}{{ uart.tx_pin.pin }} */
        GPIO_InitStruct.Pin = GPIO_PIN_{{ uart.tx_pin.pin }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
        HAL_GPIO_Init({{ uart.tx_pin.port }}, &GPIO_InitStruct);
        {% endif %}

        {% if uart.rx_pin %}
        /*Configure GPIO pin : {{ uart.rx_pin.port[4:] }}{{ uart.rx_pin.pin }} */
        GPIO_InitStruct.Pin = GPIO_PIN_{{ uart.rx_pin.pin }};
        GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        HAL_GPIO_Init({{ uart.rx_pin.port }}, &GPIO_InitStruct);
        {% endif %}
    }
{% endfor %}
}

/*
 * ----------------------------------------------------------------
 * --- Application-level Transmit/Receive Functions ---
 * ----------------------------------------------------------------
 */

/**
  * @brief  Sends an amount of data in a blocking, interrupt or DMA mode.
  * @param  huart Pointer to a UART_HandleTypeDef structure.
  * @param  data Pointer to data buffer.
  * @param  size Amount of data to be sent.
  * @param  timeout Timeout duration for blocking mode.
  * @retval HAL status.
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
        // Fallback to Polling mode if the selected mode is not recognized.
        return HAL_UART_Transmit(huart, data, size, timeout);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}

/**
  * @brief  Receives an amount of data in a blocking, interrupt or DMA mode.
  * @param  huart Pointer to a UART_HandleTypeDef structure.
  * @param  buffer Pointer to data buffer.
  * @param  size Amount of data to be received.
  * @param  timeout Timeout duration for blocking mode.
  * @retval HAL status.
  */
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
        // Fallback to Polling mode if the selected mode is not recognized.
        return HAL_UART_Receive(huart, buffer, size, timeout);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}

