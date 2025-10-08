# data.py
from __future__ import annotations
import os
from pathlib import Path
import json

THIS = Path(__file__).resolve()               # .../TCCV02/code generator/ui/gpio_generator.py
GEN_DIR = THIS.parent.parent                         # .../TCCV02/code generator/
PROJ_ROOT = GEN_DIR.parent.parent.parent                    # .../TCCv02
PATH_PIN = GEN_DIR / "Mappings" / "pin_map.json"
PATH_HAL = GEN_DIR / "Mappings" / "hal_map.json"
# Default peripheral types for the main dropdown.
DEFAULT_TYPES = ["GPIO", "I2C", "UART", "SPI", "ADC"]

# MCU_MAP will be populated at runtime by loading the JSON file.
MCU_MAP = {}
HAL_MAPPINGS = {}


def load_initial_mapping():
    """
    Loads the MCU mapping data from a JSON file into the global MCU_MAP variable.
    Returns True on success, False on failure.
    """
    global MCU_MAP
    try:
        with open(PATH_PIN, "r", encoding="utf-8") as f:
            MCU_MAP = json.load(f)
        return True
    except FileNotFoundError:
        print(f"Error: {PATH_PIN} not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {PATH_PIN}.")
        return False
    
def load_hal_mappings():
    """
    Loads the UI-to-HAL constant mappings from a JSON file into the HAL_MAPPINGS variable.
    Returns True on success, False on failure.
    """
    global HAL_MAPPINGS
    try:
        with open(PATH_HAL, "r", encoding="utf-8") as f:
            HAL_MAPPINGS = json.load(f)
        return True
    except FileNotFoundError:
        print(f"Error: {PATH_HAL} not found.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {PATH_HAL}.")
        return False
