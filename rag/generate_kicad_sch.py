
import sys
import os
sys.path.insert(0, '/teamspace/studios/this_studio/PCBSchemaGen/rag')
from kicad_sch_writer import KicadSchematic, gen_uuid

def generate_stm32_ism330_schematic():
    sch = KicadSchematic(
        title="STM32F401RET6 + ISM330DHCX I2C Circuit",
        company="SRM IST - Semiconductor Chip Design Club"
    )

    # ── Layout constants (all in mm) ──────────────────────────
    # STM32 placed at centre-left, ISM330 at centre-right
    STM_X, STM_Y = 80, 120
    ISM_X, ISM_Y = 220, 100

    # ── Add STM32F401RET6 lib symbol ──────────────────────────
    stm32_lib = '''    (symbol "MCU:STM32F401RET6" (in_bom yes) (on_board yes)
      (property "Reference" "U1" (at 0 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "STM32F401RET6" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_QFP:LQFP-64_10x10mm_P0.5mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.st.com/resource/en/datasheet/stm32f401re.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "STM32F401RET6_0_1"
        (rectangle (start -15.24 -43.18) (end 15.24 43.18) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "STM32F401RET6_1_1"
        (pin power_in line (at -2.54 45.72 270) (length 2.54) (name "VBAT" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -45.72 90) (length 2.54) (name "VSSA" (effects (font (size 1.27 1.27)))) (number "12" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 30.48 0) (length 2.54) (name "VREF+" (effects (font (size 1.27 1.27)))) (number "13" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -45.72 90) (length 2.54) (name "VSS" (effects (font (size 1.27 1.27)))) (number "18" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 45.72 270) (length 2.54) (name "VDD" (effects (font (size 1.27 1.27)))) (number "19" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 40.64 0) (length 2.54) (name "NRST" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -45.72 90) (length 2.54) (name "VSS_2" (effects (font (size 1.27 1.27)))) (number "31" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 2.54 45.72 270) (length 2.54) (name "VDD_2" (effects (font (size 1.27 1.27)))) (number "32" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -45.72 90) (length 2.54) (name "VSS_3" (effects (font (size 1.27 1.27)))) (number "47" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 5.08 45.72 270) (length 2.54) (name "VDD_3" (effects (font (size 1.27 1.27)))) (number "48" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 0 -45.72 90) (length 2.54) (name "VSS_4" (effects (font (size 1.27 1.27)))) (number "63" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 7.62 45.72 270) (length 2.54) (name "VDD_4" (effects (font (size 1.27 1.27)))) (number "64" (effects (font (size 1.27 1.27)))))
        (pin power_out line (at -17.78 -30.48 0) (length 2.54) (name "VCAP1" (effects (font (size 1.27 1.27)))) (number "30" (effects (font (size 1.27 1.27)))))
        (pin input line (at -17.78 35.56 0) (length 2.54) (name "BOOT0" (effects (font (size 1.27 1.27)))) (number "60" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -17.78 180) (length 2.54) (name "PB6/I2C1_SCL" (effects (font (size 1.27 1.27)))) (number "58" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at 17.78 -20.32 180) (length 2.54) (name "PB7/I2C1_SDA" (effects (font (size 1.27 1.27)))) (number "59" (effects (font (size 1.27 1.27)))))
      )
    )'''
    sch.lib_symbols["MCU:STM32F401RET6"] = stm32_lib

    # ── Add ISM330DHCX lib symbol ─────────────────────────────
    ism330_lib = '''    (symbol "Sensor:ISM330DHCX" (in_bom yes) (on_board yes)
      (property "Reference" "U2" (at 0 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "ISM330DHCX" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "Package_LGA:LGA-14_3x2.5mm_P0.5mm" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "https://www.st.com/resource/en/datasheet/ism330dhcx.pdf" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "ISM330DHCX_0_1"
        (rectangle (start -10.16 7.62) (end 10.16 -22.86) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "ISM330DHCX_1_1"
        (pin power_in line (at -15.24 5.08 0) (length 5.08) (name "VDD" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at -15.24 2.54 0) (length 5.08) (name "GND" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
        (pin passive line (at -15.24 0 0) (length 5.08) (name "C1" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
        (pin bidirectional line (at -15.24 -2.54 0) (length 5.08) (name "SDA" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 -5.08 0) (length 5.08) (name "SDO_SA0" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 -7.62 0) (length 5.08) (name "SCL" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
        (pin input line (at -15.24 -10.16 0) (length 5.08) (name "CS" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
        (pin output line (at 15.24 5.08 180) (length 5.08) (name "INT1" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
        (pin output line (at 15.24 2.54 180) (length 5.08) (name "INT2" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 15.24 0 180) (length 5.08) (name "GND_2" (effects (font (size 1.27 1.27)))) (number "10" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 15.24 -2.54 180) (length 5.08) (name "VDDIO" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 15.24 -5.08 180) (length 5.08) (name "GND_3" (effects (font (size 1.27 1.27)))) (number "12" (effects (font (size 1.27 1.27)))))
        (pin output line (at 15.24 -7.62 180) (length 5.08) (name "OCS_Aux" (effects (font (size 1.27 1.27)))) (number "13" (effects (font (size 1.27 1.27)))))
        (pin power_in line (at 15.24 -10.16 180) (length 5.08) (name "GND_PAD" (effects (font (size 1.27 1.27)))) (number "14" (effects (font (size 1.27 1.27)))))
      )
    )'''
    sch.lib_symbols["Sensor:ISM330DHCX"] = ism330_lib

    # ── Place ICs ─────────────────────────────────────────────
    sch.add_symbol_instance("MCU:STM32F401RET6", "U1", "STM32F401RET6",
        STM_X, STM_Y, footprint="Package_QFP:LQFP-64_10x10mm_P0.5mm",
        datasheet="https://www.st.com/resource/en/datasheet/stm32f401re.pdf")

    sch.add_symbol_instance("Sensor:ISM330DHCX", "U2", "ISM330DHCX",
        ISM_X, ISM_Y, footprint="Package_LGA:LGA-14_3x2.5mm_P0.5mm",
        datasheet="https://www.st.com/resource/en/datasheet/ism330dhcx.pdf")

    # ── VDD_3V3 power symbols (top of VDD pins) ───────────────
    # STM32 VDD pins come out top
    for vx in [STM_X-2.54, STM_X, STM_X+5.08, STM_X+7.62, STM_X-2.54]:
        sch.add_power_symbol("VDD_3V3", STM_X + vx - STM_X, STM_Y - 48.26)

    # ISM330 VDD and VDDIO
    sch.add_power_symbol("VDD_3V3", ISM_X - 15.24, ISM_Y + 5.08)
    sch.add_power_symbol("VDD_3V3", ISM_X + 15.24, ISM_Y - 2.54)

    # ── GND symbols ───────────────────────────────────────────
    # STM32 VSS pins come out bottom
    sch.add_power_symbol("GND", STM_X, STM_Y + 48.26, rotation=0)
    # ISM330 GND pins
    sch.add_power_symbol("GND", ISM_X - 15.24, ISM_Y + 2.54)
    sch.add_power_symbol("GND", ISM_X + 15.24, ISM_Y)
    sch.add_power_symbol("GND", ISM_X + 15.24, ISM_Y - 5.08)
    sch.add_power_symbol("GND", ISM_X + 15.24, ISM_Y - 10.16)

    # ── I2C bus wires ─────────────────────────────────────────
    # SCL: STM32 PB6 (pin 58) right side → ISM330 SCL (pin 6) left side
    scl_y = STM_Y - 17.78
    sch.add_wire(STM_X + 17.78, scl_y, STM_X + 30, scl_y)
    sch.add_wire(STM_X + 30, scl_y, STM_X + 30, ISM_Y - 7.62)
    sch.add_wire(STM_X + 30, ISM_Y - 7.62, ISM_X - 15.24, ISM_Y - 7.62)
    sch.add_net_label("I2C_SCL", STM_X + 20, scl_y)

    # SDA: STM32 PB7 (pin 59) right side → ISM330 SDA (pin 4) left side
    sda_y = STM_Y - 20.32
    sch.add_wire(STM_X + 17.78, sda_y, STM_X + 35, sda_y)
    sch.add_wire(STM_X + 35, sda_y, STM_X + 35, ISM_Y - 2.54)
    sch.add_wire(STM_X + 35, ISM_Y - 2.54, ISM_X - 15.24, ISM_Y - 2.54)
    sch.add_net_label("I2C_SDA", STM_X + 20, sda_y)

    # ── Pull-up resistors on I2C bus ──────────────────────────
    # R_SCL: 4.7k from VDD_3V3 to I2C_SCL
    r_scl_x = STM_X + 55
    r_scl_y = ISM_Y - 7.62
    sch.add_symbol_instance("Device:R", "R_SCL", "4k7",
        r_scl_x, r_scl_y - 5, rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric")
    sch.add_power_symbol("VDD_3V3", r_scl_x, r_scl_y - 10)
    sch.add_wire(r_scl_x, r_scl_y - 1.27, r_scl_x, r_scl_y)
    sch.add_junction(r_scl_x, r_scl_y)

    # R_SDA: 4.7k from VDD_3V3 to I2C_SDA
    r_sda_x = STM_X + 62
    r_sda_y = ISM_Y - 2.54
    sch.add_symbol_instance("Device:R", "R_SDA", "4k7",
        r_sda_x, r_sda_y - 5, rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric")
    sch.add_power_symbol("VDD_3V3", r_sda_x, r_sda_y - 10)
    sch.add_wire(r_sda_x, r_sda_y - 1.27, r_sda_x, r_sda_y)
    sch.add_junction(r_sda_x, r_sda_y)

    # ── ISM330 config pins ────────────────────────────────────
    # CS pull-up (10k to VDD)
    sch.add_symbol_instance("Device:R", "R_CS", "10k",
        ISM_X - 20, ISM_Y - 14, rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric")
    sch.add_power_symbol("VDD_3V3", ISM_X - 20, ISM_Y - 20)
    sch.add_wire(ISM_X - 20, ISM_Y - 10.16 - 1.27, ISM_X - 20, ISM_Y - 10.16)
    sch.add_wire(ISM_X - 20, ISM_Y - 10.16, ISM_X - 15.24, ISM_Y - 10.16)

    # SDO/SA0 pull-down (10k to GND) — I2C address 0x6A
    sch.add_symbol_instance("Device:R", "R_SA0", "10k",
        ISM_X - 25, ISM_Y - 5.08, rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric")
    sch.add_power_symbol("GND", ISM_X - 25, ISM_Y - 1)
    sch.add_wire(ISM_X - 25, ISM_Y - 5.08 - 3.81, ISM_X - 25, ISM_Y - 5.08)
    sch.add_wire(ISM_X - 25, ISM_Y - 5.08, ISM_X - 15.24, ISM_Y - 5.08)

    # ── Decoupling caps ───────────────────────────────────────
    # C_VDD1 for STM32 (100nF)
    sch.add_symbol_instance("Device:C", "C_VDD1", "100nF",
        STM_X - 25, STM_Y - 40, rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric")
    sch.add_power_symbol("VDD_3V3", STM_X - 25, STM_Y - 44)
    sch.add_power_symbol("GND", STM_X - 25, STM_Y - 36)

    # C_NRST (100nF on NRST)
    sch.add_symbol_instance("Device:C", "C_NRST", "100nF",
        STM_X - 30, STM_Y - 22, rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric")
    sch.add_power_symbol("GND", STM_X - 30, STM_Y - 18)
    sch.add_net_label("NRST", STM_X - 30, STM_Y - 26)

    # C_VCAP1 (1uF on VCAP1)
    sch.add_symbol_instance("Device:C", "C_VCAP1", "1uF",
        STM_X - 30, STM_Y + 5, rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric")
    sch.add_power_symbol("GND", STM_X - 30, STM_Y + 9)
    sch.add_net_label("VCAP1", STM_X - 30, STM_Y + 1)

    # C_ISM_VDD (100nF on ISM330 VDD)
    sch.add_symbol_instance("Device:C", "C_ISM_VDD", "100nF",
        ISM_X - 20, ISM_Y + 2, rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric")
    sch.add_power_symbol("VDD_3V3", ISM_X - 20, ISM_Y - 2)
    sch.add_power_symbol("GND", ISM_X - 20, ISM_Y + 6)

    # C_ISM_C1 (100nF on C1 pin)
    sch.add_symbol_instance("Device:C", "C_ISM_C1", "100nF",
        ISM_X - 20, ISM_Y + 8, rotation=0,
        footprint="Capacitor_SMD:C_0805_2012Metric")
    sch.add_wire(ISM_X - 15.24, ISM_Y, ISM_X - 20, ISM_Y)
    sch.add_wire(ISM_X - 20, ISM_Y, ISM_X - 20, ISM_Y + 4)
    sch.add_power_symbol("GND", ISM_X - 20, ISM_Y + 12)

    # ── BOOT0 pull-down ───────────────────────────────────────
    sch.add_symbol_instance("Device:R", "R_BOOT0", "10k",
        STM_X - 30, STM_Y + 18, rotation=90,
        footprint="Resistor_SMD:R_0805_2012Metric")
    sch.add_power_symbol("GND", STM_X - 30, STM_Y + 24)
    sch.add_net_label("BOOT0", STM_X - 30, STM_Y + 13)

    # ── No connects on unused ISM330 pins ─────────────────────
    sch.add_no_connect(ISM_X + 15.24, ISM_Y + 5.08)   # INT1
    sch.add_no_connect(ISM_X + 15.24, ISM_Y + 2.54)   # INT2
    sch.add_no_connect(ISM_X + 15.24, ISM_Y - 7.62)   # OCS_Aux

    # ── Save ──────────────────────────────────────────────────
    out_path = '/teamspace/studios/this_studio/PCBSchemaGen/rag/stm32_ism330_i2c.kicad_sch'
    sch.save(out_path)
    print(f"Components placed: {len(sch.symbols)}")
    print(f"Wires: {len(sch.wires)}")
    print(f"Power symbols: {len(sch.power_symbols)}")
    print(f"Net labels: {len(sch.labels)}")
    return out_path

if __name__ == "__main__":
    generate_stm32_ism330_schematic()
