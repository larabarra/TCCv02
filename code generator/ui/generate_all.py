import json
import os

# Importa os geradores modularizados
from gpio_generator import generate_gpio_config
# from i2c_generator import generate_i2c_config # Adicione este quando criado

# Dicionário de despacho: Mapeia o 'type' do JSON para a função de geração
GENERATORS = {
    "GPIO": generate_gpio_config,
    # "I2C": generate_i2c_config, # Mapeamento para o módulo I2C
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
    
    for block in config_data:
        config_type = block.get("type")
       
        if config_type in GENERATORS:
            generator_func = GENERATORS[config_type]
            print(f"--- Processando bloco: {config_type} ---")
            
            # CHAMA O GERADOR E RECEBE A LISTA [*.c, *.h]
            output_filenames = generator_func(block)
    
        else:
            print(f"AVISO: Tipo de configuração '{config_type}' não possui gerador mapeado.")
            
    print("\nGeração de todos os arquivos concluída!")
    return generated_files # Retorna todos os .c e .h gerados

