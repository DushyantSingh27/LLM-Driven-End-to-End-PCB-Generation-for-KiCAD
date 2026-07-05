from skidl import *

# Define power and ground nets
VDD_3V3 = Net("VDD_3V3")
GND = Net("GND")

# Define the STM32F411CEU6 microcontroller
stm32 = Part("test", "STM32F411CEU6", footprint="test:STM32F411CEU6")

# Define a 10k pull-up resistor for NRST
nrst_pullup = Part("test", "R", value="10k", footprint="test:R_0805")
nrst_pullup[1] += GND
nrst_pullup[2] += stm32["NRST"]

# Define a crystal oscillator
crystal = Part("test", "Crystal", footprint="test:Crystal_SMD_3225")

# Connect the crystal to the STM32F411CEU6
crystal["X1"] += stm32["XTAL1"], stm32["XTAL2"]
crystal["Y1"] += GND, GND

# Define BOOT0 pin as a floating input
boot0 = Part("test", "Pin", footprint="test:Pin_0805")
boot0[1] += stm32["BOOT0"]

# Connect power and ground to the microcontroller
VDD_3V3 += stm32["VDDA"], stm32["VBAT"]
GND += stm32["VSSA"], stm32["VSS"], stm32["NRST"], crystal["Y1"]

ERC()