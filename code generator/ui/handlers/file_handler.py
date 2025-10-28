# ui/handlers/file_handler.py
import json
import os
import importlib
from collections import defaultdict
from tkinter import filedialog, messagebox
import data

# --- ADICIONE perto do topo (após imports) ---
def _port_to_hal(port_str: str) -> str:

    s = (port_str or "").strip().upper()
    if s.startswith("GPIO"):
        return s
    if len(s) >= 2 and s[0] == "P":
        return "GPIO" + s[1]
    return s or "GPIOA"


def export_config(app):
    """
    Exports the current pinout and peripheral settings to JSON files.
    """
    if not app.selections:
        messagebox.showwarning("Nada a Exportar", "Adicione pelo menos um sinal à tabela de pinout."); return
    
    folder_path = filedialog.askdirectory(title="Selecione a Pasta de Destino para os Ficheiros de Configuração")
    if not folder_path: return

    # 1. Get the three main data dictionaries from the current UI state.
    pinout_data = get_pinout_config(app)
    peripheral_data = get_peripheral_settings(app)
    preset_data = get_preset_config(app)


    pinout_data.setdefault("artifact_manifest", {})
    pinout_data["artifact_manifest"]["peripheral_settings"] = {
    "present": bool(peripheral_data),
    "filename": "peripheral_settings.json"
    }

    pinout_data["artifact_manifest"]["preset_settings"] = {
    "present": bool(preset_data),
    "filename": "preset_settings.json"
    }


    # 2. Define file paths.
    pinout_filepath = os.path.join(folder_path, "pinout_config.json")
    peripheral_filepath = os.path.join(folder_path, "peripheral_settings.json")
    preset_filepath = os.path.join(folder_path, "preset_settings.json")

    try:
        # 3. Save the files.
        with open(pinout_filepath, "w", encoding="utf-8") as f:
            json.dump(pinout_data, f, indent=2, ensure_ascii=False)
        
        # Only save the settings file if there are any peripheral configurations.
        if peripheral_data:
            with open(peripheral_filepath, "w", encoding="utf-8") as f:
                json.dump(peripheral_data, f, indent=2, ensure_ascii=False)
        
        if preset_data:
            with open(preset_filepath, "w", encoding="utf-8") as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Exportação Concluída", f"Ficheiros de configuração salvos com sucesso em:\n{folder_path}")
    except Exception as e:
        messagebox.showerror("Erro Durante a Exportação", str(e))


def generate_files(app):
    """Asks for a folder, loads the config files, and calls the code generator module."""
    folder_path = filedialog.askdirectory(title="Selecione a Pasta com os Ficheiros de Configuração")
    if not folder_path: return
    
    pinout_path = os.path.join(folder_path, "pinout_config.json")
    settings_path = os.path.join(folder_path, "peripheral_settings.json")
    presets_path = os.path.join(folder_path, "preset_settings.json")

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
    
    preset_settings = {}

    try:
        with open(presets_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            # Aceita tanto lista (legado) quanto dict novo {"cases":[...]}
            if isinstance(raw, list):
                preset_settings = {"cases": raw}
            elif isinstance(raw, dict):
                # Garante chave "cases"
                if "cases" in raw and isinstance(raw["cases"], list):
                    preset_settings = raw
                else:
                    # tolerante: se não tiver "cases", mas for um dict válido de um caso único
                    preset_settings = {"cases": [raw]}
    except FileNotFoundError:
        preset_settings = {}

    try:
        gen = importlib.import_module("generators.generate_all")
        out_files = gen.generate_project_files(pinout_data, peripheral_data,preset_settings)
        if out_files:
            messagebox.showinfo("Geração Concluída", "Ficheiros gerados:\n\n" + "\n".join(out_files))
        else:
            messagebox.showinfo("Geração Concluída", "Nenhum ficheiro foi reportado. Verifique a consola.")
    except Exception as e:
        messagebox.showerror("Erro de Geração", str(e))


def get_pinout_config(app) -> dict:

    project_name = (app.ent_project.get().strip() if getattr(app, "ent_project", None) else "") or "MyProject"
    micro        = getattr(app, "current_mcu", "")

    gpio_entries = []
    for r in getattr(app, "selections", []):
        gpio_entries.append({
            "name":         r.get("name", ""),
            "port":         _port_to_hal(r.get("port", "")),              # --> GPIOA/GPIOB/...
            "pin":          int(str(r.get("pin", 0))),                    # int
            "mode":         (r.get("mode", "INPUT") or "INPUT").upper(),  # INPUT/OUTPUT_PP/AF_PP...
            "pull":         (r.get("pull", "NOPULL") or "NOPULL").upper(),
            "speed":        (r.get("speed", "LOW") or "LOW").upper(),
            "alternate_fn": int(str(r.get("alternate_fn", 0) or 0)),      # AF numérico
        })

    return {
        "project_name":   project_name,
        "microcontroller": micro,
        "gpio": gpio_entries,
    }

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


def get_preset_config(app) -> dict:
    """
    Consolida os casos de uso selecionados em um dict estável para preset_settings.json.
    - Aceita tanto app.use_cases (lista) quanto app.use_case_config (único).
    - Mapeia campos legíveis p/ HAL usando map_use_case_to_hal.
    """
    # Coleta casos do app
    cases = []
    if hasattr(app, "use_cases") and isinstance(app.use_cases, list) and app.use_cases:
        cases = app.use_cases
    elif hasattr(app, "use_case_config") and app.use_case_config:
        cases = [app.use_case_config]

    # Normaliza e mapeia para HAL
    mapped = []
    for c in cases:
        try:
            mc = map_use_case_to_hal(c) or c
            mapped.append(mc)
        except Exception:
            mapped.append(c)

    # Se não houver nada, retorne {}
    if not mapped:
        return {}

    # Use SEMPRE dict (evita o erro “list[Unknown]…”)
    return {"cases": mapped}

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

