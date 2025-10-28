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
    __HAL_RCC_{{ i2c.interface }}_CLK_ENABLE();

    hi2c{{ i2c.num }}.Instance             = {{ i2c.interface }};
    hi2c{{ i2c.num }}.Init.Timing          = {{ i2c.timing_reg }};
    hi2c{{ i2c.num }}.Init.OwnAddress1     = 0;
    hi2c{{ i2c.num }}.Init.AddressingMode  = {{ i2c.addressing_mode }};
    hi2c{{ i2c.num }}.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c{{ i2c.num }}.Init.OwnAddress2     = 0;
    hi2c{{ i2c.num }}.Init.OwnAddress2Masks= I2C_OA2_NOMASK;
    hi2c{{ i2c.num }}.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c{{ i2c.num }}.Init.NoStretchMode   = I2C_NOSTRETCH_DISABLE;

    if (HAL_I2C_Init(&hi2c{{ i2c.num }}) != HAL_OK)
    {
        Error_Handler();
    }

    /* Filters */
    if (HAL_I2CEx_ConfigAnalogFilter(&hi2c{{ i2c.num }}, I2C_ANALOGFILTER_ENABLE) != HAL_OK) { Error_Handler(); }
    if (HAL_I2CEx_ConfigDigitalFilter(&hi2c{{ i2c.num }}, 0) != HAL_OK) { Error_Handler(); }
{% endfor %}
}

/* MSP (opcional): sem GPIO aqui; pinmux está em gpio.c */
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    /* Intencionalmente vazio: GPIO e clocks de GPIO estão em MX_GPIO_Init().
       O clock do periférico é habilitado em MX_I2C_Init(). */
    (void)i2cHandle;
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
