cmake_minimum_required(VERSION 3.22)

#
# This file is generated only once,
# and is not re-generated if converter is called multiple times.
#
# User is free to modify the file as much as necessary
#

# Setup compiler settings
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)


# Define the build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
endif()

# Set the project name
set(CMAKE_PROJECT_NAME cmakestudy)

# Enable compile command to ease indexing with e.g. clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# Core project settings
project(${CMAKE_PROJECT_NAME})
message("Build type: " ${CMAKE_BUILD_TYPE})

# Enable CMake support for ASM and C languages
enable_language(C ASM)

# Create an executable object type
add_executable(${CMAKE_PROJECT_NAME})

# Add STM32CubeMX generated sources
add_subdirectory(cmake/stm32cubemx)

# Link directories setup
target_link_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined library search paths
)

# Add sources to executable
target_sources(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user sources here
)

# Add include paths
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined include paths
)

# Add project symbols (macros)
target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined symbols
)

# Remove wrong libob.a library dependency when using cpp files
list(REMOVE_ITEM CMAKE_C_IMPLICIT_LINK_LIBRARIES ob)

# Add linked libraries
target_link_libraries(${CMAKE_PROJECT_NAME}
    stm32cubemx

    # Add user defined libraries
)

# --- ELF -> HEX/BIN & size (pós-build) ---------------------------------------

# Tenta achar as ferramentas da GNU ARM
find_program(CMAKE_OBJCOPY arm-none-eabi-objcopy)
find_program(CMAKE_SIZE    arm-none-eabi-size)

if(NOT CMAKE_OBJCOPY)
  message(FATAL_ERROR "arm-none-eabi-objcopy não encontrado no PATH. \
Adicione, por exemplo, C:/ST/STM32CubeCLT_1.19.0/GNU-tools-for-STM32/bin ao PATH do terminal.")
endif()

if(NOT CMAKE_SIZE)
  message(WARNING "arm-none-eabi-size não encontrado; o tamanho não será mostrado.")
endif()

# Mostra o tamanho do firmware após o link (se a ferramenta existir)
if(CMAKE_SIZE)
  add_custom_command(TARGET ${CMAKE_PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${CMAKE_PROJECT_NAME}>
    COMMENT "Mostrando tamanho do firmware"
  )
endif()

# Gera .hex e .bin a partir do ELF
add_custom_command(TARGET ${CMAKE_PROJECT_NAME} POST_BUILD
  COMMAND ${CMAKE_OBJCOPY} -O ihex
          $<TARGET_FILE:${CMAKE_PROJECT_NAME}>
          $<TARGET_FILE_DIR:${CMAKE_PROJECT_NAME}>/$<TARGET_FILE_BASE_NAME:${CMAKE_PROJECT_NAME}>.hex
  COMMAND ${CMAKE_OBJCOPY} -O binary
          $<TARGET_FILE:${CMAKE_PROJECT_NAME}>
          $<TARGET_FILE_DIR:${CMAKE_PROJECT_NAME}>/$<TARGET_FILE_BASE_NAME:${CMAKE_PROJECT_NAME}>.bin
  COMMENT "Convertendo ELF -> HEX e BIN"
)

# Alvo prático: compilar e garantir .hex pronto
add_custom_target(hex ALL
  DEPENDS ${CMAKE_PROJECT_NAME}
  COMMENT "Target 'hex' garante .hex/.bin gerados"
)

# --- (Opcional) alvo de flash via STM32CubeProgrammer ------------------------
# Ajuste o caminho do CLI conforme sua instalação do CubeProgrammer:
# Ex.: C:/ST/STM32CubeProgrammer/bin/STM32_Programmer_CLI.exe
set(CUBE_PROG "C:/ST/STM32CubeCLT_1.19.0/STM32CubeProgrammer/bin/STM32_Programmer_CLI.exe")

add_custom_target(flash
  COMMAND "${CUBE_PROG}" -c port=SWD mode=UR reset=HWrst -w
          $<TARGET_FILE_DIR:${CMAKE_PROJECT_NAME}>/$<TARGET_FILE_BASE_NAME:${CMAKE_PROJECT_NAME}>.hex
          -v -rst
  DEPENDS ${CMAKE_PROJECT_NAME}
  COMMENT "Gravando .hex na placa via ST-LINK"
)
