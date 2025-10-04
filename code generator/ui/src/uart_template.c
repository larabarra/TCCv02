#include "uart.h"
#include <stddef.h> // Para NULL

// --- Handles Declaration ---
{% for uart in uart_interfaces %}
UART_HandleTypeDef huart{{ uart.num }};
{% endfor %}


// --- MX_UART_Init Functions ---
{% for uart in uart_interfaces %}
void MX_UART{{ uart.num }}_Init(void)
{
    huart{{ uart.num }}.Instance = {{ uart.interface }};
    huart{{ uart.num }}.Init.BaudRate = {{ uart.baud_rate }};
    huart{{ uart.num }}.Init.WordLength = UART_WORDLENGTH_8B;
    huart{{ uart.num }}.Init.StopBits = UART_STOPBITS_1;
    huart{{ uart.num }}.Init.Parity = UART_PARITY_NONE;
    huart{{ uart.num }}.Init.Mode = UART_MODE_TX_RX; // Modo Full Duplex
    huart{{ uart.num }}.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    huart{{ uart.num }}.Init.OverSampling = UART_OVERSAMPLING_16;
    huart{{ uart.num }}.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
    huart{{ uart.num }}.Init.ClockPrescaler = UART_PRESCALER_DIV1;
    huart{{ uart.num }}.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
    if (HAL_UART_Init(&huart{{ uart.num }}) != HAL_OK)
    {
        Error_Handler();
    }
    if (HAL_UARTEx_SetTxFifoThreshold(&huart{{ uart.num }}, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
    {
        Error_Handler();
    }
    if (HAL_UARTEx_SetRxFifoThreshold(&huart{{ uart.num }}, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
    {
        Error_Handler();
    }
    if (HAL_UARTEx_DisableFifoMode(&huart{{ uart.num }}) != HAL_OK)
    {
        Error_Handler();
    }
}
{% endfor %}


// --- HAL_UART_MspInit (Configuração de Pinos de Baixo Nível) ---
void HAL_UART_MspInit(UART_HandleTypeDef* huart)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    
{% for uart in uart_interfaces %}
    {% if loop.first %}if{% else %}else if{% endif %}(huart->Instance == {{ uart.interface }})
    {
        // --- 1. Habilita Clocks das Portas GPIO ---
        __HAL_RCC_GPIO{{ uart.tx_port }}_CLK_ENABLE();
        __HAL_RCC_GPIO{{ uart.rx_port }}_CLK_ENABLE();

        // --- 2. Configuração dos Pinos TX e RX ---
        
        // TX Pin
        GPIO_InitStruct.Pin = GPIO_PIN_{{ uart.tx_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = {{ uart.tx_pull }};
        GPIO_InitStruct.Speed = {{ uart.tx_speed }};
        GPIO_InitStruct.Alternate = {{ uart.tx_af }};
        HAL_GPIO_Init(GPIO{{ uart.tx_port }}, &GPIO_InitStruct);

        // RX Pin
        GPIO_InitStruct.Pin = GPIO_PIN_{{ uart.rx_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = {{ uart.rx_pull }};
        GPIO_InitStruct.Speed = {{ uart.rx_speed }};
        GPIO_InitStruct.Alternate = {{ uart.rx_af }};
        HAL_GPIO_Init(GPIO{{ uart.rx_port }}, &GPIO_InitStruct);
        
        // --- 3. Habilita Clock do UART ---
        __HAL_RCC_USART{{ uart.num }}_CLK_ENABLE();
        
        // --- 4. Habilita Interrupções (Opcional) ---
        HAL_NVIC_SetPriority(USART{{ uart.num }}_IRQn, 0, 0);
        HAL_NVIC_EnableIRQ(USART{{ uart.num }}_IRQn);
    }
{% endfor %}
}