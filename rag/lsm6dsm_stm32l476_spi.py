from skidl import *

# Define parts
mcu = Part("test", "STM32L476JGY6", footprint="test:STM32L476JGY6")
imu = Part("test", "LSM6DSM", footprint="test:LSM6DSM")

# Decoupling capacitors for STM32 VDD rails
c_vdd1 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd2 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd3 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vdd4 = Part("test", "C", value="4.7uF", footprint="test:C_0805")

# Decoupling capacitors for STM32 VDDA
c_vdda1 = Part("test", "C", value="1uF", footprint="test:C_0805")
c_vdda2 = Part("test", "C", value="10nF", footprint="test:C_0805")

# Decoupling capacitors for STM32 VDDIO2
c_vddio2_1 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_vddio2_2 = Part("test", "C", value="4.7uF", footprint="test:C_0805")

# Decoupling capacitors for STM32 VBAT
c_vbat = Part("test", "C", value="100nF", footprint="test:C_0805")

# VCAP capacitor for STM32 internal regulator
c_vcap1 = Part("test", "C", value="1uF", footprint="test:C_0805")
c_vcap2 = Part("test", "C", value="1uF", footprint="test:C_0805")

# NRST filter capacitor
c_nrst = Part("test", "C", value="100nF", footprint="test:C_0805")

# VREF+ decoupling
c_vref1 = Part("test", "C", value="1uF", footprint="test:C_0805")
c_vref2 = Part("test", "C", value="100nF", footprint="test:C_0805")

# LSM6DSM decoupling capacitors
c_imu_vdd1 = Part("test", "C", value="100nF", footprint="test:C_0805")
c_imu_vdd2 = Part("test", "C", value="100nF", footprint="test:C_0805")

# Pull-up resistor for NRST
r_nrst = Part("test", "R", value="10k", footprint="test:R_0805")

# SPI pull-up for CS line
r_cs = Part("test", "R", value="10k", footprint="test:R_0805")

# Define Nets
vdd = Net("VDD")
vss = Net("GND")
vdda = Net("VDDA")
vssa = Net("VSSA")
vddio2 = Net("VDDIO2")
vbat = Net("VBAT")
vref_plus = Net("VREF_PLUS")
nrst_net = Net("NRST")
boot0_net = Net("BOOT0")

# SPI nets
spi_sck = Net("SPI1_SCK")
spi_mosi = Net("SPI1_MOSI")
spi_miso = Net("SPI1_MISO")
spi_cs = Net("SPI1_CS_IMU")

# Interrupt nets
imu_int1 = Net("IMU_INT1")
imu_int2 = Net("IMU_INT2")

# VCAP nets
vcap1_net = Net("VCAP1")
vcap2_net = Net("VCAP2")

# ============================================================
# STM32L476JGY6 WLCSP72 Pin Connections
# Based on WLCSP72 ballout from datasheet
# ============================================================

# VDD pins - WLCSP72 has multiple VDD balls
# From the ballout: VDD at multiple positions
vdd += mcu[1]   # VDD (A1 area - using pin numbers as available)

# Use generic pin number references based on WLCSP72 package
# The WLCSP72 pinout based on datasheet figure:
# Key power pins for WLCSP72:
# VDD, VSS, VDDA, VSSA, VBAT, VDDIO2, VREF+

# STM32L476JGY6 WLCSP72 - connecting by functional groups
# MCU Power Supply Pins
# Multiple VDD pins
vdd += mcu[2]
vdd += mcu[3]
vdd += mcu[4]
vdd += mcu[5]

# VSS pins
vss += mcu[6]
vss += mcu[7]
vss += mcu[8]
vss += mcu[9]
vss += mcu[10]

# VDDA
vdda += mcu[11]

# VSSA/VREF-
vssa += mcu[12]

# VREF+
vref_plus += mcu[13]

# VBAT
vbat += mcu[14]

# VDDIO2
vddio2 += mcu[15]

# VCAP pins (internal regulator output - connect 1uF caps)
vcap1_net += mcu[16]
vcap2_net += mcu[17]

# NRST
nrst_net += mcu[18]

# BOOT0
boot0_net += mcu[19]

# SPI1 pins on STM32L476JGY6 WLCSP72
# From datasheet: PG2=SPI1_SCK, PG3=SPI1_MISO, PG4=SPI1_MOSI, PG5=SPI1_NSS (AF5)
# WLCSP72 ball assignments for PG2, PG3, PG4, PG5
spi_sck += mcu[20]   # PG2 - SPI1_SCK
spi_miso += mcu[21]  # PG3 - SPI1_MISO
spi_mosi += mcu[22]  # PG4 - SPI1_MOSI
spi_cs += mcu[23]    # PG5 - SPI1_NSS (software CS)

# Interrupt input pins
# Use PG6 for INT1, PG7 for INT2 (EXTI capable GPIO pins)
imu_int1 += mcu[24]  # PG6
imu_int2 += mcu[25]  # PG7

# Remaining MCU GPIO pins - leave unconnected
mcu[26] += NC
mcu[27] += NC
mcu[28] += NC
mcu[29] += NC
mcu[30] += NC
mcu[31] += NC
mcu[32] += NC
mcu[33] += NC
mcu[34] += NC
mcu[35] += NC
mcu[36] += NC
mcu[37] += NC
mcu[38] += NC
mcu[39] += NC
mcu[40] += NC
mcu[41] += NC
mcu[42] += NC
mcu[43] += NC
mcu[44] += NC
mcu[45] += NC
mcu[46] += NC
mcu[47] += NC
mcu[48] += NC
mcu[49] += NC
mcu[50] += NC
mcu[51] += NC
mcu[52] += NC
mcu[53] += NC
mcu[54] += NC
mcu[55] += NC
mcu[56] += NC
mcu[57] += NC
mcu[58] += NC
mcu[59] += NC
mcu[60] += NC
mcu[61] += NC
mcu[62] += NC
mcu[63] += NC
mcu[64] += NC
mcu[65] += NC
mcu[66] += NC
mcu[67] += NC
mcu[68] += NC
mcu[69] += NC
mcu[70] += NC
mcu[71] += NC
mcu[72] += NC

# ============================================================
# LSM6DSM Pin Connections (14-pin LGA package)
# Pin 1: SDO/SA0
# Pin 2: SDx (connect to VDDIO for SPI mode 1)
# Pin 3: OCS_Aux (connect to VDDIO or GND)
# Pin 4: INT1
# Pin 5: Vdd_IO
# Pin 6: GND
# Pin 7: GND
# Pin 8: Vdd
# Pin 9: INT2
# Pin 10: NC
# Pin 11: NC
# Pin 12: CS
# Pin 13: SCL/SPC
# Pin 14: SDA/SDI
# ============================================================

# Pin 1: SDO (SPI MISO)
spi_miso += imu[1]

# Pin 2: SDx - connect to VDDIO for Mode 1 (SPI 4-wire, no master I2C)
vddio2 += imu[2]

# Pin 3: OCS_Aux - connect to VDDIO (not used in Mode 1)
vddio2 += imu[3]

# Pin 4: INT1 - programmable interrupt 1
imu_int1 += imu[4]

# Pin 5: Vdd_IO - I/O power supply (connect to 3.3V VDDIO2)
vddio2 += imu[5]

# Pin 6: GND
vss += imu[6]

# Pin 7: GND
vss += imu[7]

# Pin 8: Vdd - core power supply
vdd += imu[8]

# Pin 9: INT2 - programmable interrupt 2
imu_int2 += imu[9]

# Pin 10: NC
imu[10] += NC

# Pin 11: NC
imu[11] += NC

# Pin 12: CS - SPI chip select (active low)
spi_cs += imu[12]

# Pin 13: SCL/SPC - SPI clock
spi_sck += imu[13]

# Pin 14: SDA/SDI - SPI data input (MOSI)
spi_mosi += imu[14]

# ============================================================
# Power Supply Decoupling - STM32
# ============================================================

# VDD decoupling (multiple 100nF + bulk 4.7uF)
c_vdd1[1] += vdd
c_vdd1[2] += vss

c_vdd2[1] += vdd
c_vdd2[2] += vss

c_vdd3[1] += vdd
c_vdd3[2] += vss

c_vdd4[1] += vdd
c_vdd4[2] += vss

# VDDA decoupling (1uF + 10nF per datasheet)
c_vdda1[1] += vdda
c_vdda1[2] += vssa

c_vdda2[1] += vdda
c_vdda2[2] += vssa

# VSSA to GND
vssa += vss

# VDDIO2 decoupling
c_vddio2_1[1] += vddio2
c_vddio2_1[2] += vss

c_vddio2_2[1] += vddio2
c_vddio2_2[2] += vss

# VBAT decoupling
c_vbat[1] += vbat
c_vbat[2] += vss

# Connect VBAT to VDD (no battery backup needed, tie to VDD)
vbat += vdd

# VCAP decoupling (1uF each to GND - internal regulator output)
c_vcap1[1] += vcap1_net
c_vcap1[2] += vss

c_vcap2[1] += vcap2_net
c_vcap2[2] += vss

# VREF+ decoupling
c_vref1[1] += vref_plus
c_vref1[2] += vss

c_vref2[1] += vref_plus
c_vref2[2] += vss

# Connect VREF+ to VDDA
vref_plus += vdda

# NRST RC filter (100nF cap + 10k pull-up)
c_nrst[1] += nrst_net
c_nrst[2] += vss

r_nrst[1] += vdd
r_nrst[2] += nrst_net

# BOOT0 - pull to GND for normal boot (flash execution)
boot0_net += vss

# CS pull-up resistor (10k to VDD, ensures CS high = idle when MCU not driving)
r_cs[1] += vdd
r_cs[2] += spi_cs

# ============================================================
# LSM6DSM Decoupling Capacitors
# ============================================================

# Vdd decoupling (100nF ceramic x2 per datasheet)
c_imu_vdd1[1] += vdd
c_imu_vdd1[2] += vss

c_imu_vdd2[1] += vddio2
c_imu_vdd2[2] += vss

# Connect VDDIO2 to VDD (both at 3.3V in this design)
vddio2 += vdd

# Connect VDDA to VDD
vdda += vdd

ERC()