#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py

from collections import defaultdict
import json
import importlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os 


# Import custom modules
import data
import utils
import tab_gpio
import tab_i2c
import tab_uart

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # --- Load initial data ---
        if not data.load_initial_mapping():
            messagebox.showerror("Fatal Error", "Could not load 'pin_map.json'. The application will now close.")
            self.destroy()
            return

        # --- Load HAL mappings ---

        if not data.load_hal_mappings(): # <-- LINHA MODIFICADA
            messagebox.showerror("Fatal Error", "Could not load 'hal_map.json'. The application will now close.")
            self.destroy()
            return


        self.title("STM32G474 — Config Generator")
        self.geometry("1150x740")
        self.minsize(980, 620)

        # --- Application State ---
        self.current_mcu = list(data.MCU_MAP.keys())[0]
        self.mcu_data = data.MCU_MAP[self.current_mcu]
        self.selections = []  # List of dictionaries for selected pins
        self.i2c_frames = {}  # To hold references to I2C configuration frames
        self.uart_frames = {}   # To hold references to UART configuration frames
        self._build_ui()
        self._refresh_mapping_view()
        self._update_i2c_tab_state()
        self._update_uart_tab_state()
        self._on_type_change() # Set initial state for the GPIO tab

    # ---------------- UI BUILDING ----------------
    def _build_ui(self):
        # --- Top frame with project name, MCU selector, and main buttons ---
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Project:").pack(side="left")
        self.ent_project = ttk.Entry(top, width=24)
        self.ent_project.insert(0, "MyProject")
        self.ent_project.pack(side="left", padx=(4,12))

        ttk.Label(top, text="MCU:").pack(side="left")
        self.cmb_mcu = ttk.Combobox(top, values=list(data.MCU_MAP.keys()), state="readonly", width=16)
        self.cmb_mcu.set(self.current_mcu)
        self.cmb_mcu.pack(side="left", padx=(4,12))
        self.cmb_mcu.bind("<<ComboboxSelected>>", self._on_mcu_change)

        ttk.Button(top, text="Load Mapping JSON...", command=self.load_mapping_json).pack(side="right", padx=4)
        ttk.Button(top, text="Generate .c/.h", command=self.generate_files).pack(side="right", padx=4)
        ttk.Button(top, text="Export project configs", command=self.export_config).pack(side="right", padx=4)

        # --- Main paned window for GPIO list and Notebook ---
        mid = ttk.Panedwindow(self, orient="horizontal")
        mid.pack(fill="both", expand=True, padx=6, pady=6)

        # --- Left pane: Available GPIOs ---
        left = ttk.Frame(mid, padding=6)
        mid.add(left, weight=1)
        ttk.Label(left, text="Available GPIOs").pack(anchor="w")
        self.lst_gpio = tk.Listbox(left, height=20)
        self.lst_gpio.pack(fill="both", expand=True)

        # --- Right pane: Notebook with configuration tabs ---
        notebook = ttk.Notebook(mid)
        mid.add(notebook, weight=2)

        # Create frames for each tab
        tab_gpio_frame = ttk.Frame(notebook, padding=6)
        tab_i2c_frame = ttk.Frame(notebook, padding=6)
        tab_uart_frame = ttk.Frame(notebook, padding=6)

        # Add frames to the notebook
        notebook.add(tab_gpio_frame, text="Pinout")
        notebook.add(tab_i2c_frame, text="I2C")
        notebook.add(tab_uart_frame, text="UART/USART")
        
        # Populate tabs by calling functions from other modules
        tab_gpio.create_gpio_tab(tab_gpio_frame, self)
        tab_i2c.create_i2c_tab(tab_i2c_frame, self)
        tab_uart.create_uart_tab(tab_uart_frame, self)

    # ---------------- I2C TAB LOGIC ----------------
    def _set_widget_state(self, parent_widget, state='disabled'):
        """Recursively enable or disable all child widgets of a parent."""
        for child in parent_widget.winfo_children():
            try:
                child.configure(state=state)
                self._set_widget_state(child, state)
            except tk.TclError:
                pass # Some widgets like Labels don't have a 'state' option

    def _update_i2c_tab_state(self):
        """Enable I2C config frames only if a corresponding I2C pin is selected."""
        active_i2c_instances = {r['instance'] for r in self.selections if r['type'] == 'I2C'}
        for instance_name, frame in self.i2c_frames.items():
            if instance_name in active_i2c_instances:
                self._set_widget_state(frame, 'normal')
            else:
                self._set_widget_state(frame, 'disabled')

    # ---------------- UART TAB LOGIC ----------------

    def _update_uart_tab_state(self):
        """Enable UART config frames only if a corresponding UART/USART pin is selected."""
        # Check for both 'UART' and 'USART' types
        active_uart_instances = {r['instance'] for r in self.selections if r['type'] in ['UART', 'USART']}
        
        for instance_name, frame in self.uart_frames.items():
            if instance_name in active_uart_instances:
                self._set_widget_state(frame, 'normal')
            else:
                self._set_widget_state(frame, 'disabled')

    # ---------------- DATA & MAPPING LOGIC ----------------
    def _on_mcu_change(self, event=None):
        """Handle MCU selection change."""
        self.current_mcu = self.cmb_mcu.get()
        self.mcu_data = data.MCU_MAP[self.current_mcu]
        self._refresh_mapping_view()
        self._on_type_change()

    def _refresh_mapping_view(self):
        """Update the available GPIO listbox."""
        self.lst_gpio.delete(0, "end")
        for p in self.mcu_data.get("gpio_pins", []):
            self.lst_gpio.insert("end", p)

    def load_mapping_json(self):
        """Load a new MCU mapping from a JSON file."""
        path = filedialog.askopenfilename(title="Open Mapping JSON", filetypes=[("JSON","*.json"), ("All files","*.*")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            data.MCU_MAP = loaded_data
            self.cmb_mcu["values"] = list(data.MCU_MAP.keys())
            self.cmb_mcu.set(list(data.MCU_MAP.keys())[0])
            self._on_mcu_change()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load mapping:\n{e}")

    # ---------------- GPIO TAB EVENT HANDLERS (CALLBACKS) ----------------
    def _on_type_change(self, event=None):
        """Handle peripheral type change."""
        t = self.cmb_type.get()
        self.cmb_inst["values"] = []
        self.cmb_role["values"] = []
        self.cmb_pin["values"] = []
        self.cmb_inst.set(""); self.cmb_role.set(""); self.cmb_pin.set("")
        self.ent_label.delete(0, "end")
        
        if t == "GPIO":
            self.cmb_mode.set("INPUT"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("LOW")
            self.ent_af.delete(0, "end")
            self.cmb_inst.configure(state="disabled"); self.cmb_role.configure(state="disabled")
            self.cmb_pin.configure(state="readonly")
            pins = self.mcu_data.get("gpio_pins", [])
            self.cmb_pin["values"] = pins
            if pins: self.cmb_pin.set(pins[0]); self._on_pin_change()
        else:
            self.cmb_inst.configure(state="readonly"); self.cmb_role.configure(state="readonly"); self.cmb_pin.configure(state="readonly")
            if t == "I2C": insts = list(self.mcu_data.get("i2c_interfaces", {}).keys())
            elif t == "UART": insts = list(self.mcu_data.get("uart_interfaces", {}).keys())
            elif t == "SPI": insts = list(self.mcu_data.get("spi_interfaces", {}).keys())
            elif t == "ADC": insts = list(self.mcu_data.get("adc_interfaces", {}).keys())
            else: insts = []
            self.cmb_inst["values"] = insts
            if insts: self.cmb_inst.set(insts[0]); self._on_instance_change()

    def _on_instance_change(self, event=None):
        """Handle peripheral instance change."""
        t = self.cmb_type.get(); inst = self.cmb_inst.get()
        if t == "I2C": roles = ["scl","sda"]
        elif t == "UART": roles = ["tx","rx"]
        elif t == "SPI": roles = ["sck","miso","mosi"]
        elif t == "ADC": roles = self.mcu_data.get("adc_interfaces", {}).get(inst, [])
        else: roles = []
        self.cmb_role["values"] = roles
        self.cmb_role.set(roles[0] if roles else "")
        self._on_role_change()

    def _on_role_change(self, event=None):
        """Handle pin function/role change."""
        t = self.cmb_type.get(); inst = self.cmb_inst.get(); role = self.cmb_role.get()
        pins = []
        if t == "I2C":
            pins = self.mcu_data.get("i2c_interfaces", {}).get(inst, {}).get(role, [])
            self.cmb_mode.set("AF_OD"); self.cmb_pull.set("PULLUP"); self.cmb_speed.set("VERY_HIGH")
        elif t == "UART":
            pins = self.mcu_data.get("uart_interfaces", {}).get(inst, {}).get(role, [])
            self.cmb_mode.set("AF_PP"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("VERY_HIGH")
        elif t == "SPI":
            pins = self.mcu_data.get("spi_interfaces", {}).get(inst, {}).get(role, [])
            self.cmb_mode.set("AF_PP"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("VERY_HIGH")
        elif t == "ADC":
            p = self.mcu_data.get("adc_pin_mapping", {}).get(inst, {}).get(role, "")
            pins = [p] if p else []
            self.cmb_mode.set("ANALOG"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("LOW")
        self.cmb_pin["values"] = pins
        if pins: self.cmb_pin.set(pins[0]); self._on_pin_change()
        else: self.cmb_pin.set(""); self.ent_af.delete(0, "end")

    def _on_pin_change(self, event=None):
        """Handle pin selection change."""
        t = self.cmb_type.get(); inst = self.cmb_inst.get(); pin = self.cmb_pin.get()
        af_num = 0
        if t == "I2C": afs = self.mcu_data.get("i2c_af_mapping", {}); af_num = utils.af_str_to_num(afs.get(inst, {}).get(pin, ""))
        elif t == "UART": afs = self.mcu_data.get("uart_af_mapping", {}); af_num = utils.af_str_to_num(afs.get(inst, {}).get(pin, ""))
        elif t == "SPI": afs = self.mcu_data.get("spi_af_mapping", {}); af_num = utils.af_str_to_num(afs.get(inst, {}).get(pin, ""))
        
        self.ent_af.delete(0, "end"); self.ent_af.insert(0, str(af_num))
        
        # Auto-generate a label if the field is empty
        if not self.ent_label.get().strip():
            if t == "GPIO": self.ent_label.insert(0, pin)
            elif t in ("I2C","UART","SPI"): self.ent_label.insert(0, f"{inst}_{self.cmb_role.get().upper()}")
            elif t == "ADC": self.ent_label.insert(0, f"{inst}_{self.cmb_role.get()}")

    # ---------------- TABLE ACTIONS ----------------
    def add_row(self):
        """Add the currently configured pin to the selection table."""
        t = self.cmb_type.get()
        name = self.ent_label.get().strip() or "SIGNAL"
        pin_label = self.cmb_pin.get().strip()
        
        if t != "GPIO" and (not self.cmb_inst.get() or not self.cmb_role.get()):
            messagebox.showwarning("Incomplete", "Please select an instance and function."); return
        if not pin_label:
            messagebox.showwarning("Incomplete", "Please select a pin."); return

        port, pin_num = utils.split_pin(pin_label)
        try: afn = int(self.ent_af.get() or "0")
        except ValueError: afn = 0

        row = {
            "type": t, "instance": "" if t=="GPIO" else self.cmb_inst.get(), "name": name,
            "port": port, "pin": pin_num, "mode": self.cmb_mode.get(), "pull": self.cmb_pull.get(),
            "speed": self.cmb_speed.get(), "alternate_fn": afn
        }
        self.selections.append(row)
        self._refresh_table()
        self.ent_label.delete(0, "end")
        self._update_i2c_tab_state()
        self._update_uart_tab_state()

    def _refresh_table(self):
       # """Clear and redraw the Treeview with current selections."""
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.selections):
            self.tree.insert("", "end", iid=str(i), values=(
                r["type"], r["instance"], r["name"], r["port"], r["pin"],
                r["mode"], r["pull"], r["speed"], r["alternate_fn"]
            ))

    def del_selected(self):
       # """Remove the selected row from the Treeview."""
        cur = self.tree.selection()
        if not cur: return
        idx = int(cur[0])
        del self.selections[idx]
        self._refresh_table()
        self._update_i2c_tab_state()
        self._update_uart_tab_state()

    # ---------------- FILE EXPORT & GENERATION ----------------
    def _get_pinout_config(self) -> dict:
        #"""Gathers pinout data from the selection table."""
        project_name = self.ent_project.get().strip() or "MyProject"
        micro = self.current_mcu
        grouped = defaultdict(list)
        for r in self.selections:
            grouped.setdefault(r["type"], []).append(r)

        peripherals = []
        for t, rows in grouped.items():
            if t == "GPIO":
                peripherals.append({
                    "type": t,
                    "pins": [{k: v for k, v in x.items() if k not in ['type', 'instance']} for x in rows]
                })
            else:
                by_inst = defaultdict(list)
                for x in rows:
                    by_inst[x["instance"]].append(x)
                for inst, lst in by_inst.items():
                    peripherals.append({
                        "type": t if t != "UART" else "USART",
                        "instance": inst,
                        "pins": [{k: v for k, v in x.items() if k not in ['type', 'instance']} for x in lst]
                    })
        return {"project_name": project_name, "microcontroller": micro, "peripherals": peripherals}

    def _get_peripheral_settings(self) -> dict:
        """
        Gathers peripheral settings from the UI tabs and maps them
        to STM32 HAL-compatible constant names.
        """
        settings = {}

        # --- I2C Settings ---
        active_i2c_instances = {r['instance'] for r in self.selections if r['type'] == 'I2C'}
        if active_i2c_instances:
            settings["I2C"] = {}
            for instance_name, widgets in self.i2c_widgets.items():
                if instance_name in active_i2c_instances:
                    # Look up the values in the dictionary loaded from the JSON file
                    speed_map = data.HAL_MAPPINGS.get("I2C", {}).get("clockSpeed", {})
                    addr_map = data.HAL_MAPPINGS.get("I2C", {}).get("addressingMode", {})
                    
                    settings["I2C"][instance_name] = {
                        "clockSpeed": speed_map.get(widgets['speed'].get(), 0),
                        "addressingMode": addr_map.get(widgets['addr_mode'].get()),
                        "transferMode": widgets['transfer'].get().upper(),
                    }

        # --- UART/USART Settings ---
        active_uart_instances = {r['instance'] for r in self.selections if r['type'] in ['UART', 'USART']}
        if active_uart_instances:
            settings["UART"] = {}
            for instance_name, widgets in self.uart_widgets.items():
                if instance_name in active_uart_instances:
                    # Look up the values in the dictionary loaded from the JSON file
                    word_map = data.HAL_MAPPINGS.get("UART", {}).get("wordLength", {})
                    stop_map = data.HAL_MAPPINGS.get("UART", {}).get("stopBits", {})
                    parity_map = data.HAL_MAPPINGS.get("UART", {}).get("parity", {})
                    flow_map = data.HAL_MAPPINGS.get("UART", {}).get("flowControl", {})

                    settings["UART"][instance_name] = {
                        "baudRate": int(widgets['baud_rate'].get()),
                        "wordLength": word_map.get(widgets['word_length'].get()),
                        "stopBits": stop_map.get(widgets['stop_bits'].get()),
                        "parity": parity_map.get(widgets['parity'].get()),
                        "flowControl": flow_map.get(widgets['flow_control'].get()),
                    }

        return settings

    def export_config(self):
        """
        Exports both pinout and peripheral settings to two separate JSON files.
        """
        if not self.selections:
            messagebox.showwarning("Nothing to Export", "Add at least one signal to the pinout table.")
            return

        # 1. Ask user to select a destination FOLDER
        folder_path = filedialog.askdirectory(title="Select Destination Folder for Configuration Files")
        if not folder_path:
            return

        # 2. Get data from helper functions
        pinout_data = self._get_pinout_config()
        peripheral_data = self._get_peripheral_settings()

        # 3. Define file paths
        pinout_filepath = os.path.join(folder_path, "pinout_config.json")
        peripheral_filepath = os.path.join(folder_path, "peripheral_settings.json")

        try:
            # 4. Save pinout_config.json
            with open(pinout_filepath, "w", encoding="utf-8") as f:
                json.dump(pinout_data, f, indent=2, ensure_ascii=False)

            # 5. Save peripheral_settings.json (only if it's not empty)
            if peripheral_data:
                with open(peripheral_filepath, "w", encoding="utf-8") as f:
                    json.dump(peripheral_data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo(
                "Export Successful",
                f"Configuration files saved successfully in:\n{folder_path}"
            )
        except Exception as e:
            messagebox.showerror("Error During Export", str(e))

    def generate_files(self):
        """
        Asks the user for a folder, loads the pinout and peripheral configuration
        files, and passes them to the code generator module.
        """
        # 1. Ask the user to select the FOLDER containing the config files.
        folder_path = filedialog.askdirectory(title="Select Folder Containing Configuration Files")
        if not folder_path:
            return

        # 2. Construct the full paths to the expected JSON files.
        pinout_path = os.path.join(folder_path, "pinout_config.json")
        settings_path = os.path.join(folder_path, "peripheral_settings.json")

        # 3. Load the data from the configuration files.
        try:
            with open(pinout_path, "r", encoding="utf-8") as f:
                pinout_data = json.load(f)
        except FileNotFoundError:
            messagebox.showerror("File Not Found", f"Could not find 'pinout_config.json' in the selected folder.")
            return
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Error parsing 'pinout_config.json':\n{e}")
            return

        # Load peripheral settings if the file exists; otherwise, use an empty dict.
        # This is not treated as a fatal error, as a project might only have GPIOs.
        peripheral_data = {}
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                peripheral_data = json.load(f)
        except FileNotFoundError:
            print("Info: 'peripheral_settings.json' not found. Proceeding without peripheral-specific settings.")
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Error parsing 'peripheral_settings.json':\n{e}")
            return

        # 4. Import the generator module and call the main generation function.
        try:
            gen = importlib.import_module("generators.generate_all")
            
            if not hasattr(gen, "generate_project_files"):
                raise AttributeError("Function 'generate_project_files' not found in generate_all.py")
                
            # 5. Call the function with BOTH configuration dictionaries.
            out_files = gen.generate_project_files(pinout_data, peripheral_data)
            
            if out_files:
                messagebox.showinfo("Generation Complete", "Generated files:\n\n" + "\n".join(out_files))
            else:
                messagebox.showinfo("Generation Complete", "No files were reported. Check the console/log.")
                
        except ImportError as e:
            messagebox.showerror("Module Not Found", "Could not find the 'generators' module.\n\nDetails:\n"+str(e))
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()