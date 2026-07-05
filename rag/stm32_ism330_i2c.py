from skidl import *

# Nets
VDD_3V3 = Net("VDD_3V3")
GND = Net("GND")
I2C_SCL = Net("I2C_SCL")
I2C_SDA = Net("I2C_SDA")
NRST_NET = Net("NRST_NET")
BOOT0_NET = Net("BOOT0_NET")

# ── STM32F401RET6 ──────────────────────────────────────────────
stm32 = Part("test", "STM32F401RET6", footprint="test:STM32F401RET6")

# Power pins
stm32[1]  += VDD_3V3   # VBAT
stm32[12] += GND       # VSSA
stm32[13] += VDD_3V3   # VREF+
stm32[18] += GND       # VSS
stm32[19] += VDD_3V3   # VDD
stm32[31] += GND       # VSS_2
stm32[32] += VDD_3V3   # VDD_2
stm32[47] += GND       # VSS_3
stm32[48] += VDD_3V3   # VDD_3
stm32[63] += GND       # VSS_4
stm32[64] += VDD_3V3   # VDD_4

# NRST - 100nF to GND
stm32[7] += NRST_NET
C_nrst = Part("test", "C", value="100nF", footprint="test:C_0805")
C_nrst[1] += NRST_NET
C_nrst[2] += GND

# VCAP1 - 1uF to GND (internal regulator bypass)
C_vcap = Part("test", "C", value="1uF", footprint="test:C_0805")
C_vcap[1] += stm32[30]  # VCAP1
C_vcap[2] += GND

# BOOT0 - 10k pull-down to GND (flash boot)
stm32[60] += BOOT0_NET
R_boot = Part("test", "R", value="10k", footprint="test:R_0805")
R_boot[1] += BOOT0_NET
R_boot[2] += GND

# VDD decoupling caps - one per VDD pin
C_vdd1 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vdd1[1] += VDD_3V3
C_vdd1[2] += GND

C_vdd2 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vdd2[1] += VDD_3V3
C_vdd2[2] += GND

C_vdd3 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vdd3[1] += VDD_3V3
C_vdd3[2] += GND

C_vdd4 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vdd4[1] += VDD_3V3
C_vdd4[2] += GND

C_vbat = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vbat[1] += VDD_3V3
C_vbat[2] += GND

# I2C1 pins - PB6=SCL(58), PB7=SDA(59)
stm32[58] += I2C_SCL   # PB6 I2C1_SCL
stm32[59] += I2C_SDA   # PB7 I2C1_SDA

# ── ISM330DHCX ─────────────────────────────────────────────────
sensor = Part("test", "ISM330DHCX", footprint="test:ISM330DHCX")

# Power pins
sensor[1]  += VDD_3V3   # VDD
sensor[2]  += GND       # GND
sensor[10] += GND       # GND_2
sensor[11] += VDD_3V3   # VDDIO
sensor[12] += GND       # GND_3
sensor[14] += GND       # GND_PAD

# C1 bypass cap - 100nF to GND (internal regulator)
C_c1 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_c1[1] += sensor[3]   # C1 pin
C_c1[2] += GND

# VDD decoupling
C_vdd_s1 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vdd_s1[1] += VDD_3V3
C_vdd_s1[2] += GND

# VDDIO decoupling
C_vdd_s2 = Part("test", "C", value="100nF", footprint="test:C_0805")
C_vdd_s2[1] += VDD_3V3
C_vdd_s2[2] += GND

# CS - pull HIGH to VDD_3V3 via 10k (selects I2C mode)
CS_NET = Net("CS_NET")
sensor[7] += CS_NET
R_cs = Part("test", "R", value="10k", footprint="test:R_0805")
R_cs[1] += VDD_3V3
R_cs[2] += CS_NET

# SDO/SA0 - pull LOW to GND via 10k (I2C address 0x6A)
SA0_NET = Net("SA0_NET")
sensor[5] += SA0_NET
R_sa0 = Part("test", "R", value="10k", footprint="test:R_0805")
R_sa0[1] += SA0_NET
R_sa0[2] += GND

# I2C bus connections
sensor[6] += I2C_SCL   # SCL
sensor[4] += I2C_SDA   # SDA

# INT1 and INT2 - unconnected
sensor[8] += NC        # INT1
sensor[9] += NC        # INT2

# OCS_Aux - unconnected
sensor[13] += NC

# ── I2C pull-up resistors ──────────────────────────────────────
R_scl = Part("test", "R", value="4k7", footprint="test:R_0805")
R_scl[1] += VDD_3V3
R_scl[2] += I2C_SCL

R_sda = Part("test", "R", value="4k7", footprint="test:R_0805")
R_sda[1] += VDD_3V3
R_sda[2] += I2C_SDA

ERC()
