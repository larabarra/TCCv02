# tab_gpio.py
import tkinter as tk
from tkinter import ttk
import data # Import the data module

def create_gpio_tab(parent_tab, app):
    """
    Creates and populates the GPIO tab with widgets for pin configuration.
    
    Args:
        parent_tab (ttk.Frame): The parent tab frame to build the UI on.
        app (App): The main application instance to link widgets and callbacks.
    """
    # --- Add peripheral / signal frame ---
    frm_add = ttk.LabelFrame(parent_tab, text="Add Peripheral / Signal", padding=8)
    frm_add.pack(fill="x")

    # Peripheral Type
    ttk.Label(frm_add, text="Type:").grid(row=0, column=0, sticky="w")
    app.cmb_type = ttk.Combobox(frm_add, values=data.DEFAULT_TYPES, state="readonly", width=10)
    app.cmb_type.set(data.DEFAULT_TYPES[0])
    app.cmb_type.grid(row=0, column=1, sticky="w", padx=(4,12))
    app.cmb_type.bind("<<ComboboxSelected>>", app._on_type_change)

    # Instance
    ttk.Label(frm_add, text="Instance:").grid(row=0, column=2, sticky="w")
    app.cmb_inst = ttk.Combobox(frm_add, values=[], state="readonly", width=14)
    app.cmb_inst.grid(row=0, column=3, sticky="w", padx=(4,12))
    app.cmb_inst.bind("<<ComboboxSelected>>", app._on_instance_change)

    # Role / Function
    ttk.Label(frm_add, text="Function:").grid(row=0, column=4, sticky="w")
    app.cmb_role = ttk.Combobox(frm_add, values=[], state="readonly", width=16)
    app.cmb_role.grid(row=0, column=5, sticky="w", padx=(4,12))
    app.cmb_role.bind("<<ComboboxSelected>>", app._on_role_change)

    # Pin
    ttk.Label(frm_add, text="Pin:").grid(row=0, column=6, sticky="w")
    app.cmb_pin = ttk.Combobox(frm_add, values=[], state="readonly", width=10)
    app.cmb_pin.grid(row=0, column=7, sticky="w", padx=(4,12))
    app.cmb_pin.bind("<<ComboboxSelected>>", app._on_pin_change)

    # Label (Signal Name)
    ttk.Label(frm_add, text="Label (Name):").grid(row=1, column=0, sticky="w", pady=(8,0))
    app.ent_label = ttk.Entry(frm_add, width=28)
    app.ent_label.grid(row=1, column=1, columnspan=2, sticky="w", pady=(8,0), padx=(4,12))

    # GPIO Mode
    ttk.Label(frm_add, text="Mode:").grid(row=1, column=3, sticky="w", pady=(8,0))
    app.cmb_mode = ttk.Combobox(frm_add, values=["INPUT","OUTPUT_PP","OUTPUT_OD","AF_PP","AF_OD","ANALOG"], state="readonly", width=12)
    app.cmb_mode.grid(row=1, column=4, sticky="w", pady=(8,0), padx=(4,12))

    # GPIO Pull
    ttk.Label(frm_add, text="Pull:").grid(row=1, column=5, sticky="w", pady=(8,0))
    app.cmb_pull = ttk.Combobox(frm_add, values=["NOPULL","PULLUP","PULLDOWN"], state="readonly", width=10)
    app.cmb_pull.grid(row=1, column=6, sticky="w", pady=(8,0), padx=(4,12))

    # GPIO Speed
    ttk.Label(frm_add, text="Speed:").grid(row=1, column=7, sticky="w", pady=(8,0))
    app.cmb_speed = ttk.Combobox(frm_add, values=["LOW","MEDIUM","HIGH","VERY_HIGH"], state="readonly", width=12)
    app.cmb_speed.grid(row=1, column=8, sticky="w", pady=(8,0), padx=(4,12))

    # Alternate Function
    ttk.Label(frm_add, text="AF#:").grid(row=1, column=9, sticky="w", pady=(8,0))
    app.ent_af = ttk.Entry(frm_add, width=6)
    app.ent_af.grid(row=1, column=10, sticky="w", pady=(8,0), padx=(4,12))

    # Add button
    ttk.Button(frm_add, text="Add", command=app.add_row).grid(row=1, column=11, sticky="w", pady=(8,0))

    # --- Selected signals frame (Treeview) ---
    frm_sel = ttk.LabelFrame(parent_tab, text="Selected Signals", padding=8)
    frm_sel.pack(fill="both", expand=True, pady=(8,0))
    
    cols = ("type","instance","name","port","pin","mode","pull","speed","af")
    app.tree = ttk.Treeview(frm_sel, columns=cols, show="headings", height=12)
    headers = ["Type","Instance","Name","Port","Pin","Mode","Pull","Speed","AF#"]
    widths  = [70, 90, 180, 70, 60, 110, 90, 80, 60]
    
    for c,h,w in zip(cols, headers, widths):
        app.tree.heading(c, text=h)
        app.tree.column(c, width=w, anchor="w")
        
    app.tree.pack(fill="both", expand=True)
    ttk.Button(frm_sel, text="Remove Selected", command=app.del_selected).pack(anchor="w", pady=(6,0))