#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tk UI para montar config.json a partir de um mapping (GPIO/I2C/UART/SPI/ADC)
e, opcionalmente, chamar o pipeline de geração (.c/.h) via generate_all.py.

- Tipo -> Instância -> Função -> Pino são povoados do mapping.
- AF é deduzido automaticamente (I2C/UART/SPI) a partir do mapping (ex.: GPIO_AF7_USART1 -> 7).
- Campo "Label" permite nomear cada sinal/pino (ex.: LED_STATUS, I2C_SCL, USART1_TX...).
- Botão "Gerar .c/.h" chama generate_all.generate_project_files(peripherals).

Coloque este arquivo e seu generate_all.py na mesma pasta.
"""

import json
import re
import importlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ========================= COLE/EDITE SEU MAPPING AQUI =========================
MCU_MAP = {
  "STM32G474RE": {
    "gpio_pins": [
      "PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PA8","PA9","PA10","PA11","PA12","PA13","PA14","PA15",
      "PB0","PB1","PB2","PB3","PB4","PB5","PB6","PB7","PB8","PB9","PB10","PB11","PB12","PB13","PB14","PB15",
      "PC0","PC1","PC2","PC3","PC4","PC5","PC6","PC7","PC8","PC9","PC10","PC11","PC12","PC13","PC14","PC15"
    ],
    "i2c_interfaces": {
      "I2C1": { "scl": ["PB6", "PB8"], "sda": ["PB7", "PB9"] },
      "I2C2": { "scl": ["PB10"], "sda": ["PB11", "PB3"] }
    },
    "i2c_af_mapping": {
      "I2C1": { "PB6": "GPIO_AF4_I2C1", "PB7": "GPIO_AF4_I2C1", "PB8": "GPIO_AF4_I2C1", "PB9": "GPIO_AF4_I2C1" },
      "I2C2": { "PB10": "GPIO_AF4_I2C2", "PB11": "GPIO_AF4_I2C2", "PB3": "GPIO_AF9_I2C2" }
    },
    "adc_interfaces": {
      "ADC1": [
        "ADC_IN1","ADC_IN2","ADC_IN3","ADC_IN4","ADC_IN5","ADC_IN6","ADC_IN7","ADC_IN8",
        "ADC_IN9","ADC_IN10","ADC_IN11","ADC_IN12","ADC_IN13","ADC_IN14","ADC_IN15","ADC_IN16"
      ]
    },
    "adc_pin_mapping": {
      "ADC1": {
        "ADC_IN1": "PA0", "ADC_IN2": "PA1", "ADC_IN3": "PA2", "ADC_IN4": "PA3", "ADC_IN5": "PA4",
        "ADC_IN6": "PA5", "ADC_IN7": "PA6", "ADC_IN8": "PA7", "ADC_IN9": "PB0", "ADC_IN10": "PB1",
        "ADC_IN11": "PC0", "ADC_IN12": "PC1", "ADC_IN13": "PC2", "ADC_IN14": "PC3", "ADC_IN15": "PC4",
        "ADC_IN16": "PC5"
      }
    },
    "uart_interfaces": {
      "UART1": { "tx": ["PA9", "PB6"], "rx": ["PA10", "PB7"] },
      "UART2": { "tx": ["PA2", "PA14"], "rx": ["PA3", "PA15"] },
      "UART3": { "tx": ["PB10", "PC4"], "rx": ["PB11", "PC5"] },
      "UART4": { "tx": ["PA0"], "rx": ["PA1"] }
    },
    "uart_af_mapping": {
      "UART1": { "PA9": "GPIO_AF7_USART1", "PA10": "GPIO_AF7_USART1", "PB6": "GPIO_AF7_USART1", "PB7": "GPIO_AF7_USART1" },
      "UART2": { "PA2": "GPIO_AF7_USART2", "PA3": "GPIO_AF7_USART2", "PA14": "GPIO_AF7_USART2", "PA15": "GPIO_AF7_USART2" },
      "UART3": { "PB10": "GPIO_AF7_USART3", "PB11": "GPIO_AF7_USART3", "PC4": "GPIO_AF7_USART3", "PC5": "GPIO_AF7_USART3" },
      "UART4": { "PA0": "GPIO_AF8_UART4", "PA1": "GPIO_AF8_UART4" }
    },
    "spi_interfaces": {
      "SPI1": { "sck": ["PA5", "PB3"], "miso": ["PA6", "PB4"], "mosi": ["PA7", "PB5"] },
      "SPI2": { "sck": ["PB13"], "miso": ["PC2"], "mosi": ["PC3"] },
      "SPI3": { "sck": ["PC10", "PB3"], "miso": ["PC11", "PB4"], "mosi": ["PC12", "PB5"] }
    },
    "spi_af_mapping": {
      "SPI1": {
        "PA5": "GPIO_AF5_SPI1", "PB3": "GPIO_AF5_SPI1", "PA6": "GPIO_AF5_SPI1", "PB4": "GPIO_AF5_SPI1", "PA7": "GPIO_AF5_SPI1", "PB5": "GPIO_AF5_SPI1"
      },
      "SPI2": { "PB13": "GPIO_AF5_SPI2", "PC2": "GPIO_AF5_SPI2", "PC3": "GPIO_AF5_SPI2" },
      "SPI3": {
        "PC10": "GPIO_AF6_SPI3", "PB3": "GPIO_AF6_SPI3", "PC11": "GPIO_AF6_SPI3", "PB4": "GPIO_AF6_SPI3",
        "PC12": "GPIO_AF6_SPI3", "PB5": "GPIO_AF6_SPI3"
      }
    }
  }
}
# ===========================================================================

DEFAULT_TYPES = ["GPIO", "I2C", "UART", "SPI", "ADC"]

def split_pin(pin_label: str):
    m = re.match(r"P([A-F])(\d{1,2})$", pin_label)
    return (f"GPIO{m.group(1)}", int(m.group(2))) if m else ("GPIOA", 0)

def af_str_to_num(af: str) -> int:
    m = re.search(r"AF(\d+)", af or "")
    return int(m.group(1)) if m else 0

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STM32G474 — config.json (Mapping + Gerador)")
        self.geometry("1150x740")
        self.minsize(980, 620)

        self.current_mcu = list(MCU_MAP.keys())[0]
        self.mcu_data = MCU_MAP[self.current_mcu]
        self.selections = []  # rows para export

        self._build_ui()
        self._refresh_mapping_view()

    # ---------------- UI ----------------
    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Projeto:").pack(side="left")
        self.ent_project = ttk.Entry(top, width=24)
        self.ent_project.insert(0, "AAAA")
        self.ent_project.pack(side="left", padx=(4,12))

        ttk.Label(top, text="MCU:").pack(side="left")
        self.cmb_mcu = ttk.Combobox(top, values=list(MCU_MAP.keys()), state="readonly", width=16)
        self.cmb_mcu.set(self.current_mcu)
        self.cmb_mcu.pack(side="left", padx=(4,12))
        self.cmb_mcu.bind("<<ComboboxSelected>>", self._on_mcu_change)

        # Botões principais (inclui Gerar .c/.h)
        ttk.Button(top, text="Carregar mapping JSON…", command=self.load_mapping_json).pack(side="right", padx=4)
        ttk.Button(top, text="Gerar .c/.h", command=self.generate_files).pack(side="right", padx=4)
        ttk.Button(top, text="Exportar config.json", command=self.export_config).pack(side="right", padx=4)

        mid = ttk.Panedwindow(self, orient="horizontal")
        mid.pack(fill="both", expand=True, padx=6, pady=6)

        # Esquerda: visual do mapping (pinos GPIO)
        left = ttk.Frame(mid, padding=6)
        mid.add(left, weight=1)
        ttk.Label(left, text="GPIO disponíveis").pack(anchor="w")
        self.lst_gpio = tk.Listbox(left, height=20)
        self.lst_gpio.pack(fill="both", expand=True)

        # Direita: add form + seleções
        right = ttk.Frame(mid, padding=6)
        mid.add(right, weight=2)

        frm_add = ttk.LabelFrame(right, text="Adicionar periférico / sinal", padding=8)
        frm_add.pack(fill="x")

        # Tipo
        ttk.Label(frm_add, text="Tipo:").grid(row=0, column=0, sticky="w")
        self.cmb_type = ttk.Combobox(frm_add, values=DEFAULT_TYPES, state="readonly", width=10)
        self.cmb_type.set(DEFAULT_TYPES[0])
        self.cmb_type.grid(row=0, column=1, sticky="w", padx=(4,12))
        self.cmb_type.bind("<<ComboboxSelected>>", self._on_type_change)

        # Instância
        ttk.Label(frm_add, text="Instância:").grid(row=0, column=2, sticky="w")
        self.cmb_inst = ttk.Combobox(frm_add, values=[], state="readonly", width=14)
        self.cmb_inst.grid(row=0, column=3, sticky="w", padx=(4,12))
        self.cmb_inst.bind("<<ComboboxSelected>>", self._on_instance_change)

        # Função / Role
        ttk.Label(frm_add, text="Função:").grid(row=0, column=4, sticky="w")
        self.cmb_role = ttk.Combobox(frm_add, values=[], state="readonly", width=16)
        self.cmb_role.grid(row=0, column=5, sticky="w", padx=(4,12))
        self.cmb_role.bind("<<ComboboxSelected>>", self._on_role_change)

        # Pino
        ttk.Label(frm_add, text="Pino:").grid(row=0, column=6, sticky="w")
        self.cmb_pin = ttk.Combobox(frm_add, values=[], state="readonly", width=10)
        self.cmb_pin.grid(row=0, column=7, sticky="w", padx=(4,12))
        self.cmb_pin.bind("<<ComboboxSelected>>", self._on_pin_change)

        # Label (nome do pino/sinal)
        ttk.Label(frm_add, text="Label (nome):").grid(row=1, column=0, sticky="w", pady=(8,0))
        self.ent_label = ttk.Entry(frm_add, width=28)
        self.ent_label.grid(row=1, column=1, columnspan=2, sticky="w", pady=(8,0), padx=(4,12))

        # Config (auto mas editável)
        ttk.Label(frm_add, text="Modo:").grid(row=1, column=3, sticky="w", pady=(8,0))
        self.cmb_mode = ttk.Combobox(frm_add, values=["INPUT","OUTPUT_PP","OUTPUT_OD","AF_PP","AF_OD","ANALOG"],
                                     state="readonly", width=12)
        self.cmb_mode.grid(row=1, column=4, sticky="w", pady=(8,0), padx=(4,12))

        ttk.Label(frm_add, text="Pull:").grid(row=1, column=5, sticky="w", pady=(8,0))
        self.cmb_pull = ttk.Combobox(frm_add, values=["NOPULL","PULLUP","PULLDOWN"], state="readonly", width=10)
        self.cmb_pull.grid(row=1, column=6, sticky="w", pady=(8,0), padx=(4,12))

        ttk.Label(frm_add, text="Velocidade:").grid(row=1, column=7, sticky="w", pady=(8,0))
        self.cmb_speed = ttk.Combobox(frm_add, values=["LOW","MEDIUM","HIGH","VERY_HIGH"], state="readonly", width=12)
        self.cmb_speed.grid(row=1, column=8, sticky="w", pady=(8,0), padx=(4,12))

        ttk.Label(frm_add, text="AF#:").grid(row=1, column=9, sticky="w", pady=(8,0))
        self.ent_af = ttk.Entry(frm_add, width=6)
        self.ent_af.grid(row=1, column=10, sticky="w", pady=(8,0), padx=(4,12))

        ttk.Button(frm_add, text="Adicionar", command=self.add_row).grid(row=1, column=11, sticky="w", pady=(8,0))

        # Tabela de seleções
        frm_sel = ttk.LabelFrame(right, text="Sinais selecionados", padding=8)
        frm_sel.pack(fill="both", expand=True, pady=(8,0))
        cols = ("type","instance","name","port","pin","mode","pull","speed","af")
        self.tree = ttk.Treeview(frm_sel, columns=cols, show="headings", height=12)
        headers = ["Tipo","Instância","Nome","Porta","Pino","Modo","Pull","Veloc.","AF#"]
        widths  = [70, 90, 180, 70, 60, 110, 90, 80, 60]
        for c,h,w in zip(cols, headers, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        ttk.Button(frm_sel, text="Remover selecionado", command=self.del_selected).pack(anchor="w", pady=(6,0))

        # Estado inicial
        self._on_type_change()

    # -------------- Mapping→UI --------------
    def _on_mcu_change(self, event=None):
        self.current_mcu = self.cmb_mcu.get()
        self.mcu_data = MCU_MAP[self.current_mcu]
        self._refresh_mapping_view()
        self._on_type_change()

    def _refresh_mapping_view(self):
        self.lst_gpio.delete(0, "end")
        for p in self.mcu_data.get("gpio_pins", []):
            self.lst_gpio.insert("end", p)

    def load_mapping_json(self):
        path = filedialog.askopenfilename(title="Abrir mapping JSON", filetypes=[("JSON","*.json"), ("Todos","*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            global MCU_MAP
            MCU_MAP = data
            self.cmb_mcu["values"] = list(MCU_MAP.keys())
            self.cmb_mcu.set(list(MCU_MAP.keys())[0])
            self._on_mcu_change()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar mapping:\n{e}")

    # -------------- Fluxo Tipo→Instância→Função→Pino --------------
    def _on_type_change(self, event=None):
        t = self.cmb_type.get()
        self.cmb_inst["values"] = []
        self.cmb_role["values"] = []
        self.cmb_pin["values"] = []
        self.cmb_inst.set(""); self.cmb_role.set(""); self.cmb_pin.set("")
        self.ent_label.delete(0, "end")
        # defaults
        if t == "GPIO":
            self.cmb_mode.set("INPUT"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("LOW")
            self.ent_af.delete(0, "end")
            self.cmb_inst.configure(state="disabled"); self.cmb_role.configure(state="disabled")
            self.cmb_pin.configure(state="readonly")
            pins = self.mcu_data.get("gpio_pins", [])
            self.cmb_pin["values"] = pins
            if pins: self.cmb_pin.set(pins[0]); self._on_pin_change()
        else:
            self.cmb_inst.configure(state="readonly"); self.cmb_role.configure(state="readonly"); self.cmb_pin.configure(state="readonly")
            if t == "I2C":
                insts = list(self.mcu_data.get("i2c_interfaces", {}).keys())
            elif t == "UART":
                insts = list(self.mcu_data.get("uart_interfaces", {}).keys())
            elif t == "SPI":
                insts = list(self.mcu_data.get("spi_interfaces", {}).keys())
            elif t == "ADC":
                insts = list(self.mcu_data.get("adc_interfaces", {}).keys())
            else:
                insts = []
            self.cmb_inst["values"] = insts
            if insts: self.cmb_inst.set(insts[0]); self._on_instance_change()

    def _on_instance_change(self, event=None):
        t = self.cmb_type.get(); inst = self.cmb_inst.get()
        if t == "I2C":
            roles = ["scl","sda"]
        elif t == "UART":
            roles = ["tx","rx"]
        elif t == "SPI":
            roles = ["sck","miso","mosi"]
        elif t == "ADC":
            roles = self.mcu_data.get("adc_interfaces", {}).get(inst, [])
        else:
            roles = []
        self.cmb_role["values"] = roles
        self.cmb_role.set(roles[0] if roles else "")
        self._on_role_change()

    def _on_role_change(self, event=None):
        t = self.cmb_type.get(); inst = self.cmb_inst.get(); role = self.cmb_role.get()
        pins = []
        if t == "I2C":
            pins = self.mcu_data.get("i2c_interfaces", {}).get(inst, {}).get(role, [])
            self.cmb_mode.set("AF_OD"); self.cmb_pull.set("PULLUP"); self.cmb_speed.set("VERY_HIGH")
        elif t == "UART":
            pins = self.mcu_data.get("uart_interfaces", {}).get(inst, {}).get(role, [])
            self.cmb_mode.set("AF_PP"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("VERY_HIGH")
        elif t == "SPI":
            pins = self.mcu_data.get("spi_interfaces", {}).get(inst, {}).get(role, [])
            self.cmb_mode.set("AF_PP"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("VERY_HIGH")
        elif t == "ADC":
            p = self.mcu_data.get("adc_pin_mapping", {}).get(inst, {}).get(role, "")
            pins = [p] if p else []
            self.cmb_mode.set("ANALOG"); self.cmb_pull.set("NOPULL"); self.cmb_speed.set("LOW")
        self.cmb_pin["values"] = pins
        if pins: self.cmb_pin.set(pins[0]); self._on_pin_change()
        else: self.cmb_pin.set(""); self.ent_af.delete(0, "end")

    def _on_pin_change(self, event=None):
        t = self.cmb_type.get(); inst = self.cmb_inst.get(); pin = self.cmb_pin.get()
        af_num = 0
        if t == "I2C":
            afs = self.mcu_data.get("i2c_af_mapping", {}).get(inst, {}); af_num = af_str_to_num(afs.get(pin, ""))
        elif t == "UART":
            afs = self.mcu_data.get("uart_af_mapping", {}).get(inst, {}); af_num = af_str_to_num(afs.get(pin, ""))
        elif t == "SPI":
            afs = self.mcu_data.get("spi_af_mapping", {}).get(inst, {}); af_num = af_str_to_num(afs.get(pin, ""))
        elif t == "ADC":
            af_num = 0
        self.ent_af.delete(0, "end"); self.ent_af.insert(0, str(af_num))
        # auto-label se vazio
        if not self.ent_label.get().strip():
            if t == "GPIO":
                self.ent_label.insert(0, pin)
            elif t in ("I2C","UART","SPI"):
                self.ent_label.insert(0, f"{inst}_{self.cmb_role.get().upper()}")
            elif t == "ADC":
                self.ent_label.insert(0, f"{inst}_{self.cmb_role.get()}")

    # -------------- Ações tabela --------------
    def add_row(self):
        t = self.cmb_type.get()
        name = self.ent_label.get().strip() or "SIGNAL"
        pin_label = self.cmb_pin.get().strip()
        if t != "GPIO" and (not self.cmb_inst.get() or not self.cmb_role.get()):
            messagebox.showwarning("Campos", "Selecione Instância e Função."); return
        if not pin_label:
            messagebox.showwarning("Campos", "Escolha um pino."); return

        port, pin_num = split_pin(pin_label)
        try: afn = int(self.ent_af.get() or "0")
        except: afn = 0

        row = {
            "type": t,
            "instance": "" if t=="GPIO" else self.cmb_inst.get(),
            "name": name,
            "port": port,
            "pin": pin_num,
            "mode": self.cmb_mode.get(),
            "pull": self.cmb_pull.get(),
            "speed": self.cmb_speed.get(),
            "alternate_fn": afn
        }
        self.selections.append(row)
        self._refresh_table()
        self.ent_label.delete(0, "end")  # pronto para o próximo

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.selections):
            self.tree.insert("", "end", iid=str(i), values=(
                r["type"], r["instance"], r["name"], r["port"], r["pin"],
                r["mode"], r["pull"], r["speed"], r["alternate_fn"]
            ))

    def del_selected(self):
        cur = self.tree.selection()
        if not cur: return
        idx = int(cur[0]); del self.selections[idx]; self._refresh_table()

    # -------------- Export JSON --------------
    def export_config(self):
        if not self.selections:
            messagebox.showwarning("Nada a exportar", "Adicione pelo menos um sinal."); return
        project_name = self.ent_project.get().strip() or "MyProject"
        micro = self.current_mcu
        grouped = {}
        for r in self.selections: grouped.setdefault(r["type"], []).append(r)

        peripherals = []
        for t, rows in grouped.items():
            if t == "GPIO":
                peripherals.append({
                    "type": t,
                    "pins": [{ "name": x["name"], "port": x["port"], "pin": x["pin"],
                               "mode": x["mode"], "pull": x["pull"], "speed": x["speed"],
                               "alternate_fn": x.get("alternate_fn",0)} for x in rows]
                })
            else:
                by_inst = {}
                for x in rows:
                    key = x["instance"] or f"{t}_X"
                    by_inst.setdefault(key, []).append(x)
                for inst, lst in by_inst.items():
                    peripherals.append({
                        "type": t if t!="UART" else "USART", 
                        "instance": inst,
                        "pins": [{ "name": x["name"], "port": x["port"], "pin": x["pin"],
                                   "mode": x["mode"], "pull": x["pull"], "speed": x["speed"],
                                   "alternate_fn": x.get("alternate_fn",0)} for x in lst]
                    })

        out = {"project_name": project_name, "microcontroller": micro, "peripherals": peripherals}

        path = filedialog.asksaveasfilename(title="Salvar config.json",
                                            defaultextension=".json",
                                            filetypes=[("JSON","*.json"), ("Todos","*.*")])
        if not path: return
        try:
            with open(path, "w", encoding="utf-8") as f: json.dump(out, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("OK", f"config.json salvo em:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # -------------- Botão: Gerar .c/.h --------------
    def generate_files(self):
        """Seleciona um config.json e chama generate_all.generate_project_files(peripherals)."""
        cfg_path = filedialog.askopenfilename(title="Selecionar config.json para gerar .c/.h",
                                              filetypes=[("JSON","*.json"), ("Todos","*.*")])
        if not cfg_path: return
        try:
            gen = importlib.import_module("generate_all")
        except Exception as e:
            messagebox.showerror("generate_all.py não encontrado",
                                 "Coloque seu 'generate_all.py' na mesma pasta do UI.\n\nDetalhes:\n"+str(e))
            return
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            blocks = data["peripherals"] if isinstance(data, dict) and "peripherals" in data else data
            if not hasattr(gen, "generate_project_files"):
                raise RuntimeError("Função 'generate_project_files' não encontrada em generate_all.py")
            out_files = gen.generate_project_files(blocks)
            if out_files:
                messagebox.showinfo("Geração concluída", "Arquivos gerados:\n\n" + "\n".join(out_files))
            else:
                messagebox.showinfo("Geração concluída", "Nenhum arquivo reportado. Veja o console/log.")
        except Exception as e:
            messagebox.showerror("Erro durante a geração", str(e))

if __name__ == "__main__":
    App().mainloop()
