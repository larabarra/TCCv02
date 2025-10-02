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


def generate_i2c_config(i2c_blocks: list[dict]) -> list[str]:

    # 1. Extrair Contexto Principal

    i2c_interfaces = []
    
    # Mapeamento para garantir que os nomes das configurações no JSON (PULLUP)
    # sejam convertidos para as constantes do HAL (GPIO_PULLUP).
    map_pull = {
        "NOPULL": "GPIO_NOPULL",
        "PULLUP": "GPIO_PULLUP",
        "PULLDOWN":"GPIO_PULLDOWN",
    }
    map_speed = {
        "LOW":       "GPIO_SPEED_FREQ_LOW",
        "MEDIUM":    "GPIO_SPEED_FREQ_MEDIUM",
        "HIGH":      "GPIO_SPEED_FREQ_HIGH",
        "VERY_HIGH": "GPIO_SPEED_FREQ_VERY_HIGH",
    }

    for block in i2c_blocks:
        
        # 1. Extração de Metadados da Instância
        instance = block.get('instance')  # Ex: "I2C1"
        pins_list = block.get('pins', [])
        
        if not instance or not pins_list:
            continue # Ignora blocos malformados
            
        # Extrai o número da instância (1, 2, etc.)
        instance_num = int(instance.replace("I2C", ""))
        
        # 2. Identificação dos Pinos SCL e SDA (O Ideal)
        scl_pin_data = None
        sda_pin_data = None
        
        # Itera sobre os pinos e usa o nome para identificação
        for pin_data in pins_list:
            name = pin_data.get('name', '').upper()
            if 'SCL' in name:
                scl_pin_data = pin_data
            elif 'SDA' in name:
                sda_pin_data = pin_data
        
        # Garante que ambos os pinos foram encontrados antes de continuar
        if scl_pin_data is None or sda_pin_data is None:
            # Em um sistema real, você registraria um erro aqui
            print(f"ERRO: Pinos SCL ou SDA não encontrados para {instance}. Ignorando o bloco.")
            continue
        
        # 3. Criação do Objeto de Contexto da Interface
        interface_context = {
            "num": instance_num,                 # 1 ou 2 (para I2C1, I2C2)
            "interface": instance,               # I2C1 ou I2C2 (para hi2c1.Instance = I2C1;)
            
            # --- Dados do SCL ---
            "scl_port": scl_pin_data['port'][3], # 'GPIOB' -> 'B' (para __HAL_RCC_GPIOB_CLK_ENABLE())
            "scl_pin_num": scl_pin_data['pin'],  # 6 (para GPIO_PIN_6)
            "scl_pull": map_pull[scl_pin_data['pull']], # Ex: "GPIO_PULLUP"
            "scl_speed": map_speed[scl_pin_data['speed']], # Ex: "GPIO_SPEED_FREQ_VERY_HIGH"
            "scl_af": scl_pin_data['alternate_fn'], # Ex: 4 (para AF4)

            # --- Dados do SDA ---
            "sda_port": sda_pin_data['port'][3], 
            "sda_pin_num": sda_pin_data['pin'],
            "sda_pull": map_pull[sda_pin_data['pull']],
            "sda_speed": map_speed[sda_pin_data['speed']],
            "sda_af": sda_pin_data['alternate_fn'],
        }
        
        i2c_interfaces.append(interface_context)

    # 6. Renderização
    if not i2c_interfaces:
        return []

    ctx = {"i2c_interfaces": i2c_interfaces}

    # Renderiza e salva os arquivos .h e .c uma única vez
    out_h = _render_and_save(TEMPLATE_H_NAME, ctx, OUT_INC)
    out_c = _render_and_save(TEMPLATE_C_NAME, ctx, OUT_SRC)

    print(f"[I2C] {len(i2c_interfaces)} instância(s) I2C processadas.")

    return [str(out_h), str(out_c)]
    