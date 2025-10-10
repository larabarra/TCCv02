cmake_minimum_required(VERSION 3.16)

# --- Project Definitions ---
project(TCCv02) # LANGUAGES removed for better toolchain compatibility

# --- Enable Languages and Set Toolchain ---
# This part assumes you are using the -D CMAKE_TOOLCHAIN_FILE flag from the command line
enable_language(C ASM)
set(CMAKE_SYSTEM_NAME Generic)

# --- Source Files (from STM32CubeMX) ---
# More robust than GLOB, as it lists files explicitly.
# All paths are now relative to the project's root directory.
set(APPLICATION_SOURCES
    "${CMAKE_SOURCE_DIR}/Core/Src/main.c"
    "${CMAKE_SOURCE_DIR}/Core/Src/gpio.c"
    "${CMAKE_SOURCE_DIR}/Core/Src/uart.c"
    "${CMAKE_SOURCE_DIR}/Core/Src/i2c.c"
    "${CMAKE_SOURCE_DIR}/Core/Src/stm32g4xx_it.c"
    "${CMAKE_SOURCE_DIR}/Core/Src/stm32g4xx_hal_msp.c"
    "${CMAKE_SOURCE_DIR}/Core/Src/system_stm32g4xx.c"
)

set(HAL_DRIVER_SOURCES
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_rcc.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_rcc_ex.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash_ex.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash_ramfunc.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_gpio.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_exti.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_dma.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_dma_ex.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_pwr.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_pwr_ex.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_cortex.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_uart.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_uart_ex.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_i2c.c"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_i2c_ex.c"
)

# Find the startup file and validate it was found.
file(GLOB STARTUP_FILE "${CMAKE_SOURCE_DIR}/startup_*.s")
if(NOT STARTUP_FILE)
    message(FATAL_ERROR "Startup file (.s) not found in the project root directory. Please check the file location.")
endif()

# --- ARM Compiler Definitions ---
add_compile_options(
    -mcpu=cortex-m4
    -mthumb
    -mfpu=fpv4-sp-d16
    -mfloat-abi=hard
    -g3
    -Wall
    -fmessage-length=0
    -ffunction-sections
    -fdata-sections
)

# --- Linker Definitions ---
file(GLOB LINKER_SCRIPT "${CMAKE_SOURCE_DIR}/*_FLASH.ld")
add_link_options(
    -T${LINKER_SCRIPT}
    -Wl,-Map=${CMAKE_PROJECT_NAME}.map
    -Wl,--gc-sections
    -specs=nosys.specs
)

# --- Include Directories (Headers) ---
include_directories(
    "${CMAKE_SOURCE_DIR}/Core/Inc"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Inc"
    "${CMAKE_SOURCE_DIR}/Drivers/STM32G4xx_HAL_Driver/Inc/Legacy"
    "${CMAKE_SOURCE_DIR}/Drivers/CMSIS/Device/ST/STM32G4xx/Include"
    "${CMAKE_SOURCE_DIR}/Drivers/CMSIS/Include"
)

# --- Macro Definitions ---
add_compile_definitions(
    DEBUG
    USE_HAL_DRIVER
    STM32G474xx
)

# --- Create the Executable (.elf) ---
add_executable(${CMAKE_PROJECT_NAME}.elf
    ${STARTUP_FILE}
    ${APPLICATION_SOURCES}
    ${HAL_DRIVER_SOURCES}
)

# --- Generate Hex and Bin files ---
add_custom_command(TARGET ${CMAKE_PROJECT_NAME}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:${CMAKE_PROJECT_NAME}.elf> ${CMAKE_PROJECT_NAME}.hex
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:${CMAKE_PROJECT_NAME}.elf> ${CMAKE_PROJECT_NAME}.bin
)

