# main_generator.py

from __future__ import annotations
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from datetime import datetime

# --- Path Definitions ---
THIS_FILE = Path(__file__).resolve()
GEN_DIR = THIS_FILE.parent.parent.parent
PROJ_ROOT = GEN_DIR.parent
TPL_DIR_INC = GEN_DIR / "TEMPLATES" / "inc"
TPL_DIR_SRC = GEN_DIR / "TEMPLATES" / "src"
OUT_SRC_PATH = PROJ_ROOT / "Core" / "Src" / "main.c"
OUT_INC_PATH = PROJ_ROOT / "Core" / "Inc" / "main.h" # Path for main.h
TEMPLATE_C_NAME = "main_template.c"
TEMPLATE_H_NAME = "main_template.h" # Template for main.h

# --- Jinja2 Environment Setup ---
# The loader now searches in both 'inc' and 'src' template folders.
env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

def _render_and_save(template_name: str, context: dict, output_path: Path) -> Path:
    """Renders a Jinja2 template and saves it to a file."""
    print(f"[JINJA] Looking for '{template_name}' in loader paths...")
    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Template '{template_name}' not found") from e

    rendered_content = template.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_content)
    print(f"[SUCCESS] -> Generated file: {output_path}")
    return output_path

def _get_digits(s: str) -> str:
    """Extracts the first sequence of digits from a string."""
    m = re.findall(r"\d+", s or "")
    return m[0] if m else ""

def generate_main_files(pinout_config: dict, peripheral_settings: dict) -> list[str]:
    """
    Analyzes the user's configuration and generates main.c and main.h files
    with relevant example tasks and pin definitions.
    """
    # 1. Initialize a comprehensive context for the templates
    context = {
        "now": datetime.now,
        "all_pins": [],
        "gpio_configs": [],
        "i2c_interfaces": [],
        "uart_interfaces": [],
        "gpio_example_needed": False,
        "i2c_example_needed": False,
        "uart_example_needed": False,
        "first_gpio_input": None,
        "first_gpio_output": None,
    }

    pinout_blocks = pinout_config.get("peripherals", [])
    
    # 2. First pass: group configurations by type and gather all pins for main.h
    for block in pinout_blocks:
        # Add all pins from this block to the global pin list for #defines
        context["all_pins"].extend(block.get("pins", []))
        
        block_type = block.get("type")
        if block_type == "GPIO":
            context["gpio_configs"].append(block)
        elif block_type == "I2C":
            context["i2c_interfaces"].append(block)
        elif block_type in ["UART", "USART"]:
            context["uart_interfaces"].append(block)
    
    # 3. Second pass: determine which examples are needed for main.c
    output_pins = [p for p in context["all_pins"] if "OUTPUT" in p.get("mode", "")]
    if output_pins:
        context["gpio_example_needed"] = True
        context["first_gpio_output"] = output_pins[0]
        input_pins = [p for p in context["all_pins"] if "INPUT" in p.get("mode", "")]
        if input_pins:
            context["first_gpio_input"] = input_pins[0]

    if context["i2c_interfaces"]:
        first_i2c_instance = context["i2c_interfaces"][0].get("instance")
        i2c_settings = peripheral_settings.get("I2C", {}).get(first_i2c_instance, {})
        if i2c_settings and i2c_settings.get("devices"):
            context["i2c_example_needed"] = True
            context["i2c_interfaces"][0]["num"] = _get_digits(first_i2c_instance)
            context["i2c_interfaces"][0]["devices"] = i2c_settings.get("devices")

    if context["uart_interfaces"]:
        context["uart_example_needed"] = True
        first_uart_instance = context["uart_interfaces"][0].get("instance")
        context["uart_interfaces"][0]["num"] = _get_digits(first_uart_instance)

    # 4. Render and save both main.c and main.h
    main_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)
    main_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    
    return [str(main_c_path), str(main_h_path)]

