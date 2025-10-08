#include "gpio_config.h"


void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  /* Enable GPIO Clocks */
{% set ports = pins | map(attribute='port') | list %}
{% for p in ports | unique | sort %}
  __HAL_RCC_{{ p }}_CLK_ENABLE();
{% endfor %}

  /* Configure pins */
{% for p in pins %}
  /* {{ p.name }} */
  GPIO_InitStruct.Pin = GPIO_PIN_{{ p.pin }};
  GPIO_InitStruct.Mode = {{ map_mode.get(p.mode, "GPIO_MODE_INPUT") }};
  GPIO_InitStruct.Pull = {{ map_pull.get(p.pull, "GPIO_NOPULL") }};
  GPIO_InitStruct.Speed = {{ map_speed.get(p.speed, "GPIO_SPEED_FREQ_LOW") }};
{% if "AF" in p.mode %}
  GPIO_InitStruct.Alternate = {{ p.alternate_fn|int }};
{% endif %}
  HAL_GPIO_Init({{ p.port }}, &GPIO_InitStruct);

{% endfor %}
}
