import os
import pandas as pd
from scipy.integrate import trapz
import datetime

# Obtain the full path of the CSV file in the same folder as the script
archivo_csv = os.path.join(os.path.dirname(__file__), "battery_data_sustrend_bank_2023-11-14_11-32-36.csv")

# Load the CSV file into a DataFrame
df = pd.read_csv(archivo_csv)

# Define the number of cells (N_CELLS)
N_CELLS = 2  # You can change this value based on your actual scenario

# Initialize variables
interval_number = 0
current_interval = None
total_capacity = [0.0] * N_CELLS  # Store the total capacity for each cell in Ah (ampere-hours)
capacidades_por_intervalo = [[0.0] * N_CELLS]  # Store capacities for each cell in each interval
tiempo_por_intervalo = []  # Store time taken for each interval

# Lists to store current and time values in the current interval for each cell
current_values = {cell: [] for cell in range(1, N_CELLS + 1)}
time_values = []

# Iterate through the rows of the DataFrame
for index, row in df.iterrows():
    if row['Cell 1 Current'] < 0:
        # If the current is negative and we are not in a current interval, start a new one
        if current_interval is None:
            current_interval = interval_number
        # Add current and time values to the current interval for each cell
        for cell in range(1, N_CELLS + 1):
            if row[f'Cell {cell} Voltage'] >= 2:
                current_values[cell].append(row[f'Cell {cell} Current'])
        time_values.append(pd.Timestamp(row['Timestamp']))
    else:
        # If the current is not negative and we are in a current interval, end it
        if current_interval is not None:
            interval_number += 1
            current_interval = None
            # Calculate the capacity for each cell in the current interval using trapz
            for cell in range(1, N_CELLS + 1):
                if len(time_values) > 1:
                    delta_time = [(t - time_values[0]).total_seconds() / 3600.0 for t in time_values]
                    capacity = trapz(current_values[cell], delta_time)
                    total_capacity[cell - 1] += capacity
                    capacidades_por_intervalo[-1][cell - 1] += capacity
            tiempo_por_intervalo.append(time_values[-1] - time_values[0])  # Calculate time taken for the interval
            # Clear the lists for the next interval
            current_values = {cell: [] for cell in range(1, N_CELLS + 1)}
            time_values = []
            # Initialize a new row for the next interval
            capacidades_por_intervalo.append([0.0] * N_CELLS)

# If the last interval is a discharge interval, end it
if current_interval is not None:
    if len(time_values) > 1:
        delta_time = [(t - time_values[0]).total_seconds() / 3600.0 for t in time_values]
        for cell in range(1, N_CELLS + 1):
            capacity = trapz(current_values[cell], delta_time)
            total_capacity[cell - 1] += capacity
            capacidades_por_intervalo[-1][cell - 1] += capacity
        tiempo_por_intervalo.append(time_values[-1] - time_values[0])  # Calculate time taken for the interval

# If no discharge intervals were detected but there is at least one negative reading, count it as an interval
if interval_number == 0 and len(current_values[1]) > 0:
    interval_number = 1

# Print the number of discharge intervals
print("Number of discharge intervals:", interval_number)

# Print the capacity and time taken for each cell in each interval in milliampere-hours (mAh) and formatted time (hh:mm:ss)
for cell in range(1, N_CELLS + 1):
    print(f"Cell {cell} Discharge Intervals:")
    for i, (capacity, time_interval) in enumerate(zip(capacidades_por_intervalo[:-1], tiempo_por_intervalo)):
        print(f"  Interval {i + 1}:")
        print(f"    Capacity (mAh): {(capacity[cell - 1] * 1000):.4f} mAh")
        # Format and print the time taken
        hours, remainder = divmod(int(time_interval.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            print(f"    Time taken: {hours:02d} hours, {minutes:02d} minutes, {seconds:02d} seconds")
        else:
            print(f"    Time taken: {minutes:02d} minutes, {seconds:02d} seconds")

# Calculate and print the average capacity for each cell in milliampere-hours (mAh)
for cell in range(1, N_CELLS + 1):
    if interval_number > 0:
        promedio_capacidades = total_capacity[cell - 1] / interval_number
    else:
        promedio_capacidades = 0.0
    print(f"Cell {cell} Average capacity (mAh): {(promedio_capacidades * 1000):.4f} mAh")
