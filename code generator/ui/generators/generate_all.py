# generate_all.py

from collections import defaultdict
import re
from pathlib import Path

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
        files_gpio = gpio_generator.generate_gpio_config(pinout_config.get("gpio", []))
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
    
    # Find the MX_Application_Src section and add our files before the closing parenthesis
    pattern = r'(set\(MX_Application_Src\s*\n.*?)(\s*\))'
    
    def replace_sources(match):
        existing_content = match.group(1)
        closing_paren = match.group(2)
        
        # Add generated files with proper indentation and newlines
        new_files = []
        for file_path in generated_c_files:
            new_files.append(f"    {file_path}")
        
        return existing_content + '\n' + '\n'.join(new_files) + '\n' + closing_paren
    
    updated_content = re.sub(pattern, replace_sources, content, flags=re.DOTALL)
    
    # Write back the updated CMakeLists.txt
    with open(cmake_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Added {len(generated_c_files)} generated files to CMakeLists.txt")
