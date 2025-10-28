# generators/presets_generator.py
from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import re

THIS_FILE = Path(__file__).resolve()
GEN_DIR   = THIS_FILE.parent.parent.parent
PROJ_ROOT = GEN_DIR.parent

TPL_DIR_INC = GEN_DIR / "TEMPLATES" / "inc"
TPL_DIR_SRC = GEN_DIR / "TEMPLATES" / "src"

OUT_PRESETS_IN_H  = PROJ_ROOT / "Core" / "Inc" / "presets_in.h"
OUT_PRESETS_IN_C  = PROJ_ROOT / "Core" / "Src" / "presets_in.c"
OUT_PRESETS_OUT_H = PROJ_ROOT / "Core" / "Inc" / "presets_out.h"
OUT_PRESETS_OUT_C = PROJ_ROOT / "Core" / "Src" / "presets_out.c"

env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False, trim_blocks=True, lstrip_blocks=True,
)

def _digits(name: str) -> str:
    """Extract digits from a string."""
    m = re.search(r"(\d+)", name or "")
    return m.group(1) if m else ""

def _handle_from_instance(kind: str, instance: str) -> str:
    """Generate HAL handle name from peripheral instance.
    Args:
        kind: One of {"i2c", "uart", "tim"}
        instance: Like "I2C1", "UART2", etc.
    Returns:
        Like "hi2c1", "huart2", "htim2" or empty string
    """
    n = _digits(instance)
    prefix = {"i2c": "hi2c", "uart": "huart", "tim": "htim"}[kind]
    return f"{prefix}{n}" if n else ""

def _render(name: str, ctx: dict, outpath: Path):
    """Render template to file."""
    try:
        tpl = env.get_template(name)
    except TemplateNotFound as e:
        raise FileNotFoundError(f"Template {name} não encontrado em {TPL_DIR_SRC} ou {TPL_DIR_INC}") from e
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(tpl.render(**ctx), encoding="utf-8")
    return str(outpath)

def _get_device_list(devices: list[dict] | None, name_contains: str) -> list[dict]:
    """Find all devices whose name contains name_contains.
    Returns list of dicts with {name, address, handle, addr_macro, num}.
    """
    result = []
    for d in devices or []:
        nm = (str(d.get("name") or "")).upper()
        if name_contains.upper() in nm:
            addr_int = d.get("address")
            # Get handle from I2C instance
            handle = ""  # Will be populated by caller
            num = _digits(nm)
            addr_macro = f"0x{addr_int:02X}" if addr_int is not None else ""
            result.append({
                "name": nm,
                "address": addr_int,
                "handle": handle,
                "addr_macro": addr_macro,
                "num": num
            })
    return result

def _get_lcd_addr_hal(devices: list[dict] | None) -> str | None:
    """Get LCD PCF8574 address in HAL format (8-bit, left-shifted)."""
    for d in devices or []:
        nm = str(d.get("name") or "").upper()
        if "LCD" in nm or "PCF8574" in nm:
            addr7 = d.get("address")
            if addr7 is not None:
                addr8 = int(addr7) << 1
                return f"0x{addr8:02X}"
    return None

def _pick_first_key(d: dict, prefix: str) -> str | None:
    """Get first key in dict that starts with prefix."""
    for k in d.keys():
        if isinstance(k, str) and k.startswith(prefix):
            return k
    return None

def generate_presets_files(
    preset_settings: dict,
    peripheral_settings: dict,
    pinout_config: dict,
) -> list[str]:
    """
    Generate presets_in/out .c/.h files.
    Args:
        preset_settings: Configuration from preset_settings.json
        peripheral_settings: Configuration from peripheral_settings.json
        pinout_config: Configuration from pinout_config.json
    """
    out_files = []

    # --- Discover active peripheral instances ---
    i2c_inst = None
    uart_inst = None
    tim_inst = None

    i2c_dict = (peripheral_settings or {}).get("I2C", {}) or {}
    uart_dict = (peripheral_settings or {}).get("UART", {}) or {}
    usart_dict = (peripheral_settings or {}).get("USART", {}) or {}
    tim_dict = (peripheral_settings or {}).get("TIM", {}) or {}

    if i2c_dict:
        i2c_inst = _pick_first_key(i2c_dict, "I2C")
    if uart_dict:
        uart_inst = _pick_first_key(uart_dict, "UART")
    if not uart_inst and usart_dict:
        uart_inst = _pick_first_key(usart_dict, "USART")
    if tim_dict:
        tim_inst = _pick_first_key(tim_dict, "TIM")

    # --- Build HAL handles ---
    i2c_handle = _handle_from_instance("i2c", i2c_inst or "")
    uart_handle = _handle_from_instance("uart", uart_inst or "")
    tim_handle = _handle_from_instance("tim", tim_inst or "")

    # --- Extract inputs/outputs from preset_settings ---
    cases = (preset_settings or {}).get("cases", []) or []
    
    # Check if inputs/outputs are enabled in any case
    has_gy521 = False
    has_din = False
    has_dht11 = False
    has_ky013 = False
    has_pot = False
    
    has_lcd = False
    has_uart = False
    has_pwm = False
    has_dout = False
    
    # Collect GY521 devices
    gy521_devices = []
    lcd_addr_hal = None
    
    for case in cases:
        input_key = case.get("input_key", "")
        output_key = case.get("output_key", "")
        
        # Check inputs
        if "GY-521" in input_key or "MPU6050" in input_key:
            has_gy521 = True
        if "Digital Input" in input_key or "DIN" in input_key:
            has_din = True
        if "DHT11" in input_key:
            has_dht11 = True
        if "KY-013" in input_key or "KY013" in input_key:
            has_ky013 = True
        if "Potentiometer" in input_key or "POT" in input_key:
            has_pot = True
            
        # Check outputs
        if "LCD" in output_key:
            has_lcd = True
        if "UART" in output_key:
            has_uart = True
        if "PWM" in output_key:
            has_pwm = True
        if "LED" in output_key or "Digital Output" in output_key:
            has_dout = True
        
        # Extract device information from peripheral_settings in this case
        ps = case.get("peripheral_settings", {})
        input_periph = ps.get("input_peripheral", {})
        output_periph = ps.get("output_peripheral", {})
        
        # Check input peripheral for devices
        if input_periph.get("type") == "I2C":
            inst = input_periph.get("instance", "")
            if i2c_dict.get(inst):
                devices = i2c_dict[inst].get("devices", [])
                gy521_list = _get_device_list(devices, "GY521")
                gy521_list = _get_device_list(devices, "MPU6050")
                for dev in gy521_list:
                    dev["handle"] = i2c_handle
                gy521_devices.extend(gy521_list)
                
        # Check output peripheral for LCD
        if output_periph.get("type") == "I2C":
            inst = output_periph.get("instance", "")
            if i2c_dict.get(inst):
                devices = i2c_dict[inst].get("devices", [])
                if not lcd_addr_hal:
                    lcd_addr_hal = _get_lcd_addr_hal(devices)
    
    # If no cases, fall back to old structure
    if not cases:
        inputs = (preset_settings or {}).get("inputs", {}) or {}
        outputs = (preset_settings or {}).get("outputs", {}) or {}
        
        has_gy521 = bool(inputs.get("GY-521 Sensor"))
        has_din = bool(inputs.get("Digital Input"))
        has_dht11 = bool(inputs.get("DHT11 Humidity & Temp Sensor"))
        has_ky013 = bool(inputs.get("KY-013 Analog Temp Sensor"))
        has_pot = bool(inputs.get("Potentiometer (ADC)"))
        
        has_lcd = bool(outputs.get("LCD 20x4 (I2C)"))
        has_uart = bool(outputs.get("UART"))
        has_pwm = bool(outputs.get("PWM"))
        has_dout = bool(outputs.get("Digital Output (LED)"))
    
    # --- Build pin information from pinout_config ---
    gpio_config = (pinout_config or {}).get("gpio", []) or []
    din_pin = None
    dht_pin = None
    
    for pin_cfg in gpio_config:
        name = (pin_cfg.get("name") or "").upper()
        
        # Digital Input
        if "DIN" in name or ("DIGITAL" in name and "INPUT" in name):
            din_pin = {
                "name": pin_cfg.get("name", ""),
                "port": pin_cfg.get("port", ""),
                "pin": pin_cfg.get("pin", "")
            }
            
        # DHT11
        if "DHT11" in name or "DHT" in name:
            dht_pin = {
                "name": pin_cfg.get("name", ""),
                "port": pin_cfg.get("port", ""),
                "pin": pin_cfg.get("pin", "")
            }

    # --- Build context for input templates ---
    ctx_in = {
        "i2c_handle": i2c_handle,
        "uart_handle": uart_handle,
        "tim_handle": tim_handle,
        "lcd_addr": lcd_addr_hal,
        "IN": {
            "gy521": has_gy521,
            "din": has_din,
            "dht11": has_dht11,
            "ky013": has_ky013,
            "pot": has_pot,
        },
        # For .c template
        "include_gy521": has_gy521,
        "gy521_list": gy521_devices,
        "include_din": has_din,
        "din_pin": din_pin,
        "include_dht11": has_dht11,
        "dht_pin": dht_pin,
        "include_ky013": has_ky013,
        "include_pot": has_pot,
    }
    
    # --- Build context for output templates ---
    ctx_out = {
        "i2c_handle": i2c_handle,
        "uart_handle": uart_handle,
        "tim_handle": tim_handle,
        "lcd_addr": lcd_addr_hal,
        "OUT": {
            "lcd": has_lcd,
            "uart": has_uart,
            "pwm": has_pwm,
            "dout": has_dout,
        }
    }
    
    # --- Render templates ---
    out_files.append(_render("presets_in_template.h", ctx_in, OUT_PRESETS_IN_H))
    out_files.append(_render("presets_in_template.c", ctx_in, OUT_PRESETS_IN_C))
    out_files.append(_render("presets_out_template.h", ctx_out, OUT_PRESETS_OUT_H))
    out_files.append(_render("presets_out_template.c", ctx_out, OUT_PRESETS_OUT_C))
    
    print(f"[SUCCESS] Generated presets files: {out_files}")
    return out_files
