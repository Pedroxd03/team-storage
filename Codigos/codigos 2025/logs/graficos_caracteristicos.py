import pandas as pd
import os
import matplotlib.pyplot as plt

# Definir la corriente nominal
corriente_nominal = 2.6

# Cargar el archivo CSV de intervalos
script_folder = os.path.dirname(__file__)
csv_path = os.path.join(script_folder + "/processed/", "datos_descarga_resampled.csv")
data = pd.read_csv(csv_path, parse_dates=["Timestamp"])

# Obtener todas las columnas que contienen 'C_rate' y 'Voltage'
c_rate_columns = [col for col in data.columns if "C_rate" in col]
voltage_columns = [col for col in data.columns if "Voltage" in col]

# Obtener colores únicos para cada C_rate
colores_c_rate = {c_rate: f"C{idx}" for idx, c_rate in enumerate(c_rate_columns)}

# Crear el gráfico
plt.figure(figsize=(10, 6))

# Iterar sobre las columnas 'C_rate'
for c_rate_col, voltage_col in zip(c_rate_columns, voltage_columns):
    for intervalo in data["Interval Number"].unique():
        interval_data = data[data["Interval Number"] == intervalo]
        if not interval_data.empty:
            tiempo_transcurrido = (interval_data["Timestamp"] - interval_data["Timestamp"].iloc[0]).dt.total_seconds()
            capacidad_ah = corriente_nominal * tiempo_transcurrido / 3600  # Convertir segundos a horas y multiplicar por corriente nominal
            capacidad_mah = capacidad_ah * 1000  # Convertir Ah a mAh

            # Usar el color asignado al C_rate
            plt.plot(
                capacidad_mah,
                interval_data[voltage_col],
                label=f"{c_rate_col} - {voltage_col}",
                color=colores_c_rate[c_rate_col],
            )

plt.xlabel("Capacidad (mAh)")
plt.ylabel("Voltaje de la Celda")
plt.title("Voltaje de Celda en Intervalos de Descarga")
plt.tight_layout()

# Mostrar la leyenda con los colores y sus correspondientes C-rate
handles = [
    plt.Line2D(
        [0],
        [0],
        marker="o",
        color="w",
        label=f"{c_rate_col} - {voltage_col}",
        markersize=10,
        markerfacecolor=color,
    )
    for c_rate_col, color in colores_c_rate.items()
]
plt.legend(handles=handles)
plt.show()