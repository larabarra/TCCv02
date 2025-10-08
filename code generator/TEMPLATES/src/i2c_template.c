#include "i2c.h"

// --- Handles Declaration ---
// Declara os handles para todas as interfaces selecionadas
{% for i2c in i2c_interfaces %}
I2C_HandleTypeDef hi2c{{ i2c.num }};
{% endfor %}

// --- MX_I2C_Init Functions ---
// Gera a função de inicialização de alto nível para cada interface
{% for i2c in i2c_interfaces %}
void MX_I2C{{ i2c.num }}_Init(void)
{
    hi2c{{ i2c.num }}.Instance = {{ i2c.interface }};
    hi2c{{ i2c.num }}.Init.Timing = 0x00503D58; // Exemplo de Timing
    hi2c{{ i2c.num }}.Init.OwnAddress1 = 0;
    hi2c{{ i2c.num }}.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c{{ i2c.num }}.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c{{ i2c.num }}.Init.OwnAddress2 = 0;
    hi2c{{ i2c.num }}.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
    hi2c{{ i2c.num }}.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c{{ i2c.num }}.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c{{ i2c.num }}) != HAL_OK)
    {
        Error_Handler();
    }
    // Filtros...
    if (HAL_I2CEx_ConfigAnalogFilter(&hi2c{{ i2c.num }}, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
    {
        Error_Handler();
    }
}
{% endfor %}

// ----------------------------------------------------------------
// --- HAL_I2C_MspInit (Configuração de Pinos de Baixo Nível) ---
// ----------------------------------------------------------------
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    RCC_PeriphCLKInitTypeDef PeriphClkInit = {0}; // Para clocks granulares, se necessário

{% for i2c in i2c_interfaces %}
    {% if loop.first %}if{% else %}else if{% endif %}(i2cHandle->Instance == {{ i2c.interface }})
    {
        // --- 1. Configuração de Clocks do Periférico (Se necessário) ---
        // Este bloco é fixo para cada interface I2C
        // Ex: PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_I2C{{ i2c.num }};
        // Ex: HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit);

        // --- 2. Habilita Clocks das Portas GPIO ---
        __HAL_RCC_GPIO{{ i2c.scl_port }}_CLK_ENABLE();
        __HAL_RCC_GPIO{{ i2c.sda_port }}_CLK_ENABLE();
        
        // --- 3. Configuração dos Pinos (SCL e SDA) ---
        
        // SCL Pin
        GPIO_InitStruct.Pin = GPIO_PIN_{{ i2c.scl_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = {{ i2c.scl_pull }};
        GPIO_InitStruct.Speed = {{ i2c.scl_speed }};
        GPIO_InitStruct.Alternate = {{ i2c.scl_af }};
        HAL_GPIO_Init(GPIO{{ i2c.scl_port }}, &GPIO_InitStruct);

        // SDA Pin
        GPIO_InitStruct.Pin = GPIO_PIN_{{ i2c.sda_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = {{ i2c.sda_pull }};
        GPIO_InitStruct.Speed = {{ i2c.sda_speed }};
        GPIO_InitStruct.Alternate = {{ i2c.sda_af }};
        HAL_GPIO_Init(GPIO{{ i2c.sda_port }}, &GPIO_InitStruct);
        
        // --- 4. Habilita Clock do I2C e Interrupções ---
        __HAL_RCC_I2C{{ i2c.num }}_CLK_ENABLE();
        HAL_NVIC_SetPriority(I2C{{ i2c.num }}_EV_IRQn, 0, 0);
        HAL_NVIC_EnableIRQ(I2C{{ i2c.num }}_EV_IRQn);
    }
{% endfor %}
}
// --- HAL_I2C_MspDeInit (Poderia ser gerado aqui também) ---