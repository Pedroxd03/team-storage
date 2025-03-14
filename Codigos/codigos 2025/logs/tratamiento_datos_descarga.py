import pandas as pd
import os

script_folder = os.path.dirname(__file__)
corriente_nominal = 2.6
N_CELLS = 2  # Cambia esto a la cantidad real de celdas

# Carga los datos desde el archivo CSV
data = pd.read_csv(script_folder + '/processed/datos_descarga_unificados.csv', parse_dates=['Timestamp'])

# Establece el índice como la columna de Timestamp
data.set_index('Timestamp', inplace=True)

# Resample para rellenar los valores faltantes dentro de cada intervalo
resampled_data = pd.DataFrame()
for interval, group in data.groupby('Interval Number'):
    interval_resampled = group.resample('S').asfreq()
    interval_resampled_filled = interval_resampled.ffill()
    resampled_data = pd.concat([resampled_data, interval_resampled_filled])

# Calcular la duración de cada intervalo
interval_durations = resampled_data.groupby('Interval Number').apply(lambda x: x.index[-1] - x.index[0])

# Filtrar los intervalos con duración diferente de 0
nonzero_durations = interval_durations[interval_durations.dt.total_seconds() > 0]

# Eliminar los intervalos con duración 0 y actualizar los datos
filtered_resampled_data = resampled_data[resampled_data['Interval Number'].isin(nonzero_durations.index)]

# Eliminar la primera fila de cada grupo
filtered_resampled_data = filtered_resampled_data.groupby('Interval Number').apply(lambda x: x.iloc[1:])

# Define una lista de valores de 'c_rate' que deseas eliminar
c_rate_to_remove = [0, 1.9, 2.8]  # Agrega los valores específicos que deseas eliminar

# Filtra las filas que no tienen 'C_rate' en la lista definida
filtered_resampled_data = filtered_resampled_data[~filtered_resampled_data.filter(like='C_rate').isin(c_rate_to_remove).any(axis=1)]

# Inicializar la columna "capacidad" en 0
filtered_resampled_data["capacidad"] = 0

# Inicializar el valor del último "Interval Number" como None
ultimo_interval_number = None

# Lista de 'Interval number' a eliminar
intervals_to_drop = []

# Filtrando el DataFrame para mantener solo las filas que no están en la lista
filtered_resampled_data = filtered_resampled_data[~filtered_resampled_data['Interval Number'].isin(intervals_to_drop)]

# Reiniciar el índice después de eliminar las filas
filtered_resampled_data.reset_index(level='Interval Number', drop=True, inplace=True)

# Iterar a través de las filas del DataFrame
for index, fila in filtered_resampled_data.iterrows():
    # Verificar si el "Interval Number" cambió
    if fila["Interval Number"] != ultimo_interval_number:
        valor_capacidad = 0  # Reiniciar la capacidad a 0
        ultimo_interval_number = fila["Interval Number"]
    else:
        # Iterar sobre las celdas
        for cell in range(1, N_CELLS + 1):
            valor_capacidad += fila[f"Cell {cell} C_rate"] * (corriente_nominal * 1000 / 3600)  # Aumentar la capacidad en 1

    # Asignar el valor de capacidad actual a la fila
    filtered_resampled_data.at[index, "capacidad"] = int(valor_capacidad)

# Guardar los datos procesados en un nuevo archivo CSV
filtered_resampled_data.to_csv(script_folder + '/processed/datos_descarga_resampled.csv', index=True)
