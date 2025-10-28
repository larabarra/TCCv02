#include "i2c.h"

// --- Handles Declaration ---
{% for i2c in i2c_interfaces %}
I2C_HandleTypeDef hi2c{{ i2c.num }};
{% endfor %}

// --- MX_I2C_Init Function ---
void MX_I2C_Init(void)
{
{% for i2c in i2c_interfaces %}
    /* {{ i2c.interface }} */
    __HAL_RCC_{{ i2c.interface }}_CLK_ENABLE();  // só o clock do PERIFÉRICO aqui

    hi2c{{ i2c.num }}.Instance             = {{ i2c.interface }};
    hi2c{{ i2c.num }}.Init.Timing          = {{ i2c.timing_reg }};
    hi2c{{ i2c.num }}.Init.OwnAddress1     = {{ i2c.own_address1 }};
    hi2c{{ i2c.num }}.Init.AddressingMode  = {{ i2c.addressing_mode }};
    hi2c{{ i2c.num }}.Init.DualAddressMode = {{ i2c.dual_address_mode }};
    hi2c{{ i2c.num }}.Init.OwnAddress2     = {{ i2c.own_address2 }};
    hi2c{{ i2c.num }}.Init.OwnAddress2Masks= {{ i2c.own_address2_masks }};
    hi2c{{ i2c.num }}.Init.GeneralCallMode = {{ i2c.general_call_mode }};
    hi2c{{ i2c.num }}.Init.NoStretchMode   = {{ i2c.no_stretch_mode }};

    if (HAL_I2C_Init(&hi2c{{ i2c.num }}) != HAL_OK)
    {
        Error_Handler();
    }

    /* Filters */
    if (HAL_I2CEx_ConfigAnalogFilter(&hi2c{{ i2c.num }}, I2C_ANALOGFILTER_ENABLE) != HAL_OK) { Error_Handler(); }
    if (HAL_I2CEx_ConfigDigitalFilter(&hi2c{{ i2c.num }}, 0) != HAL_OK) { Error_Handler(); }
{% endfor %}
}

/* MSP: NÃO configurar GPIO aqui (pinmux e __HAL_RCC_GPIOx_CLK_ENABLE ficam no gpio.c) */
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    (void)i2cHandle;
    /* Intencionalmente vazio. Se quiser NVIC/DMA, configure aqui. */
}

/*
 * ----------------------------------------------------------------
 * --- Application-level Read/Write Functions ---
 * ----------------------------------------------------------------
 */

HAL_StatusTypeDef I2C_Write(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t *data, uint16_t size)
{
    {% for i2c in i2c_interfaces %}
    if (hi2c->Instance == {{ i2c.interface }})
    {
        {% if i2c.transferMode == 'POLLING' %}
        return HAL_I2C_Master_Transmit(hi2c, dev_address, data, size, HAL_MAX_DELAY);
        {% elif i2c.transferMode == 'INTERRUPT' %}
        return HAL_I2C_Master_Transmit_IT(hi2c, dev_address, data, size);
        {% elif i2c.transferMode == 'DMA' %}
        return HAL_I2C_Master_Transmit_DMA(hi2c, dev_address, data, size);
        {% else %}
        return HAL_I2C_Master_Transmit(hi2c, dev_address, data, size, HAL_MAX_DELAY);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}

HAL_StatusTypeDef I2C_Read(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t *buffer, uint16_t size)
{
    {% for i2c in i2c_interfaces %}
    if (hi2c->Instance == {{ i2c.interface }})
    {
        {% if i2c.transferMode == 'POLLING' %}
        return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, size, HAL_MAX_DELAY);
        {% elif i2c.transferMode == 'INTERRUPT' %}
        return HAL_I2C_Master_Receive_IT(hi2c, dev_address, buffer, size);
        {% elif i2c.transferMode == 'DMA' %}
        return HAL_I2C_Master_Receive_DMA(hi2c, dev_address, buffer, size);
        {% else %}
        return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, size, HAL_MAX_DELAY);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}

HAL_StatusTypeDef I2C_Read_Register(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t reg_address, uint8_t *buffer)
{
    if (HAL_I2C_Master_Transmit(hi2c, dev_address, &reg_address, 1, HAL_MAX_DELAY) != HAL_OK)
    {
        return HAL_ERROR;
    }
    return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, 1, HAL_MAX_DELAY);
}

HAL_StatusTypeDef I2C_Write_Register(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t reg_address, uint8_t value)
{
    uint8_t data[2] = { reg_address, value };
    return HAL_I2C_Master_Transmit(hi2c, dev_address, data, 2, HAL_MAX_DELAY);
}
