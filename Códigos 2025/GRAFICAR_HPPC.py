import pandas as pd
import matplotlib.pyplot as plt

# Leer los datos del archivo CSV
df = pd.read_csv('C:/Users/Lorenzo/INVENT UACh/Repositorios/battery-cycler-uach/logs/battery_HPPC_2024-11-03_13-48-10.csv')

# Convertir la columna 'Timestamp' a datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Calcular el tiempo en segundos desde el primer registro
df['Time_seconds'] = (df['Timestamp'] - df['Timestamp'][0]).dt.total_seconds()

# Crear la figura y los subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

# Gráfico del voltaje en el subplot superior
ax1.plot(df['Time_seconds'], df['Avg Voltage'], label='Vbatt', color='red')
ax1.set_title('HPPC Test')
ax1.set_ylabel('Vbatt (V)')
#ax1.grid(True)
ax1.legend()

# Gráfico de la corriente en el subplot inferior
ax2.plot(df['Time_seconds'], df['Current'], label='Current', color='mediumaquamarine')
ax2.set_xlabel('Time (s)')
ax2.set_ylabel('Current (A)')
#ax2.grid(True)
ax2.legend()

# Mostrar la gráfica
plt.show()
