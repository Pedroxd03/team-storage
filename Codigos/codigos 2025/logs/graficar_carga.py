import os
import matplotlib.pyplot as plt
import pandas as pd

N_CELLS = 2
# Define the CSV file name and folder path
csv_name = "battery_data_sustrend_bank_2023-11-12_00-05-36.csv"
folder_path = os.path.dirname(__file__)
csv = os.path.join(folder_path, csv_name)

# Load the CSV file into a pandas DataFrame
data = pd.read_csv(csv)

# Filter data for charging cycles where Cell 1 Current > 0
cargas = data[data[f"Cell 1 Current"] < 0]
print(data.describe())
print(cargas.describe())

# Create the first subplot for voltage and current
figure1 = plt.gca()

# Plot voltage and current for each cell
for i in range(1, N_CELLS + 1):
    plt.plot(cargas[f"Cell {i} Voltage"], label=f"Cell {i} Voltage")
    #plt.plot(cargas[f"Cell {i} Current"], label=f"Cell {i} Current")

# Customize the first subplot
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V) / Current (A)')
plt.title("Descarga: " + csv_name)
plt.xticks(rotation=45)

# Create a second subplot for temperature
figure2 = figure1.twinx()

# Plot temperature for each cell
#for i in range(1, N_CELLS + 1):
#    plt.plot(cargas[f"Cell {i} Temp"], label=f"Cell {i} Temperature")

# Customize the second subplot
#plt.ylabel('Temperature (°C)')

# Combine legends from both subplots
figure1.legend(loc='upper left')
figure2.legend(loc='lower left')

# Save the combined figure as an image
plt.savefig("charging_cycles.png")

# Show the combined figure
plt.show()