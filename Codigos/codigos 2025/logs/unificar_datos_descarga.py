import os
import matplotlib.pyplot as plt
import pandas as pd

N_CELLS = 2
# Obtener la ruta de la carpeta del script
script_folder = os.path.dirname(__file__)
print(script_folder)

# Definir la corriente nominal
corriente_nominal = 2.6

# Crear un DataFrame vacío para almacenar los datos filtrados
filtered_data = pd.DataFrame()

# Inicializar los contadores globales de intervalos
global_interval_counter = 0
total_interval_counter = 0

# Obtener una lista de nombres de archivos CSV en la carpeta
csv_files = [file for file in os.listdir(script_folder) if file.startswith('battery_data_sustrend_bank_2023-11-14_11-32-36') and file.endswith('.csv')]

# Función para detectar los intervalos de descarga
def detect_discharge_intervals(data, interval_counter, N_CELLS):
    discharge_intervals = []
    is_discharging = False
    for index, row in data.iterrows():
        if any(row[f'Cell {i} Current'] < 0 for i in range(1, N_CELLS + 1)):
            if not is_discharging:
                discharge_start = row['Timestamp']
                is_discharging = True
                interval_counter += 1  # Nuevo intervalo de descarga
        else:
            if is_discharging:
                discharge_end = row['Timestamp']
                discharge_intervals.append((discharge_start, discharge_end, interval_counter))
                is_discharging = False
    return discharge_intervals, interval_counter

# Iterar sobre cada archivo CSV
for csv_file in csv_files:
    # Construir la ruta completa al archivo CSV
    csv_path = os.path.join(script_folder, csv_file)

    # Cargar el archivo CSV
    data = pd.read_csv(csv_path)

    # Obtener los intervalos de descarga y actualizar los contadores globales
    discharge_intervals, global_interval_counter = detect_discharge_intervals(data, global_interval_counter, N_CELLS)
    print(f"Archivo: {csv_file}")
    print(f"Número de intervalos de descarga: {len(discharge_intervals)}")
    
    if len(discharge_intervals) == 0:
        print("No se encontraron intervalos de descarga.")
        #os.remove(csv_path)
        #print(f"Archivo {csv_file} eliminado.")
    else:
        total_interval_counter += len(discharge_intervals)
    
    if not data.empty:
        print("El archivo contiene datos. No se eliminará.")
    else:
        # Si no hay datos en el DataFrame, eliminamos el archivo
        os.remove(csv_path)
        print(f"El archivo '{csv_path}' ha sido eliminado.")
        continue
    
    print("---------------------")

    # Filtrar los datos con corriente negativa y agregar al DataFrame
    filtered_data = pd.concat([filtered_data, data[data[f'Cell 1 Current'] < 0]], ignore_index=True)

    # Calcular la relación de corriente con la capacidad nominal y aproximar al decimal más cercano
    for i in range(1, N_CELLS + 1):
        filtered_data[f'Cell {i} C_rate'] = (filtered_data[f'Cell {i} Current'] / corriente_nominal).abs().round(1)

    # Agregar la columna de número de intervalo utilizando el contador global y convertir a entero
    for interval_start, interval_end, interval_number in discharge_intervals:
        filtered_data.loc[(filtered_data['Timestamp'] >= interval_start) & (filtered_data['Timestamp'] <= interval_end), 'Interval Number'] = interval_number

# Convertir la columna 'Interval Number' a enteros
filtered_data['Interval Number'] = pd.to_numeric(filtered_data['Interval Number'], errors='coerce')
filtered_data = filtered_data.dropna(subset=['Interval Number'])
filtered_data['Interval Number'] = filtered_data['Interval Number'].astype(int)

# Ruta para el archivo CSV final filtrado
if not os.path.exists(os.path.join(script_folder, "processed")):
    os.makedirs(os.path.join(script_folder, "processed"))

filtered_file_path = os.path.join(script_folder, "processed", 'datos_descarga_unificados.csv')

# Guardar todos los datos filtrados en un solo archivo CSV (sobreescribiendo si existe)
filtered_data.to_csv(filtered_file_path, index=False)
filtered_file_path = os.path.join(script_folder, "processed", 'datos_descarga_unificados.csv')
print(f"Número total de intervalos de descarga: {total_interval_counter}")

