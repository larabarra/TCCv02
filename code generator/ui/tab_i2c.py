# tab_i2c.py
import tkinter as tk
from tkinter import ttk

def create_i2c_tab(parent_tab, app):
    """
    Creates and populates the I2C tab with configuration frames for each I2C instance.
    
    Args:
        parent_tab (ttk.Frame): The parent tab frame to build the UI on.
        app (App): The main application instance to link widgets and callbacks.
    """
    # A dictionary to hold the widgets for each I2C instance
    app.i2c_widgets = {}

    # Create a configuration frame for I2C1, I2C2, and I2C3
    for i in range(1, 4):
        instance_name = f"I2C{i}"
        
        # Create the main frame for this instance
        frame = ttk.LabelFrame(parent_tab, text=f"{instance_name} Configuration", padding=10)
        frame.pack(fill="x", padx=5, pady=5)
        app.i2c_frames[instance_name] = frame

        # Create a dictionary to hold this instance's widgets
        widgets = {}

        # Clock Speed
        ttk.Label(frame, text="Clock Speed:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        combo_speed = ttk.Combobox(frame, state="readonly", values=['100 kHz (Standard)', '400 kHz (Fast)', '1 MHz (Fast+)'])
        combo_speed.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        widgets['speed'] = combo_speed

        # Addressing Mode
        ttk.Label(frame, text="Addressing Mode:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        combo_addr_mode = ttk.Combobox(frame, state="readonly", values=['7-bit', '10-bit'])
        combo_addr_mode.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        widgets['addr_mode'] = combo_addr_mode

        # Transfer Mode
        ttk.Label(frame, text="Transfer Mode:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        combo_transfer = ttk.Combobox(frame, state="readonly", values=['Polling', 'Interrupt', 'DMA'])
        combo_transfer.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        widgets['transfer'] = combo_transfer

        # Make widget columns expandable
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        
        # Store the dictionary of widgets for this instance
        app.i2c_widgets[instance_name] = widgets