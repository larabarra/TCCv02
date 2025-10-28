#include "i2c.h"

// --- Handles Declaration ---

// --- MX_I2C_Init Function ---
void MX_I2C_Init(void)
{
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
    return HAL_ERROR;
}

HAL_StatusTypeDef I2C_Read(I2C_HandleTypeDef *hi2c, uint16_t dev_address, uint8_t *buffer, uint16_t size)
{
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