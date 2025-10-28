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


def _map_uart_interface_name(instance: str) -> str:
    s = (instance or "").upper()
    if s == "UART1": return "USART1"
    if s == "UART2": return "USART2"
    return s  

def generate_uart_config(a, b=None) -> list[str]:
 
    # Detecta modo novo/antigo
    if isinstance(a, dict):
        uart_settings = a

    if not uart_settings:
        return []

    uart_interfaces = []
    for instance, inst_set in uart_settings.items():
        iface = _map_uart_interface_name(instance)
        uart_interfaces.append({
            "num": "".join([c for c in instance if c.isdigit()]),
            "interface": iface,  # USART1/2/3 ou UART4
            "baud_rate": inst_set.get("baudRate", 115200),
            "word_length": inst_set.get("wordLength", "UART_WORDLENGTH_8B"),
            "stop_bits": inst_set.get("stopBits", "UART_STOPBITS_1"),
            "parity": inst_set.get("parity", "UART_PARITY_NONE"),
            "hw_flow_ctl": inst_set.get("flowControl", "UART_HWCONTROL_NONE"),
            "transferMode": (inst_set.get("transferMode") or "POLLING").upper(),
            "mode": inst_set.get("mode", "UART_MODE_TX_RX"),
            "oversampling": "UART_OVERSAMPLING_16",
        })

    context = { "uart_interfaces": uart_interfaces, "now": datetime.now }

    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)
    return [str(out_c_path), str(out_h_path)]
