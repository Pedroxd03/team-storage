import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Cargar el archivo CSV
file_path = 'C:/Users/franc/OneDrive/Documents/GitHub/battery-cycler-uach/logs/battery_HPPC_2024-08-21_13-03-23.csv'
df = pd.read_csv(file_path)

V1_points = []  # Lista para almacenar los datos de V1 en cada intervalo
V2_points = []  

# Cambiar el tipo de datos de Timestamp
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Calcular el tiempo en segundos desde el inicio
df['Time_in_seconds'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()

# Filtrar los datos a partir del segundo 7700
df_filtered = df[df['Time_in_seconds'] >= 5000].copy()

# Identificar los intervalos donde la corriente es negativa por más de 20 segundos
negative_intervals = []
current_interval = []

for i in range(1, len(df_filtered)):
    if df_filtered['Current'].iloc[i] < 0:
        current_interval.append(i)
    else:
        if current_interval:
            duration = df_filtered['Time_in_seconds'].iloc[current_interval[-1]] - df_filtered['Time_in_seconds'].iloc[current_interval[0]]
            if duration >= 20:
                negative_intervals.append(current_interval)
            current_interval = []

# Asegurarse de agregar el último intervalo si terminó en negativo
if current_interval:
    duration = df_filtered['Time_in_seconds'].iloc[current_interval[-1]] - df_filtered['Time_in_seconds'].iloc[current_interval[0]]
    if duration >= 20:
        negative_intervals.append(current_interval)

# Plotting de los datos
fig, ax1 = plt.subplots()

ax1.plot(df['Time_in_seconds'], df['Voltage'], 'r-', label='Voltaje')
ax1.set_xlabel('Tiempo (s)')
ax1.set_ylabel('Voltaje (V)', color='r')

ax2 = ax1.twinx()
ax2.plot(df['Time_in_seconds'], df['Current'], 'c-', label='Corriente')
ax2.set_ylabel('Corriente (A)', color='c')

for interval in negative_intervals:
    V1_idx = interval[0]
    V1 = df_filtered['Voltage'].iloc[V1_idx]
    time_V1 = df_filtered['Time_in_seconds'].iloc[V1_idx]
    I1 = df_filtered['Current'].iloc[V1_idx]

    print(f"Intervalo:\n  V1: {V1} V en {time_V1} s con corriente {I1} A")
    ax1.plot(time_V1, V1, 'ko')  # Marcador para V1
    ax1.text(time_V1, V1, 'V1', fontsize=12, verticalalignment='bottom', horizontalalignment='right')

    # Buscar el punto V2
    for j in interval:
        if df_filtered['Current'].iloc[j] <= -2.5:
            V2_idx = j
            V2 = df_filtered['Voltage'].iloc[V2_idx]
            time_V2 = df_filtered['Time_in_seconds'].iloc[V2_idx]
            I2 = df_filtered['Current'].iloc[V2_idx]
            
            # Verificar si el voltaje cambia de lineal a exponencial
            if V2 < V1 and I2 < I1:  # Condiciones básicas, ajustar según comportamiento real
                print(f"  V2: {V2} V en {time_V2} s con corriente {I2} A")
                ax1.plot(time_V2, V2, 'mo')  # Marcador para V2
                ax1.text(time_V2, V2, 'V2', fontsize=12, verticalalignment='bottom', horizontalalignment='left')
                
                # Cálculo de la resistencia
                delta_V = V1 - V2
                resistencia = abs(delta_V / I2)  # R = V/I, considerando R positivo
                
                print(f"  Resistencia: {resistencia} ohms")
                break
    else:
        print("  No se encontró un punto V2 para este intervalo.")

plt.title('TEST HPPC')
fig.tight_layout()
plt.show()
