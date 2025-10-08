## STM32 Peripheral Configurator & Code Generator
Uma ferramenta com interface gráfica (GUI) desenvolvida em Python para simplificar e acelerar a configuração inicial de periféricos e pinos para microcontroladores STM32, gerando código de inicialização compatível com a biblioteca HAL da ST.

# Visão Geral
Configurar os pinos (GPIO) e periféricos (I2C, UART, etc.) de um STM32 pode ser um processo repetitivo e propenso a erros. Esta ferramenta oferece uma interface visual para selecionar os pinos, configurar os parâmetros de cada periférico e gerar automaticamente os arquivos .c e .h de inicialização, economizando tempo e garantindo consistência.

# Principais Funcionalidades
Interface Gráfica Intuitiva: Selecione pinos e configure periféricos facilmente com tkinter.

Geração de Código Baseada em Templates: Utiliza o motor de templates Jinja2 para criar código C limpo e customizável.

Altamente Configurável: As definições do microcontrolador (pinos, funções alternativas) e os mapeamentos para constantes HAL são carregados a partir de arquivos JSON, permitindo fácil expansão para outros MCUs.

Estrutura Modular: A lógica da UI, os geradores de código e os dados de configuração são separados em módulos distintos, facilitando a manutenção e a adição de novos periféricos.

Exportação de Configurações: Salva as seleções do usuário em arquivos JSON legíveis, separando a configuração de pinos (pinout_config.json) da configuração de parâmetros (peripheral_settings.json).

Screenshot
----
# Como Funciona
O fluxo de trabalho da aplicação é dividido em duas etapas principais: Configuração e Geração.

Configuração (UI):

O usuário interage com a interface gráfica para selecionar os pinos e configurar os parâmetros de periféricos como I2C e UART.

Ao clicar em "Exportar", a UI gera dois arquivos:

pinout_config.json: Descreve quais pinos foram selecionados e suas configurações básicas (modo, pull, etc.).

peripheral_settings.json: Descreve os parâmetros operacionais de cada periférico (ex: baud rate do UART, velocidade do I2C).

Geração (Scripts):

Ao clicar em "Gerar .c/.h", a UI invoca o módulo orquestrador generate_all.py.

O orquestrador lê os dois arquivos JSON.

Ele agrupa as configurações por tipo de periférico e chama o gerador específico (ex: i2c_generator.py).

O gerador específico usa os dados dos JSONs para renderizar os templates Jinja2 (.c e .h).

Os arquivos de código C finais são salvos no diretório de destino.

