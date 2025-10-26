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

def create_presets_tab(parent_tab, app):
    """
    Aba 'Construtor de Casos de Uso'
      1) Fonte de Entrada  (combobox vem de presets.json, direction=input)
      2) Processamento (opcional)
      3) Ação de Saída    (combobox vem de presets.json, direction=output)
      4) Botão 'Adicionar Caso de Uso ao Projeto'
    """
    # --- container principal ---
    main = ttk.Frame(parent_tab)
    main.pack(fill="both", expand=True, padx=6, pady=6)

    # ===================== 1) FONTE DE ENTRADA =====================
    frm_in = ttk.LabelFrame(main, text="1. Fonte de Entrada", padding=10)
    frm_in.pack(fill="x", pady=(0, 10))

    input_options, output_options = _split_by_direction()

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
    # exemplo padrão para ADC
    app.ent_formula.insert(0, "(value / 4095.0) * 3.3")

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

    # ===================== 4) APLICAR =====================
    ttk.Button(
        main,
        text="Adicionar Caso de Uso ao Projeto",
        command=lambda: use_case_handler.apply_use_case(app),
    ).pack(pady=12)

    # estado inicial dos campos condicionais
    use_case_handler.toggle_formula_field(app)
    use_case_handler.toggle_threshold_field(app)
