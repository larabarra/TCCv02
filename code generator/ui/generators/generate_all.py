# generate_all.py

from collections import defaultdict
import re
from pathlib import Path
from datetime import datetime

# Import the modular generator scripts from the same package.
from . import gpio_generator
from . import i2c_generator
from . import uart_generator
from . import main_generator
from . import presets_generator

def _gpio_list_from_pinout(pinout_config: dict) -> list[dict]:
    """
    Backward compatibility: if 'gpio' doesn't exist, tries to build the list from
    pinout_config['peripherals'] (when it still came grouped by type).
    Always returns a list of pins (dicts with port/pin/mode/pull/speed/...).
    """
    if not pinout_config:
        return []
    if "gpio" in pinout_config:
        return pinout_config.get("gpio", [])

    # Legacy mode: search within peripherals -> type == "GPIO"
    all_gpio = []
    for blk in pinout_config.get("peripherals", []):
        if blk.get("type") == "GPIO":
            all_gpio.extend(blk.get("pins", []))
    return all_gpio


def generate_project_files(pinout_config: dict, peripheral_settings: dict, preset_settings: dict | None = None) -> list[str]:
    """Generate STM32 project files.
    
    Workflow:
      1) GPIO (with pinout_config['gpio'])
      2) I2C/UART (with peripheral_settings)
      3) PRESETS (if preset_settings["cases"] exists)
      4) main.c/h
    """
    all_generated_files = []

    # 1) GPIO
    try:
        print("--- Processing: GPIO (MX_GPIO_Init) ---")
        files_gpio = gpio_generator.generate_gpio_config(pinout_config)
        if files_gpio: all_generated_files.extend(files_gpio)
    except Exception as e:
        print(f"[GPIO] generation error: {e}")

    # 2) I2C
    try:
        i2c_settings = (peripheral_settings or {}).get("I2C", {})
        if i2c_settings:
            print(f"--- Processing: I2C ({len(i2c_settings)} instance(s)) ---")
            files_i2c = i2c_generator.generate_i2c_config(i2c_settings, pinout_config.get("gpio", []))
            if files_i2c: all_generated_files.extend(files_i2c)
    except Exception as e:
        print(f"[I2C] generation error: {e}")

    # 3) UART/USART
    try:
        uart_settings = (peripheral_settings or {}).get("UART", {})
        if uart_settings:
            print(f"--- Processing: UART ({len(uart_settings)} instance(s)) ---")
            files_uart = uart_generator.generate_uart_config(uart_settings, pinout_config.get("gpio", []))
            if files_uart: all_generated_files.extend(files_uart)
    except Exception as e:
        print(f"[UART] generation error: {e}")

    # 4) PRESETS (only if "cases" exist)
    try:
        ps = preset_settings or {}
        cases = ps.get("cases", []) if isinstance(ps, dict) else []
        if cases:
            print(f"--- Processing: PRESETS ({len(cases)} case(s)) ---")
            files_p = presets_generator.generate_presets_files(ps, peripheral_settings, pinout_config)
            if files_p: all_generated_files.extend(files_p)
        else:
            print("[SKIP] PRESETS: preset_settings missing or no 'cases'.")
    except Exception as e:
        print(f"[PRESETS] generation error: {e}")

    # 5) main.c/h
    try:
        print("--- Processing: main.c and main.h ---")
        main_files = main_generator.generate_main_files(pinout_config, peripheral_settings, preset_settings)
        if main_files: all_generated_files.extend(main_files)
    except Exception as e:
        print(f"[MAIN] generation error: {e}")

    # 6) Update HAL configuration
    try:
        print("--- Processing: HAL Configuration ---")
        _update_hal_config(peripheral_settings, preset_settings)
    except Exception as e:
        print(f"[HAL CONFIG] generation error: {e}")

    # 7) Update CMakeLists.txt with generated files
    try:
        print("--- Processing: CMakeLists.txt Update ---")
        _update_cmake_lists(all_generated_files)
    except Exception as e:
        print(f"[CMAKE UPDATE] generation error: {e}")

    # 8) Generate README with pin configuration
    try:
        print("--- Processing: README Generation ---")
        _generate_readme(pinout_config, peripheral_settings, preset_settings)
    except Exception as e:
        print(f"[README] generation error: {e}")

    print("\nProject file generation complete!")
    return all_generated_files


def _update_hal_config(peripheral_settings: dict, preset_settings: dict | None = None):
    """Update stm32g4xx_hal_conf.h to enable required HAL modules."""
    # Go up one directory from code generator to project root
    project_root = Path(__file__).parent.parent.parent
    hal_conf_path = project_root / "Core" / "Inc" / "stm32g4xx_hal_conf.h"
    
    if not hal_conf_path.exists():
        print("Warning: stm32g4xx_hal_conf.h not found")
        return
    
    # Read current configuration
    with open(hal_conf_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Determine which modules to enable
    modules_to_enable = set()
    
    # Check peripheral settings
    if peripheral_settings:
        if peripheral_settings.get("I2C"):
            modules_to_enable.add("HAL_I2C_MODULE_ENABLED")
        if peripheral_settings.get("UART") or peripheral_settings.get("USART"):
            modules_to_enable.add("HAL_UART_MODULE_ENABLED")
        if peripheral_settings.get("TIM"):
            modules_to_enable.add("HAL_TIM_MODULE_ENABLED")
        if peripheral_settings.get("ADC"):
            modules_to_enable.add("HAL_ADC_MODULE_ENABLED")
    
    # Check preset settings for additional requirements
    if preset_settings and preset_settings.get("cases"):
        cases = preset_settings.get("cases", [])
        for case in cases:
            # Check input types
            input_key = case.get("input_key", "").lower()
            if "potentiometer" in input_key or "ky-013" in input_key or "ky013" in input_key:
                modules_to_enable.add("HAL_ADC_MODULE_ENABLED")
            
            # Check output types  
            output_key = case.get("output_key", "").lower()
            if "pwm" in output_key:
                modules_to_enable.add("HAL_TIM_MODULE_ENABLED")
    
    # Update the configuration file
    for module in modules_to_enable:
        # Enable module (uncomment)
        pattern = f"/*#define {module}.*?*/"
        replacement = f"#define {module}"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write back the updated configuration
    with open(hal_conf_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Enabled HAL modules: {', '.join(modules_to_enable)}")


def _update_cmake_lists(generated_files: list[str]):
    """Update CMakeLists.txt to include all generated source files."""
    # Use current working directory as project root (when run from code generator directory)
    project_root = Path.cwd().parent
    cmake_file = project_root / "cmake" / "stm32cubemx" / "CMakeLists.txt"
    
    if not cmake_file.exists():
        print("Warning: CMakeLists.txt not found")
        return
    
    # Extract generated .c files from the list
    generated_c_files = []
    for file_path in generated_files:
        if file_path.endswith('.c'):
            # Convert absolute path to relative path from cmake/stm32cubemx/
            rel_path = Path(file_path).relative_to(project_root)
            cmake_path = f"${{CMAKE_CURRENT_SOURCE_DIR}}/../../{rel_path.as_posix()}"
            generated_c_files.append(cmake_path)
    
    if not generated_c_files:
        print("No generated .c files to add to CMakeLists.txt")
        return
    
    # Read current CMakeLists.txt
    with open(cmake_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rebuild MX_Application_Src section completely to only include current files
    # Define core STM32CubeMX files that should always be present (non-generated)
    core_files = [
        "${CMAKE_CURRENT_SOURCE_DIR}/../../Core/Src/stm32g4xx_it.c",
        "${CMAKE_CURRENT_SOURCE_DIR}/../../Core/Src/stm32g4xx_hal_msp.c",
        "${CMAKE_CURRENT_SOURCE_DIR}/../../Core/Src/sysmem.c",
        "${CMAKE_CURRENT_SOURCE_DIR}/../../Core/Src/syscalls.c",
        "${CMAKE_CURRENT_SOURCE_DIR}/../../startup_stm32g474xx.s",
    ]
    
    # Read as lines for easier processing
    lines = content.split('\n')
    new_lines = []
    in_sources_section = False
    
    for line in lines:
        if line.strip().startswith('set(MX_Application_Src'):
            in_sources_section = True
            new_lines.append(line)
            # Add only currently generated files (main.c, gpio.c, i2c.c, etc.)
            for file_path in generated_c_files:
                new_lines.append(f"    {file_path}")
            # Add core files (non-generated, always present)
            for core_file in core_files:
                new_lines.append(f"    {core_file}")
            continue
        elif in_sources_section and line.strip() == ')':
            new_lines.append(line)
            in_sources_section = False
            continue
        elif in_sources_section:
            # Skip old entries (we've already rebuilt the section)
            continue
        else:
            new_lines.append(line)
    
    updated_content = '\n'.join(new_lines)
    
    # Write back the updated CMakeLists.txt
    with open(cmake_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Added {len(generated_c_files)} generated files to CMakeLists.txt")


def _generate_readme(pinout_config: dict, peripheral_settings: dict, preset_settings: dict | None = None):
    """Generate README.md with pin configuration summary."""
    # Use current working directory as project root (when run from code generator directory)
    project_root = Path.cwd().parent
    readme_file = project_root / "README.md"
    
    # Extract GPIO configuration
    gpio_config = (pinout_config or {}).get("gpio", []) or []
    
    # Extract peripheral information
    peripherals = []
    if peripheral_settings:
        for periph_type, instances in peripheral_settings.items():
            for instance, settings in instances.items():
                peripherals.append({
                    "type": periph_type,
                    "instance": instance,
                    "settings": settings
                })
    
    # Extract preset information
    presets = []
    if preset_settings:
        presets = preset_settings.get("cases", []) or []
    
    # Generate README content
    readme_content = f"""# STM32 Project Configuration

## Pin Configuration Summary

### GPIO Pins
"""
    
    if gpio_config:
        readme_content += "| Pin | Function | Port | Mode | Pull | Speed | Alternate |\n"
        readme_content += "|-----|----------|------|------|------|-------|----------|\n"
        
        for pin in gpio_config:
            pin_name = pin.get("name", "Unknown")
            pin_num = pin.get("pin", "?")
            port = pin.get("port", "?")
            mode = pin.get("mode", "?")
            pull = pin.get("pull", "-")
            speed = pin.get("speed", "-")
            alternate = pin.get("alternate_fn", pin.get("alternate", "-"))
            
            readme_content += f"| {pin_name} | {pin_num} | {port} | {mode} | {pull} | {speed} | {alternate} |\n"
    else:
        readme_content += "No GPIO pins configured.\n"
    
    readme_content += "\n### Peripheral Configuration\n"
    
    if peripherals:
        for periph in peripherals:
            periph_type = periph.get("type", "Unknown")
            periph_instance = periph.get("instance", "Unknown")
            periph_settings = periph.get("settings", {})
            
            readme_content += f"\n#### {periph_type} ({periph_instance})\n"
            
            if periph_type == "I2C":
                # Show I2C pins
                i2c_pins = [p for p in gpio_config if periph_instance.upper() in str(p.get("alternate_fn", "")).upper()]
                if i2c_pins:
                    readme_content += "**Pins:**\n"
                    for pin in i2c_pins:
                        readme_content += f"- {pin.get('name', '?')} → {pin.get('port', '?')}{pin.get('pin', '?')}\n"
                
                # Show connected devices
                devices = periph_settings.get("devices", [])
                if devices:
                    readme_content += "\n**Connected Devices:**\n"
                    for device in devices:
                        device_name = device.get("name", "Unknown")
                        device_addr = device.get("address", "Unknown")
                        readme_content += f"- {device_name} (Address: 0x{device_addr:02X})\n"
                else:
                    readme_content += "\nNo devices configured.\n"
            
            elif periph_type == "UART":
                baudrate = periph_settings.get("baudrate", "Unknown")
                readme_content += f"**Baudrate:** {baudrate}\n"
            
            elif periph_type == "ADC":
                channels = periph_settings.get("channels", [])
                if channels:
                    readme_content += "**ADC Channels:**\n"
                    for channel in channels:
                        channel_name = channel.get("name", "Unknown")
                        channel_num = channel.get("channel", "Unknown")
                        readme_content += f"- {channel_name} (Channel {channel_num})\n"
                else:
                    readme_content += "No ADC channels configured.\n"
            
            elif periph_type == "PWM":
                timers = periph_settings.get("timers", [])
                if timers:
                    readme_content += "**PWM Timers:**\n"
                    for timer in timers:
                        timer_name = timer.get("name", "Unknown")
                        timer_freq = timer.get("frequency", "Unknown")
                        readme_content += f"- {timer_name} (Frequency: {timer_freq}Hz)\n"
                else:
                    readme_content += "No PWM timers configured.\n"
    else:
        readme_content += "No peripherals configured.\n"
    
    readme_content += "\n### Preset Use Cases\n"
    
    if presets:
        for i, preset in enumerate(presets, 1):
            input_key = preset.get("input_key", "Unknown Input")
            output_key = preset.get("output_key", "Unknown Output")
            
            readme_content += f"\n**Use Case {i}:** {input_key} → {output_key}\n"
            
            # Show input peripheral
            input_periph = preset.get("peripheral_settings", {}).get("input_peripheral", {})
            if input_periph:
                readme_content += f"- Input: {input_periph.get('type', '?')} ({input_periph.get('instance', '?')})\n"
            
            # Show output peripheral
            output_periph = preset.get("peripheral_settings", {}).get("output_peripheral", {})
            if output_periph:
                readme_content += f"- Output: {output_periph.get('type', '?')} ({output_periph.get('instance', '?')})\n"
            
            # Show formula if enabled
            processing = preset.get("processing", {})
            if processing.get("enabled"):
                readme_content += f"- Formula: `{processing.get('formula', 'N/A')}`\n"
            
            # Show threshold if enabled
            threshold = preset.get("threshold", {})
            if threshold.get("enabled"):
                readme_content += f"- Threshold: {threshold.get('value', 'N/A')}\n"
    else:
        readme_content += "No preset use cases configured.\n"
    
    readme_content += f"""
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
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by STM32 Code Generator*
"""
    
    # Write README file
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"Generated README.md with pin configuration summary")
