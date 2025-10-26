# ui/handlers/use_case_handler.py
from tkinter import messagebox
import data
import utils

def toggle_formula_field(app):
    """Habilita/Desabilita o campo de fórmula conforme o checkbox."""
    if hasattr(app, "var_convert") and hasattr(app, "ent_formula") and app.var_convert and app.ent_formula:
        state = "normal" if app.var_convert.get() else "disabled"
        app.ent_formula.config(state=state)

def toggle_threshold_field(app, event=None):
    """Mostra/Esconde o campo de threshold conforme a saída escolhida."""
    if hasattr(app, "cmb_preset_output") and hasattr(app, "frm_threshold") and app.cmb_preset_output and app.frm_threshold:
        is_visible = app.cmb_preset_output.get() in ["Digital Output (LED)", "PWM"]
        if is_visible:
            app.frm_threshold.pack(fill="x", pady=(10, 0))
        else:
            app.frm_threshold.pack_forget()

def apply_use_case(app):
    """
    Aplica o caso de uso:
      - Adiciona pinos ao Pinout (app.selections)
      - Permite compartilhar pinos no MESMO barramento I2C (mesma instância)
      - Popula as abas I2C/UART com as configurações e devices dos presets
    """

    # ===================== valida presets e chaves =====================
    maps = data.PRESETS.get("mappings", {})
    if not maps:
        messagebox.showerror(
            "Presets",
            "Nenhum preset carregado. Verifique o arquivo presets.json e a função data.load_presets()."
        )
        return

    input_key  = app.cmb_preset_input.get()  if hasattr(app, "cmb_preset_input")  else ""
    output_key = app.cmb_preset_output.get() if hasattr(app, "cmb_preset_output") else ""

    if input_key not in maps:
        messagebox.showerror("Preset inválido", f"A entrada '{input_key}' não existe em presets.json.")
        return
    if output_key not in maps:
        messagebox.showerror("Preset inválido", f"A saída '{output_key}' não existe em presets.json.")
        return

    input_map  = maps.get(input_key, {})
    output_map = maps.get(output_key, {})

    # ===================== helpers =====================
    def _find_selection_by_pin(pin_str: str):
        """Retorna o registro já existente em app.selections para esse pino (ou None)."""
        try:
            port, pin_num = utils.split_pin(pin_str)
        except Exception:
            port, pin_num = pin_str[:2], pin_str[2:]
        if not hasattr(app, "selections"):
            return None
        for r in app.selections:
            if r.get("port") == port and str(r.get("pin")) == str(pin_num):
                return r
        return None

    def _safe_is_pin_used(pin_str: str) -> bool:
        """Usa app.is_pin_used se existir; caso contrário, consulta app.selections."""
        if hasattr(app, "is_pin_used") and callable(app.is_pin_used):
            try:
                return bool(app.is_pin_used(pin_str))
            except Exception:
                pass
        return _find_selection_by_pin(pin_str) is not None

    def _same_i2c_bus(existing_rec, new_type: str, new_instance: str) -> bool:
        """True se ambos são I2C e a instância é a mesma (ex.: I2C1)."""
        if not existing_rec:
            return False
        return (
            str(existing_rec.get("type") or "").upper() == "I2C" and
            str(new_type or "").upper() == "I2C" and
            str(existing_rec.get("instance") or "") == str(new_instance or "")
        )

    # ===================== estado base =====================
    if not hasattr(app, "selections"):
        app.selections = []
    if not hasattr(app, "i2c_widgets"):
        app.i2c_widgets = {}
    if not hasattr(app, "uart_widgets"):
        app.uart_widgets = {}

    # ===================== lista de pinos a processar =====================
    pins_to_process = []
    if input_map:
        for p in input_map.get("pins", [input_map]):
            pins_to_process.append((p, input_map, input_key or "input"))
    if output_map:
        for p in output_map.get("pins", [output_map]):
            pins_to_process.append((p, output_map, output_key or "output"))

    # ===================== conflitos (exceto I2C mesmo barramento) =====================
    conflicts = []
    reused_ok = []  # pinos já presentes no mesmo I2C (aceitos sem re-adicionar)
    for pin_cfg, parent_map, owner in pins_to_process:
        p_pin = pin_cfg.get("pin_choice")
        if not p_pin:
            continue
        if _safe_is_pin_used(p_pin):
            existing = _find_selection_by_pin(p_pin)
            if _same_i2c_bus(existing, parent_map.get("type"), parent_map.get("instance")):
                reused_ok.append(p_pin)
            else:
                conflicts.append(
                    f"{p_pin} (em '{owner}', já usado por {existing.get('type')} {existing.get('instance') or ''})"
                )

    if conflicts:
        messagebox.showwarning(
            "Conflito de Pinos",
            "Os seguintes pinos já estão em uso e não podem ser adicionados:\n" + "\n".join(conflicts)
        )
        return

    # ===================== adiciona pinos =====================
    added, reused = [], []
    for pin_cfg, parent_map, _owner in pins_to_process:
        p_pin = pin_cfg.get("pin_choice")
        if not p_pin:
            continue
        existing = _find_selection_by_pin(p_pin)
        if existing:
            if _same_i2c_bus(existing, parent_map.get("type"), parent_map.get("instance")):
                reused.append(p_pin)
                continue
            # outros casos já teriam sido capturados como conflito
            continue
        # adiciona normalmente
        if _add_pin_from_config(app, pin_cfg, parent_map):
            added.append(p_pin)

    # ===================== merge de settings por instância =====================
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

    # ===================== popula abas (I2C / UART) =====================
    updated_ifaces = []
    for inst, st in settings_to_apply.items():
        # I2C
        if inst.startswith("I2C") and inst in app.i2c_widgets:
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
        elif inst.startswith("UART") and inst in app.uart_widgets:
            w = app.uart_widgets[inst]
            if "baud_rate" in w:      w["baud_rate"].set(st.get("baudRate", ""))
            if "word_length" in w:    w["word_length"].set(st.get("wordLength", ""))
            if "stop_bits" in w:      w["stop_bits"].set(st.get("stopBits", ""))
            if "parity" in w:         w["parity"].set(st.get("parity", ""))
            if "flow_control" in w:   w["flow_control"].set(st.get("flowControl", ""))
            if "transfer_mode" in w:  w["transfer_mode"].set(st.get("transferMode", ""))
            updated_ifaces.append(inst)

    # ===================== refresh de UI =====================
    if hasattr(app, "refresh_table"):
        app.refresh_table()
    if hasattr(app, "update_peripheral_tabs_state"):
        app.update_peripheral_tabs_state()

    # ===================== hard-sync direto da tree (se existir) =====================
    try:
        if hasattr(app, "tree") and app.tree is not None:
            app.tree.delete(*app.tree.get_children())
            for r in app.selections:
                app.tree.insert(
                    "", "end",
                    values=(
                        r.get("type",""),
                        r.get("instance",""),
                        r.get("name",""),
                        r.get("port",""),
                        r.get("pin",""),
                        r.get("mode",""),
                        r.get("pull",""),
                        r.get("speed",""),
                        r.get("alternate_fn",""),
                    )
                )
    except Exception:
        # não falha se a tree ainda não existir
        pass

    # ===================== resumo =====================
    parts = [f"{len(added)} pino(s) adicionados."]
    if added:
        parts.append("Adicionados: " + ", ".join(sorted(set(added))))
    if reused:
        parts.append("Reutilizados (I2C mesmo barramento): " + ", ".join(sorted(set(reused))))
    if updated_ifaces:
        parts.append("Periféricos atualizados: " + ", ".join(sorted(set(updated_ifaces))))
    else:
        parts.append("Nenhum periférico foi atualizado (confira as abas).")

    messagebox.showinfo("Preset Aplicado", "\n".join(parts))

def _add_pin_from_config(app, pin_config, parent_mapping) -> bool:
    """
    Adiciona um pino individual à lista principal (app.selections).
    Retorna True se adicionou, False se já existia ou não havia escolha de pino.
    """
    p_pin = pin_config.get("pin_choice")
    if not p_pin:
        return False

    port, pin_num = utils.split_pin(p_pin)

    # não duplica na tabela principal (normaliza como string para evitar int vs str)
    if any(r.get('port') == port and str(r.get('pin')) == str(pin_num) for r in app.selections):
        return False

    # metadados do parent
    p_type = (parent_mapping.get("type") or "GPIO").strip()
    p_instance = (parent_mapping.get("instance") or "").strip()

    # label/role
    p_role = (pin_config.get("role") or "").strip()
    label_prefix = (parent_mapping.get("label_prefix") or parent_mapping.get("type") or "PIN").strip()
    explicit_label = (pin_config.get("label") or parent_mapping.get("label") or "").strip()

    if explicit_label:
        p_label = explicit_label
    elif p_role:
        p_label = f"{label_prefix}_{p_role.upper()}"
    else:
        # fallback: TYPE_PORTPIN
        p_label = f"{label_prefix}_{p_pin}".replace(" ", "_")

    # derive config
    mode = pin_config.get("mode", "INPUT")
    pull = pin_config.get("pull", "NOPULL")
    speed, afn = "LOW", 0

    if p_type.upper() == "I2C":
        mode, pull, speed = "AF_OD", "PULLUP", "VERY_HIGH"
        afs = app.mcu_data.get("i2c_af_mapping", {}).get(p_instance, {}) if hasattr(app, "mcu_data") else {}
        afn = utils.af_str_to_num(afs.get(p_pin, "")) if hasattr(utils, "af_str_to_num") else 0

    elif p_type.upper() in ("UART", "USART"):
        mode, pull, speed = "AF_PP", "NOPULL", "VERY_HIGH"
        afs = app.mcu_data.get("uart_af_mapping", {}).get(p_instance, {}) if hasattr(app, "mcu_data") else {}
        afn = utils.af_str_to_num(afs.get(p_pin, "")) if hasattr(utils, "af_str_to_num") else 0

    elif p_type.upper() == "TIM":
        # PWM/TIM normalmente AF_PP
        mode, pull, speed = "AF_PP", "NOPULL", "HIGH"

    elif p_type.upper() == "GPIO":
        # GPIO simples: respeita overrides do parent (se fornecidos)
        mode = parent_mapping.get("mode", mode)
        pull = parent_mapping.get("pull", pull)

    # adiciona na lista principal
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
