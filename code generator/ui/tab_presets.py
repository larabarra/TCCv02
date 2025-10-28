# tab_presets.py
import tkinter as tk
from tkinter import ttk
import data
from handlers import use_case_handler

def _split_by_direction():
    """
    Lê data.PRESETS["mappings"] e separa as chaves por 'direction'.
    Qualquer item sem 'direction' vira 'input' por padrão.
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
    """
    Habilita/Desabilita todos os widgets da aba de presets conforme 'locked'.
    """
    app.use_case_locked = bool(locked)

    # Combos
    for w in (app.cmb_preset_input, app.cmb_preset_output):
        if w and w.winfo_exists():
            w.config(state="disabled" if locked else "readonly")

    # Processamento (checkbox + entry)
    if app.chk_convert and app.chk_convert.winfo_exists():
        app.chk_convert.state(["disabled"] if locked else ["!disabled"])
    if app.ent_formula and app.ent_formula.winfo_exists():
        app.ent_formula.config(state="disabled" if locked or not app.var_convert.get() else "normal")

    # Threshold frame (só aparece para LED/PWM)
    if app.frm_threshold and app.frm_threshold.winfo_exists():
        # Mesmo travado, mantemos visível/oculto conforme seleção, mas desabilitamos filhos
        for child in app.frm_threshold.winfo_children():
            try:
                child.state(["disabled"] if locked else ["!disabled"])
            except Exception:
                pass

    # Botões
    if app.btn_apply_case and app.btn_apply_case.winfo_exists():
        app.btn_apply_case.state(["disabled"] if locked else ["!disabled"])
    if app.btn_unlock_case and app.btn_unlock_case.winfo_exists():
        app.btn_unlock_case.state(["!disabled"] if locked else ["disabled"])

def _unlock_only(app):
    """
    Destrava a UI para permitir escolher outro caso de uso.
    Não mexe nos pinos já adicionados (evita apagar trabalho do usuário).
    """
    _set_locked_state(app, False)

def create_presets_tab(parent_tab, app):
    """
    Aba 'Construtor de Casos de Uso'
      1) Fonte de Entrada  (combobox vem de presets.json, direction=input)
      2) Processamento (opcional)
      3) Ação de Saída    (combobox vem de presets.json, direction=output)
      4) Botão 'Adicionar Caso de Uso ao Projeto' (travará a aba após aplicar)
    """
    # Guard para estado de lock
    app.use_case_locked = getattr(app, "use_case_locked", False)

    # --- container principal ---
    main = ttk.Frame(parent_tab)
    main.pack(fill="both", expand=True, padx=6, pady=6)

    input_options, output_options = _split_by_direction()

    # ===================== 1) FONTE DE ENTRADA =====================
    frm_in = ttk.LabelFrame(main, text="1. Fonte de Entrada", padding=10)
    frm_in.pack(fill="x", pady=(0, 10))

    app.cmb_preset_input = ttk.Combobox(frm_in, values=input_options, state="readonly")
    app.cmb_preset_input.pack(fill="x")
    if input_options:
        app.cmb_preset_input.set(input_options[0])

    # ===================== 2) PROCESSAMENTO (OPCIONAL) =====================
    frm_proc = ttk.LabelFrame(main, text="2. Processamento (Opcional)", padding=10)
    frm_proc.pack(fill="x", pady=(0, 10))

    app.var_convert = tk.BooleanVar(value=False)
    app.chk_convert = ttk.Checkbutton(
        frm_proc,
        text="Deseja conversão de valores?",
        variable=app.var_convert,
        command=lambda: use_case_handler.toggle_formula_field(app),
    )
    app.chk_convert.pack(anchor="w")

    ttk.Label(frm_proc, text="Fórmula (use 'value' como a variável de entrada):").pack(
        anchor="w", pady=(6, 0)
    )
    app.ent_formula = ttk.Entry(frm_proc, state="disabled")
    app.ent_formula.pack(fill="x")
    app.ent_formula.insert(0, "(value / 4095.0) * 3.3")  # exemplo p/ ADC

    # ===================== 3) AÇÃO DE SAÍDA =====================
    frm_out = ttk.LabelFrame(main, text="3. Ação de Saída", padding=10)
    frm_out.pack(fill="x", pady=(0, 10))

    app.cmb_preset_output = ttk.Combobox(frm_out, values=output_options, state="readonly")
    app.cmb_preset_output.pack(fill="x")
    if output_options:
        app.cmb_preset_output.set(output_options[0])
    app.cmb_preset_output.bind(
        "<<ComboboxSelected>>",
        lambda e: use_case_handler.toggle_threshold_field(app, e),
    )

    # --- campo condicional (threshold) — mostrado só p/ LED/PWM ---
    app.frm_threshold = ttk.Frame(frm_out)
    ttk.Label(app.frm_threshold, text="Ativar saída alta quando o valor for maior que:").pack(anchor="w")
    app.ent_threshold = ttk.Entry(app.frm_threshold)
    app.ent_threshold.pack(fill="x")
    app.ent_threshold.insert(0, "2048")

    # ===================== 4) AÇÕES =====================
    btns = ttk.Frame(main)
    btns.pack(fill="x", pady=(10, 0))

    # Aplicar (trava depois de sucesso)
    app.btn_apply_case = ttk.Button(
        btns,
        text="Adicionar Caso de Uso ao Projeto",
        command=lambda: use_case_handler.apply_use_case(app),
    )
    app.btn_apply_case.pack(side="left")

    # Destravar (para permitir alterar a escolha)
    app.btn_unlock_case = ttk.Button(
        btns,
        text="Alterar caso de uso",
        command=lambda: _unlock_only(app),
    )
    app.btn_unlock_case.pack(side="left", padx=8)

    # Estado inicial (handlers ajustam visibilidade do threshold e fórmula)
    use_case_handler.toggle_formula_field(app)
    use_case_handler.toggle_threshold_field(app)

    # Aplica estado de lock inicial
    _set_locked_state(app, bool(app.use_case_locked))
