import csv
import numpy as np
import os

def get_resistance(temperature):
    closest_index = np.argmin(np.abs(lut[:, 0] - temperature))
    return lut[closest_index, 1]

script_directory = os.path.dirname(os.path.abspath(__file__))    
# Cargar datos desde el archivo CSV
filename = os.path.join(script_directory, 'NTCM-100K-B3950.csv')
lut_data = []

with open(filename, 'r') as csv_file:
    csv_reader = csv.reader(csv_file)
    next(csv_reader)
    for row in csv_reader:
        temperature = float(row[0])
        resistance = float(row[2])
        lut_data.append((temperature, resistance))

lut_data.sort(key=lambda x: x[0])

# Crear una matriz NumPy para la LUT
lut = np.array(lut_data)

# Guardar la LUT en un archivo CSV
lut_filename = 'LUT_res_temp.csv'
with open(lut_filename, 'w', newline='') as lut_file:
    csv_writer = csv.writer(lut_file)
    csv_writer.writerow(['Temperature (C)', 'Resistance (K)'])  # Encabezados
    csv_writer.writerows(lut)  # Escribir los datos de la LUT en el archivo

if __name__ == "__main__":
    desired_temps = [i for i in range(-30, 30)]
    resistances = []

    for temp in desired_temps:
        resistances.append(get_resistance(temp))

    for i, temp in enumerate(desired_temps):
        print(f"Para {temp}°C, la resistencia es {resistances[i]} KΩ")
