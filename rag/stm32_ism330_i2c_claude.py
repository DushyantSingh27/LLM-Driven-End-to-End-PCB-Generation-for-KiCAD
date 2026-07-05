from skidl import *

# Define nets
VDD_3V3 = Net("VDD_3V3")
GND = Net("GND")
I2C_SCL = Net("I2C_SCL")
I2C_SDA = Net("I2C_SDA")

# STM32F401RET6
mcu = Part("test", "STM32F401RET6", footprint="test:STM32F401RET6")

# ISM330DHCX
imu = Part("test", "ISM330DHCX", footprint="test:ISM330DHCX")

# Pull-up resistors for I2C
r_scl = Part("test", "R", value="4k7", footprint="test:R_0805")
r_sda = Part("test", "R", value="4k7", footprint="test:R_0805")

# Pull-down/config resistors
r_boot0 = Part("test", "R", value="10k", footprint="test:R_0805")
r_cs = Part("test", "R", value="10k", footprint="test:R_0805")
r_sdo = Part("test", "R", value="10k", footprint="test:R_0805")

# Decoupling caps for MCU VDD pins
c_vdd19 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd32 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd48 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd64 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vbat = Part("test", "C", value="100nF", footprint="test:C_0805")

# VCAP1 capacitor
c_vcap1 = Part("test", "C", value="1uF", footprint="test:C_0805")

# NRST capacitor
c_nrst = Part("test", "C", value="100nF", footprint="test:C_0805")

# ISM330DHCX decoupling caps
c_imu_vdd = Part("test", "C", value="100nF", footprint="test:C_0805")
c_imu_vddio = Part("test", "C", value="100nF", footprint="test:C_0805")
c_imu_c1 = Part("test", "C", value="100nF", footprint="test:C_0805")

# --- MCU Power Connections ---

# VBAT (pin 1)
VDD_3V3 += mcu[1]
VDD_3V3 += c_vbat[1]
GND += c_vbat[2]

# VSSA (pin 12)
GND += mcu[12]

# VREF+ (pin 13)
VDD_3V3 += mcu[13]

# VSS pin 18
GND += mcu[18]

# VDD pin 19 with decoupling cap
VDD_3V3 += mcu[19]
VDD_3V3 += c_vdd19[1]
GND += c_vdd19[2]

# VCAP1 (pin 30) to GND through 1uF cap
mcu[30] += c_vcap1[1]
GND += c_vcap1[2]

# VSS pin 31
GND += mcu[31]

# VDD pin 32 with decoupling cap
VDD_3V3 += mcu[32]
VDD_3V3 += c_vdd32[1]
GND += c_vdd32[2]

# VSS pin 47
GND += mcu[47]

# VDD pin 48 with decoupling cap
VDD_3V3 += mcu[48]
VDD_3V3 += c_vdd48[1]
GND += c_vdd48[2]

# VSS pin 63
GND += mcu[63]

# VDD pin 64 with decoupling cap
VDD_3V3 += mcu[64]
VDD_3V3 += c_vdd64[1]
GND += c_vdd64[2]

# NRST (pin 7) to GND through 100nF cap
mcu[7] += c_nrst[1]
GND += c_nrst[2]

# BOOT0 (pin 60) to GND through 10k resistor
mcu[60] += r_boot0[1]
GND += r_boot0[2]

# --- MCU I2C Connections ---
# PB6 (pin 58) -> I2C_SCL
I2C_SCL += mcu[58]

# PB7 (pin 59) -> I2C_SDA
I2C_SDA += mcu[59]

# --- I2C Pull-up Resistors ---
VDD_3V3 += r_scl[1]
I2C_SCL += r_scl[2]

VDD_3V3 += r_sda[1]
I2C_SDA += r_sda[2]

# --- ISM330DHCX Connections ---

# VDD (pin 1) to VDD_3V3 with decoupling cap
VDD_3V3 += imu[1]
VDD_3V3 += c_imu_vdd[1]
GND += c_imu_vdd[2]

# GND pins (2, 10, 12, 14)
GND += imu[2]
GND += imu[10]
GND += imu[12]
GND += imu[14]

# C1 (pin 3) to GND through 100nF cap
imu[3] += c_imu_c1[1]
GND += c_imu_c1[2]

# SDA (pin 4) to I2C_SDA
I2C_SDA += imu[4]

# SDO_SA0 (pin 5) to GND through 10k resistor
imu[5] += r_sdo[1]
GND += r_sdo[2]

# SCL (pin 6) to I2C_SCL
I2C_SCL += imu[6]

# CS (pin 7) to VDD_3V3 through 10k resistor (I2C mode)
VDD_3V3 += r_cs[1]
imu[7] += r_cs[2]

# INT1 (pin 8) and INT2 (pin 9) unconnected
imu[8] += NC
imu[9] += NC

# VDDIO (pin 11) to VDD_3V3 with decoupling cap
VDD_3V3 += imu[11]
VDD_3V3 += c_imu_vddio[1]
GND += c_imu_vddio[2]

ERC()