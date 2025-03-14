import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Cargar el archivo CSV
file_path = 'c:/Users/franc/OneDrive/Documents/GitHub/battery-cycler-uach/logs/battery_data_bank_3s_2024-07-20_20-09-40.csv'
data = pd.read_csv(file_path)

# Convertir la estampilla de tiempo a un objeto datetime
data['Timestamp'] = pd.to_datetime(data['Timestamp'])

# Calcular el tiempo en segundos desde el inicio
start_time = data['Timestamp'].iloc[0]
data['Time in Seconds'] = (data['Timestamp'] - start_time).dt.total_seconds()

# Aplicar filtro de media móvil
window_size = 2000  # Puedes ajustar el tamaño de la ventana según sea necesario

data['Cell 1 Voltage Smoothed'] = data['Cell 1 Voltage'].rolling(window=window_size).mean()
data['Cell 2 Voltage Smoothed'] = data['Cell 2 Voltage'].rolling(window=window_size).mean()
data['Cell 3 Voltage Smoothed'] = data['Cell 3 Voltage'].rolling(window=window_size).mean()

# Graficar los voltajes suavizados vs el tiempo en segundos
plt.figure(figsize=(10, 6))

plt.plot(data['Time in Seconds'], data['Cell 1 Voltage Smoothed'], label='Cell 1 Voltage (Smoothed)')
plt.plot(data['Time in Seconds'], data['Cell 2 Voltage Smoothed'], label='Cell 2 Voltage (Smoothed)')
plt.plot(data['Time in Seconds'], data['Cell 3 Voltage Smoothed'], label='Cell 3 Voltage (Smoothed)')

plt.xlabel('Time in Seconds')
plt.ylabel('Voltage (V)')
plt.title('Smoothed Voltage vs Time')
plt.legend()
plt.grid(True)

plt.show()
