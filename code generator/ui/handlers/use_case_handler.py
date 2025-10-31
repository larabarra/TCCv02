# ui/handlers/use_case_handler.py
from tkinter import messagebox
import data
import utils

# ============================ UI helpers ============================

def toggle_formula_field(app, event=None):
    """Shows/enables the formula field only for ADC-related inputs (Potentiometer, KY-013)."""
    if hasattr(app, "cmb_preset_input") and hasattr(app, "var_convert") and hasattr(app, "ent_formula") and hasattr(app, "chk_convert"):
        if app.cmb_preset_input and app.var_convert and app.ent_formula and app.chk_convert:
            selected_input = app.cmb_preset_input.get()
            # Only ADC-related inputs can use formulas
            is_adc = "Potentiometer" in selected_input or "KY-013" in selected_input or "KY013" in selected_input
            
            if is_adc:
                # Show the checkbox and formula field for ADC inputs
                app.chk_convert.pack(anchor="w", pady=(0, 0))
                app.ent_formula.config(state="disabled" if not app.var_convert.get() else "normal")
            else:
                # Hide the checkbox and formula field for non-ADC inputs
                app.chk_convert.pack_forget()
                # Keep ent_formula but hide it
                if hasattr(app, "ent_formula"):
                    state = app.ent_formula.cget("state")
                    if state == "normal":
                        app.ent_formula.config(state="disabled")
                app.var_convert.set(False)  # Reset checkbox

def toggle_threshold_field(app, event=None):
    """Shows/hides the threshold field based on the selected output.
    Threshold is only available for Digital Output (LED) / GPIO outputs.
    """
    if hasattr(app, "cmb_preset_output") and hasattr(app, "frm_threshold") and app.cmb_preset_output and app.frm_threshold:
        selected_output = app.cmb_preset_output.get()
        # Threshold is only available for Digital Output (LED) / GPIO
        is_visible = selected_output == "Digital Output (LED)"
        if is_visible:
            app.frm_threshold.pack(fill="x", pady=(10, 0))
        else:
            app.frm_threshold.pack_forget()

# ============================ Internal helpers ============================

def _reset_ui_for_new_case(app):
    """One case at a time mode: clears pin selection and zeros device lists in tabs."""
    # Clear selected pinout
    app.selections = []
    # Clear tree if it exists
    if hasattr(app, "tree") and app.tree is not None:
        try:
            app.tree.delete(*app.tree.get_children())
        except Exception:
            pass
    # Clear I2C tab devices
    if hasattr(app, "i2c_widgets"):
        for _inst, w in app.i2c_widgets.items():
            tree = w.get("devices_tree")
            if tree:
                for iid in tree.get_children():
                    tree.delete(iid)
    # Reset config in memory
    app.use_case_config = None

def _find_selection_by_pin(app, pin_str: str):
    """Returns the existing record in app.selections for this pin (or None)."""
    try:
        port, pin_num = utils.split_pin(pin_str)
    except Exception:
        port, pin_num = pin_str[:2], pin_str[2:]
    for r in getattr(app, "selections", []):
        if r.get("port") == port and str(r.get("pin")) == str(pin_num):
            return r
    return None

def _safe_is_pin_used(app, pin_str: str) -> bool:
    """Uses app.is_pin_used if it exists; otherwise checks app.selections."""
    if hasattr(app, "is_pin_used") and callable(app.is_pin_used):
        try:
            return bool(app.is_pin_used(pin_str))
        except Exception:
            pass
    return _find_selection_by_pin(app, pin_str) is not None

def _same_i2c_bus(existing_rec, new_type: str, new_instance: str) -> bool:
    """Returns True if both are I2C and the instance is the same (e.g., I2C1)."""
    if not existing_rec:
        return False
    return (
        str(existing_rec.get("type") or "").upper() == "I2C" and
        str(new_type or "").upper() == "I2C" and
        str(existing_rec.get("instance") or "") == str(new_instance or "")
    )

def _add_pin_from_config(app, pin_config, parent_mapping) -> bool:
    """Adds an individual pin to the main list (app.selections).
    
    Returns:
        True if added, False if already exists or no pin choice was available.
    """
    p_pin = pin_config.get("pin_choice")
    if not p_pin:
        return False

    port, pin_num = utils.split_pin(p_pin)

    # Don't duplicate in main table (normalize as string)
    if any(r.get('port') == port and str(r.get('pin')) == str(pin_num) for r in app.selections):
        return False

    # Parent metadata
    p_type = (parent_mapping.get("type") or "GPIO").strip()
    p_instance = (parent_mapping.get("instance") or "").strip()

    # Label/role
    p_role = (pin_config.get("role") or "").strip()
    label_prefix = (parent_mapping.get("label_prefix") or parent_mapping.get("type") or "PIN").strip()
    explicit_label = (pin_config.get("label") or parent_mapping.get("label") or "").strip()

    if explicit_label:
        p_label = explicit_label
    elif p_role:
        p_label = f"{label_prefix}_{p_role.upper()}"
    else:
        p_label = f"{label_prefix}_{p_pin}".replace(" ", "_")

    # Derive configuration
    mode = pin_config.get("mode", "INPUT")
    pull = pin_config.get("pull", "NOPULL")
    speed, afn = "LOW", ""

    if p_type.upper() == "I2C":
        mode, pull, speed = "AF_OD", "PULLUP", "VERY_HIGH"
        afs = app.mcu_data.get("i2c_af_mapping", {}).get(p_instance, {}) if hasattr(app, "mcu_data") else {}
        afn = afs.get(p_pin, "")  # Store full AF constant like "GPIO_AF4_I2C1"

    elif p_type.upper() in ("UART", "USART"):
        mode, pull, speed = "AF_PP", "NOPULL", "VERY_HIGH"
        afs = app.mcu_data.get("uart_af_mapping", {}).get(p_instance, {}) if hasattr(app, "mcu_data") else {}
        afn = afs.get(p_pin, "")  # Store full AF constant

    elif p_type.upper() == "TIM":
        # PWM/TIM normally AF_PP
        mode, pull, speed = "AF_PP", "NOPULL", "HIGH"
        afs = app.mcu_data.get("tim_af_mapping", {}).get(p_instance, {}) if hasattr(app, "mcu_data") else {}
        afn = afs.get(p_pin, "")  # Store full AF constant

    elif p_type.upper() == "GPIO":
        # Simple GPIO: respects parent overrides (if provided)
        mode = parent_mapping.get("mode", mode)
        pull = parent_mapping.get("pull", pull)

    # Add to main list
    app.selections.append({
        "type": p_type,
        "instance": p_instance,
        "name": p_label,
        "port": port,
        "pin": pin_num,
        "mode": mode,
        "pull": pull,
        "speed": speed,
        "alternate_fn": afn
    })
    return True

# ============================ Main flow ============================

def apply_use_case(app):
    """Applies the use case (one case at a time mode):
      - Clears pinout/tabs before applying
      - Adds pins from input+output presets
      - Allows pin sharing on the SAME I2C (same instance)
      - Populates I2C/UART tabs
      - Saves summary in app.use_case_config and accumulates in app.use_cases (for presets_generator)
    """
    # Validate presets and keys
    maps = data.PRESETS.get("mappings", {})
    if not maps:
        messagebox.showerror("Presets", "No presets loaded. Check presets.json and data.load_presets().")
        return

    input_key  = app.cmb_preset_input.get()  if hasattr(app, "cmb_preset_input")  else ""
    output_key = app.cmb_preset_output.get() if hasattr(app, "cmb_preset_output") else ""

    if input_key not in maps:
        messagebox.showerror("Invalid Preset", f"Input '{input_key}' does not exist in presets.json.")
        return
    if output_key not in maps:
        messagebox.showerror("Invalid Preset", f"Output '{output_key}' does not exist in presets.json.")
        return

    input_map  = maps.get(input_key, {})
    output_map = maps.get(output_key, {})

    # One case at a time mode
    _reset_ui_for_new_case(app)

    # Pins to process
    pins_to_process = []
    if input_map:
        for p in input_map.get("pins", [input_map]):
            pins_to_process.append((p, input_map, input_key or "input"))
    if output_map:
        for p in output_map.get("pins", [output_map]):
            pins_to_process.append((p, output_map, output_key or "output"))

    # Add pins (no conflicts after reset)
    added = []
    for pin_cfg, parent_map, _owner in pins_to_process:
        if _add_pin_from_config(app, pin_cfg, parent_map):
            added.append(pin_cfg.get("pin_choice"))

    # Merge settings by instance
    settings_to_apply = {}
    for p_map in (input_map, output_map):
        if not p_map or "settings" not in p_map:
            continue
        inst = p_map.get("instance")
        if not inst:
            continue
        settings_to_apply.setdefault(inst, {})
        for k, v in p_map["settings"].items():
            if k == "devices":
                lst = settings_to_apply[inst].setdefault("devices", [])
                existing = {d.get("name") for d in lst}
                for dev in v:
                    if dev.get("name") not in existing:
                        lst.append(dev)
                        existing.add(dev.get("name"))
            else:
                settings_to_apply[inst][k] = v

    # Populate tabs
    updated_ifaces = []
    for inst, st in settings_to_apply.items():
        # I2C
        if inst.startswith("I2C") and hasattr(app, "i2c_widgets") and inst in app.i2c_widgets:
            w = app.i2c_widgets[inst]
            if "speed" in w:      w["speed"].set(st.get("clockSpeed", ""))
            if "addr_mode" in w:  w["addr_mode"].set(st.get("addressingMode", ""))
            if "transfer" in w:   w["transfer"].set(st.get("transferMode", ""))
            tree = w.get("devices_tree")
            if tree is not None:
                tree.delete(*tree.get_children())
                for dev in st.get("devices", []):
                    tree.insert("", "end", values=(dev.get("name"), dev.get("address")))
            updated_ifaces.append(inst)

        # UART
        elif inst.startswith("UART") and hasattr(app, "uart_widgets") and inst in app.uart_widgets:
            w = app.uart_widgets[inst]
            if "baud_rate" in w:      w["baud_rate"].set(st.get("baudRate", ""))
            if "word_length" in w:    w["word_length"].set(st.get("wordLength", ""))
            if "stop_bits" in w:      w["stop_bits"].set(st.get("stopBits", ""))
            if "parity" in w:         w["parity"].set(st.get("parity", ""))
            if "flow_control" in w:   w["flow_control"].set(st.get("flowControl", ""))
            if "transfer_mode" in w:  w["transfer_mode"].set(st.get("transferMode", ""))
            updated_ifaces.append(inst)

    # refresh UI
    if hasattr(app, "refresh_table"):
        app.refresh_table()
    if hasattr(app, "update_peripheral_tabs_state"):
        app.update_peripheral_tabs_state()

    # Save case summary in memory (for presets_generator)
    processing_enabled = bool(getattr(app, "var_convert", None) and app.var_convert.get())
    formula_text = (app.ent_formula.get().strip() if getattr(app, "ent_formula", None) else "")

    threshold_enabled = False
    threshold_value = ""
    if hasattr(app, "cmb_preset_output") and app.cmb_preset_output:
        threshold_enabled = app.cmb_preset_output.get() in ["Digital Output (LED)", "PWM"]
    if threshold_enabled and getattr(app, "ent_threshold", None):
        threshold_value = app.ent_threshold.get().strip()

    input_inst  = input_map.get("instance", "")
    output_inst = output_map.get("instance", "")

    app.use_case_config = {
        "input_key": input_key,
        "output_key": output_key,
        "processing": {
            "enabled": processing_enabled,
            "formula": formula_text,
        },
        "threshold": {
            "enabled": threshold_enabled,
            "value": threshold_value,
        },
        "peripheral_settings": {
            "input_peripheral": {
                "type": input_map.get("type"),
                "instance": input_inst,
                "settings": settings_to_apply.get(input_inst, {}) if input_inst else {}
            },
            "output_peripheral": {
                "type": output_map.get("type"),
                "instance": output_inst,
                "settings": settings_to_apply.get(output_inst, {}) if output_inst else {}
            }
        }
    }

    # Maintain a list of applied cases (history)
    if not hasattr(app, "use_cases"):
        app.use_cases = []
    app.use_cases.append(app.use_case_config)

    # Try to automatically persist preset_settings.json if available
    try:
        from handlers import file_handler as _fh
        if hasattr(_fh, "save_selected_use_case"):
            _fh.save_selected_use_case(app)
    except Exception:
        # OK to not persist if something is missing
        pass

    # Summary
    parts = [f"{len([p for p in added if p])} pin(s) added."]
    if added:
        parts.append("Added: " + ", ".join(sorted({a for a in added if a})))
    if updated_ifaces:
        parts.append("Peripherals updated: " + ", ".join(sorted(set(updated_ifaces))))
    else:
        parts.append("No peripherals were updated (check the tabs).")
    parts.append("Mode: One case at a time (previous pinout was cleared).")

    messagebox.showinfo("Preset Applied", "\n".join(parts))
