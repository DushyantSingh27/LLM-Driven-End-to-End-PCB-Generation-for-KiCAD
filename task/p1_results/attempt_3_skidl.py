from skidl import *

# Define the nets
vin = Net("VIN")
gnd = Net("GND")
vout = Net("VOUT")

# Define the resistors using Part() function
r1 = Part("test", "R", value="10k", footprint="test:R_0805")
r2 = Part("test", "R", value="1k", footprint="test:R_0805")  # Changed from 10k to 1k for a more realistic voltage divider

# Connect the resistors and nets
vin += r1[1]
r1[2] += r2[1]
r2[2] += gnd
vout += r1[2]

# Perform ERC (Electrical Rules Check)
ERC()
