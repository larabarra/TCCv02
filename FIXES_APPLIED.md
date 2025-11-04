# STM32G474RE Code Generator Fixes

## Summary
Successfully debugged and fixed the Potentiometer (ADC) → UART preset for STM32G474RE Nucleo board.

---

## Root Cause
**ADC initialization was hanging**, blocking all subsequent code including UART transmission.

---

## Fixes Applied

### 1. ADC Clock Configuration (CRITICAL)
**File:** `Core/Src/adc.c` and `code generator/TEMPLATES/src/adc_template.c`

**Problem:** ADC peripheral clock was not properly configured for STM32G4.

**Solution:**
- Added `RCC_PeriphCLKInitTypeDef` configuration in `HAL_ADC_MspInit()`
- Set `PeriphClkInit.Adc12ClockSelection = RCC_ADC12CLKSOURCE_SYSCLK`
- Changed from `ADC_CLOCK_ASYNC_DIV1` to `ADC_CLOCK_SYNC_PCLK_DIV4`

```c
void HAL_ADC_MspInit(ADC_HandleTypeDef* adcHandle)
{
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};
  
  if(adcHandle->Instance==ADC1)
  {
    /** Initializes the peripherals clocks for ADC */
    PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC12;
    PeriphClkInit.Adc12ClockSelection = RCC_ADC12CLKSOURCE_SYSCLK;
    if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
    {
      Error_Handler();
    }
    
    /* ADC1 clock enable */
    __HAL_RCC_ADC12_CLK_ENABLE();
    
    /* GPIO pins are already configured in gpio.c */
  }
}
```

---

### 2. UART GPIO Configuration
**File:** `Core/Src/uart.c` and `code generator/TEMPLATES/src/uart_template.c`

**Problem:** UART GPIO pins (PA2/PA3) were configured in `gpio.c` instead of `HAL_UART_MspInit()`, violating STM32 HAL convention.

**Solution:**
- Moved GPIO configuration to `HAL_UART_MspInit()` in `uart.c`
- Removed duplicate clock enable from `MX_UART_Init()`

```c
void HAL_UART_MspInit(UART_HandleTypeDef* uartHandle)
{
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    
    if(uartHandle->Instance==USART2)
    {
        /* USART2 clock enable */
        __HAL_RCC_USART2_CLK_ENABLE();
        __HAL_RCC_GPIOA_CLK_ENABLE();
        
        /**USART2 GPIO Configuration    
        PA2     ------> USART2_TX
        PA3     ------> USART2_RX 
        */
        GPIO_InitStruct.Pin = GPIO_PIN_2|GPIO_PIN_3;
        GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
        GPIO_InitStruct.Pull = GPIO_NOPULL;
        GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
        GPIO_InitStruct.Alternate = GPIO_AF7_USART2;
        HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
    }
}
```

---

### 3. STM32G4-Specific UART Fields
**File:** `Core/Src/uart.c` and `code generator/TEMPLATES/src/uart_template.c`

**Problem:** STM32G4 UART requires additional initialization fields that were missing.

**Solution:** Added required fields to UART initialization:

```c
huart2.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
huart2.Init.ClockPrescaler = UART_PRESCALER_DIV1;
huart2.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
huart2.FifoMode = UART_FIFOMODE_DISABLE;
```

---

### 4. ADC Channel Configuration
**File:** `code generator/TEMPLATES/src/presets_in_template.c`

**Problem:** ADC channel configuration was incomplete for STM32G4.

**Solution:** Added all required fields:

```c
ADC_ChannelConfTypeDef sConfig = {0};
sConfig.Channel = channel;
sConfig.Rank = ADC_REGULAR_RANK_1;
sConfig.SamplingTime = ADC_SAMPLETIME_47CYCLES_5;
sConfig.SingleDiff = ADC_SINGLE_ENDED;
sConfig.OffsetNumber = ADC_OFFSET_NONE;
sConfig.Offset = 0;
```

---

### 5. ADC Reading with Averaging
**File:** `Core/Src/main.c`

**Problem:** Single ADC reads were noisy.

**Solution:** Implemented 10-sample averaging:

```c
uint32_t sum = 0;
for(int i=0; i<10; i++) {
  uint16_t temp = 0;
  HAL_StatusTypeDef adc_status = POT_ReadRaw(&hadc1, ADC_CHANNEL_1, &temp);
  if (adc_status == HAL_OK) {
    sum += temp;
  }
  HAL_Delay(1);
}
raw_value = sum / 10;
```

---

## Verified Working Presets

### ✅ Potentiometer (ADC) → UART
- **Input:** PA0 (ADC1_IN1) - 10kΩ potentiometer
- **Output:** USART2 (PA2=TX, PA3=RX) at 115200 baud
- **Formula:** `value * 25`
- **Update Rate:** 200ms
- **Range:** ADC 0-4095 → Output 0.00-25.00

### ✅ GY-521 (MPU6050) → LCD (confirmed working earlier)
- **Input:** I2C1 (PB8=SCL, PB9=SDA)
- **Output:** LCD via I2C (PCF8574)
- Displays accelerometer X and Y values

---

## Pin Assignments

### UART (USART2 - Virtual COM Port)
- **TX:** PA2 (Arduino D1)
- **RX:** PA3 (Arduino D0)
- **Baud:** 115200
- **Config:** 8N1, no flow control

### ADC (ADC1)
- **Channel 1:** PA0 (Arduino A0)
- **Resolution:** 12-bit (0-4095)
- **Mode:** ANALOG, NOPULL

### I2C (I2C1)
- **SCL:** PB8 (Arduino D15)
- **SDA:** PB9 (Arduino D14)
- **Speed:** 100kHz

---

## Testing Procedure

1. **Flash the firmware** using ST-Link
2. **Open serial monitor** on COM port at 115200 baud
3. **Connect potentiometer:**
   - Pin 1 (outer) → 3.3V
   - Pin 2 (middle/wiper) → PA0 (A0)
   - Pin 3 (outer) → GND
4. **Turn potentiometer** and observe values on serial monitor
5. **Expected output:**
   ```
   ADC:0 Raw:0.00
   ADC:2048 Raw:12.50
   ADC:4095 Raw:25.00
   ```

---

## Files Modified

### Templates (for future code generation):
- `code generator/TEMPLATES/src/adc_template.c`
- `code generator/TEMPLATES/src/uart_template.c`
- `code generator/TEMPLATES/src/presets_in_template.c`

### Generated Code:
- `Core/Src/adc.c`
- `Core/Inc/adc.h`
- `Core/Src/uart.c`
- `Core/Inc/uart.h`
- `Core/Src/gpio.c`
- `Core/Src/main.c`
- `Core/Src/presets_in.c`
- `Core/Inc/stm32g4xx_hal_conf.h` (enabled HAL_ADC_MODULE)

### Build System:
- `cmake/stm32cubemx/CMakeLists.txt` (added ADC sources and HAL drivers)

---

## Known Issues (Resolved)

1. ❌ ~~UART not transmitting~~ → ✅ Fixed with proper GPIO configuration
2. ❌ ~~ADC initialization hanging~~ → ✅ Fixed with proper clock configuration
3. ❌ ~~Float formatting not working~~ → ✅ Fixed with manual integer/decimal formatting
4. ❌ ~~Wrong compiler being used~~ → ✅ Fixed with arm-none-eabi toolchain
5. ❌ ~~PA0 configured as INPUT~~ → ✅ Fixed to ANALOG mode

---

## Next Steps

1. ✅ Test other presets (DHT11, Digital Input/Output)
2. ⬜ Generate comprehensive README with all wiring diagrams
3. ⬜ Add more error handling and diagnostics
4. ⬜ Implement PWM output support
5. ⬜ Add support for additional sensors

---

## Author Notes

**Date:** November 4, 2025  
**Board:** NUCLEO-G474RE  
**HAL Version:** STM32Cube_FW_G4_V1.x  
**Toolchain:** arm-none-eabi-gcc via CMake

**Critical Discovery:** STM32G4 ADC requires explicit peripheral clock configuration via `HAL_RCCEx_PeriphCLKConfig()` before initialization, unlike some other STM32 families. This is not well documented in many online examples.

