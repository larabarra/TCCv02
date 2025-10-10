cmake_minimum_required(VERSION 3.22)
project(tcc_g4 LANGUAGES C ASM)


set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)


# Definições do MCU / HAL
add_compile_definitions(STM32G474xx USE_HAL_DRIVER)

# Seu script de link (apenas aqui!)
set(LINKER_SCRIPT "${CMAKE_SOURCE_DIR}/STM32G474XX_FLASH.ld")

# Ferramentas trazidas pelo toolchain file (já estão em cache)
if(NOT ARM_OBJCOPY OR NOT ARM_SIZE)
  message(FATAL_ERROR "ARM_OBJCOPY/ARM_SIZE não encontrados (toolchain?).")
endif()

# Target principal
add_executable(${PROJECT_NAME}.elf
  # === fontes do projeto ===
  Core/Src/main.c
  Core/Src/system_stm32g4xx.c
  Core/Src/stm32g4xx_it.c

  Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal.c
  Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_gpio.c
  Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash.c
  Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash_ex.c
  Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash_ramfunc.c
)

# Includes
target_include_directories(${PROJECT_NAME}.elf PRIVATE
  ${CMAKE_SOURCE_DIR}/Core/Inc
  ${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Inc
  ${CMAKE_SOURCE_DIR}/Drivers/CMSIS/Device/ST/STM32G4xx/Include
  ${CMAKE_SOURCE_DIR}/Drivers/CMSIS/Include
)

# Flags adicionais por alvo (compilação)
target_compile_options(${PROJECT_NAME}.elf PRIVATE
  -ffunction-sections -fdata-sections -Wall -Wextra
)

# Flags de link (driver é o gcc; -T só aqui!)
target_link_options(${PROJECT_NAME}.elf PRIVATE
  -Wl,--gc-sections
  -T${LINKER_SCRIPT}
  -Wl,-Map,$<TARGET_FILE_DIR:${PROJECT_NAME}.elf>/${PROJECT_NAME}.map
)

# Saída organizada
set_target_properties(${PROJECT_NAME}.elf PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/firmware
)

# Artefatos derivados
set(HEX_FILE  $<TARGET_FILE_DIR:${PROJECT_NAME}.elf>/${PROJECT_NAME}.hex)
set(BIN_FILE  $<TARGET_FILE_DIR:${PROJECT_NAME}.elf>/${PROJECT_NAME}.bin)
set(SREC_FILE $<TARGET_FILE_DIR:${PROJECT_NAME}.elf>/${PROJECT_NAME}.srec)

add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
  COMMAND "${ARM_OBJCOPY}" -O ihex   $<TARGET_FILE:${PROJECT_NAME}.elf> "${HEX_FILE}"
  COMMAND "${ARM_OBJCOPY}" -O binary $<TARGET_FILE:${PROJECT_NAME}.elf> "${BIN_FILE}"
  COMMAND "${ARM_OBJCOPY}" -O srec   $<TARGET_FILE:${PROJECT_NAME}.elf> "${SREC_FILE}"
  COMMAND "${ARM_SIZE}" --format=berkeley $<TARGET_FILE:${PROJECT_NAME}.elf>
  COMMENT "Gerando HEX/BIN/SREC e mostrando tamanho"
)
