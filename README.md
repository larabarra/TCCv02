# STM32 Project Configuration

## Pin Configuration Summary

### GPIO Pins
| Pin | Function | Port | Mode | Pull | Speed | Alternate |
|-----|----------|------|------|------|-------|----------|
| GY521_SCL | 6 | GPIOB | AF_OD | PULLUP | VERY_HIGH | - |
| GY521_SDA | 7 | GPIOB | AF_OD | PULLUP | VERY_HIGH | - |

### Peripheral Configuration

#### I2C (I2C1)
**Connected Devices:**
- GY521_MPU6050 (Address: 0x68)
- LCD_PCF8574 (Address: 0x27)

### Preset Use Cases
No preset use cases configured.

## Build Instructions

1. **Hardware Setup:** Connect your STM32 board according to the pin configuration above
2. **Build:** Use the "Build & Flash" button in the configuration tool
3. **Manual Build:** 
   ```bash
   cmake -B build
   cmake --build build
   cmake --build build --target flash
   ```

## Generated Files

- `Core/Src/main.c` - Main application code
- `Core/Src/gpio.c` - GPIO configuration
- `Core/Src/i2c.c` - I2C peripheral configuration
- `Core/Src/presets_in.c` - Input sensor functions
- `Core/Src/presets_out.c` - Output functions
- `Core/Inc/` - Header files

---
*Generated on 2025-10-28 22:13:29 by STM32 Code Generator*
