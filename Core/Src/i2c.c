#include "i2c.h"

// --- Handles Declaration ---
I2C_HandleTypeDef hi2c1;
I2C_HandleTypeDef hi2c2;

// --- MX_I2C_Init Function ---
void MX_I2C_Init(void)
{
    hi2c1.Instance = I2C1;
    hi2c1.Init.Timing = 0x30909DEC;
    hi2c1.Init.OwnAddress1 = 0;
    hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c1.Init.OwnAddress2 = 0;
    hi2c1.Init.OwnAddress2Masks = I2C_OAR2_OA2NOMASK;
    hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c1) != HAL_OK)
    {
        Error_Handler();
    }
    hi2c2.Instance = I2C2;
    hi2c2.Init.Timing = 0x30909DEC;
    hi2c2.Init.OwnAddress1 = 0;
    hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
    hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
    hi2c2.Init.OwnAddress2 = 0;
    hi2c2.Init.OwnAddress2Masks = I2C_OAR2_OA2NOMASK;
    hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
    hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
    if (HAL_I2C_Init(&hi2c2) != HAL_OK)
    {
        Error_Handler();
    }
}

// --- HAL_I2C_MspInit (Low-Level Pin Configuration) ---
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    if(i2cHandle->Instance==I2C1)
    {
        __HAL_RCC_GPIOB_CLK_ENABLE();
        __HAL_RCC_GPIOB_CLK_ENABLE();

        GPIO_InitStruct.Pin = GPIO_PIN_6;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = GPIO_AF4_I2C1;
        HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

        GPIO_InitStruct.Pin = GPIO_PIN_7;
        GPIO_InitStruct.Alternate = GPIO_AF4_I2C1;
        HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

        __HAL_RCC_I2C1_CLK_ENABLE();
    }
    if(i2cHandle->Instance==I2C2)
    {
        __HAL_RCC_GPIOB_CLK_ENABLE();
        __HAL_RCC_GPIOB_CLK_ENABLE();

        GPIO_InitStruct.Pin = GPIO_PIN_10;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_OD;
        GPIO_InitStruct.Pull = GPIO_PULLUP;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
        GPIO_InitStruct.Alternate = GPIO_AF4_I2C2;
        HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

        GPIO_InitStruct.Pin = GPIO_PIN_11;
        GPIO_InitStruct.Alternate = GPIO_AF4_I2C2;
        HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

        __HAL_RCC_I2C2_CLK_ENABLE();
    }
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
    if (hi2c->Instance == I2C1)
    {
        return HAL_I2C_Master_Transmit(hi2c, dev_address, data, size, HAL_MAX_DELAY);
    }
    if (hi2c->Instance == I2C2)
    {
        return HAL_I2C_Master_Transmit(hi2c, dev_address, data, size, HAL_MAX_DELAY);
    }
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
    if (hi2c->Instance == I2C1)
    {
        return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, size, HAL_MAX_DELAY);
    }
    if (hi2c->Instance == I2C2)
    {
        return HAL_I2C_Master_Receive(hi2c, dev_address, buffer, size, HAL_MAX_DELAY);
    }
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