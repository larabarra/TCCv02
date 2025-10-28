from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from datetime import datetime
import data

# --- Paths ---
THIS_FILE = Path(__file__).resolve()
GEN_DIR   = THIS_FILE.parent.parent.parent
PROJ_ROOT = GEN_DIR.parent

TPL_DIR_INC = GEN_DIR / "TEMPLATES" / "inc"
TPL_DIR_SRC = GEN_DIR / "TEMPLATES" / "src"

OUT_INC_PATH = PROJ_ROOT / "Core" / "Inc" / "i2c.h"
OUT_SRC_PATH = PROJ_ROOT / "Core" / "Src" / "i2c.c"

TEMPLATE_C_NAME = "i2c_template.c"
TEMPLATE_H_NAME = "i2c_template.h"

env = Environment(
    loader=FileSystemLoader([str(TPL_DIR_SRC), str(TPL_DIR_INC)]),
    autoescape=False, trim_blocks=True, lstrip_blocks=True,
)


def _render_and_save(template_name: str, context: dict, output_path: Path) -> Path:
    print(f"[JINJA] Looking for '{template_name}' in: {TPL_DIR_SRC} and {TPL_DIR_INC}")
    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise FileNotFoundError(
            f"Template '{template_name}' not found. Ensure it exists in {TPL_DIR_SRC} or {TPL_DIR_INC}"
        ) from e
    rendered_content = template.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_content, encoding="utf-8")
    print(f"[SUCCESS] -> Generated file: {output_path}")
    return output_path

def _as_hal_const(value: str | None, default: str) -> str:
    """Retorna uma string HAL válida, com fallback caso value esteja vazio."""
    v = (value or "").strip()
    return v if v else default

def _to_int(v, default=0) -> int:
    try:
        return int(str(v).replace("_","").split()[0], 0)
    except Exception:
        return default

def _addr7_to_hal(addr_any) -> int:
    a7 = _to_int(addr_any, 0)
    return (a7 << 1) & 0xFF

def generate_i2c_config(a, b=None) -> list[str]:
    # NOVA assinatura: (i2c_settings: dict, gpio_list=None)
    if isinstance(a, dict):
        i2c_settings = a
    else:
        # compat com assinatura antiga: (pinout_list, settings)
        i2c_settings = b or {}

    if not i2c_settings:
        return []

    i2c_interfaces = []
    for instance, inst_set in i2c_settings.items():
        # clock -> timing fixo (HSI16)
        speed_hz  = _to_int(inst_set.get("clockSpeed", 100000), 100000)
        if speed_hz >= 1_000_000:
            timing = "0x00300F33"   # ~1MHz @ HSI16
        elif speed_hz >= 400_000:
            timing = "0x00602173"   # ~400kHz @ HSI16
        else:
            timing = "0x10707DBC"   # ~100kHz @ HSI16

        # campos vindos do settings (mapeados para HAL lá no export)
        addr_mode         = _as_hal_const(inst_set.get("addressingMode"), "I2C_ADDRESSINGMODE_7BIT")
        xfer_mode         = (inst_set.get("transferMode") or "POLLING").upper()

        own_address1      = str(inst_set.get("ownAddress1", "0"))
        dual_address_mode = _as_hal_const(inst_set.get("dualAddressMode"),  "I2C_DUALADDRESS_DISABLE")
        own_address2      = str(inst_set.get("ownAddress2", "0"))
        own_address2_masks= _as_hal_const(inst_set.get("ownAddress2Masks"), "I2C_OA2_NOMASK")
        general_call_mode = _as_hal_const(inst_set.get("generalCallMode"),  "I2C_GENERALCALL_DISABLE")
        no_stretch_mode   = _as_hal_const(inst_set.get("noStretchMode"),    "I2C_NOSTRETCH_DISABLE")

        # devices -> 7-bit << 1
        processed_devices = []
        for dev in inst_set.get("devices", []):
            processed_devices.append({
                "name": dev.get("name", "DEV"),
                "address_hal": _addr7_to_hal(dev.get("address", "0x00")),
            })

        i2c_interfaces.append({
            "num": int(instance.replace("I2C","")),
            "interface": instance,
            "timing_reg": timing,
            "addressing_mode": addr_mode,
            "transferMode": xfer_mode,

            # >>> estes campos agora SEMPRE existem no contexto <<<
            "own_address1":       own_address1,
            "dual_address_mode":  dual_address_mode,
            "own_address2":       own_address2,
            "own_address2_masks": own_address2_masks,
            "general_call_mode":  general_call_mode,
            "no_stretch_mode":    no_stretch_mode,

            "devices": processed_devices,
        })

    if not i2c_interfaces:
        return []

    context = {"i2c_interfaces": i2c_interfaces, "now": datetime.now}
    out_h_path = _render_and_save(TEMPLATE_H_NAME, context, OUT_INC_PATH)
    out_c_path = _render_and_save(TEMPLATE_C_NAME, context, OUT_SRC_PATH)
    return [str(out_c_path), str(out_h_path)]