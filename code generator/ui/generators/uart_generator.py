# uart_generator.py

from __future__ import annotations
from datetime import datetime
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


def generate_uart_config(uart_pinout_blocks: list[dict], uart_settings: dict) -> list[str]:
    """
    Generates uart.c and uart.h files by merging pinout data with peripheral settings.

    Args:
        uart_pinout_blocks (list[dict]): A list of pinout configs for UART instances.
        uart_settings (dict): A dictionary with operational settings for UART instances.

    Returns:
        list[str]: A list of paths to the generated files.
    """
    uart_interfaces = []

    for block in uart_pinout_blocks:
        instance = block.get('instance')
        pins_list = block.get('pins', [])
        if not instance: continue

        instance_settings = uart_settings.get(instance, {})
        if not instance_settings:
            print(f"WARNING: No peripheral settings found for {instance}. Using defaults.")

        # Find TX and RX pins for this instance
        tx_pin = next((p for p in pins_list if 'TX' in p.get('name', '').upper()), None)
        rx_pin = next((p for p in pins_list if 'RX' in p.get('name', '').upper()), None)

        # Deduce the operational mode based on which pins are configured
        if tx_pin and rx_pin:
            mode = "UART_MODE_TX_RX"
        elif tx_pin:
            mode = "UART_MODE_TX"
        elif rx_pin:
            mode = "UART_MODE_RX"
        else:
            print(f"ERROR: No TX or RX pins found for {instance}. Skipping.")
            continue

        interface_context = {
            "num": _get_digits(instance),
            "interface": instance.replace("UART", "USART"), # HAL uses USARTx
            
            # Get settings from peripheral_settings.json, with safe defaults
            "baud_rate": instance_settings.get("baudRate", 115200),
            "word_length": instance_settings.get("wordLength", "UART_WORDLENGTH_8B"),
            "stop_bits": instance_settings.get("stopBits", "UART_STOPBITS_1"),
            "parity": instance_settings.get("parity", "UART_PARITY_NONE"),
            "hw_flow_ctl": instance_settings.get("flowControl", "UART_HWCONTROL_NONE"),
            "transferMode": instance_settings.get("transferMode", "POLLING"),
            # Use the automatically deduced mode
            "mode": mode,

            # Add fixed default values for advanced parameters
            "oversampling": "UART_OVERSAMPLING_16",
            
            # Store pin data if it exists
            "tx_pin": tx_pin,
            "rx_pin": rx_pin,
        }
        
        uart_interfaces.append(interface_context)

    if not uart_interfaces:
        return []

    context = {
        "uart_interfaces": uart_interfaces,
        "now": datetime.now
    }
    
    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)

    return [str(out_c_path), str(out_h_path)]
