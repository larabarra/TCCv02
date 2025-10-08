# tab_i2c.py
import tkinter as tk
from tkinter import ttk

def create_i2c_tab(parent_tab, app):
    """
    Creates and populates the I2C tab with configuration frames for each I2C instance.
    """
    app.i2c_widgets = {}

    for i in range(1, 4):
        instance_name = f"I2C{i}"
        
        # --- Main Frame for the Instance ---
        instance_frame = ttk.Frame(parent_tab)
        instance_frame.pack(fill="x", padx=5, pady=5)
        app.i2c_frames[instance_name] = instance_frame

        # --- General Settings Frame ---
        settings_frame = ttk.LabelFrame(instance_frame, text=f"{instance_name} Configuration", padding=10)
        settings_frame.pack(fill="x")
        
        widgets = {}

        ttk.Label(settings_frame, text="Clock Speed:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        combo_speed = ttk.Combobox(settings_frame, state="readonly", values=['100 kHz (Standard)', '400 kHz (Fast)', '1 MHz (Fast+)'])
        combo_speed.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        widgets['speed'] = combo_speed

        ttk.Label(settings_frame, text="Addressing Mode:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        combo_addr_mode = ttk.Combobox(settings_frame, state="readonly", values=['7-bit', '10-bit'])
        combo_addr_mode.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        widgets['addr_mode'] = combo_addr_mode

        ttk.Label(settings_frame, text="Transfer Mode:").grid(row=0, column=2, sticky="w", padx=(20, 5), pady=5)
        combo_transfer = ttk.Combobox(settings_frame, state="readonly", values=['Polling', 'Interrupt', 'DMA'])
        combo_transfer.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        widgets['transfer'] = combo_transfer

        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)

        # --- Slave Devices Frame ---
        devices_frame = ttk.LabelFrame(instance_frame, text="Connected Slave Devices", padding=10)
        devices_frame.pack(fill="x", pady=(5, 0))

        # Input fields for adding a new device
        ttk.Label(devices_frame, text="Name (for #define):").grid(row=0, column=0, sticky="w", padx=5)
        entry_name = ttk.Entry(devices_frame)
        entry_name.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        widgets['dev_name_entry'] = entry_name

        ttk.Label(devices_frame, text="7-bit Address (e.g., 0x4A):").grid(row=0, column=1, sticky="w", padx=5)
        entry_addr = ttk.Entry(devices_frame, width=20)
        entry_addr.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        widgets['dev_addr_entry'] = entry_addr
        
        # Treeview for listing devices
        tree = ttk.Treeview(devices_frame, columns=("name", "addr"), show="headings", height=3)
        tree.heading("name", text="Device Name")
        tree.heading("addr", text="Address")
        tree.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=10, pady=2)
        widgets['devices_tree'] = tree

        # Action buttons for the list
        btn_frame = ttk.Frame(devices_frame)
        btn_frame.grid(row=0, column=3, rowspan=3, sticky="ns", padx=5)
        
        # The add/remove command is passed from the main app to avoid circular dependencies
        add_btn = ttk.Button(btn_frame, text="Add",
                             command=lambda inst=instance_name: app.add_i2c_device(inst))
        add_btn.pack(pady=2, fill="x")
        
        del_btn = ttk.Button(btn_frame, text="Remove",
                             command=lambda inst=instance_name: app.remove_i2c_device(inst))
        del_btn.pack(pady=2, fill="x")

        devices_frame.columnconfigure(2, weight=1)
        
        app.i2c_widgets[instance_name] = widgets
