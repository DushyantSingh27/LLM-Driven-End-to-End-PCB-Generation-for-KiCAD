from skidl import *
vin = Net("VIN")
gnd = Net("GND")
vout = Net("VOUT")
r1 = Part("test", "R", value="10k", footprint="test:R_0805")
r2 = Part("test", "R", value="10k", footprint="test:R_0805")
vin += r1[1]
r1[2] += r2[1]
r2[2] += gnd
vout += r1[2]
ERC()
