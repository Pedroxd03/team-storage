import matplotlib.pyplot as plt
import csv
import numpy as np
from scipy.optimize import curve_fit

# Función exponencial decreciente
def exponential_decay(x, a, b, c):
    return a * np.exp(-b * x) + c

# Nombre del archivo CSV
nombre_archivo = 'NTCM-100K-B3950.csv'

# Listas para almacenar los datos
eje_horizontal = []
eje_vertical = []

# Lectura de los datos desde el archivo CSV
with open(nombre_archivo, 'r') as archivo_csv:
    lector_csv = csv.reader(archivo_csv)
    next(lector_csv)  # Saltar la fila de encabezado si existe
    for fila in lector_csv:
        eje_horizontal.append(float(fila[0]))  # Convertir a float si es necesario
        eje_vertical.append(float(fila[2]))    # Convertir a float si es necesario


# Función exponencial decreciente
def exponential_decay(x, a, b, c):
    return a * np.exp(-b * x) + c


# Dividir los datos en columnas x (temperatura) e y (resistencia)
x_data = eje_horizontal
y_data = eje_vertical

# Ajuste de la función a los datos
params, covariance = curve_fit(exponential_decay, x_data, y_data, p0=[10000, 0.01, 1000])

# Parámetros del ajuste
a_fit, b_fit, c_fit = params

# Generar puntos ajustados para trazar la curva
x_fit = np.linspace(min(x_data), max(x_data), 100)
y_fit = exponential_decay(x_fit, a_fit, b_fit, c_fit)

# Crear una figura con dos subgráficos uno debajo del otro
plt.figure(figsize=(12, 6))  # Tamaño de la figura

# Subgráfico 1: Gráfica lineal
plt.subplot(1, 2, 1)  # 1 fila, 2 columnas, subgráfico 1
plt.xlabel('Temperatura (°C)')
plt.ylabel('Resistencia (KΩ)')
plt.title('Gráfica de Resistencia vs. Temperatura')
plt.plot(eje_horizontal, eje_vertical, marker='o', linestyle='-', color='b', label='Datos')
plt.grid(True, color='green')  # Agregar un grid de color verde
plt.legend()

# Gráfico de los datos originales y la curva ajustada
plt.scatter(x_data, y_data, label='Datos')
plt.plot(x_fit, y_fit, label='Ajuste exponencial decreciente', color='red')
plt.xlabel('Temperatura (°C)')
plt.ylabel('Resistencia (KΩ)')
plt.legend()
plt.title('Ajuste Exponencial Decreciente')
plt.grid(True)

# Subgráfico 2: Gráfica con eje vertical en escala logarítmica
plt.subplot(1, 2, 2)  # 1 fila, 2 columnas, subgráfico 2
plt.xlabel('Temperatura (°C)')
plt.ylabel('Resistencia (KΩ)')
plt.title('Gráfica de Resistencia vs. Temperatura (Log)')
plt.plot(eje_horizontal, eje_vertical, marker='o', linestyle='-', color='r', label='Datos')
plt.yscale('log')  # Cambiar la escala del eje vertical a logarítmica
plt.grid(True, color='green')  # Agregar un grid de color verde
plt.legend()


# Ajustar el espaciado entre subgráficos
plt.tight_layout()

plt.show()


print(f'Parámetros del ajuste: a = {a_fit:.2f}, b = {b_fit:.2f}, c = {c_fit:.2f}')
print(f'Función de ajuste: y = {a_fit:.2f} * exp(-{b_fit:.2f} * x) + {c_fit:.2f}')