# tab_uart.py
import tkinter as tk
from tkinter import ttk

def create_uart_tab(parent_tab, app):
    """
    Creates and populates the UART/USART tab with configuration frames.
    
    Args:
        parent_tab (ttk.Frame): The parent tab frame to build the UI on.
        app (App): The main application instance to link widgets and callbacks.
    """
    # A dictionary to hold the widgets for each UART instance
    app.uart_widgets = {}

    # Create a configuration frame for UART1 -> UART4
    for i in range(1, 5):
        instance_name = f"UART{i}"
        
        # Main frame for this instance
        frame = ttk.LabelFrame(parent_tab, text=f"{instance_name} Configuration", padding=10)
        frame.pack(fill="x", padx=5, pady=5)
        app.uart_frames[instance_name] = frame

        # Create a dictionary to hold this instance's widgets
        widgets = {}
        
        # --- First Column ---
        # Baud Rate
        ttk.Label(frame, text="Baud Rate:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        combo_baud = ttk.Combobox(frame, state="readonly", values=['9600', '19200', '57600', '115200', '921600'])
        combo_baud.set('115200') # Common default
        combo_baud.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        widgets['baud_rate'] = combo_baud

        # Word Length
        ttk.Label(frame, text="Word Length:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        combo_word = ttk.Combobox(frame, state="readonly", values=['8 Bits', '9 Bits'])
        combo_word.set('8 Bits')
        combo_word.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        widgets['word_length'] = combo_word

        # Stop Bits
        ttk.Label(frame, text="Stop Bits:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        combo_stop = ttk.Combobox(frame, state="readonly", values=['1', '2'])
        combo_stop.set('1')
        combo_stop.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        widgets['stop_bits'] = combo_stop
        
        # --- Second Column ---
        # Parity
        ttk.Label(frame, text="Parity:").grid(row=0, column=2, sticky="w", padx=(20, 5), pady=5)
        combo_parity = ttk.Combobox(frame, state="readonly", values=['None', 'Even', 'Odd'])
        combo_parity.set('None')
        combo_parity.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        widgets['parity'] = combo_parity

        # Hardware Flow Control
        ttk.Label(frame, text="Flow Control:").grid(row=1, column=2, sticky="w", padx=(20, 5), pady=5)
        combo_flow = ttk.Combobox(frame, state="readonly", values=['None', 'RTS/CTS'])
        combo_flow.set('None')
        combo_flow.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        widgets['flow_control'] = combo_flow

        # Make widget columns expandable
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        
        # Store the dictionary of widgets for this instance
        app.uart_widgets[instance_name] = widgets