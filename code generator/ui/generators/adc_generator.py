# ui/generators/adc_generator.py
from jinja2 import Template
from datetime import datetime
import os

def generate_adc_files(output_dir_inc, output_dir_src, template_dir):
    """
    Generate adc.c and adc.h files for ADC peripheral.
    Always generates basic ADC1 configuration.
    """
    results = []
    
    # Render adc.h
    template_path_h = os.path.join(template_dir, "inc", "adc_template.h")
    if os.path.exists(template_path_h):
        with open(template_path_h, 'r', encoding='utf-8') as f:
            template_h = Template(f.read())
        
        context = {
            "now": datetime.now
        }
        
        rendered_h = template_h.render(context)
        output_path_h = os.path.join(output_dir_inc, "adc.h")
        
        with open(output_path_h, 'w', encoding='utf-8') as f:
            f.write(rendered_h)
        
        results.append(f"Generated: {output_path_h}")
    
    # Render adc.c
    template_path_c = os.path.join(template_dir, "src", "adc_template.c")
    if os.path.exists(template_path_c):
        with open(template_path_c, 'r', encoding='utf-8') as f:
            template_c = Template(f.read())
        
        context = {
            "now": datetime.now
        }
        
        rendered_c = template_c.render(context)
        output_path_c = os.path.join(output_dir_src, "adc.c")
        
        with open(output_path_c, 'w', encoding='utf-8') as f:
            f.write(rendered_c)
        
        results.append(f"Generated: {output_path_c}")
    
    return results

