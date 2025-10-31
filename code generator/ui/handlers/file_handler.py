# ui/handlers/file_handler.py
import json
import os
import subprocess
import importlib
from collections import defaultdict
from tkinter import filedialog, messagebox
import data

# Port conversion helper function
def _port_to_hal(port_str: str) -> str:

    s = (port_str or "").strip().upper()
    if s.startswith("GPIO"):
        return s
    if len(s) >= 2 and s[0] == "P":
        return "GPIO" + s[1]
    return s or "GPIOA"


def export_config(app):
    """Exports the current pinout and peripheral settings to JSON files.
    
    Prompts user to select a destination folder and saves three configuration files:
    - pinout_config.json
    - peripheral_settings.json  
    - preset_settings.json
    """
    if not app.selections:
        messagebox.showwarning("Nothing to Export", "Please add at least one signal to the pinout table."); return
    
    folder_path = filedialog.askdirectory(title="Select Destination Folder for Configuration Files")
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
        # 3. Erase any previous config files to avoid stale configs
        for fp in (pinout_filepath, peripheral_filepath, preset_filepath):
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception:
                # Non-fatal: continue attempting to write fresh files below
                pass

        # 4. Always (re)create all three files
        with open(pinout_filepath, "w", encoding="utf-8") as f:
            json.dump(pinout_data, f, indent=2, ensure_ascii=False)

        with open(peripheral_filepath, "w", encoding="utf-8") as f:
            json.dump(peripheral_data or {}, f, indent=2, ensure_ascii=False)

        with open(preset_filepath, "w", encoding="utf-8") as f:
            json.dump(preset_data or {}, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Export Successful", (
            "Configuration files recreated successfully in:\n" + folder_path +
            "\n\nFiles:\n- pinout_config.json\n- peripheral_settings.json\n- preset_settings.json"
        ))
    except Exception as e:
        messagebox.showerror("Export Error", str(e))


def build_and_flash(app):
    """Builds the project using CMake and flashes it to the board."""
    try:
        # Change to project root directory (one level up from code generator)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        # Check if code has been generated first
        if not os.path.exists("Core/Src/main.c"):
            messagebox.showwarning("Code Not Generated", "Please generate code first before building and flashing.")
            os.chdir(original_cwd)
            return
        
        messagebox.showinfo("Build & Flash", f"Starting build and flash process...\nWorking directory: {os.getcwd()}")
        
        # Find STM32CubeIDE toolchain
        toolchain_path = None
        possible_paths = [
            r"C:\Users\laram\AppData\Local\stm32cube\bundles\gnu-tools-for-stm32\13.3.1+st.9\bin\arm-none-eabi-gcc.exe",
            r"C:\ST\STM32CubeIDE_1.15.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.1+st.9.win32_1.0.0.202404081157\tools\bin\arm-none-eabi-gcc.exe",
            r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                toolchain_path = os.path.dirname(path)
                break
        
        if not toolchain_path:
            messagebox.showerror("Toolchain Not Found", 
                "STM32 ARM toolchain not found. Please ensure STM32CubeIDE or STM32CubeMX is installed.")
            return
        
        # Set up environment with ARM toolchain
        env = os.environ.copy()
        env["PATH"] = toolchain_path + os.pathsep + env.get("PATH", "")
        
        # First, configure CMake with ARM toolchain
        build_dir = "build"
        
        # Always clean build directory to ensure correct generator is used
        if os.path.exists(build_dir):
            import shutil
            shutil.rmtree(build_dir)
            print(f"Cleaned existing build directory: {build_dir}")
        
        messagebox.showinfo("Configuring", "Configuring CMake with ARM toolchain...")
        
        # Try to find the toolchain file
        toolchain_file = None
        toolchain_candidates = [
            "cmake/gcc-arm-none-eabi.cmake",
            "cmake/stm32cubemx/STM32G474xx.cmake",
            "cmake/stm32cubemx/STM32G4xx.cmake",
            "cmake/stm32cubemx/toolchain.cmake"
        ]
        
        for candidate in toolchain_candidates:
            if os.path.exists(candidate):
                toolchain_file = candidate
                break
        
        config_cmd = ["cmake", "-B", build_dir, "-G", "MinGW Makefiles"]
        if toolchain_file:
            config_cmd.extend(["--toolchain", toolchain_file])
        
        print(f"Running CMake command: {' '.join(config_cmd)}")
        
        config_result = subprocess.run(
            config_cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        if config_result.returncode != 0:
            messagebox.showerror("CMake Config Error", 
                f"CMake configuration failed:\n{config_result.stderr}\n\n"
                f"Tried toolchain file: {toolchain_file or 'None found'}")
            return
        
        # Build the project
        messagebox.showinfo("Building", "Building project...")
        result = subprocess.run(
            ["cmake", "--build", build_dir],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            env=env
        )
        
        if result.returncode == 0:
            messagebox.showinfo("Success", "Build completed successfully!")
            
            # Try to flash if build succeeded
            flash_result = subprocess.run(
                ["cmake", "--build", build_dir, "--target", "flash"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            
            if flash_result.returncode == 0:
                messagebox.showinfo("Flash Success", "Build and flash completed successfully!")
            else:
                messagebox.showwarning("Flash Failed", 
                    f"Build succeeded but flash failed:\n{flash_result.stderr}\n\n"
                    f"You can manually flash the .elf file from the build directory.")
        else:
            messagebox.showerror("Build Error", f"Build failed:\n{result.stderr}")
            
    except subprocess.TimeoutExpired:
        messagebox.showerror("Timeout", "Build/flash process timed out.")
    except FileNotFoundError:
        messagebox.showerror("CMake Not Found", 
            "CMake is not installed or not in PATH.\n\n"
            "Please install CMake and ensure it's available in your system PATH.")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
    finally:
        # Always restore original working directory
        try:
            os.chdir(original_cwd)
        except:
            pass


def generate_files(app):
    """Asks for a folder, loads the config files, and calls the code generator module.
    
    Prompts user to select configuration folder and generates STM32 project files.
    """
    folder_path = filedialog.askdirectory(title="Select Folder with Configuration Files")
    if not folder_path: return
    
    pinout_path = os.path.join(folder_path, "pinout_config.json")
    settings_path = os.path.join(folder_path, "peripheral_settings.json")
    presets_path = os.path.join(folder_path, "preset_settings.json")

    try:
        with open(pinout_path, "r", encoding="utf-8") as f: pinout_data = json.load(f)
    except Exception as e:
        messagebox.showerror("Read Error", f"Could not read 'pinout_config.json':\n{e}"); return

    peripheral_data = {}
    try:
        with open(settings_path, "r", encoding="utf-8") as f: peripheral_data = json.load(f)
    except FileNotFoundError:
        print("Info: 'peripheral_settings.json' not found. Continuing without peripheral-specific settings.")
    except Exception as e:
        messagebox.showerror("Read Error", f"Error processing 'peripheral_settings.json':\n{e}"); return
    
    preset_settings = {}

    try:
        with open(presets_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            # Accepts both list (legacy) and new dict {"cases":[...]}
            if isinstance(raw, list):
                # Only use if list is not empty
                if raw:
                    preset_settings = {"cases": raw}
            elif isinstance(raw, dict):
                # Ensure "cases" key
                if "cases" in raw and isinstance(raw["cases"], list):
                    # Only use if cases list is not empty
                    if raw["cases"]:
                        preset_settings = raw
                elif raw:
                    # Only treat as single case if dict has meaningful content
                    # Check if dict has any non-empty values
                    if any(v for v in raw.values() if v):
                        preset_settings = {"cases": [raw]}
                # If raw is empty dict {}, preset_settings stays {}
    except FileNotFoundError:
        preset_settings = {}

    try:
        gen = importlib.import_module("generators.generate_all")
        out_files = gen.generate_project_files(pinout_data, peripheral_data,preset_settings)
        if out_files:
            messagebox.showinfo("Generation Complete", "Generated files:\n\n" + "\n".join(out_files))
        else:
            messagebox.showinfo("Generation Complete", "No files were reported. Check the console.")
    except Exception as e:
        messagebox.showerror("Generation Error", str(e))


def get_pinout_config(app) -> dict:
    """Extracts pinout configuration from the application state.
    
    Args:
        app: Application instance with selections.
        
    Returns:
        Dictionary with project name, microcontroller, and GPIO entries.
    """
    project_name = (app.ent_project.get().strip() if getattr(app, "ent_project", None) else "") or "MyProject"
    micro        = getattr(app, "current_mcu", "")

    gpio_entries = []
    for r in getattr(app, "selections", []):
        # Extract alternate function: handle both "GPIO_AF4_I2C1" and "4" formats
        af_value = r.get("alternate_fn", 0) or 0
        if isinstance(af_value, str) and af_value.startswith("GPIO_AF"):
            # Extract number from "GPIO_AF4_I2C1" -> store the full string
            alternate_fn = af_value
        elif isinstance(af_value, str) and af_value.isdigit():
            # If it's a string number like "4", convert to int then back to string
            alternate_fn = f"GPIO_AF{af_value}"
        elif isinstance(af_value, int):
            # If it's an int, format as GPIO_AFx
            alternate_fn = f"GPIO_AF{af_value}" if af_value > 0 else ""
        else:
            alternate_fn = ""
        
        gpio_entries.append({
            "name":         r.get("name", ""),
            "port":         _port_to_hal(r.get("port", "")),              # Convert to GPIOA/GPIOB/...
            "pin":          int(str(r.get("pin", 0))),                    # Pin number as int
            "mode":         (r.get("mode", "INPUT") or "INPUT").upper(),  # INPUT/OUTPUT_PP/AF_PP...
            "pull":         (r.get("pull", "NOPULL") or "NOPULL").upper(),
            "speed":        (r.get("speed", "LOW") or "LOW").upper(),
            "alternate_fn": alternate_fn,                                  # Full AF constant string
        })

    return {
        "project_name":   project_name,
        "microcontroller": micro,
        "gpio": gpio_entries,
    }

def get_peripheral_settings(app) -> dict:
    """Gathers all peripheral settings directly from the UI tabs for active peripherals.
    
    Processes I2C and UART peripheral configurations from the application state.
    """
    settings = {}
    
    # Process all active I2C peripherals based on the pinout selection
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
    """Consolidates selected use cases into a stable dict for preset_settings.json.
    
    - Accepts both app.use_cases (list) and app.use_case_config (single).
    - Maps user-friendly fields to HAL using map_use_case_to_hal.
    
    Args:
        app: Application instance with use case configurations.
        
    Returns:
        Dictionary with "cases" key containing mapped use cases.
    """
    # Collect cases from app
    cases = []
    if hasattr(app, "use_cases") and isinstance(app.use_cases, list) and app.use_cases:
        cases = app.use_cases
    elif hasattr(app, "use_case_config") and app.use_case_config:
        cases = [app.use_case_config]

    # Normalize and map to HAL
    mapped = []
    for c in cases:
        try:
            mc = map_use_case_to_hal(c) or c
            mapped.append(mc)
        except Exception:
            mapped.append(c)

    # If nothing, return {}
    if not mapped:
        return {}

    # Always use dict (avoids "list[Unknown]..." error)
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

