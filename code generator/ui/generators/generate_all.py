# generate_all.py

from collections import defaultdict

# Import the modular generator scripts from the same package.
from . import gpio_generator
from . import i2c_generator
from . import uart_generator
from . import main_generator
from . import presets_generator  # mantém import (vai ser chamado condicionalmente)

def _gpio_list_from_pinout(pinout_config: dict) -> list[dict]:
    """
    Retrocompat: se 'gpio' não existir, tenta montar a lista a partir de
    pinout_config['peripherals'] (quando ainda vinha agrupado por tipo).
    Retorna SEMPRE uma lista de pinos (dicts com port/pin/mode/pull/speed/...).
    """
    if not pinout_config:
        return []
    if "gpio" in pinout_config:
        return pinout_config.get("gpio", [])

    # modo legado: buscar dentro de peripherals -> type == "GPIO"
    all_gpio = []
    for blk in pinout_config.get("peripherals", []):
        if blk.get("type") == "GPIO":
            all_gpio.extend(blk.get("pins", []))
    return all_gpio


def generate_project_files(pinout_config: dict, peripheral_settings: dict, preset_settings: dict | None = None) -> list[str]:
    """
    Fluxo:
      1) GPIO (com pinout_config['gpio'])
      2) I2C/UART (com peripheral_settings)
      3) PRESETS (se houver preset_settings["cases"])
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

    # 4) PRESETS (somente se houver "cases")
    try:
        ps = preset_settings or {}
        cases = ps.get("cases", []) if isinstance(ps, dict) else []
        if cases:
            print(f"--- Processing: PRESETS ({len(cases)} case(s)) ---")
            files_p = presets_generator.generate_presets_files(ps, peripheral_settings, pinout_config)
            if files_p: all_generated_files.extend(files_p)
        else:
            print("[SKIP] PRESETS: preset_settings ausente ou sem 'cases'.")
    except Exception as e:
        print(f"[PRESETS] generation error: {e}")

    # 5) main.c/h
    try:
        print("--- Processing: main.c and main.h ---")
        main_files = main_generator.generate_main_files(pinout_config, peripheral_settings)
        if main_files: all_generated_files.extend(main_files)
    except Exception as e:
        print(f"[MAIN] generation error: {e}")

    print("\nProject file generation complete!")
    return all_generated_files
