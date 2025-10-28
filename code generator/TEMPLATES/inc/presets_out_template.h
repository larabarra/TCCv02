#ifndef __PRESETS_OUT_H__
#define __PRESETS_OUT_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"
#include "i2c.h"
#include "usart.h"
#include "tim.h"

{% if OUT.lcd %}
void LCD_Init(void);
void LCD_Clear(void);
void LCD_SendString(const char *s);
{% endif %}

{% if OUT.uart %}
HAL_StatusTypeDef OUT_UART_Print(const char *s);
{% endif %}

{% if OUT.pwm %}
void PWM_Set(uint16_t duty_0_1000);
{% endif %}

{% if OUT.dout %}
void DOUT_Write(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState s);
{% endif %}

#ifdef __cplusplus
}
#endif
#endif /* __PRESETS_OUT_H__ */
