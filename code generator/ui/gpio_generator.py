# gpio_generator.py (Atualizado para gerar .c e .h)

from __future__ import annotations
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

THIS = Path(__file__).resolve()               # .../TCCV02/code generator/gpio_generator.py
GEN_DIR = THIS.parent                         # .../TCCV02/code generator
PROJ_ROOT = GEN_DIR.parent.parent                    # .../TCCV02
print("alou")
print(PROJ_ROOT)
# Paths de templates 
TPL_DIR_INC = GEN_DIR /  "inc"
TPL_DIR_SRC = GEN_DIR /  "src"

# Saída nos diretórios padrão do Cube
OUT_INC = PROJ_ROOT / "core" / "inc" / "gpio.h"
OUT_SRC = PROJ_ROOT / "core" / "src" / "gpio.c"

# Nomes dos arquivos de template
TEMPLATE_C_NAME = "gpio_template.c"
TEMPLATE_H_NAME = "gpio_template.h"

env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
)

def _render_and_save(template_name: str, context: dict, output_path: Path) -> Path:
    # Debug útil
    print(f"[JINJA] cwd={Path.cwd()}")
    print(f"[JINJA] procurando '{template_name}' em: {TPL_DIR_SRC} ; {TPL_DIR_INC}")

    try:
        template = env.get_template(template_name)  # usa só o NOME, não passe path absoluto
    except TemplateNotFound as e:
        raise FileNotFoundError(
            f"Template '{template_name}' não encontrado. "
            f"Verifique se ele existe em {TPL_DIR_SRC} ou {TPL_DIR_INC}"
        ) from e

    rendered = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"[OK] -> Arquivo gerado: {output_path}")
    return output_path


def generate_gpio_config(block: dict) -> list[str]:

    pins = block.get("pins", [])
    if not pins:
        print("[GPIO] nenhum pino configurado.")
        return []

    # Contexto para os templates Jinja
    ctx = {
        "pins": pins,
        # Macros simples de mapeamento (úteis no template):
        "map_mode": {
            "INPUT":     "GPIO_MODE_INPUT",
            "OUTPUT_PP": "GPIO_MODE_OUTPUT_PP",
            "OUTPUT_OD": "GPIO_MODE_OUTPUT_OD",
            "AF_PP":     "GPIO_MODE_AF_PP",
            "AF_OD":     "GPIO_MODE_AF_OD",
            "ANALOG":    "GPIO_MODE_ANALOG",
        },
        "map_pull": {
            "NOPULL": "GPIO_NOPULL",
            "PULLUP": "GPIO_PULLUP",
            "PULLDOWN":"GPIO_PULLDOWN",
        },
        "map_speed": {
            "LOW":       "GPIO_SPEED_FREQ_LOW",
            "MEDIUM":    "GPIO_SPEED_FREQ_MEDIUM",
            "HIGH":      "GPIO_SPEED_FREQ_HIGH",
            "VERY_HIGH": "GPIO_SPEED_FREQ_VERY_HIGH",
        }
    }

    out_h = _render_and_save(TEMPLATE_H_NAME, ctx, OUT_INC)
    out_c = _render_and_save(TEMPLATE_C_NAME, ctx, OUT_SRC)
    return [str(out_c), str(out_h)]

