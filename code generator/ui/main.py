#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import importlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ==================== PRESETS DE INSTÂNCIAS (ajuste conforme seu MCU/placa) ====================
INSTANCE_PRESETS = {
    "GPIO":   [],
    "I2C":    ["I2C1", "I2C2", "I2C3", "I2C4"],
    "USART":  ["USART1", "USART2", "USART3", "UART4", "UART5", "LPUART1"],
    "SPI":    ["SPI1", "SPI2", "SPI3"],
    "TIMER":  ["TIM1", "TIM2", "TIM3", "TIM4", "TIM6", "TIM7", "TIM15", "TIM16", "TIM17", "HRTIM1"],
    "ADC":    ["ADC1", "ADC2", "ADC3", "ADC4", "ADC5"],
}
DEFAULT_TYPES = ["GPIO", "I2C", "USART", "SPI", "TIMER", "ADC"]

# ==================== MAPA EMBUTIDO (parcial) ====================
EMBEDDED_MAP = {
    "microcontroller": "STM32G474xx",
    "schema_version": "1.0",
    "ports": {
        "GPIOA": { "pins": [
            { "pin": 0, "af": {}, "notes": "" },
            { "pin": 1, "af": {}, "notes": "" },
            { "pin": 2, "af": {}, "notes": "" },
            { "pin": 3, "af": {}, "notes": "" },
            { "pin": 4, "af": {}, "notes": "" },
            { "pin": 5, "af": { "SPI1_SCK": 5, "TIM2_CH1_ETR": 1 }, "notes": "LED em Nucleo; AF5=SPI1_SCK" },
            { "pin": 6, "af": { "SPI1_MISO": 5, "TIM3_CH1": 2 }, "notes": "" },
            { "pin": 7, "af": { "SPI1_MOSI": 5, "TIM3_CH2": 2 }, "notes": "" },
            { "pin": 8, "af": { "USART1_CK": 7 }, "notes": "" },
            { "pin": 9, "af": { "USART1_TX": 7 }, "notes": "" },
            { "pin": 10,"af": { "USART1_RX": 7 }, "notes": "" },
            { "pin": 11,"af": {}, "notes": "" },
            { "pin": 12,"af": {}, "notes": "" },
            { "pin": 13,"af": {}, "notes": "" },
            { "pin": 14,"af": { "USART2_TX": 7 }, "notes": "" },
            { "pin": 15,"af": { "USART2_RX": 7 }, "notes": "" }
        ]},
        "GPIOB": { "pins": [
            { "pin": 0, "af": {}, "notes": "" },
            { "pin": 1, "af": {}, "notes": "" },
            { "pin": 2, "af": {}, "notes": "" },
            { "pin": 3, "af": { "SPI1_SCK": 5, "USART1_TX": 7 }, "notes": "" },
            { "pin": 4, "af": { "SPI1_MISO": 5 }, "notes": "" },
            { "pin": 5, "af": { "SPI1_MOSI": 5 }, "notes": "" },
            { "pin": 6, "af": { "I2C1_SCL": 4, "USART1_TX": 7 }, "notes": "I2C1_SCL AF4" },
            { "pin": 7, "af": { "I2C1_SDA": 4, "USART1_RX": 7 }, "notes": "I2C1_SDA AF4" },
            { "pin": 8, "af": { "I2C1_SCL": 4 }, "notes": "Alt SCL" },
            { "pin": 9, "af": { "I2C1_SDA": 4 }, "notes": "Alt SDA" },
            { "pin": 10,"af": { "USART3_TX": 7 }, "notes": "" },
            { "pin": 11,"af": { "USART3_RX": 7 }, "notes": "" },
            { "pin": 12,"af": {}, "notes": "" },
            { "pin": 13,"af": {}, "notes": "" },
            { "pin": 14,"af": {}, "notes": "" },
            { "pin": 15,"af": {}, "notes": "" }
        ]},
        "GPIOC": { "pins": [
            { "pin": 0, "af": {}, "notes": "" },
            { "pin": 1, "af": {}, "notes": "" },
            { "pin": 2, "af": {}, "notes": "" },
            { "pin": 3, "af": {}, "notes": "" },
            { "pin": 4, "af": {}, "notes": "" },
            { "pin": 5, "af": {}, "notes": "" },
            { "pin": 6, "af": {}, "notes": "" },
            { "pin": 7, "af": {}, "notes": "" },
            { "pin": 8, "af": {}, "notes": "" },
            { "pin": 9, "af": {}, "notes": "" },
            { "pin": 10,"af": {}, "notes": "" },
            { "pin": 11,"af": {}, "notes": "" },
            { "pin": 12,"af": {}, "notes": "" },
            { "pin": 13,"af": {}, "notes": "Botão user em muitas Nucleo" },
            { "pin": 14,"af": {}, "notes": "" },
            { "pin": 15,"af": {}, "notes": "" }
        ]}
    },
    "modes": ["INPUT", "OUTPUT_PP", "OUTPUT_OD", "AF_PP", "AF_OD", "ANALOG"],
    "pull": ["NOPULL", "PULLUP", "PULLDOWN"],
    "speed": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STM32G474 — Gerador de config.json (Tkinter)")
        self.geometry("1120x660")
        self.minsize(980, 600)

        self.pinmap = None
        # cada item: {type, instance, name, port, pin, mode, pull, speed, alternate_fn}
        self.selections = []

        self._build_ui()
        self.use_embedded_map()

    # -------------------- UI --------------------
    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Projeto:").pack(side="left")
        self.ent_project = ttk.Entry(top, width=24)
        self.ent_project.insert(0, "AAAA")
        self.ent_project.pack(side="left", padx=(4,12))

        ttk.Label(top, text="Microcontrolador:").pack(side="left")
        self.ent_mcu = ttk.Entry(top, width=24)
        self.ent_mcu.insert(0, "STM32G474RE")
        self.ent_mcu.pack(side="left", padx=(4,12))

        # Botões principais (inclui Gerar .c/.h)
        ttk.Button(top, text="Carregar mapeamento JSON…", command=self.load_map).pack(side="right", padx=4)
        ttk.Button(top, text="Usar mapa embutido", command=self.use_embedded_map).pack(side="right", padx=4)
        ttk.Button(top, text="Gerar .c/.h", command=self.generate_files).pack(side="right", padx=4)
        ttk.Button(top, text="Exportar config.json", command=self.export_config).pack(side="right", padx=12)

        mid = ttk.Panedwindow(self, orient="horizontal")
        mid.pack(fill="both", expand=True, padx=6, pady=6)

        # Left: mapping viewer
        left = ttk.Frame(mid, padding=6)
        mid.add(left, weight=1)

        ttk.Label(left, text="Mapeamento carregado (visualização rápida)").pack(anchor="w")
        columns = ("port","pin","afs","notes")
        self.tree_map = ttk.Treeview(left, columns=columns, show="headings", height=14)
        for c, w in zip(columns, (70, 50, 420, 200)):
            self.tree_map.heading(c, text=c.upper())
            self.tree_map.column(c, width=w, anchor="w")
        self.tree_map.pack(fill="both", expand=True, pady=(4,0))
        self.lbl_map_meta = ttk.Label(left, text="Nenhum mapeamento.")
        self.lbl_map_meta.pack(anchor="w", pady=(4,0))

        # Right: add form + selections
        right = ttk.Frame(mid, padding=6)
        mid.add(right, weight=2)

        frm_add = ttk.LabelFrame(right, text="Adicionar periférico / sinal", padding=8)
        frm_add.pack(fill="x")

        ttk.Label(frm_add, text="Tipo:").grid(row=0, column=0, sticky="w")
        self.cmb_type = ttk.Combobox(frm_add, values=DEFAULT_TYPES, state="readonly", width=12)
        self.cmb_type.set(DEFAULT_TYPES[0])
        self.cmb_type.grid(row=0, column=1, sticky="w", padx=(4,12))
        self.cmb_type.bind("<<ComboboxSelected>>", self._on_type_changed)

        ttk.Label(frm_add, text="Instância:").grid(row=0, column=2, sticky="w")
        self.cmb_instance = ttk.Combobox(frm_add, values=[], state="readonly", width=16)
        self.cmb_instance.grid(row=0, column=3, sticky="w", padx=(4,6))
        self.cmb_instance.bind("<<ComboboxSelected>>", self._on_instance_changed)

        self.ent_instance_custom = ttk.Entry(frm_add, width=18)  # aparece se "Custom…"
        self.ent_instance_custom.grid(row=0, column=4, sticky="w", padx=(0,12))
        self.ent_instance_custom.grid_remove()

        ttk.Label(frm_add, text="Nome/Label:").grid(row=0, column=5, sticky="w")
        self.ent_label = ttk.Entry(frm_add, width=20)
        self.ent_label.grid(row=0, column=6, sticky="w", padx=(4,12))

        ttk.Button(frm_add, text="Adicionar", command=self.add_row).grid(row=0, column=7, sticky="w")

        # Tabela de seleções
        frm_sel = ttk.LabelFrame(right, text="Sinais / Seleções", padding=8)
        frm_sel.pack(fill="both", expand=True, pady=(8,0))
        cols_sel = ("type","instance","name","port","pin","mode","pull","speed","af")
        self.tree_sel = ttk.Treeview(frm_sel, columns=cols_sel, show="headings", height=10, selectmode="browse")
        headers = ["Tipo","Instância","Nome","Porta","Pino","Modo","Pull","Veloc.","AF#"]
        widths  = [80, 100, 160, 70, 60, 110, 90, 70, 60]
        for c,h,w in zip(cols_sel, headers, widths):
            self.tree_sel.heading(c, text=h)
            self.tree_sel.column(c, width=w, anchor="w")
        self.tree_sel.grid(row=0, column=0, sticky="nsew", columnspan=6)
        frm_sel.rowconfigure(0, weight=1)
        frm_sel.columnconfigure(0, weight=1)

        btns = ttk.Frame(frm_sel)
        btns.grid(row=1, column=0, sticky="w", pady=(6,0))
        ttk.Button(btns, text="Remover selecionado", command=self.del_selected).pack(side="left")

        # Editor
        editor = ttk.LabelFrame(frm_sel, text="Editor da linha selecionada", padding=8)
        editor.grid(row=2, column=0, sticky="ew", pady=(8,0))
        for i in range(0, 16):
            editor.columnconfigure(i, weight=1)

        ttk.Label(editor, text="Porta:").grid(row=0, column=0, sticky="w")
        self.cmb_port = ttk.Combobox(editor, values=[], state="readonly", width=10)
        self.cmb_port.grid(row=0, column=1, sticky="w", padx=(4,12))
        self.cmb_port.bind("<<ComboboxSelected>>", self._on_port_change)

        ttk.Label(editor, text="Pino:").grid(row=0, column=2, sticky="w")
        self.cmb_pin = ttk.Combobox(editor, values=[], state="readonly", width=10)
        self.cmb_pin.grid(row=0, column=3, sticky="w", padx=(4,12))

        ttk.Label(editor, text="Modo:").grid(row=0, column=4, sticky="w")
        self.cmb_mode = ttk.Combobox(editor, values=[], state="readonly", width=12)
        self.cmb_mode.grid(row=0, column=5, sticky="w", padx=(4,12))

        ttk.Label(editor, text="Pull:").grid(row=0, column=6, sticky="w")
        self.cmb_pull = ttk.Combobox(editor, values=[], state="readonly", width=10)
        self.cmb_pull.grid(row=0, column=7, sticky="w", padx=(4,12))

        ttk.Label(editor, text="Velocidade:").grid(row=0, column=8, sticky="w")
        self.cmb_speed = ttk.Combobox(editor, values=[], state="readonly", width=12)
        self.cmb_speed.grid(row=0, column=9, sticky="w", padx=(4,12))

        ttk.Label(editor, text="AF#:").grid(row=0, column=10, sticky="w")
        self.ent_af = ttk.Entry(editor, width=6)
        self.ent_af.grid(row=0, column=11, sticky="w", padx=(4,12))

        ttk.Button(editor, text="Aplicar edição", command=self.apply_edit).grid(row=0, column=12, sticky="e")

        self.tree_sel.bind("<<TreeviewSelect>>", self.populate_editor_from_selection)

        # estilo
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except:
            pass

        self._on_type_changed()

    # -------------------- Helpers de UI --------------------
    def _on_type_changed(self, event=None):
        t = self.cmb_type.get()
        insts = INSTANCE_PRESETS.get(t, [])
        if t == "GPIO":
            self.cmb_instance["values"] = []
            self.cmb_instance.set("")
            self.cmb_instance.configure(state="disabled")
            self.ent_instance_custom.grid_remove()
        else:
            self.cmb_instance.configure(state="readonly")
            self.cmb_instance["values"] = insts
            if insts:
                self.cmb_instance.set(insts[0])
            else:
                self.cmb_instance.set("")
            self._toggle_custom_instance_field()

    def _on_instance_changed(self, event=None):
        self._toggle_custom_instance_field()

    def _toggle_custom_instance_field(self):
        if self.cmb_instance.get() == "Custom…":
            self.ent_instance_custom.grid()
            if not self.ent_instance_custom.get():
                self.ent_instance_custom.insert(0, "EX: I2C5")
        else:
            self.ent_instance_custom.grid_remove()

    def _current_instance_value(self):
        t = self.cmb_type.get()
        if t == "GPIO":
            return ""
        sel = self.cmb_instance.get()
        if sel == "Custom…":
            return self.ent_instance_custom.get().strip()
        return sel.strip()

    # -------------------- Map handling --------------------
    def use_embedded_map(self):
        self.set_pinmap(EMBEDDED_MAP, meta="Mapa embutido (parcial)")

    def load_map(self):
        path = filedialog.askopenfilename(
            title="Selecionar stm32g474xx_pins.json",
            filetypes=[("JSON","*.json"), ("Todos","*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                mp = json.load(f)
            self.set_pinmap(mp, meta=f"Arquivo: {path}")
        except Exception as e:
            messagebox.showerror("Erro ao carregar JSON", str(e))

    def set_pinmap(self, mp, meta=""):
        self.pinmap = mp
        self.refresh_map_table()
        modes = (self.pinmap.get("modes") or ["INPUT","OUTPUT_PP","AF_PP","AF_OD","ANALOG"])
        pulls = (self.pinmap.get("pull") or ["NOPULL","PULLUP","PULLDOWN"])
        speeds = (self.pinmap.get("speed") or ["LOW","MEDIUM","HIGH","VERY_HIGH"])
        self.cmb_mode["values"]  = modes
        self.cmb_pull["values"]  = pulls
        self.cmb_speed["values"] = speeds
        ports = sorted((self.pinmap.get("ports") or {}).keys())
        self.cmb_port["values"]  = ports
        self.lbl_map_meta.configure(text=f'{meta} • MCU: {mp.get("microcontroller","?")} • schema: {mp.get("schema_version","?")}')

    def refresh_map_table(self):
        for item in self.tree_map.get_children():
            self.tree_map.delete(item)
        if not self.pinmap:
            return
        for port in sorted(self.pinmap.get("ports", {}).keys()):
            for p in self.pinmap["ports"][port].get("pins", []):
                afs = p.get("af", {})
                af_text = " ".join([f"{k}:{v}" for k,v in afs.items()]) if afs else "—"
                self.tree_map.insert("", "end", values=(port, p.get("pin"), af_text, p.get("notes","")))

    # -------------------- Selections --------------------
    def add_row(self):
        if not self.pinmap:
            messagebox.showwarning("Mapa ausente", "Carregue um mapeamento ou use o embutido.")
            return

        t = self.cmb_type.get()
        inst_value = self._current_instance_value()  # "" para GPIO
        label = self.ent_label.get().strip() or ("SIGNAL" if t=="GPIO" else (t+"_SIG"))

        ports = sorted((self.pinmap.get("ports") or {}).keys())
        first_port = ports[0] if ports else "GPIOA"
        pins = self.pinmap["ports"][first_port].get("pins", []) if ports else []
        first_pin = pins[0]["pin"] if pins else 0

        mode_default = "INPUT" if t=="GPIO" else "AF_PP"
        row = {
            "type": t, "instance": inst_value, "name": label,
            "port": first_port, "pin": first_pin,
            "mode": mode_default, "pull": "NOPULL", "speed": "LOW",
            "alternate_fn": 0
        }
        self.selections.append(row)
        self._refresh_sel_tree()

    def _refresh_sel_tree(self):
        self.tree_sel.delete(*self.tree_sel.get_children())
        for i, r in enumerate(self.selections):
            self.tree_sel.insert("", "end", iid=str(i), values=(
                r["type"], r["instance"], r["name"], r["port"], r["pin"],
                r["mode"], r["pull"], r["speed"], r["alternate_fn"]
            ))

    def del_selected(self):
        cur = self.tree_sel.selection()
        if not cur: return
        idx = int(cur[0])
        del self.selections[idx]
        self._refresh_sel_tree()

    def populate_editor_from_selection(self, event=None):
        cur = self.tree_sel.selection()
        if not cur: return
        idx = int(cur[0])
        r = self.selections[idx]

        ports = sorted((self.pinmap.get("ports") or {}).keys())
        self.cmb_port["values"] = ports
        try:
            self.cmb_port.set(r["port"])
        except:
            if ports:
                self.cmb_port.set(ports[0])

        self._populate_pins_for_port(self.cmb_port.get())
        self.cmb_pin.set(str(r["pin"]))

        self.cmb_mode.set(r["mode"])
        self.cmb_pull.set(r["pull"])
        self.cmb_speed.set(r["speed"])
        self.ent_af.delete(0, 'end')
        self.ent_af.insert(0, str(r.get("alternate_fn",0)))

    def _populate_pins_for_port(self, port):
        pins = []
        if self.pinmap and self.pinmap.get("ports") and self.pinmap["ports"].get(port):
            pins = [str(p["pin"]) for p in self.pinmap["ports"][port].get("pins", [])]
        self.cmb_pin["values"] = pins

    def _on_port_change(self, event=None):
        port = self.cmb_port.get()
        self._populate_pins_for_port(port)
        vals = self.cmb_pin["values"]
        if vals:
            self.cmb_pin.set(vals[0])

    def apply_edit(self):
        cur = self.tree_sel.selection()
        if not cur:
            messagebox.showinfo("Seleção", "Selecione uma linha na tabela de sinais.")
            return
        idx = int(cur[0])

        port = self.cmb_port.get()
        pin  = int(self.cmb_pin.get()) if self.cmb_pin.get().isdigit() else 0
        mode = self.cmb_mode.get()
        pull = self.cmb_pull.get()
        spd  = self.cmb_speed.get()
        try:
            afn = int(self.ent_af.get())
        except:
            afn = 0

        self.selections[idx]["port"] = port
        self.selections[idx]["pin"]  = pin
        self.selections[idx]["mode"] = mode
        self.selections[idx]["pull"] = pull
        self.selections[idx]["speed"] = spd
        self.selections[idx]["alternate_fn"] = afn

        self._refresh_sel_tree()

    # -------------------- Export JSON --------------------
    def export_config(self):
        if not self.selections:
            messagebox.showwarning("Nada a exportar", "Adicione pelo menos um sinal/periférico.")
            return

        project_name = self.ent_project.get().strip() or "MyProject"
        micro = self.ent_mcu.get().strip() or (self.pinmap.get("microcontroller") if self.pinmap else "STM32")
        grouped = {}

        for r in self.selections:
            t = r["type"]
            grouped.setdefault(t, []).append(r)

        peripherals = []
        for t, rows in grouped.items():
            if t == "GPIO":
                peripherals.append({
                    "type": t,
                    "pins": [
                        {
                            "name": x["name"], "port": x["port"], "pin": x["pin"],
                            "mode": x["mode"], "pull": x["pull"], "speed": x["speed"],
                            "alternate_fn": x.get("alternate_fn",0)
                        } for x in rows
                    ]
                })
            else:
                by_inst = {}
                for x in rows:
                    key = x["instance"].strip() if x.get("instance") else f"{t}_X"
                    by_inst.setdefault(key, []).append(x)
                for inst, lst in by_inst.items():
                    peripherals.append({
                        "type": t,
                        "instance": inst,
                        "pins": [
                            {
                                "name": x["name"], "port": x["port"], "pin": x["pin"],
                                "mode": x["mode"], "pull": x["pull"], "speed": x["speed"],
                                "alternate_fn": x.get("alternate_fn",0)
                            } for x in lst
                        ]
                    })

        out = {
            "project_name": project_name,
            "microcontroller": micro,
            "peripherals": peripherals
        }

        path = filedialog.asksaveasfilename(
            title="Salvar config.json",
            defaultextension=".json",
            filetypes=[("JSON","*.json"), ("Todos","*.*")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Exportado", f"Arquivo salvo em:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    # -------------------- Botão: Gerar .c/.h --------------------
    def generate_files(self):
        """
        Abre um config.json, importa generate_all e chama generate_project_files(...).
        - Se o seu generate_all.py já existir, ele será usado.
        - Se não existir, mostre um erro amigável.
        """
        cfg_path = filedialog.askopenfilename(
            title="Selecionar config.json para gerar .c/.h",
            filetypes=[("JSON","*.json"), ("Todos","*.*")]
        )
        if not cfg_path:
            return

        try:
            gen = importlib.import_module("generate_all") 
        except Exception as e:
            messagebox.showerror(
                "generate_all.py não encontrado",
                "Coloque seu arquivo 'generate_all.py' na mesma pasta do UI.\n\nDetalhes:\n" + str(e)
            )
            return

        try:
            # Se o seu módulo tiver load_config_data, use-o. Senão, carregamos aqui mesmo.
        
            with open(cfg_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

            # O seu generate_project_files parece esperar uma LISTA de blocos.
            # Nosso JSON exportado tem {"peripherals": [ ... ]}.
            if isinstance(config_data, dict) and "peripherals" in config_data:
                blocks = config_data["peripherals"]
            else:
                blocks = config_data  # já é lista

            if not hasattr(gen, "generate_project_files"):
                raise RuntimeError("Função 'generate_project_files' não encontrada em generate_all.py")

            out_files = gen.generate_project_files(blocks)
            if not out_files:
                messagebox.showinfo("Geração concluída", "Nenhum arquivo reportado, verifique os logs/console.")
            else:
                msg = "Arquivos gerados:\n\n" + "\n".join(out_files)
                messagebox.showinfo("Geração concluída", msg)

        except Exception as e:
            messagebox.showerror("Erro durante a geração", str(e))


if __name__ == "__main__":
    App().mainloop()
