# tab_presets.py
import tkinter as tk
from tkinter import ttk
import data
from handlers import use_case_handler

def _split_by_direction():
    """Reads data.PRESETS["mappings"] and separates keys by 'direction'.
    
    Any item without 'direction' becomes 'input' by default.
    """
    maps = data.PRESETS.get("mappings", {})
    inputs, outputs = [], []
    for key, cfg in maps.items():
        dirn = (cfg.get("direction", "input") or "input").strip().lower()
        if dirn == "output":
            outputs.append(key)
        else:
            inputs.append(key)
    return sorted(inputs), sorted(outputs)

def _set_locked_state(app, locked: bool):
    """Enables/disables all widgets in the presets tab based on 'locked' state."""
    app.use_case_locked = bool(locked)

    # Combos
    for w in (app.cmb_preset_input, app.cmb_preset_output):
        if w and w.winfo_exists():
            w.config(state="disabled" if locked else "readonly")

    # Processing (checkbox + entry)
    if app.chk_convert and app.chk_convert.winfo_exists():
        app.chk_convert.state(["disabled"] if locked else ["!disabled"])
    if app.ent_formula and app.ent_formula.winfo_exists():
        app.ent_formula.config(state="disabled" if locked or not app.var_convert.get() else "normal")

    # Threshold frame (only appears for LED/PWM)
    if app.frm_threshold and app.frm_threshold.winfo_exists():
        # Even when locked, we keep visible/hidden based on selection, but disable children
        for child in app.frm_threshold.winfo_children():
            try:
                child.state(["disabled"] if locked else ["!disabled"])
            except Exception:
                pass

    # Buttons
    if app.btn_apply_case and app.btn_apply_case.winfo_exists():
        app.btn_apply_case.state(["disabled"] if locked else ["!disabled"])
    if app.btn_unlock_case and app.btn_unlock_case.winfo_exists():
        app.btn_unlock_case.state(["!disabled"] if locked else ["disabled"])

def _unlock_only(app):
    """Unlocks the UI to allow choosing another use case.
    
    Doesn't touch pins already added (avoids erasing user's work).
    """
    _set_locked_state(app, False)

def create_presets_tab(parent_tab, app):
    """Creates the 'Use Case Builder' tab
      
      1) Input Source  (combobox from presets.json, direction=input)
      2) Processing (optional)
      3) Output Action (combobox from presets.json, direction=output)
      4) 'Add Use Case to Project' button (will lock the tab after applying)
    """
    # Guard for lock state
    app.use_case_locked = getattr(app, "use_case_locked", False)

    # --- Main container ---
    main = ttk.Frame(parent_tab)
    main.pack(fill="both", expand=True, padx=6, pady=6)

    input_options, output_options = _split_by_direction()

    # ===================== 1) INPUT SOURCE =====================
    frm_in = ttk.LabelFrame(main, text="1. Input Source", padding=10)
    frm_in.pack(fill="x", pady=(0, 10))

    app.cmb_preset_input = ttk.Combobox(frm_in, values=input_options, state="readonly")
    app.cmb_preset_input.pack(fill="x")
    if input_options:
        app.cmb_preset_input.set(input_options[0])
    app.cmb_preset_input.bind(
        "<<ComboboxSelected>>",
        lambda e: use_case_handler.toggle_formula_field(app, e),
    )

    # ===================== 2) PROCESSING (OPTIONAL) =====================
    frm_proc = ttk.LabelFrame(main, text="2. Processing (Optional)", padding=10)
    frm_proc.pack(fill="x", pady=(0, 10))

    app.var_convert = tk.BooleanVar(value=False)
    app.chk_convert = ttk.Checkbutton(
        frm_proc,
        text="Enable value conversion?",
        variable=app.var_convert,
        command=lambda: use_case_handler.toggle_formula_field(app),
    )
    app.chk_convert.pack(anchor="w")

    ttk.Label(frm_proc, text="Formula (use 'value' as the input variable):").pack(
        anchor="w", pady=(6, 0)
    )
    app.ent_formula = ttk.Entry(frm_proc, state="disabled")
    app.ent_formula.pack(fill="x")
    app.ent_formula.insert(0, "(value / 4095.0) * 3.3")  # example for ADC

    # ===================== 3) OUTPUT ACTION =====================
    frm_out = ttk.LabelFrame(main, text="3. Output Action", padding=10)
    frm_out.pack(fill="x", pady=(0, 10))

    app.cmb_preset_output = ttk.Combobox(frm_out, values=output_options, state="readonly")
    app.cmb_preset_output.pack(fill="x")
    if output_options:
        app.cmb_preset_output.set(output_options[0])
    app.cmb_preset_output.bind(
        "<<ComboboxSelected>>",
        lambda e: use_case_handler.toggle_threshold_field(app, e),
    )

    # --- Conditional field (threshold) - shown only for Digital Output (LED) ---
    app.frm_threshold = ttk.Frame(frm_out)
    ttk.Label(app.frm_threshold, text="Activate GPIO high output when value is greater than:").pack(anchor="w")
    app.ent_threshold = ttk.Entry(app.frm_threshold)
    app.ent_threshold.pack(fill="x")
    app.ent_threshold.insert(0, "2048")

    # ===================== 4) ACTIONS =====================
    btns = ttk.Frame(main)
    btns.pack(fill="x", pady=(10, 0))

    # Apply (locks after success)
    app.btn_apply_case = ttk.Button(
        btns,
        text="Add Use Case to Project",
        command=lambda: use_case_handler.apply_use_case(app),
    )
    app.btn_apply_case.pack(side="left")

    # Unlock (to allow changing the selection)
    app.btn_unlock_case = ttk.Button(
        btns,
        text="Change Use Case",
        command=lambda: _unlock_only(app),
    )
    app.btn_unlock_case.pack(side="left", padx=8)

    # Initial state (handlers adjust visibility of threshold and formula)
    use_case_handler.toggle_formula_field(app, None)
    use_case_handler.toggle_threshold_field(app)

    # Apply initial lock state
    _set_locked_state(app, bool(app.use_case_locked))
