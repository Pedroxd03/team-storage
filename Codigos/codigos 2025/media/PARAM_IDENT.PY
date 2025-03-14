import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np

# Cargar los datos
df = pd.read_csv('C:/Users/franc/OneDrive/Documents/GitHub/battery-cycler-uach/logs/battery_HPPC_2024-08-19_15-34-45.csv')

# Convertir la columna 'Timestamp' a datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Convertir la columna 'Current' y 'Voltage' a float
df['Current'] = df['Current'].astype(float)
df['Voltage'] = df['Voltage'].astype(float)

# Detectar cambios significativos en la corriente
threshold = 0.1  # Define un umbral para detectar cambios significativos en la corriente
pulse_data = df[df['Current'].diff().abs() > threshold].copy()

# Verificar que pulse_data no esté vacío
if not pulse_data.empty:
    # Calcular la resistencia serie para cada pulso
    pulse_data['Delta_V_instant'] = pulse_data['Voltage'].diff()
    pulse_data['Delta_I'] = pulse_data['Current'].diff()
    pulse_data['R0'] = pulse_data['Delta_V_instant'] / pulse_data['Delta_I']

    # Obtener el valor promedio de R0
    R0 = pulse_data['R0'].mean()
    print(f"Resistencia serie (R0): {R0} Ohms")

    # Definir la función exponencial para ajustar
    def double_exp_func(t, V0, A1, tau1, A2, tau2):
        return V0 + A1 * np.exp(-t / tau1) + A2 * np.exp(-t / tau2)

    # Consolidar los datos de relajación globalmente
    relaxation_data = df[df['Current'] == 0]
    if len(relaxation_data) > 1:
        # Calcular el tiempo desde el inicio de la prueba
        time_since_pulse = (relaxation_data['Timestamp'] - relaxation_data['Timestamp'].iloc[0]).dt.total_seconds()
        voltages = relaxation_data['Voltage']

        # Ajuste de la curva de doble exponencial con valores iniciales
        initial_guess = [voltages.min(), 0.1, 100, 0.1, 100]
        popt, _ = curve_fit(double_exp_func, time_since_pulse, voltages, p0=initial_guess, maxfev=10000)

        # Extraer los parámetros
        V0, A1, tau1, A2, tau2 = popt
        R1 = tau1 / (A1 / R0)
        C1 = A1 * tau1 / R1
        R2 = tau2 / (A2 / R0)
        C2 = A2 * tau2 / R2

        print(f"Resistencia R1: {R1} Ohm")
        print(f"Capacitancia C1: {C1} F")
        print(f"Resistencia R2: {R2} Ohm")
        print(f"Capacitancia C2: {C2} F")

        # Graficar la curva de relajación y el ajuste global
        plt.figure(figsize=(10, 6))
        plt.plot(time_since_pulse, voltages, label='Datos de relajación global')
        plt.plot(time_since_pulse, double_exp_func(time_since_pulse, *popt), 'r--', label='Ajuste doble exponencial')
        plt.xlabel('Tiempo desde el inicio (s)')
        plt.ylabel('Voltaje (V)')
        plt.title('Curva de relajación del voltaje - Ajuste global')
        plt.legend()
        plt.grid(True)
        plt.show()
else:
    print("No se encontraron pulsos significativos en los datos.")
