#ifndef __PRESETS_IN_H__
#define __PRESETS_IN_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"
#include "i2c.h"
#include "adc.h"

/* DHT11 Data structure */
typedef struct {
    HAL_StatusTypeDef status;
    uint8_t hum_int;
    uint8_t hum_dec;
    uint8_t temp_int;
    uint8_t temp_dec;
} DHT11_Data_t;

{% if IN.gy521 %}
/* GY-521 / MPU6050 */
void MPU6050_Init(void);
void MPU6050_Read_Accel(float *ax, float *ay, float *az);
void MPU6050_Read_Gyro(float *gx, float *gy, float *gz);
{% endif %}

{% if IN.din %}
/* Digital input */
uint8_t DIN_Read(GPIO_TypeDef *port, uint16_t pin);
{% endif %}

{% if IN.dht11 %}
/* DHT11 */
DHT11_Data_t DHT11_Read(void);
{% endif %}

{% if IN.ky013 or IN.pot %}
/* ADC helpers para sensores analógicos */
HAL_StatusTypeDef ADC_Read_Channel(ADC_HandleTypeDef *hadc, uint32_t channel, uint16_t *raw);
{% endif %}

#ifdef __cplusplus
}
#endif
#endif /* __PRESETS_IN_H__ */
