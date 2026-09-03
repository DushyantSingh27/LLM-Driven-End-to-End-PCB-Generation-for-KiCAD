from roles import parse_value, classify_components

print("=== value parsing (fixes the '100n' vs '100nF' brittleness) ===")
for t, want in [("100nF",1e-7), ("100n",1e-7), ("4.7uF",4.7e-6), ("10uF",1e-5),
                ("1uF",1e-6), ("10k",1e4), ("4u7",4.7e-6), ("",None), ("22pF",2.2e-11)]:
    got = parse_value(t)
    ok = (got is None and want is None) or (got and abs(got-want)/want < 1e-9)
    print("  %-8r -> %-12s %s" % (t, got, "OK" if ok else "FAIL want %s" % want))

# ---- benchmark board, but with DELIBERATELY WRONG-LOOKING ref names ----
print("\n=== benchmark topology, refs renamed to prove names are irrelevant ===")
pads = {"IC_MAIN":72, "SENS":14}
for i in range(1,17): pads["CAP%d"%i] = 2
for i in range(1,5):  pads["RES%d"%i] = 2
nets = {
 "/VDD_3V3":[("IC_MAIN","A9","VDD","power_in"),("SENS","8","VDD","power_in")] +
            [("CAP%d"%i,"1",None,"passive") for i in (7,8,9,10,11,12,13,14)] +
            [("RES%d"%i,"1",None,"passive") for i in (1,3,4)],
 "GND":[("IC_MAIN","A8","VSS","power_in")] +
       [("CAP%d"%i,"2",None,"passive") for i in range(1,17)] +
       [("RES2","2",None,"passive")],
 "/VBAT":[("IC_MAIN","B9","VBAT","power_in"),("CAP3","1",None,"passive")],
 "VDDA":[("IC_MAIN","H9","VDDA","power_in"),("CAP4","1",None,"passive")],
 "/NRST":[("IC_MAIN","E9","NRST","input"),("CAP1","1",None,"passive")],
 "/SPI_CS":[("IC_MAIN","C3","PA15","bidirectional"),("SENS","12","CS","input"),
            ("RES1","2",None,"passive")],
 "/BOOT0":[("IC_MAIN","A7","BOOT0","input"),("RES2","1",None,"passive")],
 "/IMU_INT1":[("IC_MAIN","E8","PB6","bidirectional"),("SENS","4","INT1","output"),
              ("RES3","2",None,"passive")],
}
ncls = {"/VDD_3V3":"POWER","GND":"GND","/VBAT":"POWER","VDDA":"ANALOG",
        "/NRST":"SIGNAL","/SPI_CS":"SIGNAL","/BOOT0":"SIGNAL","/IMU_INT1":"SIGNAL"}
vals = {"CAP%d"%i:"100nF" for i in range(1,17)}
vals.update({"CAP9":"10uF","CAP11":"10uF","CAP14":"4.7uF"})
r = classify_components(pads, nets, ncls, vals)
print("  anchor:", r["anchor"], "| ICs:", r["ics"])
for role in sorted(r["by_role"]):
    print("   %-11s %s" % (role, r["by_role"][role]))

# ---- smartwatch-shaped: 5 ICs, no single anchor ----
print("\n=== smartwatch-shaped topology (PMIC + MCU + 3 sensors) ===")
pads2 = {"MCU":100, "PMIC":40, "IMU":14, "HRM":12, "BARO":8, "CONN":24}
for i in range(1,9): pads2["C%d"%i] = 2
pads2["R1"] = 2; pads2["R2"] = 2
nets2 = {
 "VSYS":[("PMIC","1","VIN","power_in"),("CONN","1","VBUS","power_in"),
         ("C1","1",None,"passive")],
 "V1V8":[("PMIC","5","VOUT","power_out"),("MCU","A1","VDD","power_in"),
         ("IMU","8","VDD","power_in"),("C2","1",None,"passive"),
         ("C3","1",None,"passive")],
 "GND":[("PMIC","2","GND","power_in"),("MCU","A2","VSS","power_in"),
        ("IMU","6","GND","power_in"),("HRM","3","GND","power_in"),
        ("BARO","2","GND","power_in")] +
       [("C%d"%i,"2",None,"passive") for i in range(1,9)],
 "I2C_SDA":[("MCU","B1","PB7","bidirectional"),("IMU","14","SDA","bidirectional"),
            ("HRM","5","SDA","bidirectional"),("R1","2",None,"passive")],
 "VDDA_HRM":[("HRM","1","AVDD","power_in"),("C8","1",None,"passive")],
}
ncls2 = {"VSYS":"POWER","V1V8":"POWER","GND":"GND","I2C_SDA":"SIGNAL",
         "VDDA_HRM":"ANALOG"}
vals2 = {"C1":"10uF","C2":"100n","C3":"4u7","C8":"100nF","R1":"4.7k"}
r2 = classify_components(pads2, nets2, ncls2, vals2)
print("  anchor:", r2["anchor"], "| ICs:", r2["ics"])
for role in sorted(r2["by_role"]):
    print("   %-11s %s" % (role, r2["by_role"][role]))
