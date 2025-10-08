# uart_generator.py

from __future__ import annotations
import os
import json
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# --- Path Definitions ---
# The script calculates key directory paths by navigating up from its own location.
THIS_FILE = Path(__file__).resolve()
# Assumes a structure like: .../TCCV02/code generator/ui/generators/uart_generator.py
# GEN_DIR should point to .../TCCV02/code generator/
GEN_DIR = THIS_FILE.parent.parent.parent
# PROJ_ROOT should point to the main project folder, e.g., .../TCCV02/
PROJ_ROOT = GEN_DIR.parent

# --- Template and Output Paths ---
# Define where the Jinja2 templates are located.
TPL_DIR_INC = GEN_DIR / "TEMPLATES" / "inc"
TPL_DIR_SRC = GEN_DIR / "TEMPLATES" / "src"

# Define the output paths for the generated files, matching STM32CubeIDE's structure.
OUT_INC_PATH = PROJ_ROOT / "Core" / "Inc" / "uart.h"
OUT_SRC_PATH = PROJ_ROOT / "Core" / "Src" / "uart.c"

# Path to the MCU mapping definition file.
MAP_PATH = GEN_DIR/ "Mappings" / "pin_map.json"

# Template filenames to be used.
TEMPLATE_C_NAME = "uart_template.c"
TEMPLATE_H_NAME = "uart_template.h"

# --- Jinja2 Environment Setup ---
# Initialize the Jinja2 environment. The FileSystemLoader is configured to
# search for templates in both the 'src' and 'inc' template directories.
env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

def _load_mappings() -> dict:
    """Loads and parses the pin_map.json file."""
    try:
        with open(MAP_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {MAP_PATH.name}: {e}")
        return {}

def _get_digits(s: str) -> str:
    """Extracts the first sequence of digits from a string (e.g., 'UART1' -> '1')."""
    m = re.findall(r"\d+", s or "")
    return m[0] if m else ""

def _render_and_save(template_name: str, context: dict, output_path: Path) -> Path:
    """
    Renders a Jinja2 template with the given context and saves it to a file.

    Args:
        template_name (str): The filename of the template to render.
        context (dict): A dictionary of data to pass to the template.
        output_path (Path): The absolute path where the rendered file will be saved.

    Returns:
        Path: The path to the newly created file.
    """
    print(f"[JINJA] Looking for '{template_name}' in: {TPL_DIR_SRC} and {TPL_DIR_INC}")

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise FileNotFoundError(
            f"Template '{template_name}' not found. "
            f"Ensure it exists in {TPL_DIR_SRC} or {TPL_DIR_INC}"
        ) from e

    rendered_content = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_content)

    print(f"[SUCCESS] -> Generated file: {output_path}")
    return output_path


def generate_uart_config(config_blocks: list[dict]) -> list[str]:
    """
    Generates uart.c and uart.h files based on a list of UART/USART configuration blocks.

    Args:
        config_blocks (list[dict]): A list of dictionaries, where each dictionary
                                    represents a UART/USART instance and its pins.

    Returns:
        list[str]: A list containing the string paths of the generated .c and .h files.
    """
    mcu_map = _load_mappings()
    af_mapping = mcu_map.get("STM32G474RE", {}).get("uart_af_mapping", {})

    uart_interfaces_list = []
        
    for cfg in config_blocks:
        instance = cfg.get('instance', 'UART_UNKNOWN')
        pins = cfg.get('pins', [])
        
        # 1. Find the TX and RX pin data within the list of pins for this instance.
        tx_pin_data = next((p for p in pins if 'TX' in p.get('name', '')), None)
        rx_pin_data = next((p for p in pins if 'RX' in p.get('name', '')), None)
    
        # Basic validation to ensure both pins are present.
        if not tx_pin_data or not rx_pin_data:
            print(f"Warning: Incomplete TX/RX pin configuration for {instance}. Skipping.")
            continue
    
        # 2. Look up and format the Alternate Function (AF) macro.
        
        # Construct the pin name key for the mapping lookup (e.g., 'PA9', 'PB10').
        tx_pin_key = f"P{tx_pin_data['port'][4:]}{tx_pin_data['pin']}"
        rx_pin_key = f"P{rx_pin_data['port'][4:]}{rx_pin_data['pin']}"

        # The mapping file uses 'USART' even if the UI uses 'UART'.
        af_instance_key = instance.replace('UART', 'USART') 
        
        # Look up the full AF macro in the mapping file. Fall back to a generic macro if not found.
        tx_af = af_mapping.get(af_instance_key, {}).get(tx_pin_key, f"GPIO_AF{tx_pin_data['alternate_fn']}_{instance}")
        rx_af = af_mapping.get(af_instance_key, {}).get(rx_pin_key, f"GPIO_AF{rx_pin_data['alternate_fn']}_{instance}")
        
        # 3. Build the context dictionary for this UART interface.
        uart_interfaces_list.append({
            "num": _get_digits(instance),
            "interface": instance,
            "baud_rate": 115200, # This will eventually come from the UI configuration.
            
            # Formatted TX pin data
            "tx_port": tx_pin_data['port'][4],
            "tx_pin_num": str(tx_pin_data['pin']),
            "tx_pull": f"GPIO_{tx_pin_data['pull']}",
            "tx_speed": f"GPIO_SPEED_FREQ_{tx_pin_data['speed'].upper()}",
            "tx_af": tx_af,
            
            # Formatted RX pin data
            "rx_port": rx_pin_data['port'][4],
            "rx_pin_num": str(rx_pin_data['pin']),
            "rx_pull": f"GPIO_{rx_pin_data['pull']}",
            "rx_speed": f"GPIO_SPEED_FREQ_{rx_pin_data['speed'].upper()}",
            "rx_af": rx_af,
        })

    # 4. Render the templates if any valid interfaces were found.
    if not uart_interfaces_list:
        print("[UART] No valid UART interfaces to render.")
        return []
        
    context = {"uart_interfaces": uart_interfaces_list}

    print(f"[UART] {len(uart_interfaces_list)} UART instance(s) ready for rendering.")

    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)

    return [str(out_c_path), str(out_h_path)]
