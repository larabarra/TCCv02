# i2c_generator.py

from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from datetime import datetime

# --- Path Definitions ---
# The script calculates key directory paths by navigating up from its own location.
THIS_FILE = Path(__file__).resolve()
# Assumes a structure like: .../TCCV02/code generator/ui/generators/i2c_generator.py
# GEN_DIR should point to .../TCCV02/code generator/
GEN_DIR = THIS_FILE.parent.parent.parent
# PROJ_ROOT should point to the main project folder, e.g., .../TCCV02/
PROJ_ROOT = GEN_DIR.parent

# --- Template and Output Paths ---
# Define where the Jinja2 templates are located.
TPL_DIR_INC = GEN_DIR / "TEMPLATES" / "inc"
TPL_DIR_SRC = GEN_DIR / "TEMPLATES" / "src"

# Define the output paths for the generated files, matching STM32CubeIDE's structure.
OUT_INC_PATH = PROJ_ROOT / "Core" / "Inc" / "i2c.h"
OUT_SRC_PATH = PROJ_ROOT / "Core" / "Src" / "i2c.c"

# Template filenames to be used.
TEMPLATE_C_NAME = "i2c_template.c"
TEMPLATE_H_NAME = "i2c_template.h"

# --- Jinja2 Environment Setup ---
# Initialize the Jinja2 environment. The FileSystemLoader is configured to
# search for templates in both the 'src' and 'inc' template directories.
env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
    trim_blocks=True,      # Removes the first newline after a block
    lstrip_blocks=True,    # Strips leading whitespace from a block
)

# --- Timing Register Map ---
# Pre-calculated values for STM32G4 series at a typical 100MHz I2CCLK.
# These values should be adjusted if the system clock changes significantly.
TIMING_REGISTER_MAP = {
    100000: "0x30909DEC",  # Standard Mode (100kHz)
    400000: "0x10B0B0EB",  # Fast Mode (400kHz)
    1000000: "0x00D0268A", # Fast Mode Plus (1MHz)
}

def _render_and_save(template_name: str, context: dict, output_path: Path) -> Path:
    """
    Renders a Jinja2 template with the given context and saves it to a file.

    Args:
        template_name (str): The filename of the template to render.
        context (dict): A dictionary of data to pass to the template.
        output_path (Path): The absolute path where the rendered file will be saved.

    Returns:
        Path: The path to the newly created file.
        
    Raises:
        FileNotFoundError: If the specified template cannot be found in the loader paths.
    """
    print(f"[JINJA] Looking for '{template_name}' in: {TPL_DIR_SRC} and {TPL_DIR_INC}")

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise FileNotFoundError(
            f"Template '{template_name}' not found. "
            f"Ensure it exists in {TPL_DIR_SRC} or {TPL_DIR_INC}"
        ) from e

    # Render the template with the provided context data.
    rendered_content = template.render(**context)

    # Create the parent directory for the output file if it doesn't exist.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the rendered content to the output file.
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_content)

    print(f"[SUCCESS] -> Generated file: {output_path}")
    return output_path


def generate_i2c_config(i2c_pinout_blocks: list[dict], i2c_settings: dict) -> list[str]:
    """
    Generates i2c.c and i2c.h files by merging pinout data with peripheral settings.

    Args:
        i2c_pinout_blocks (list[dict]): A list of pinout configs for I2C instances.
        i2c_settings (dict): A dictionary with operational settings for I2C instances.

    Returns:
        list[str]: A list of paths to the generated files.
    """
    i2c_interfaces = []

    for block in i2c_pinout_blocks:
        instance = block.get('instance')
        pins_list = block.get('pins', [])
        if not instance or not pins_list:
            continue
            
        instance_settings = i2c_settings.get(instance, {})
        if not instance_settings:
            print(f"WARNING: No peripheral settings found for {instance}. Using defaults.")

        scl_pin_data = next((p for p in pins_list if 'SCL' in p.get('name', '').upper()), None)
        sda_pin_data = next((p for p in pins_list if 'SDA' in p.get('name', '').upper()), None)
        if not scl_pin_data or not sda_pin_data:
            print(f"ERROR: SCL or SDA pin data not found for {instance}. Skipping.")
            continue
        
        # Pre-process the device list to perform the address calculation in Python.
        processed_devices = []
        devices_from_settings = instance_settings.get("devices", [])
        for device in devices_from_settings:
            address_7bit = device.get("address", 0)
            # The left-shift calculation is done here, safely, in Python.
            address_hal = address_7bit << 1
            processed_devices.append({
                "name": device.get("name", "UNKNOWN_DEVICE"),
                "address_hal": address_hal # Pass the pre-calculated value.
            })

        interface_context = {
            "num": int(instance.replace("I2C", "")),
            "interface": instance,
            "timing_reg": TIMING_REGISTER_MAP.get(instance_settings.get("clockSpeed"), "0x30909DEC"),
            "addressing_mode": instance_settings.get("addressingMode", "I2C_ADDRESSINGMODE_7BIT"),
            "devices": processed_devices, # Use the pre-processed list.
            "dual_address_mode": "I2C_DUALADDRESS_DISABLE",
            "transferMode": instance_settings.get("transferMode", "POLLING"),
            "own_address1": "0",
            "own_address2": "0",
            "own_address2_masks": "I2C_OA2MSK_NOMASK",
            "general_call_mode": "I2C_GENERALCALL_DISABLE",
            "no_stretch_mode": "I2C_NOSTRETCH_DISABLE",
            "scl_port_char": scl_pin_data['port'][4],
            "scl_pin_num": scl_pin_data['pin'],
            "sda_port_char": sda_pin_data['port'][4],
            "sda_pin_num": sda_pin_data['pin'],
            "scl_af": scl_pin_data['alternate_fn'],
            "sda_af": sda_pin_data['alternate_fn'],
        }
        
        i2c_interfaces.append(interface_context)

    if not i2c_interfaces:
        return []

    context = {
        "i2c_interfaces": i2c_interfaces,
        "now": datetime.now
    }
    
    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)

    return [str(out_c_path), str(out_h_path)]

