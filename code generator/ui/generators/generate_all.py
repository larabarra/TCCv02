# generate_all.py

import json
from collections import defaultdict

# Import the modular generator scripts from the same package.
from . import gpio_generator
from . import i2c_generator
from . import uart_generator
from . import main_generator # Import the new main.c generator

# Dispatch table: Maps the 'type' string from the config data
# to the corresponding generator function.
GENERATORS = {
    "GPIO": gpio_generator.generate_gpio_config,
    "I2C": i2c_generator.generate_i2c_config,
    "USART": uart_generator.generate_uart_config,
    "UART": uart_generator.generate_uart_config,
}

def generate_project_files(pinout_config: dict, peripheral_settings: dict) -> list[str]:
    """
    Iterates through configuration blocks, groups them by type, and
    calls the appropriate generator function for each type. Finally,
    it generates the main.c and main.h files.
    """
    all_generated_files = []
    
    # Get the list of peripheral pinout configurations.
    pinout_blocks = pinout_config.get("peripherals", [])
    
    # Group all pinout blocks by their 'type'.
    grouped_pinouts = defaultdict(list)
    for block in pinout_blocks:
        config_type = block.get("type")
        if config_type:
            grouped_pinouts[config_type].append(block)

    # Iterate through the grouped configurations and call the corresponding peripheral generator.
    for config_type, pinout_list in grouped_pinouts.items():
        if config_type in GENERATORS:
            generator_func = GENERATORS[config_type]
            print(f"--- Processing: {config_type} ({len(pinout_list)} instance(s)) ---")
            
            # Pass the specific settings to each generator.
            if config_type == "I2C":
                settings = peripheral_settings.get("I2C", {})
                output_filenames = generator_func(pinout_list, settings)
            elif config_type in ["UART", "USART"]:
                settings = peripheral_settings.get("UART", {})
                output_filenames = generator_func(pinout_list, settings)
            else: # For simple generators like GPIO
                output_filenames = generator_func(pinout_list)

            if output_filenames:
                all_generated_files.extend(output_filenames)
    
        else:
            print(f"WARNING: Configuration type '{config_type}' has no mapped generator.")
            
    # After generating all peripheral files, generate the main.c and main.h files.
    print("--- Processing: main.c and main.h ---")
    main_files = main_generator.generate_main_files(pinout_config, peripheral_settings)
    if main_files:
        all_generated_files.extend(main_files)

    print("\nProject file generation complete!")
    return all_generated_files

