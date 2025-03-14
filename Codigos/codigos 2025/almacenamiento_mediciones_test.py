import csv
import time
import os
import random
from datetime import datetime

n_celdas = 2  # Cambiar con el número real de celdas

# Crear la carpeta "logs" si no existe
if not os.path.exists("logs"):
    os.makedirs("logs")
print("se supone que se creó la carpeta")

# Obtener la ruta completa del archivo CSV
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = os.path.join("logs", f"battery_data_{current_datetime}.csv")

# Crear un nuevo archivo CSV con el nombre basado en la fecha y hora
with open(csv_filename, "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    header = ["Timestamp"]
    header.extend([f"Cell {i+1} Voltage" for i in range(n_celdas)])
    header.extend([f"Cell {i+1} Current" for i in range(n_celdas)])
    header.extend([f"Cell {i+1} Temp" for i in range(n_celdas)])
    csv_writer.writerow(header)
print("se supone que se creó el header")
# Simulación de adquisición de datos y guardado
while True:
    # Generar valores aleatorios para las mediciones
    timestamp = time.time()
    voltage = [round(random.uniform(3.6, 3.9), 2) for _ in range(n_celdas)]
    current = [round(random.uniform(1.0, 2.0), 2) for _ in range(n_celdas)]
    cell_temperatures = [round(random.uniform(25.0, 30.0), 2) for _ in range(n_celdas)]

    # Formatear el timestamp como una cadena de fecha y hora legible
    formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    # Guardar los datos en el archivo CSV
    with open(csv_filename, "a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([formatted_timestamp]+ voltage + current + cell_temperatures)

    # Simular intervalo entre mediciones
    time.sleep(0.01)
