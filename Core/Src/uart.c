#include "uart.h"



// --- MX_UART_Init Function ---
void MX_UART_Init(void)
{
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 9600;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_EVEN;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl = UART_HWCONTROL_RTS_CTS;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        Error_Handler();
    }
}

// --- HAL_UART_MspInit (Low-Level Pin Configuration) ---
void HAL_UART_MspInit(UART_HandleTypeDef* uartHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    if(uartHandle->Instance==USART1)
    {
        /* Peripheral clock enable */
        __HAL_RCC_USART1_CLK_ENABLE();

        /* GPIO Clocks Enable */
__HAL_RCC_GPIOA_CLK_ENABLE();
        /**USART1 GPIO Configuration
PA9     ------> USART1_TX
PA10     ------> USART1_RX
*/
        
        /*Configure GPIO pin : A9 */
        GPIO_InitStruct.Pin = GPIO_PIN_9;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
        HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

        /*Configure GPIO pin : A10 */
        GPIO_InitStruct.Pin = GPIO_PIN_10;
        GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
    }
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
    if (huart->Instance == USART1)
    {
        return HAL_UART_Transmit(huart, data, size, timeout);
    }
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
    if (huart->Instance == USART1)
    {
        return HAL_UART_Receive(huart, buffer, size, timeout);
    }
    return HAL_ERROR;
}
