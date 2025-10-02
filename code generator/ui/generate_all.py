import json
import os
from collections import defaultdict

# Importa os geradores modularizados
from gpio_generator import generate_gpio_config
from i2c_generator import generate_i2c_config
# from i2c_generator import generate_i2c_config # Adicione este quando criado

# Dicionário de despacho: Mapeia o 'type' do JSON para a função de geração
GENERATORS = {
    "GPIO": generate_gpio_config,
    "I2C": generate_i2c_config, 
    # "UART": generate_uart_config,
}

def load_config_data(json_file_path):
    """Carrega os dados de configuração do JSON."""
    with open(json_file_path, 'r') as f:
        return json.load(f)


def generate_project_files(config_data):
    """
    Itera os blocos de configuração e chama o gerador correto.
    """
    generated_files = []
    
    grouped_configs = defaultdict(list)


    for block in config_data:
        config_type = block.get("type")
        if config_type:
            grouped_configs[config_type].append(block)

    print(grouped_configs)
    for config_type, config_list in grouped_configs.items():
        if config_type in GENERATORS:
            generator_func = GENERATORS[config_type] 
            print(f"--- Processando : {config_type} ({len(config_list)} instância(s)) ---")
            
            # CHAMA O GERADOR UMA ÚNICA VEZ COM TODOS OS DADOS
            output_filenames = generator_func(config_list)
    
        else:
            print(f"AVISO: Tipo de configuração '{config_type}' não possui gerador mapeado.")
            
    print("\nGeração de todos os arquivos concluída!")
    return generated_files # Retorna todos os .c e .h gerados

