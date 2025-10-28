#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py

import json
import re
import importlib
import os
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import BooleanVar

# Import custom modules
import data
import utils
import tab_gpio
import tab_i2c
import tab_uart
import tab_presets
# Import the new handler modules
from handlers import use_case_handler, pinout_handler, file_handler

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # --- Load initial data ---
        data.load_initial_mapping(); data.load_hal_mappings(); data.load_presets()

        # --- Application State ---
        self.title("STM32 Config Generator")
        self.geometry("1150x740"); self.minsize(980, 620)
        self.current_mcu = list(data.MCU_MAP.keys())[0]; self.mcu_data = data.MCU_MAP[self.current_mcu]
        self.selections = []; self.use_case_config = None
        self.i2c_frames = {}; self.uart_frames = {}

        # --- UI Widget References ---
        self.cmb_preset_input: ttk.Combobox | None = None; self.cmb_preset_output: ttk.Combobox | None = None
        self.var_convert: BooleanVar | None = None
        self.ent_formula: ttk.Entry | None = None
        self.frm_threshold: ttk.Frame | None = None; self.ent_threshold: ttk.Entry | None = None
        self.cmb_type: ttk.Combobox | None = None; self.cmb_inst: ttk.Combobox | None = None
        self.cmb_role: ttk.Combobox | None = None; self.cmb_pin: ttk.Combobox | None = None
        self.ent_label: ttk.Entry | None = None; self.cmb_mode: ttk.Combobox | None = None
        self.cmb_pull: ttk.Combobox | None = None; self.cmb_speed: ttk.Combobox | None = None
        self.ent_af: ttk.Entry | None = None; self.tree: ttk.Treeview | None = None

        # --- Build UI and set initial state ---
        self._build_ui()
        self.refresh_mapping_view()
        self.update_peripheral_tabs_state()
        pinout_handler.on_type_change(self)

        self.use_cases = []        # lista de casos de uso selecionados
        self.last_use_case = None  # opcional: referência ao último aplicado

    def _build_ui(self):
        # --- Top frame ---
        top = ttk.Frame(self, padding=8); top.pack(fill="x")
        ttk.Label(top, text="Project:").pack(side="left")
        self.ent_project = ttk.Entry(top, width=24); self.ent_project.insert(0, "MyProject"); self.ent_project.pack(side="left", padx=(4,12))
        ttk.Label(top, text="MCU:").pack(side="left")
        self.cmb_mcu = ttk.Combobox(top, values=list(data.MCU_MAP.keys()), state="readonly", width=16); self.cmb_mcu.set(self.current_mcu); self.cmb_mcu.pack(side="left", padx=(4,12)); self.cmb_mcu.bind("<<ComboboxSelected>>", self.on_mcu_change)
        ttk.Button(top, text="Generate Code", command=lambda: file_handler.generate_files(self)).pack(side="right", padx=4)
        ttk.Button(top, text="Export Configs", command=lambda: file_handler.export_config(self)).pack(side="right", padx=4)
        
        # --- Main paned window ---
        mid = ttk.Panedwindow(self, orient="horizontal"); mid.pack(fill="both", expand=True, padx=6, pady=6)
        left = ttk.Frame(mid, padding=6); mid.add(left, weight=1)
        ttk.Label(left, text="Available GPIOs").pack(anchor="w")
        self.lst_gpio = tk.Listbox(left, height=20); self.lst_gpio.pack(fill="both", expand=True)
        
        # --- Notebook with tabs ---
        notebook = ttk.Notebook(mid); mid.add(notebook, weight=2)
        tab_presets_frame = ttk.Frame(notebook, padding=6)
        tab_gpio_frame = ttk.Frame(notebook, padding=6)
        tab_i2c_frame = ttk.Frame(notebook, padding=6)
        tab_uart_frame = ttk.Frame(notebook, padding=6)

        notebook.add(tab_presets_frame, text="Construtor de Casos de Uso")
        notebook.add(tab_gpio_frame, text="Pinout Detalhado")
        notebook.add(tab_i2c_frame, text="I2C")
        notebook.add(tab_uart_frame, text="UART/USART")
        
        tab_presets.create_presets_tab(tab_presets_frame, self)
        tab_gpio.create_gpio_tab(tab_gpio_frame, self)
        tab_i2c.create_i2c_tab(tab_i2c_frame, self)
        tab_uart.create_uart_tab(tab_uart_frame, self)

    # --- METHODS THAT MANAGE THE APP'S STATE ---

    def is_pin_used(self, pin_label):
        if not pin_label: return False
        port, pin_num = utils.split_pin(pin_label)
        return any(r['port'] == port and str(r['pin']) == str(pin_num) for r in self.selections)

    def refresh_table(self):
        if not self.tree: return
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.selections):
            self.tree.insert("", "end", iid=str(i), values=(
                r.get("type",""),
                r.get("instance",""),
                r.get("name",""),
                r.get("port",""),
                r.get("pin",""),
                r.get("mode",""),
                r.get("pull",""),
                r.get("speed",""),
                r.get("alternate_fn",""),
            ))


    def on_mcu_change(self, event=None):
        """Handles MCU selection change."""
        self.current_mcu = self.cmb_mcu.get(); self.mcu_data = data.MCU_MAP[self.current_mcu]
        self.refresh_mapping_view(); pinout_handler.on_type_change(self)

    def refresh_mapping_view(self):
        """Updates the available GPIO listbox."""
        self.lst_gpio.delete(0, "end"); [self.lst_gpio.insert("end", p) for p in self.mcu_data.get("gpio_pins", [])]

    def update_peripheral_tabs_state(self):
        """Updates the enabled/disabled state of the peripheral tabs."""
        self._update_i2c_tab_state(); self._update_uart_tab_state()

    def _set_widget_state_recursive(self, parent_widget, state_flag):
        for child in parent_widget.winfo_children():
            if isinstance(child, (ttk.Combobox, ttk.Entry, ttk.Button, ttk.Checkbutton, tk.Text, ttk.Treeview)): child.state([state_flag])
            if child.winfo_children(): self._set_widget_state_recursive(child, state_flag)

    def _update_i2c_tab_state(self):
        active = {r['instance'] for r in self.selections if r['type'] == 'I2C'}
        for name, frame in self.i2c_frames.items(): self._set_widget_state_recursive(frame, '!disabled' if name in active else 'disabled')

    def _update_uart_tab_state(self):
        active = {r['instance'] for r in self.selections if r['type'] in ['UART', 'USART']}
        for name, frame in self.uart_frames.items(): self._set_widget_state_recursive(frame, '!disabled' if name in active else 'disabled')
    
    # --- I2C DEVICE MANAGEMENT (These methods stay in the main App) ---
    def add_i2c_device(self, instance_name):
        widgets = self.i2c_widgets.get(instance_name, {})
        name_entry = widgets.get('dev_name_entry'); addr_entry = widgets.get('dev_addr_entry'); tree = widgets.get('devices_tree')
        if not all([name_entry, addr_entry, tree]): return
        dev_name = name_entry.get().strip().upper().replace(" ", "_"); dev_addr = addr_entry.get().strip()
        if not dev_name or not dev_addr: messagebox.showwarning("Campos Vazios", "Por favor, preencha o Nome e o Endereço."); return
        try:
            addr_int = int(dev_addr, 0)
            if not (0 <= addr_int <= 0x7F): raise ValueError("Address out of 7-bit range.")
        except ValueError: messagebox.showerror("Endereço Inválido", "Por favor, insira um endereço 7-bit válido (ex: 68 ou 0x44)."); return
        tree.insert("", "end", values=(dev_name, dev_addr))
        name_entry.delete(0, "end"); addr_entry.delete(0, "end")

    def remove_i2c_device(self, instance_name):
        widgets = self.i2c_widgets.get(instance_name, {}); tree = widgets.get('devices_tree')
        selected_item = tree.selection()
        if not selected_item: messagebox.showwarning("Nenhum Item", "Selecione um dispositivo para remover."); return
        tree.delete(selected_item)

if __name__ == "__main__":
    app = App()
    app.mainloop()

