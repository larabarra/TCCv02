#include "i2c.h"

// --- Handles Declaration ---
// Declara os handles para todas as interfaces selecionadas


// --- MX_I2C_Init Functions ---
// Gera a função de inicialização de alto nível para cada interface


// ----------------------------------------------------------------
// --- HAL_I2C_MspInit (Configuração de Pinos de Baixo Nível) ---
// ----------------------------------------------------------------
void HAL_I2C_MspInit(I2C_HandleTypeDef* i2cHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    RCC_PeriphCLKInitTypeDef PeriphClkInit = {0}; // Para clocks granulares, se necessário


}
// --- HAL_I2C_MspDeInit (Poderia ser gerado aqui também) ---