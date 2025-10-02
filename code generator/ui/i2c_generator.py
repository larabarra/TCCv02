from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import json
import os

# Ajuste os caminhos conforme sua estrutura
THIS = Path(__file__).resolve()
GEN_DIR = THIS.parent 
PROJ_ROOT = GEN_DIR.parent.parent 

# Paths de templates
TPL_DIR_INC = GEN_DIR / "inc"
TPL_DIR_SRC = GEN_DIR / "src"

# Saída nos diretórios padrão do Cube
OUT_INC = PROJ_ROOT / "core" / "inc" / "i2c.h"
OUT_SRC = PROJ_ROOT / "core" / "src" / "i2c.c"

# Nomes dos arquivos de template
TEMPLATE_C_NAME = "i2c_template.c"
TEMPLATE_H_NAME = "i2c_template.h"
MAP_PATH = GEN_DIR / "mapping.json" 


# --- LOAD MAPPINGS ---
def _load_mappings() -> dict:
    """Carrega o arquivo mapping.json."""
    try:
        with open(MAP_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar {MAP_PATH.name}: {e}")
        return {}

env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
)

def _render_and_save(template_name: str, context: dict, output_path: Path) -> Path:
    """Função reutilizável para renderizar e salvar templates."""
    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise FileNotFoundError(
            f"Template '{template_name}' não encontrado. Verifique os caminhos."
        ) from e

    rendered = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"[OK] -> Arquivo gerado: {output_path}")
    return output_path




def generate_i2c_config(block: dict) -> list[str]:
    """
    Processa TODAS as configurações I2C encontradas no dicionário de configuração do projeto ('block')
    e as formata para o template Jinja2.
    """
    
    # 1. Extrair Contexto Principal
    microcontroller = block.get('microcontroller')
    
    # 2. FILTRAGEM CRÍTICA: Extrai APENAS as configurações I2C da lista de periféricos
    i2c_configs = [p for p in block.get('peripherals', []) if p.get('type') == 'I2C']
    print("oiii")
    print(block.items())
    if not i2c_configs:
        print("[I2C] Nenhuma interface I2C configurada. Pulando geração.")
        return []

    # Prepara o mapeamento de Alternate Function (AF) do MCU (usa a constante global MAPPINGS)
    mcu_af_map = _load_mappings().get(microcontroller, {}).get("i2c_af_mapping", {})
    
    i2c_data_for_jinja = []

    # 3. Loop sobre CADA instância I2C (I2C1, I2C2, etc.)
    for cfg in i2c_configs:
        instance = cfg.get("instance", "I2C_UNKNOWN") 
        pins = cfg.get("pins", [])
        
        # Lógica de validação e extração de pinos
        scl_pin_data = next((p for p in pins if 'SCL' in p['name']), None)
        sda_pin_data = next((p for p in pins if 'SDA' in p['name']), None)

        if not scl_pin_data or not sda_pin_data or len(pins) < 2:
            print(f"[I2C] Erro: Configuração de pinos incompleta para {instance}. Ignorando.")
            continue
        
        # 4. Formatação e Mapeamento de AF
        scl_pin_full = f"{scl_pin_data['port'][3]}{scl_pin_data['pin']}"
        sda_pin_full = f"{sda_pin_data['port'][3]}{sda_pin_data['pin']}"
        
        scl_af = mcu_af_map.get(instance, {}).get(scl_pin_full, "GPIO_AF_UNKNOWN")
        sda_af = mcu_af_map.get(instance, {}).get(sda_pin_full, "GPIO_AF_UNKNOWN")

        # 5. Criação do Dicionário Limpo para o Jinja2
        i2c_data_for_jinja.append({
            "num": instance.replace("I2C", ""),
            "interface": instance,
            "address": cfg.get('device_address', '0'),
            
            "scl_port": scl_pin_data['port'][3],
            "scl_pin_num": str(scl_pin_data['pin']),
            "scl_pull": f"GPIO_{scl_pin_data['pull']}",
            "scl_speed": f"GPIO_SPEED_FREQ_{scl_pin_data['speed']}",
            "scl_af": scl_af,
            
            "sda_port": sda_pin_data['port'][3],
            "sda_pin_num": str(sda_pin_data['pin']),
            "sda_pull": f"GPIO_{sda_pin_data['pull']}",
            "sda_speed": f"GPIO_SPEED_FREQ_{sda_pin_data['speed']}",
            "sda_af": sda_af,
        })

    # 6. Renderização
    if not i2c_data_for_jinja:
        return []

    ctx = {"i2c_interfaces": i2c_data_for_jinja}
    print("alou")
    print(ctx)
    
    # Renderiza e salva os arquivos .h e .c uma única vez
    out_h = _render_and_save(TEMPLATE_H_NAME, ctx, OUT_INC / "i2c.h")
    out_c = _render_and_save(TEMPLATE_C_NAME, ctx, OUT_SRC / "i2c.c")

    print(f"[I2C] {len(i2c_data_for_jinja)} instância(s) I2C processadas.")
    return [str(out_h), str(out_c)]