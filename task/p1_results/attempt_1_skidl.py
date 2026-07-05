# Define the resistor values for the voltage divider
R1 = 10.0  # in ohms
R2 = 1.0   # in ohms

# Calculate the output voltage of the voltage divider
Vout = (R2 / (R1 + R2)) * Vin

# Print the calculated output voltage
print(f"The output voltage Vout is {Vout} V")
