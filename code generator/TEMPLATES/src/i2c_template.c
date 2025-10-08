#include "i2c.h"

// --- Handles Declaration ---
{% for i2c in i2c_interfaces %}
I2C_HandleTypeDef hi2c{{ i2c.num }};
{% endfor %}

// --- MX_I2C_Init Function ---
void MX_I2C_Init(void)
{
{% for i2c in i2c_interfaces %}
    hi2c{{ i2c.num }}.Instance = {{ i2c.interface }};
    hi2c{{ i2c.num }}.Init.Timing = {{ i2c.timing_reg }};
    hi2c{{ i2c.num }}.Init.OwnAddress1 = {{ i2c.own_address1 }};
    hi2c{{ i2c.num }}.Init.AddressingMode = {{ i2c.addressing_mode }};
    hi2c{{ i2c.num }}.Init.DualAddressMode = {{ i2c.dual_address_mode }};
    hi2c{{ i2c.num }}.Init.OwnAddress2 = {{ i2c.own_address2 }};
    hi2c{{ i2c.num }}.Init.OwnAddress2Masks = {{ i2c.own_address2_masks }};
    hi2c{{ i2c.num }}.Init.GeneralCallMode = {{ i2c.general_call_mode }};
    hi2c{{ i2c.num }}.Init.NoStretchMode = {{ i2c.no_stretch_mode }};
    if (HAL_I2C_Init(&hi2c{{ i2c.num }}) != HAL_OK)
    {
        Error_Handler();
    }
{% endfor %}
}

// --- HAL_I2C_MspInit (Low-Level Pin Configuration) ---
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
{% for i2c in i2c_interfaces %}
    if(i2cHandle->Instance=={{ i2c.interface }})
    {
        __HAL_RCC_GPIO{{ i2c.scl_port_char }}_CLK_ENABLE();
        __HAL_RCC_GPIO{{ i2c.sda_port_char }}_CLK_ENABLE();

        GPIO_InitStruct.Pin = GPIO_PIN_{{ i2c.scl_pin_num }};
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = GPIO_AF{{ i2c.scl_af }}_{{ i2c.interface }};
        HAL_GPIO_Init(GPIO{{ i2c.scl_port_char }}, &GPIO_InitStruct);

        GPIO_InitStruct.Pin = GPIO_PIN_{{ i2c.sda_pin_num }};
        GPIO_InitStruct.Alternate = GPIO_AF{{ i2c.sda_af }}_{{ i2c.interface }};
        HAL_GPIO_Init(GPIO{{ i2c.sda_port_char }}, &GPIO_InitStruct);

        __HAL_RCC_{{ i2c.interface }}_CLK_ENABLE();
    }
{% endfor %}
}