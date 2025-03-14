import pandas as pd
import os
import matplotlib.pyplot as plt

# Definir la corriente nominal
corriente_nominal = 2.6

# Cargar el archivo CSV de intervalos
script_folder = os.path.dirname(__file__)
csv_path = os.path.join(script_folder+"/processed/", 'datos_descarga_resampled.csv')
data = pd.read_csv(csv_path, parse_dates=["Timestamp"])

# Convertir la columna "Timestamp" a datetime
data['Timestamp'] = pd.to_datetime(data['Timestamp'])

# Obtener todas las columnas que contienen 'C_rate', 'Temp', y 'Voltage'
c_rate_columns = [col for col in data.columns if "C_rate" in col]
temp_columns = [col for col in data.columns if "Temp" in col]
voltage_columns = [col for col in data.columns if "Voltage" in col]

# Crear el gráfico
plt.figure(figsize=(10, 6))

# Variable para rastrear los C_rate que ya han sido anotados
annotated_c_rates = set()

# Tamaño de la ventana de la media móvil
ventana_media_movil = 40  # Ajusta este valor según tus necesidades

# Iterar sobre los valores únicos de C_rate
for c_rate_col, temp_col, voltage_col in zip(c_rate_columns, temp_columns, voltage_columns):
    for intervalo in data['Interval Number'].unique():
        interval_data = data[(data['Interval Number'] == intervalo)]
        tiempo_transcurrido = (interval_data['Timestamp'] - interval_data['Timestamp'].iloc[0]).dt.total_seconds()
        capacidad_ah = corriente_nominal * tiempo_transcurrido / 3600  # Convertir segundos a horas y multiplicar por corriente nominal
        capacidad_mah = capacidad_ah * 1000  # Convertir Ah a mAh
        label = f'Intervalo {intervalo} - {c_rate_col}'

        # Calcular la media móvil
        media_movil = interval_data[temp_col].rolling(window=ventana_media_movil).mean()

        # Usar el color asignado al C_rate
        plt.plot(
            capacidad_mah,
            media_movil,
            label=label,
        )

        indice_punto_medio = len(interval_data) // 2
        if c_rate_col not in annotated_c_rates:
            annotation_text = f'{c_rate_col}'
            plt.annotate(
                annotation_text,
                xy=(max(capacidad_mah) / 2, media_movil.iloc[indice_punto_medio]),
                xytext=(15, 0),
                textcoords='offset points',
                arrowprops=dict(facecolor='black', arrowstyle='wedge')
            )

            annotated_c_rates.add(c_rate_col)

# Configurar el gráfico
plt.xlabel('Capacidad (mAh)')
plt.ylabel('Temperatura de la Celda')
plt.title('Media Móvil de Temperatura de Celda en Intervalos de Descarga (ventana = {})'.format(ventana_media_movil))
plt.tight_layout()
plt.legend()

# Mostrar el gráfico
plt.show()
