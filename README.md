# STM32 Project Configuration - LCD Test

## ⚠️ Current Test Mode: LCD Only

Testing LCD communication on I2C1 with "Hello World!" message.
MPU6050 sensor is disabled for this test.

## Pin Configuration Summary

### I2C1 Pins (UPDATED)
| Pin Name | STM32 Pin | Function | Port | Mode | Pull | Speed | Alternate |
|----------|-----------|----------|------|------|------|-------|-----------|
| I2C1_SCL | **PB8** | SCL | GPIOB | AF_OD | PULLUP | VERY_HIGH | GPIO_AF4_I2C1 |
| I2C1_SDA | **PB9** | SDA | GPIOB | AF_OD | PULLUP | VERY_HIGH | GPIO_AF4_I2C1 |

## Hardware Connections

### LCD 20x4 with PCF8574 I2C Backpack

```
LCD Pin → STM32 Pin
────────────────────
VCC     → 5V         ⚠️ Most LCDs need 5V!
GND     → GND
SCL     → PB8        ⚡ NEW PIN!
SDA     → PB9        ⚡ NEW PIN!
```

## 🔍 Troubleshooting Checklist

### 1. **Check Power & Backlight**
- [ ] LCD backlight is ON
- [ ] Using 5V supply (most LCDs require 5V, not 3.3V)
- [ ] Power supply can provide enough current

### 2. **Adjust Contrast**
- [ ] Locate the blue potentiometer on the PCF8574 backpack
- [ ] Turn it slowly with a small screwdriver
- [ ] You should see blocks or text appear

### 3. **Verify I2C Address**

Current address: **0x4E** (0x27 << 1)

If nothing appears, try these common alternatives in `Core/Src/presets_out.c`:

| 7-bit Address | 8-bit (HAL) | To Try |
|--------------|-------------|---------|
| 0x27 | 0x4E | ✅ Currently using |
| 0x3F | 0x7E | Common alternative |
| 0x20 | 0x40 | PCF8574A variant |

**To change address:** Edit line 13 in `Core/Src/presets_out.c`:
```c
#define LCD_ADDR 0x7E  // Try 0x7E if 0x4E doesn't work
```

### 4. **Check Wiring**
- [ ] SCL connected to PB8 (NOT PB6!)
- [ ] SDA connected to PB9 (NOT PB7!)
- [ ] All GND connections are common
- [ ] No loose connections

### 5. **LCD Module Check**
- [ ] Backlight jumper is ON
- [ ] Contrast pot is not at extreme position
- [ ] PCF8574 chip is properly soldered to LCD

## Build Instructions

1. **Save all files** in VS Code
2. **Build & Flash:**
   - Click "Build & Flash" in the UI, OR
   - In VS Code terminal: `cmake --build build --target flash`
3. **Watch the LCD** - "Hello World!" should appear after ~500ms

## Expected Behavior

1. Power on → Backlight turns on
2. After 500ms → LCD initialization
3. "Hello World!" appears on first line
4. Message refreshes every 1 second

## If Still Not Working

### Try Manual I2C Scanner
Add this code to find the correct address:

```c
// In main loop, before LCD init:
for(uint8_t addr = 0x20; addr < 0x80; addr += 2) {
    if(HAL_I2C_IsDeviceReady(&hi2c1, addr, 1, 100) == HAL_OK) {
        // Device found at 'addr' - blink LED or use debugger
    }
}
```

### Common Issues
- **Backlight ON, no text** → Wrong contrast or address
- **No backlight** → Power issue or wrong voltage
- **Intermittent display** → Loose wiring or bad solder joints
- **Garbage characters** → Wrong timing or electrical noise

---
*Last updated: 2025-10-30 - Testing LCD on PB8/PB9*
