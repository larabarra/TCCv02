#include "i2c.h"

// --- Handles Declaration ---
// Declara os handles para todas as interfaces selecionadas

I2C_HandleTypeDef hi2c1;

I2C_HandleTypeDef hi2c2;


// --- MX_I2C_Init Functions ---
// Gera a função de inicialização de alto nível para cada interface

void MX_I2C1_Init(void)
{
    hi2c1.Instance = I2C1;
    hi2c1.Init.Timing = 0x00503D58; // Exemplo de Timing
    hi2c1.Init.OwnAddress1 = 0;
    hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.OwnAddress2 = 0;
    hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c1) != HAL_OK)
    {
        Error_Handler();
    }
    // Filtros...
    if (HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
    {
        Error_Handler();
    }
}

void MX_I2C2_Init(void)
{
    hi2c2.Instance = I2C2;
    hi2c2.Init.Timing = 0x00503D58; // Exemplo de Timing
    hi2c2.Init.OwnAddress1 = 0;
    hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c2.Init.OwnAddress2 = 0;
    hi2c2.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
    hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c2) != HAL_OK)
    {
        Error_Handler();
    }
    // Filtros...
    if (HAL_I2CEx_ConfigAnalogFilter(&hi2c2, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
    {
        Error_Handler();
    }
}


// ----------------------------------------------------------------
// --- HAL_I2C_MspInit (Configuração de Pinos de Baixo Nível) ---
// ----------------------------------------------------------------
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    RCC_PeriphCLKInitTypeDef PeriphClkInit = {0}; // Para clocks granulares, se necessário


    if(i2cHandle->Instance == I2C1)
    {
        // --- 1. Configuração de Clocks do Periférico (Se necessário) ---
        // Este bloco é fixo para cada interface I2C
        // Ex: PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_I2C1;
        // Ex: HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit);

        // --- 2. Habilita Clocks das Portas GPIO ---
        __HAL_RCC_GPIOO_CLK_ENABLE();
        __HAL_RCC_GPIOO_CLK_ENABLE();
        
        // --- 3. Configuração dos Pinos (SCL e SDA) ---
        
        // SCL Pin
        GPIO_InitStruct.Pin = GPIO_PIN_6;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = 4;
        HAL_GPIO_Init(GPIOO, &GPIO_InitStruct);

        // SDA Pin
        GPIO_InitStruct.Pin = GPIO_PIN_7;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = 4;
        HAL_GPIO_Init(GPIOO, &GPIO_InitStruct);
        
        // --- 4. Habilita Clock do I2C e Interrupções ---
        __HAL_RCC_I2C1_CLK_ENABLE();
        HAL_NVIC_SetPriority(I2C1_EV_IRQn, 0, 0);
        HAL_NVIC_EnableIRQ(I2C1_EV_IRQn);
    }

    else if(i2cHandle->Instance == I2C2)
    {
        // --- 1. Configuração de Clocks do Periférico (Se necessário) ---
        // Este bloco é fixo para cada interface I2C
        // Ex: PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_I2C2;
        // Ex: HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit);

        // --- 2. Habilita Clocks das Portas GPIO ---
        __HAL_RCC_GPIOO_CLK_ENABLE();
        __HAL_RCC_GPIOO_CLK_ENABLE();
        
        // --- 3. Configuração dos Pinos (SCL e SDA) ---
        
        // SCL Pin
        GPIO_InitStruct.Pin = GPIO_PIN_10;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = 4;
        HAL_GPIO_Init(GPIOO, &GPIO_InitStruct);

        // SDA Pin
        GPIO_InitStruct.Pin = GPIO_PIN_11;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = 4;
        HAL_GPIO_Init(GPIOO, &GPIO_InitStruct);
        
        // --- 4. Habilita Clock do I2C e Interrupções ---
        __HAL_RCC_I2C2_CLK_ENABLE();
        HAL_NVIC_SetPriority(I2C2_EV_IRQn, 0, 0);
        HAL_NVIC_EnableIRQ(I2C2_EV_IRQn);
    }

}
// --- HAL_I2C_MspDeInit (Poderia ser gerado aqui também) ---