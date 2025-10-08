# utils.py
import re

def split_pin(pin_label: str):
    """Splits a pin label like 'PA5' into port ('GPIOA') and pin number (5)."""
    m = re.match(r"P([A-F])(\d{1,2})$", pin_label)
    return (f"GPIO{m.group(1)}", int(m.group(2))) if m else ("GPIOA", 0)

def af_str_to_num(af: str) -> int:
    """Extracts the Alternate Function number from a string like 'GPIO_AF7_USART1'."""
    m = re.search(r"AF(\d+)", af or "")
    return int(m.group(1)) if m else 0