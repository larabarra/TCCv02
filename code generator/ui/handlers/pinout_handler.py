# ui/handlers/pinout_handler.py
from tkinter import ttk, messagebox
import utils

def on_type_change(app, event=None):
    t = app.cmb_type.get()
    app.cmb_inst.set(""); app.cmb_role.set(""); app.cmb_pin.set(""); app.ent_label.delete(0, "end")
    if t == "GPIO":
        app.cmb_mode.set("INPUT"); app.cmb_pull.set("NOPULL"); app.cmb_speed.set("LOW"); app.ent_af.delete(0, "end")
        app.cmb_inst.config(state="disabled"); app.cmb_role.config(state="disabled")
        pins = app.mcu_data.get("gpio_pins", [])
        app.cmb_pin["values"] = pins
        if pins: app.cmb_pin.set(pins[0]); on_pin_change(app)
    else:
        app.cmb_inst.config(state="readonly"); app.cmb_role.config(state="readonly")
        insts = list(app.mcu_data.get(f"{t.lower()}_interfaces", {}).keys())
        app.cmb_inst["values"] = insts
        if insts: app.cmb_inst.set(insts[0]); on_instance_change(app)

def on_instance_change(app, event=None):
    t = app.cmb_type.get()
    roles = {"I2C": ["scl", "sda"], "UART": ["tx", "rx"]}.get(t, [])
    app.cmb_role["values"] = roles
    if roles: app.cmb_role.set(roles[0]); on_role_change(app)

def on_role_change(app, event=None):
    t = app.cmb_type.get(); inst = app.cmb_inst.get(); role = app.cmb_role.get()
    pins = app.mcu_data.get(f"{t.lower()}_interfaces", {}).get(inst, {}).get(role, [])
    if t == "I2C": app.cmb_mode.set("AF_OD"); app.cmb_pull.set("PULLUP"); app.cmb_speed.set("VERY_HIGH")
    elif t == "UART": app.cmb_mode.set("AF_PP"); app.cmb_pull.set("NOPULL"); app.cmb_speed.set("VERY_HIGH")
    app.cmb_pin["values"] = pins
    if pins: app.cmb_pin.set(pins[0]); on_pin_change(app)
    else: app.cmb_pin.set(""); app.ent_af.delete(0, "end")

def on_pin_change(app, event=None):
    t = app.cmb_type.get(); inst = app.cmb_inst.get(); pin = app.cmb_pin.get()
    afs = app.mcu_data.get(f"{t.lower()}_af_mapping", {}).get(inst, {}); af_const = afs.get(pin, "")
    app.ent_af.delete(0, "end"); app.ent_af.insert(0, af_const)
    if not app.ent_label.get().strip(): app.ent_label.insert(0, f"{inst}_{app.cmb_role.get().upper()}")

def add_row(app):
    pin_label = app.cmb_pin.get().strip()
    if not pin_label: messagebox.showwarning("Incomplete", "Please select a pin."); return
    if app.is_pin_used(pin_label): messagebox.showwarning("Pin Conflict", f"Pin {pin_label} is already in use."); return
    t = app.cmb_type.get()
    if t != "GPIO" and (not app.cmb_inst.get() or not app.cmb_role.get()): messagebox.showwarning("Incomplete", "Please select instance and function."); return
    port, pin_num = utils.split_pin(pin_label)
    afn = app.ent_af.get().strip() or ""  # Store full AF constant string
    app.selections.append({"type": t, "instance": "" if t=="GPIO" else app.cmb_inst.get(), "name": app.ent_label.get().strip() or "SIGNAL", "port": port, "pin": pin_num, "mode": app.cmb_mode.get(), "pull": app.cmb_pull.get(), "speed": app.cmb_speed.get(), "alternate_fn": afn})
    app.refresh_table(); app.ent_label.delete(0, "end"); app.update_peripheral_tabs_state()

def del_selected(app):
    cur = app.tree.selection()
    if not cur: return
    selected_values = app.tree.item(cur[0], "values"); port, pin_num_str = selected_values[3], selected_values[4]
    app.selections = [r for r in app.selections if not (r['port'] == port and str(r['pin']) == pin_num_str)]
    app.refresh_table(); app.update_peripheral_tabs_state()
