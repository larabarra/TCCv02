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

⚙️ Instalação e Execução
Pré-requisitos
Python 3.9 ou superior

Pip (gerenciador de pacotes do Python)

Passos
Clone o repositório:

git clone <URL_DO_SEU_REPOSITORIO>
cd <NOME_DA_PASTA_DO_PROJETO>

(Recomendado) Crie e ative um ambiente virtual:

python -m venv .venv
# Windows
.\.venv\Scripts\activate


Instale as dependências:
Crie um arquivo requirements.txt na raiz do projeto com o seguinte conteúdo:

jinja2

Em seguida, instale-o:

pip install -r requirements.txt

Execute a aplicação:
O ponto de entrada da UI está no arquivo main.py.

python ui/main.py

# Como Usar
Inicie a aplicação conforme o passo anterior.

Na aba "GPIO / Pinout", selecione o tipo de periférico, instância e função para cada pino que deseja configurar. Adicione-os à tabela.

Vá para as abas específicas de cada periférico (ex: "I2C", "UART/USART") para ajustar os parâmetros detalhados (velocidade, baud rate, etc.). As seções só estarão ativas se você tiver adicionado um pino correspondente na primeira aba.

Clique no botão "Exportar config.json" e selecione uma pasta para salvar os arquivos de configuração (pinout_config.json e peripheral_settings.json).

Clique no botão "Gerar .c/.h", selecione a pasta onde salvou as configurações, e os arquivos de código serão gerados na estrutura de pastas do projeto.

