
from __future__ import annotations
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# --- Path Definitions ---
# The script calculates key directory paths by navigating up from its own location.
THIS_FILE = Path(__file__).resolve()
# Assumes a structure like: .../TCCV02/code generator/ui/generators/gpio_generator.py
# GEN_DIR should point to .../TCCV02/code generator/
GEN_DIR = THIS_FILE.parent.parent.parent
# PROJ_ROOT should point to the main project folder, e.g., .../TCCV02/
PROJ_ROOT = GEN_DIR.parent

# --- Template and Output Paths ---
# Define where the Jinja2 templates are located.
TPL_DIR_INC = GEN_DIR / "TEMPLATES" / "inc"
TPL_DIR_SRC = GEN_DIR / "TEMPLATES" / "src"

# Define the output paths for the generated files, matching STM32CubeIDE's structure.
OUT_INC_PATH = PROJ_ROOT / "Core" / "Inc" / "gpio.h"
OUT_SRC_PATH = PROJ_ROOT / "Core" / "Src" / "gpio.c"

# Template filenames to be used.
TEMPLATE_C_NAME = "gpio_template.c"
TEMPLATE_H_NAME = "gpio_template.h"

# --- Jinja2 Environment Setup ---
# Initialize the Jinja2 environment. The FileSystemLoader is configured to
# search for templates in both the 'src' and 'inc' template directories.
env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
    trim_blocks=True,      # Removes the first newline after a block
    lstrip_blocks=True,    # Strips leading whitespace from a block
)

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


def generate_gpio_config(config_blocks: list[dict]) -> list[str]:
    """
    Generates gpio.c and gpio.h files based on a list of GPIO configuration blocks.

    Args:
        config_blocks (list[dict]): A list of dictionaries, where each dictionary
                                    represents a peripheral and contains a 'pins' key.

    Returns:
        list[str]: A list containing the string paths of the generated .c and .h files.
    """
    # Extract all pin configurations from the different peripheral blocks into a single list.
    all_pins = []
    for peripheral_dict in config_blocks:
        all_pins.extend(peripheral_dict.get("pins", []))
    
    # Create the context dictionary to pass data to the Jinja2 templates.
    context = {
        "pins": all_pins,
        
        # Mapping dictionaries to convert UI strings to HAL-compatible definitions.
        # This allows the templates to be clean and readable.
        "map_mode": {
            "INPUT":     "GPIO_MODE_INPUT",
            "OUTPUT_PP": "GPIO_MODE_OUTPUT_PP",
            "OUTPUT_OD": "GPIO_MODE_OUTPUT_OD",
            "AF_PP":     "GPIO_MODE_AF_PP",
            "AF_OD":     "GPIO_MODE_AF_OD",
            "ANALOG":    "GPIO_MODE_ANALOG",
        },
        "map_pull": {
            "NOPULL":   "GPIO_NOPULL",
            "PULLUP":   "GPIO_PULLUP",
            "PULLDOWN": "GPIO_PULLDOWN",
        },
        "map_speed": {
            "LOW":       "GPIO_SPEED_FREQ_LOW",
            "MEDIUM":    "GPIO_SPEED_FREQ_MEDIUM",
            "HIGH":      "GPIO_SPEED_FREQ_HIGH",
            "VERY_HIGH": "GPIO_SPEED_FREQ_VERY_HIGH",
        }
    }

    # Render the header and source files.
    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)
    
    # Return the paths of the generated files.
    return [str(out_c_path), str(out_h_path)]
