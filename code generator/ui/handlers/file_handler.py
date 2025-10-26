# ui/handlers/file_handler.py
import json
import os
import importlib
from collections import defaultdict
from tkinter import filedialog, messagebox
import data

def export_config(app):
    """
    Exports the current pinout and peripheral settings to JSON files.
    """
    if not app.selections:
        messagebox.showwarning("Nada a Exportar", "Adicione pelo menos um sinal à tabela de pinout."); return
    
    folder_path = filedialog.askdirectory(title="Selecione a Pasta de Destino para os Ficheiros de Configuração")
    if not folder_path: return

    # 1. Get the two main data dictionaries from the current UI state.
    pinout_data = get_pinout_config(app)
    peripheral_data = get_peripheral_settings(app)

    # 2. Define file paths.
    pinout_filepath = os.path.join(folder_path, "pinout_config.json")
    peripheral_filepath = os.path.join(folder_path, "peripheral_settings.json")

    try:
        # 3. Save the files.
        with open(pinout_filepath, "w", encoding="utf-8") as f:
            json.dump(pinout_data, f, indent=2, ensure_ascii=False)
        
        # Only save the settings file if there are any peripheral configurations.
        if peripheral_data:
            with open(peripheral_filepath, "w", encoding="utf-8") as f:
                json.dump(peripheral_data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Exportação Concluída", f"Ficheiros de configuração salvos com sucesso em:\n{folder_path}")
    except Exception as e:
        messagebox.showerror("Erro Durante a Exportação", str(e))


def generate_files(app):
    """Asks for a folder, loads the config files, and calls the code generator module."""
    folder_path = filedialog.askdirectory(title="Selecione a Pasta com os Ficheiros de Configuração")
    if not folder_path: return
    
    pinout_path = os.path.join(folder_path, "pinout_config.json")
    settings_path = os.path.join(folder_path, "peripheral_settings.json")
    
    try:
        with open(pinout_path, "r", encoding="utf-8") as f: pinout_data = json.load(f)
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Não foi possível ler 'pinout_config.json':\n{e}"); return

    peripheral_data = {}
    try:
        with open(settings_path, "r", encoding="utf-8") as f: peripheral_data = json.load(f)
    except FileNotFoundError:
        print("Info: 'peripheral_settings.json' not found. Continuing without peripheral-specific settings.")
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Erro ao processar 'peripheral_settings.json':\n{e}"); return

    try:
        gen = importlib.import_module("generators.generate_all")
        # The generator function now only needs to accept two arguments.
        out_files = gen.generate_project_files(pinout_data, peripheral_data)
        if out_files:
            messagebox.showinfo("Geração Concluída", "Ficheiros gerados:\n\n" + "\n".join(out_files))
        else:
            messagebox.showinfo("Geração Concluída", "Nenhum ficheiro foi reportado. Verifique a consola.")
    except Exception as e:
        messagebox.showerror("Erro de Geração", str(e))



def get_pinout_config(app) -> dict:
    """Gathers all pinout data from the main selection table."""
    project_name = app.ent_project.get().strip() or "MyProject"; micro = app.current_mcu
    grouped = defaultdict(list); [grouped.setdefault(r["type"], []).append(r) for r in app.selections]
    peripherals = []
    for t, rows in grouped.items():
        if t == "GPIO": peripherals.append({"type": t, "pins": [{k: v for k, v in x.items() if k not in ['type', 'instance']} for x in rows]})
        else:
            by_inst = defaultdict(list); [by_inst[x["instance"]].append(x) for x in rows]
            for inst, lst in by_inst.items(): peripherals.append({"type": t if t != "UART" else "USART", "instance": inst, "pins": [{k: v for k, v in x.items() if k not in ['type', 'instance']} for x in lst]})
    return {"project_name": project_name, "microcontroller": micro, "peripherals": peripherals}

def get_peripheral_settings(app) -> dict:
    """Gathers all peripheral settings directly from the UI tabs for active peripherals."""
    settings = {}
    
    # Process all active I2C peripherals based on the pinout selection.
    active_i2c = {r['instance'] for r in app.selections if r['type'] == 'I2C'}
    if active_i2c:
        settings["I2C"] = {}
        for inst_name in active_i2c:
            if inst_name in app.i2c_widgets:
                widgets = app.i2c_widgets[inst_name]
                i2c_settings = {
                    "clockSpeed": widgets['speed'].get(), 
                    "addressingMode": widgets['addr_mode'].get(), 
                    "transferMode": widgets['transfer'].get(), 
                    "devices": _get_i2c_devices_from_tree(app, inst_name)
                }
                map_peripheral_to_hal(i2c_settings, "I2C")
                settings["I2C"][inst_name] = i2c_settings

    # Process all active UART peripherals based on the pinout selection.
    active_uart = {r['instance'] for r in app.selections if r['type'] in ['UART', 'USART']}
    if active_uart:
        settings["UART"] = {}
        for inst_name in active_uart:
            if inst_name in app.uart_widgets:
                widgets = app.uart_widgets[inst_name]
                uart_settings = {
                    "baudRate": widgets['baud_rate'].get(), 
                    "wordLength": widgets['word_length'].get(), 
                    "stopBits": widgets['stop_bits'].get(), 
                    "parity": widgets['parity'].get(), 
                    "flowControl": widgets['flow_control'].get(), 
                    "transferMode": widgets['transfer_mode'].get()
                }
                map_peripheral_to_hal(uart_settings, "UART")
                settings["UART"][inst_name] = uart_settings
                
    return settings

def _get_i2c_devices_from_tree(app, instance_name):
    """Helper function to extract device list from an I2C treeview."""
    devices_list = []
    widgets = app.i2c_widgets.get(instance_name, {})
    tree = widgets.get('devices_tree')
    if tree:
        for item_id in tree.get_children():
            values = tree.item(item_id, 'values')
            devices_list.append({"name": values[0], "address": values[1]})
    return devices_list

def map_peripheral_to_hal(peripheral, p_type):
    """Helper function to map user-friendly UI strings to HAL constants."""
    if not peripheral: return
    if p_type == "I2C":
        peripheral["clockSpeed"] = data.HAL_MAPPINGS.get("I2C", {}).get("clockSpeed", {}).get(peripheral["clockSpeed"])
        peripheral["addressingMode"] = data.HAL_MAPPINGS.get("I2C", {}).get("addressingMode", {}).get(peripheral["addressingMode"])
        peripheral["transferMode"] = peripheral.get("transferMode", "POLLING").upper()
        for device in peripheral.get("devices", []):
            try: device["address"] = int(device["address"], 0)
            except (ValueError, TypeError): device["address"] = 0
    elif p_type == "UART":
        peripheral["baudRate"] = int(peripheral.get("baudRate", "0"))
        peripheral["wordLength"] = data.HAL_MAPPINGS.get("UART", {}).get("wordLength", {}).get(peripheral["wordLength"])
        peripheral["stopBits"] = data.HAL_MAPPINGS.get("UART", {}).get("stopBits", {}).get(peripheral["stopBits"])
        peripheral["parity"] = data.HAL_MAPPINGS.get("UART", {}).get("parity", {}).get(peripheral["parity"])
        peripheral["flowControl"] = data.HAL_MAPPINGS.get("UART", {}).get("flowControl", {}).get(peripheral["flowControl"])
        peripheral["transferMode"] = peripheral.get("transferMode", "POLLING").upper()

def map_use_case_to_hal(use_case_config):
    if not use_case_config: return None
    mapped_config = json.loads(json.dumps(use_case_config))
    for key in ["input_peripheral", "output_peripheral"]:
        peripheral = mapped_config.get("peripheral_settings", {}).get(key)
        if peripheral: map_peripheral_to_hal(peripheral, peripheral.get("type"))
    return mapped_config

