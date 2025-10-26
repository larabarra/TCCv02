# tab_gpio.py
import tkinter as tk
from tkinter import ttk, messagebox
import data
from handlers import pinout_handler
import utils

def create_gpio_tab(parent_tab, app):
    """
    Cria a aba 'Pinout Detalhado' e registra no app:
      - app.selections (lista de dicts que o handler popula)
      - app.is_pin_used(pin_str)
      - app.refresh_table()  -> renderiza app.selections em app.tree
      - app.remove_selected_pinout() (opcional)
    Obs: mantém toda a tua UI original e adiciona apenas os shims necessários.
    """

    # ---------- estado base usado pelo handler ----------
    if not hasattr(app, "selections"):
        app.selections = []  # cada item: {"type","instance","name","port","pin","mode","pull","speed","alternate_fn"}

    # --- Add peripheral / signal frame ---
    frm_add = ttk.LabelFrame(parent_tab, text="Configuração Detalhada de Pino", padding=8)
    frm_add.pack(fill="x")

    # Peripheral Type
    ttk.Label(frm_add, text="Tipo:").grid(row=0, column=0, sticky="w")
    app.cmb_type = ttk.Combobox(frm_add, values=getattr(data, "DEFAULT_TYPES", ["GPIO","I2C","UART","TIM","ADC","SPI","CAN"]), state="readonly", width=10)
    app.cmb_type.set(getattr(data, "DEFAULT_TYPES", ["GPIO"])[0] if getattr(data, "DEFAULT_TYPES", None) else "GPIO")
    app.cmb_type.grid(row=0, column=1, sticky="w", padx=(4,12))
    app.cmb_type.bind("<<ComboboxSelected>>", lambda event: pinout_handler.on_type_change(app, event))

    # Instance
    ttk.Label(frm_add, text="Instância:").grid(row=0, column=2, sticky="w")
    app.cmb_inst = ttk.Combobox(frm_add, values=[], state="readonly", width=14)
    app.cmb_inst.grid(row=0, column=3, sticky="w", padx=(4,12))
    app.cmb_inst.bind("<<ComboboxSelected>>", lambda event: pinout_handler.on_instance_change(app, event))

    # Role / Function
    ttk.Label(frm_add, text="Função:").grid(row=0, column=4, sticky="w")
    app.cmb_role = ttk.Combobox(frm_add, values=[], state="readonly", width=16)
    app.cmb_role.grid(row=0, column=5, sticky="w", padx=(4,12))
    app.cmb_role.bind("<<ComboboxSelected>>", lambda event: pinout_handler.on_role_change(app, event))

    # Pin
    ttk.Label(frm_add, text="Pino:").grid(row=0, column=6, sticky="w")
    app.cmb_pin = ttk.Combobox(frm_add, values=[], state="readonly", width=10)
    app.cmb_pin.grid(row=0, column=7, sticky="w", padx=(4,12))
    app.cmb_pin.bind("<<ComboboxSelected>>", lambda event: pinout_handler.on_pin_change(app, event))

    # Label (Signal Name)
    ttk.Label(frm_add, text="Nome do Sinal (Label):").grid(row=1, column=0, sticky="w", pady=(8,0))
    app.ent_label = ttk.Entry(frm_add, width=28)
    app.ent_label.grid(row=1, column=1, columnspan=2, sticky="w", pady=(8,0), padx=(4,12))

    # GPIO Mode
    ttk.Label(frm_add, text="Modo:").grid(row=1, column=3, sticky="w", pady=(8,0))
    app.cmb_mode = ttk.Combobox(frm_add, values=["INPUT","OUTPUT_PP","OUTPUT_OD","AF_PP","AF_OD","ANALOG"], state="readonly", width=12)
    app.cmb_mode.grid(row=1, column=4, sticky="w", pady=(8,0), padx=(4,12))

    # GPIO Pull
    ttk.Label(frm_add, text="Pull:").grid(row=1, column=5, sticky="w", pady=(8,0))
    app.cmb_pull = ttk.Combobox(frm_add, values=["NOPULL","PULLUP","PULLDOWN"], state="readonly", width=10)
    app.cmb_pull.grid(row=1, column=6, sticky="w", pady=(8,0), padx=(4,12))

    # GPIO Speed
    ttk.Label(frm_add, text="Velocidade:").grid(row=1, column=7, sticky="w", pady=(8,0))
    app.cmb_speed = ttk.Combobox(frm_add, values=["LOW","MEDIUM","HIGH","VERY_HIGH"], state="readonly", width=12)
    app.cmb_speed.grid(row=1, column=8, sticky="w", pady=(8,0), padx=(4,12))

    # Alternate Function
    ttk.Label(frm_add, text="AF#:").grid(row=1, column=9, sticky="w", pady=(8,0))
    app.ent_af = ttk.Entry(frm_add, width=6)
    app.ent_af.grid(row=1, column=10, sticky="w", pady=(8,0), padx=(4,12))

    # Add button (manual)
    ttk.Button(frm_add, text="Adicionar", command=lambda: pinout_handler.add_row(app)).grid(row=1, column=11, sticky="w", pady=(8,0))

    # --- Selected signals frame (Treeview) ---
    frm_sel = ttk.LabelFrame(parent_tab, text="Pinout Configurado", padding=8)
    frm_sel.pack(fill="both", expand=True, pady=(8,0))

    cols = ("type","instance","name","port","pin","mode","pull","speed","af")
    app.tree = ttk.Treeview(frm_sel, columns=cols, show="headings", height=12)
    headers = ["Tipo","Instância","Nome","Porta","Pino","Modo","Pull","Velocidade","AF#"]
    widths  = [70, 90, 200, 70, 60, 110, 90, 100, 60]

    for c,h,w in zip(cols, headers, widths):
        app.tree.heading(c, text=h)
        app.tree.column(c, width=w, anchor="w")
    app.tree.pack(fill="both", expand=True)

    ttk.Button(frm_sel, text="Remover Selecionado", command=lambda: pinout_handler.del_selected(app)).pack(anchor="w", pady=(6,0))

    # ---------- SHIMS: funções que o handler usa ----------

    def is_pin_used(pin_str: str) -> bool:
        """
        Retorna True se 'PA0' etc já estiver em app.selections.
        """
        try:
            port, pin_num = utils.split_pin(pin_str)
        except Exception:
            port, pin_num = pin_str[:2], pin_str[2:]
        for r in app.selections:
            if r.get("port") == port and str(r.get("pin")) == str(pin_num):
                return True
        return False
    app.is_pin_used = is_pin_used

    def refresh_table():
        """
        Re-renderiza app.selections na Treeview.
        Converte 'alternate_fn' -> coluna 'af'.
        """
        app.tree.delete(*app.tree.get_children())
        for r in app.selections:
            vals = (
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
            app.tree.insert("", "end", values=vals)
    app.refresh_table = refresh_table

    # Alguma parte da tua app pode chamar isso; se não existir, vira no-op.
    if not hasattr(app, "update_peripheral_tabs_state"):
        app.update_peripheral_tabs_state = lambda: None
