from __future__ import annotations
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

THIS = Path(__file__).resolve()               # .../TCCV02/code generator/ui/gpio_generator.py
GEN_DIR = THIS.parent                         # .../TCCV02/code generator/ui
PROJ_ROOT = GEN_DIR.parent.parent.parent                   # .../TCCV02

print(THIS)
print(GEN_DIR)
print(PROJ_ROOT)
