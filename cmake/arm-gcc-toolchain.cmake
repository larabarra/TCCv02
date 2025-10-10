# cmake/arm-gcc-toolchain.cmake  (MINIMAL)
set(CMAKE_SYSTEM_NAME        Generic)
set(CMAKE_SYSTEM_PROCESSOR   arm)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# Ajuste este prefixo para o seu PC (confira se os .exe existem aí)
set(CLT "C:/ST/STM32CubeCLT_1.19.0/GNU-tools-for-STM32/bin")

# Compiladores (precisam existir!)
set(CMAKE_C_COMPILER   "${CLT}/arm-none-eabi-gcc.exe")
set(CMAKE_ASM_COMPILER "${CLT}/arm-none-eabi-gcc.exe")
# (Opcional) C++
# set(CMAKE_CXX_COMPILER "${CLT}/arm-none-eabi-g++.exe")

# Ferramentas auxiliares (usaremos no CMakeLists)
set(ARM_OBJCOPY "${CLT}/arm-none-eabi-objcopy.exe" CACHE FILEPATH "")
set(ARM_SIZE    "${CLT}/arm-none-eabi-size.exe"    CACHE FILEPATH "")

# Evita .exe
set(CMAKE_EXECUTABLE_SUFFIX_C   ".elf")
set(CMAKE_EXECUTABLE_SUFFIX_ASM ".elf")

# Flags básicas do MCU (ajuste se precisar)
set(TARGET_FLAGS "-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb")
set(CMAKE_C_FLAGS_INIT          "${TARGET_FLAGS} -ffunction-sections -fdata-sections -Wall -Wextra")
set(CMAKE_ASM_FLAGS_INIT        "${TARGET_FLAGS} -x assembler-with-cpp -MMD -MP")
set(CMAKE_EXE_LINKER_FLAGS_INIT "${TARGET_FLAGS} -Wl,--gc-sections --specs=nano.specs -Wl,--print-memory-usage")
