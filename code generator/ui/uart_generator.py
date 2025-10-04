# gpio_generator.py (Atualizado para gerar .c e .h)

from __future__ import annotations
import os, json,re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

THIS = Path(__file__).resolve()               # .../TCCV02/code generator/gpio_generator.py
GEN_DIR = THIS.parent                         # .../TCCV02/code generator
PROJ_ROOT = GEN_DIR.parent.parent                    # .../TCCV02

# Paths de templates 
TPL_DIR_INC = GEN_DIR /  "inc"
TPL_DIR_SRC = GEN_DIR /  "src"

# Saída nos diretórios padrão do Cube
OUT_INC = PROJ_ROOT / "core" / "inc" / "uart.h"
OUT_SRC = PROJ_ROOT / "core" / "src" / "uart.c"
MAP_PATH = GEN_DIR / "mapping.json"
# Nomes dos arquivos de template
TEMPLATE_C_NAME = "uart_template.c"
TEMPLATE_H_NAME = "uart_template.h"

env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False,
)

def _load_mappings() -> dict:
    """Carrega o arquivo mapping.json."""
    try:
        with open(MAP_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar {MAP_PATH.name}: {e}")
        return {}

def _digits(s: str) -> str:
    """Extrai apenas os números de uma string (e.g., 'UART1' -> '1')."""
    m = re.findall(r"\d+", s or "")
    return m[0] if m else ""

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


def generate_uart_config(block: list[dict]) -> list[str]:

    mcu_af_map = _load_mappings()
    af_mapping = mcu_af_map.get("STM32G474RE", {}).get("uart_af_mapping", {})

    gpio_blocks = block
    pins = []

    uart_interfaces_list = []
        
    for cfg in gpio_blocks:
        instance = cfg.get('instance', 'UART_UNKNOWN')
        pins = cfg.get('pins', [])
        
        # 1. Agrupamento de pinos TX/RX
        tx_pin_data = next((p for p in pins if 'TX' in p['name']), None)
        rx_pin_data = next((p for p in pins if 'RX' in p['name']), None)
    
        # Validação básica
        if not tx_pin_data or not rx_pin_data:
            print(f"Alerta: Pinos TX/RX incompletos para {instance}. Pulando.")
            continue

    
        # 2. Busca e Formatação da Alternate Function (AF)
        
        # Constrói a chave de busca para o mapping.json (e.g., 'PA9', 'PB10')
        tx_pin_full = f"{tx_pin_data['port'][3]}{tx_pin_data['pin']}"
        rx_pin_full = f"{rx_pin_data['port'][3]}{rx_pin_data['pin']}"


    
        # Busca a macro AF completa no mapping.json
        # Nota: O 'instance' aqui pode ser 'UART1' ou 'USART1'
        af_instance_key = instance.replace('UART', 'USART').replace('USART', 'USART') 

        tx_af = af_mapping.get(af_instance_key, {}).get(tx_pin_full, f"GPIO_AF{tx_pin_data['alternate_fn']}_{instance}")
        rx_af = af_mapping.get(af_instance_key, {}).get(rx_pin_full, f"GPIO_AF{rx_pin_data['alternate_fn']}_{instance}")
        
        
        uart_interfaces_list.append({
            "num": _digits(instance),
            "interface": instance,
            "baud_rate": 115200, # Valor fixo ou virá do JSON se você adicionar a opção na UI
            
            # TX - Dados formatados
            "tx_port": tx_pin_data['port'][3],
            "tx_pin_num": str(tx_pin_data['pin']),
            "tx_pull": f"GPIO_{tx_pin_data['pull']}",
            "tx_speed": f"GPIO_SPEED_FREQ_{tx_pin_data['speed']}",
            "tx_af": tx_af,
            
            # RX - Dados formatados
            "rx_port": rx_pin_data['port'][3],
            "rx_pin_num": str(rx_pin_data['pin']),
            "rx_pull": f"GPIO_{rx_pin_data['pull']}",
            "rx_speed": f"GPIO_SPEED_FREQ_{rx_pin_data['speed']}",
            "rx_af": rx_af,
        })

        # 3. Renderização
    if not uart_interfaces_list:
        print("[UART] Nenhuma interface UART válida para renderizar.")
        return[]
        
    ctx = {"uart_interfaces": uart_interfaces_list}

    # Chama a função de renderização (substitua a chamada real no seu código)
    # out_h = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC / "uart.h")
    # out_c = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC / "uart.c")

    print(f"[UART] {len(uart_interfaces_list)} instância(s) UART prontas para renderização.")

    out_h = _render_and_save(TEMPLATE_H_NAME, ctx, OUT_INC)
    out_c = _render_and_save(TEMPLATE_C_NAME, ctx, OUT_SRC)

    return [str(out_c), str(out_h)]

