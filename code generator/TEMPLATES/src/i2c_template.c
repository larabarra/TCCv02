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

/*
 * ----------------------------------------------------------------
 * --- Application-level Read/Write Functions ---
 * ----------------------------------------------------------------
 */

/**
  * @brief  Writes an amount of data to a specific device on the I2C bus.
  * @param  hi2c Pointer to a I2C_HandleTypeDef structure.
  * @param  dev_address Target device address: The device 7-bit address left-shifted.
  * @param  data Pointer to data buffer.
  * @param  size Amount of data to be sent.
  * @retval HAL status.
  */
HAL_StatusTypeDef I2C_Write(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t *data, uint16_t size)
{
    // The template will generate the correct HAL call based on the user's choice in the UI.
    // This logic assumes that for a given I2C instance, only one transfer mode is used.
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
        // Fallback to Polling mode if the selected mode is not recognized.
        return HAL_I2C_Master_Transmit(hi2c, dev_address, data, size, HAL_MAX_DELAY);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR; // Return error if the handle does not match any initialized interface.
}

/**
  * @brief  Reads an amount of data from a specific device on the I2C bus.
  * @param  hi2c Pointer to a I2C_HandleTypeDef structure.
  * @param  dev_address Target device address: The device 7-bit address left-shifted.
  * @param  buffer Pointer to data buffer.
  * @param  size Amount of data to be received.
  * @retval HAL status.
  */
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
        // Fallback to Polling mode if the selected mode is not recognized.
        return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, size, HAL_MAX_DELAY);
        {% endif %}
    }
    {% endfor %}
    return HAL_ERROR;
}

/**
 * @brief Reads a single byte from a specific register of a slave device.
 * @note This is a common pattern for many sensors.
 */
HAL_StatusTypeDef I2C_Read_Register(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t reg_address, uint8_t *buffer)
{
    // First, send the address of the register we want to read.
    if (HAL_I2C_Master_Transmit(hi2c, dev_address, &reg_address, 1, HAL_MAX_DELAY) != HAL_OK)
    {
        return HAL_ERROR;
    }
    // Then, read the value from that register.
    return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, 1, HAL_MAX_DELAY);
}

/**
 * @brief Writes a single byte to a specific register of a slave device.
 */
HAL_StatusTypeDef I2C_Write_Register(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t reg_address, uint8_t value)
{
    uint8_t data[2];
    data[0] = reg_address; // The first byte is the register address.
    data[1] = value;       // The second byte is the value to be written.
    return HAL_I2C_Master_Transmit(hi2c, dev_address, data, 2, HAL_MAX_DELAY);
}