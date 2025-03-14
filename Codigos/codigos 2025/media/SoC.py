import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import minimize
# Cargar el archivo CSV

file_path = 'C:/Users/franc/OneDrive/Documents/GitHub/battery-cycler-uach/logs/battery_HPPC_2024-08-26_10-47-20.csv'
df = pd.read_csv(file_path)

# Convertir la columna 'Timestamp' a un formato de tiempo adecuado
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Preparar los datos para la optimización
time = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds().values
voltage_measured = df['Voltage'].values
current_measured = df['Current'].values
start_index = time >= 9500  # Segundos
filtered_data = df[(df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds() >= start_index]
time_filtered = time[start_index]
current_filtered = current_measured[start_index]
voltage_filtered = voltage_measured[start_index]

time_filtered = np.linspace(0, 1000, 10)
current_filtered = np.sin(time_filtered)
voltage_filtered = 3.7 + 0.5 * np.sin(time_filtered)

def second_order_state_space_model(params, time, current, voltage_measured):
    R0, R1, C1, R2, C2, Voc = params
    
    # Asegurando límites mínimos en tau1 y tau2
    tau1 = max(R1 * C1, 1e-6)
    tau2 = max(R2 * C2, 1e-6)
    
    # Matrices del modelo
    A = np.array([
        [1, 0, 0],
        [0, np.exp(-1/tau1), 0],
        [0, 0, np.exp(-1/tau2)]
    ])
    B = np.array([
        [0],
        [R1 * (1 - np.exp(-1/tau1))],
        [R2 * (1 - np.exp(-1/tau2))]
    ])
    C = np.array([1, -1, -1])
    D = -R0

    x_k = np.array([Voc, 0, 0])  # Estado inicial
    Vt = []

    for k in range(len(time)):
        x_k1 = A @ x_k + B.flatten() * current[k]
        vt = C @ x_k1 + D * current[k]
        Vt.append(vt)
        x_k = x_k1

    Vt = np.array(Vt)
    
    # Función de error
    error = np.mean((Vt - voltage_measured) ** 2)
    
    return error

# Ajuste con valores iniciales más conservadores
initial_guess = [0.008, 20, 100.0, 1, 4000.0, 3.7]
result = minimize(second_order_state_space_model, initial_guess, args=(time_filtered, current_filtered, voltage_filtered))

# Resultados del ajuste
R0, R1, C1, R2, C2, Voc = result.x
print(f"R0: {R0}, R1: {R1}, C1: {C1}, R2: {R2}, C2: {C2}, Voc: {Voc}")

# Graficar los resultados
import matplotlib.pyplot as plt

# Simular el voltaje con los parámetros ajustados
Vt_estimated = []
x_k = np.array([Voc, 0, 0])  # Estado inicial

for k in range(len(time_filtered)):
    tau1 = max(R1 * C1, 1e-6)
    tau2 = max(R2 * C2, 1e-6)
    
    A = np.array([
        [1, 0, 0],
        [0, np.exp(-1/tau1), 0],
        [0, 0, np.exp(-1/tau2)]
    ])
    B = np.array([
        [0],
        [R1 * (1 - np.exp(-1/tau1))],
        [R2 * (1 - np.exp(-1/tau2))]
    ])
    C = np.array([1, -1, -1])
    D = -R0
    
    x_k1 = A @ x_k + B.flatten() * current_filtered[k]
    vt = C @ x_k1 + D * current_filtered[k]
    Vt_estimated.append(vt)
    x_k = x_k1

Vt_estimated = np.array(Vt_estimated)

# Gráfica
plt.figure(figsize=(10, 5))
plt.plot(time_filtered, voltage_filtered, label="Voltaje Medido", color="blue")
plt.plot(time_filtered, Vt_estimated, label="Voltaje Estimado", color="red", linestyle="--")
plt.xlabel("Tiempo (s)")
plt.ylabel("Voltaje (V)")
plt.title("Comparación entre Voltaje Medido y Estimado")
plt.legend()
plt.grid()
plt.show()