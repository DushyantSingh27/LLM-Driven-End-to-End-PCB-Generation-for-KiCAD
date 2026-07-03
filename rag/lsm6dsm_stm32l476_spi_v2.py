from skidl import *
lib_search_paths[KICAD].append("/mnt/c/Program Files/KiCad/9.0/share/kicad/symbols")

# Parts
mcu = Part("MCU_ST_STM32L4", "STM32L476JGYxP", footprint="Package_CSP:STM32L476JGYxP")
imu = Part("Sensor_Motion", "LSM6DSM", footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm")

# Passive components
# MCU Power decoupling
c_vdd1   = Part("Device", "C", value="100nF")
c_vdd2   = Part("Device", "C", value="100nF")
c_vdd3   = Part("Device", "C", value="100nF")
c_vdd_bulk = Part("Device", "C", value="4.7uF")
c_vdd12_1 = Part("Device", "C", value="1uF")
c_vdd12_2 = Part("Device", "C", value="100nF")
c_vdda1  = Part("Device", "C", value="1uF")
c_vdda2  = Part("Device", "C", value="10nF")
c_vddio2_1 = Part("Device", "C", value="100nF")
c_vddio2_2 = Part("Device", "C", value="1uF")
c_vddusb = Part("Device", "C", value="1uF")
c_vbat   = Part("Device", "C", value="100nF")
c_vref   = Part("Device", "C", value="1uF")
c_vref2  = Part("Device", "C", value="10nF")
# NRST filter cap
c_nrst   = Part("Device", "C", value="100nF")

# Sensor decoupling
c_imu_vdd1  = Part("Device", "C", value="100nF")
c_imu_vdd2  = Part("Device", "C", value="10uF")
c_imu_vddio1 = Part("Device", "C", value="100nF")
c_imu_vddio2 = Part("Device", "C", value="10uF")

# SPI pull-up resistors (optional, CS pull-up)
r_cs = Part("Device", "R", value="10k")

# BOOT0 pull-down resistor (boot from flash)
r_boot0 = Part("Device", "R", value="10k")

# INT pull-up resistors
r_int1 = Part("Device", "R", value="10k")
r_int2 = Part("Device", "R", value="10k")

# ── Nets ──────────────────────────────────────────────────────────────────────
vdd      = Net("VDD_3V3")
vdd12    = Net("VDD12")
vdda     = Net("VDDA")
vddio2   = Net("VDDIO2")
vddusb   = Net("VDDUSB")
vbat     = Net("VBAT")
vref_p   = Net("VREF_PLUS")
gnd      = Net("GND")

# SPI1 on STM32L476JGYxP:
#   SCK  -> PB3  (ball A6)  AF5=SPI1
#   MISO -> PB4  (ball C5)  AF5=SPI1
#   MOSI -> PB5  (ball E7)  AF5=SPI1
#   CS   -> PA15 (ball C3)  AF5=SPI1_NSS  (used as GPIO CS)
spi_sck  = Net("SPI_SCK")
spi_miso = Net("SPI_MISO")
spi_mosi = Net("SPI_MOSI")
spi_cs   = Net("SPI_CS")

# INT lines
int1_net = Net("IMU_INT1")
int2_net = Net("IMU_INT2")

# NRST
nrst_net = Net("NRST")

# BOOT0 (GND = boot from flash)
boot0_net = Net("BOOT0")

# ── MCU Power rails ────────────────────────────────────────────────────────────
# VDD pins: A9, F1, H8
vdd += mcu["A9"], mcu["F1"], mcu["H8"]
# VSS pins: A8, B1, J2, J9
gnd += mcu["A8"], mcu["B1"], mcu["J2"], mcu["J9"]
# VDD12 pins: B8, J1
vdd12 += mcu["B8"], mcu["J1"]
# VDDA
vdda += mcu["H9"]
# VSSA
gnd += mcu["G9"]
# VDDIO2
vddio2 += mcu["B6"]
# VDDUSB
vddusb += mcu["A1"]
# VBAT
vbat += mcu["B9"]
# VREF+
vref_p += mcu["G8"]

# ── MCU Power Decoupling ───────────────────────────────────────────────────────
# VDD
c_vdd1[1] += vdd
c_vdd1[2] += gnd
c_vdd2[1] += vdd
c_vdd2[2] += gnd
c_vdd3[1] += vdd
c_vdd3[2] += gnd
c_vdd_bulk[1] += vdd
c_vdd_bulk[2] += gnd

# VDD12 (internal SMPS output – 1 µF + 100 nF)
c_vdd12_1[1] += vdd12
c_vdd12_1[2] += gnd
c_vdd12_2[1] += vdd12
c_vdd12_2[2] += gnd

# VDDA
c_vdda1[1] += vdda
c_vdda1[2] += gnd
c_vdda2[1] += vdda
c_vdda2[2] += gnd

# VDDIO2
c_vddio2_1[1] += vddio2
c_vddio2_1[2] += gnd
c_vddio2_2[1] += vddio2
c_vddio2_2[2] += gnd

# VDDUSB
c_vddusb[1] += vddusb
c_vddusb[2] += gnd

# VBAT
c_vbat[1] += vbat
c_vbat[2] += gnd

# VREF+
c_vref[1]  += vref_p
c_vref[2]  += gnd
c_vref2[1] += vref_p
c_vref2[2] += gnd

# ── NRST ──────────────────────────────────────────────────────────────────────
nrst_net += mcu["E9"]
c_nrst[1] += nrst_net
c_nrst[2] += gnd

# ── BOOT0 (pull-down → boot from flash) ───────────────────────────────────────
boot0_net += mcu["A7"]
r_boot0[1] += boot0_net
r_boot0[2] += gnd

# ── SPI connections (MCU side) ─────────────────────────────────────────────────
spi_sck  += mcu["A6"]   # PB3
spi_miso += mcu["C5"]   # PB4
spi_mosi += mcu["E7"]   # PB5
spi_cs   += mcu["C3"]   # PA15

# CS pull-up to VDD
r_cs[1] += vdd
r_cs[2] += spi_cs

# ── INT lines (MCU side) ───────────────────────────────────────────────────────
# Use PB6 (E8) for INT1, PB7 (B7) for INT2
int1_net += mcu["E8"]   # PB6
int2_net += mcu["B7"]   # PB7

# INT pull-ups to VDD
r_int1[1] += vdd
r_int1[2] += int1_net
r_int2[1] += vdd
r_int2[2] += int2_net

# ── IMU Power ─────────────────────────────────────────────────────────────────
imu_vdd   = Net("IMU_VDD")
imu_vddio = Net("IMU_VDDIO")

imu_vdd   += imu["8"]
imu_vddio += imu["5"]

# Connect IMU power to VDD rail
imu_vdd   += vdd
imu_vddio += vdd

# IMU GND
gnd += imu["6"], imu["7"]

# IMU VDD decoupling
c_imu_vdd1[1]  += imu_vdd
c_imu_vdd1[2]  += gnd
c_imu_vdd2[1]  += imu_vdd
c_imu_vdd2[2]  += gnd

# IMU VDDIO decoupling
c_imu_vddio1[1] += imu_vddio
c_imu_vddio1[2] += gnd
c_imu_vddio2[1] += imu_vddio
c_imu_vddio2[2] += gnd

# ── IMU SPI connections ────────────────────────────────────────────────────────
# SPI 4-wire mode: CS low selects SPI
# imu pin 12 = CS (active low)
# imu pin 13 = SCL (clock)
# imu pin 14 = SDA (MOSI)
# imu pin 1  = SDO/SA0 (MISO)
spi_cs   += imu["12"]
spi_sck  += imu["13"]
spi_mosi += imu["14"]
spi_miso += imu["1"]

# ── IMU Interrupt outputs ──────────────────────────────────────────────────────
int1_net += imu["4"]
int2_net += imu["9"]

# ── IMU auxiliary SPI pins (not used in SPI Mode 1 – tie per datasheet) ────────
# SDX (pin 2): connect to VDDIO or GND in Mode 1 (SPI only, no aux)
imu["2"] += gnd
# SCX (pin 3): leave as NC (auxiliary SPI clock – not used)
imu["3"] += NC
# OCS_Aux (pin 10): leave NC
imu["10"] += NC
# SDO_Aux (pin 11): leave NC
imu["11"] += NC

ERC()