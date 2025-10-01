#include "i2c.h"

// --- I2C Handles Declaration ---
{% for i2c in i2c_interfaces %}
I2C_HandleTypeDef hi2c{{ i2c.num }};
{% endfor %}


{% for i2c in i2c_interfaces %}
/* I2C{{ i2c.num }} init function */
void MX_I2C{{ i2c.num }}_Init(void)
{
    /* USER CODE BEGIN I2C{{ i2c.num }}_Init 1 */
    /* USER CODE END I2C{{ i2c.num }}_Init 1 */

    hi2c{{ i2c.num }}.Instance = {{ i2c.interface }};
    hi2c{{ i2c.num }}.Init.Timing = 0x00503D58; // Placeholder: {{ i2c.timing }}
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

    /** Configure Analogue filter */
    if (HAL_I2CEx_ConfigAnalogFilter(&hi2c{{ i2c.num }}, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
    {
        Error_Handler();
    }

    /** Configure Digital filter */
    if (HAL_I2CEx_ConfigDigitalFilter(&hi2c{{ i2c.num }}, 0) != HAL_OK)
    {
        Error_Handler();
    }
}
{% endfor %}

// --- I2C MspInit Function (Requires a loop/logic too) ---

void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

{% for i2c in i2c_interfaces %}
    {% if loop.first %}if{% else %}else if{% endif %}(i2cHandle->Instance == {{ i2c.interface }})
    {
        // Initializes the peripherals clocks (Placeholder for complex clock logic)
        PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_I2C{{ i2c.num }};
        PeriphClkInit.I2c{{ i2c.num }}ClockSelection = RCC_I2C{{ i2c.num }}CLKSOURCE_PCLK1;
        if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
        {
            Error_Handler();
        }

        // Enable GPIO Clocks (Assuming SCL/SDA ports are provided in the data)
        __HAL_RCC_GPIO{{ i2c.scl_port }}_CLK_ENABLE();
        __HAL_RCC_GPIO{{ i2c.sda_port }}_CLK_ENABLE();
        
        // --- SCL Pin Configuration ---
        GPIO_InitStruct.Pin = GPIO_PIN_{{ i2c.scl_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
        GPIO_InitStruct.Alternate = {{ i2c.scl_af }};
        HAL_GPIO_Init(GPIO{{ i2c.scl_port }}, &GPIO_InitStruct);

        // --- SDA Pin Configuration ---
        GPIO_InitStruct.Pin = GPIO_PIN_{{ i2c.sda_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
        GPIO_InitStruct.Alternate = {{ i2c.sda_af }};
        HAL_GPIO_Init(GPIO{{ i2c.sda_port }}, &GPIO_InitStruct);
        
        // I2C Clock Enable & Interrupt Init...
        __HAL_RCC_I2C{{ i2c.num }}_CLK_ENABLE();
        HAL_NVIC_SetPriority(I2C{{ i2c.num }}_EV_IRQn, 0, 0);
        HAL_NVIC_EnableIRQ(I2C{{ i2c.num }}_EV_IRQn);
    }
{% endfor %}
}