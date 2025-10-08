# i2c_generator.py

from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

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
        i2c_blocks (list[dict]): A list of dictionaries, where each dictionary
                                 represents an I2C peripheral instance and its pins.

    Returns:
        list[str]: A list containing the string paths of the generated .c and .h files.
    """
    i2c_interfaces = []
    
    # Mapping dictionaries to convert UI strings to HAL-compatible definitions.
    map_pull = {
        "NOPULL":   "GPIO_NOPULL",
        "PULLUP":   "GPIO_PULLUP",
        "PULLDOWN": "GPIO_PULLDOWN",
    }
    map_speed = {
        "LOW":       "GPIO_SPEED_FREQ_LOW",
        "MEDIUM":    "GPIO_SPEED_FREQ_MEDIUM",
        "HIGH":      "GPIO_SPEED_FREQ_HIGH",
        "VERY_HIGH": "GPIO_SPEED_FREQ_VERY_HIGH",
    }

    print(i2c_pinout_blocks)
    print(i2c_settings)

    # Process each I2C peripheral block from the configuration.
    for block in i2c_pinout_blocks:
        instance = block.get('instance')  # e.g., "I2C1"
        pins_list = block.get('pins', [])
        
        if not instance or not pins_list:
            continue # Skip malformed blocks.
            

        instance_settings = i2c_settings.get(instance, {})
        if not instance_settings:
            print(f"WARNING: No peripheral settings found for {instance}. Using defaults.")


        # Extract the instance number (1, 2, etc.) from the instance name.
        instance_num = int(instance.replace("I2C", ""))
        
        # Identify the SCL and SDA pins from the pins list by checking their name.
        scl_pin_data = next((p for p in pins_list if 'SCL' in p.get('name', '').upper()), None)
        sda_pin_data = next((p for p in pins_list if 'SDA' in p.get('name', '').upper()), None)
        
        # Ensure both SCL and SDA pins were found before proceeding.
        if scl_pin_data is None or sda_pin_data is None:
            print(f"ERROR: SCL or SDA pin data not found for {instance}. Skipping block.")
            continue
        
        # Build a context dictionary for this specific I2C interface.
        interface_context = {
            "num": int(instance.replace("I2C", "")),
            "interface": instance,
            
            # HAL Init settings (from peripheral_settings.json)
            "timing_reg": TIMING_REGISTER_MAP.get(instance_settings.get("clockSpeed"), "0x30909DEC"), # Default to 100kHz
            "addressing_mode": instance_settings.get("addressingMode", "I2C_ADDRESSINGMODE_7BIT"),
            
            # Default values for other settings
            "own_address1": "0",
            "dual_address_mode": "I2C_DUALADDRESS_DISABLE",
            "own_address2": "0",
            "own_address2_masks": "I2C_OA2MSK_NOMASK",
            "general_call_mode": "I2C_GENERALCALL_DISABLE",
            "no_stretch_mode": "I2C_NOSTRETCH_DISABLE",
            
            # Pin data for MSP init (from pinout configuration)
            "scl_port_char": scl_pin_data['port'][4],
            "scl_pin_num": scl_pin_data['pin'],
            "sda_port_char": sda_pin_data['port'][4],
            "sda_pin_num": sda_pin_data['pin'],
            "scl_af": scl_pin_data['alternate_fn'],
            "sda_af": sda_pin_data['alternate_fn'],
        }
        
        i2c_interfaces.append(interface_context)

    # If no valid I2C interfaces were configured, do not generate any files.
    if not i2c_interfaces:
        print("[I2C] No valid I2C interfaces found in configuration. No files generated.")
        return []

    # Create the final context for rendering the templates.
    context = {"i2c_interfaces": i2c_interfaces}

    # Render and save the .h and .c files.
    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)

    print(f"[I2C] Processed {len(i2c_interfaces)} I2C instance(s).")

    return [str(out_c_path), str(out_h_path)]
