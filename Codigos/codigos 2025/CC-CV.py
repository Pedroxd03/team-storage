import pyvisa
import time
import os
import nidaqmx
import csv
import math
import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime
from HPPC import hppc_test

def thermocoupleVoltageToTemperature(Vth):
    R = 100 * Vth / (5 - Vth)
    T = (298.15 * 3950) / (3950 + math.log(R / 100e3) * 298.15) - 273.15
    return T

def check_temperature_limit(temp):
    if temp > Tmax:
        print(f"Temperature limit exceeded!")
        return True
    return False

def moving_average(data, window_size):
    if not isinstance(data, (list, deque)):
        raise TypeError("Data must be a list or deque.")
    if len(data) == 0:
        return None
    if len(data) < window_size:
        return sum(data) / len(data)
    else:
        return sum(list(data)[-window_size:]) / window_size

# LOGGING
N_CELLS = 1

if not os.path.exists("logs"):
    os.makedirs("logs")

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = os.path.join("logs", f"battery_data_{current_datetime}.csv")

with open(csv_filename, "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    header = ["Timestamp", "Voltage", "Current", "Temperature", "Vbatt"]
    csv_writer.writerow(header)

x = []
yvoltajes = []
ycorrientes = []
ytemperaturas = []

# Parameters
Vmax = 4.2
Vmmax = 4.3
Vmin = 3.0
Imax_ch = 1.3
Imin = 0.07
Imax_disch = 1.3
Tmax = 80
window_size = 10  # Tamaño de la ventana para la media móvil


# Initialization
mode = 4  # Cambiar a 4 para iniciar en modo de solo medición
t0 = time.time()

# Configure hardware
rm = pyvisa.ResourceManager()
print("Resources detected\n{}".format(rm.list_resources()))

supply = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C224204541::INSTR')
load = rm.open_resource('USB0::0x1AB1::0x0E11::DL3C213000056::INSTR')

if mode == 1:
    supply.write(":APPL CH2," + str(Vmmax) + "," + str(Imax_ch))
    supply.write(':OUTP CH2, ON')
    supply.write(":APPL CH3, 5, 1")
    supply.write(':OUTP CH3, ON')
    time.sleep(1)
elif mode == 3:
    load.write(":SOUR:CURR " + str(Imax_disch))
    load.write(':SOUR:INP:STAT ON')
    time.sleep(1)
elif mode == 4:
    print("Modo de solo medición iniciado. Equipos apagados.")
    supply.write(':OUTP CH2, OFF')
    load.write(':SOUR:INP:STAT OFF')
    time.sleep(0.1)
plt.ion()
fig, ax1 = plt.subplots()

line_voltage, = ax1.plot([], [], label="Voltage (V)", color='b')

if mode in [1, 3]:
    ax2 = ax1.twinx()
    line_current, = ax2.plot([], [], label="Current (A)", color='g')
    ax2.set_ylabel("Current (A)", color='g')
    ax2.legend(loc='upper right')

ax1.set_xlabel("Time (seconds)")
ax1.set_ylabel("Voltage (V)", color='b')
ax1.legend(loc='upper left')

# Historial de las últimas mediciones para la media móvil
voltages_window = deque(maxlen=window_size)
currents_window = deque(maxlen=window_size)
temperatures_window = deque(maxlen=window_size)

try:
    while True:
        with nidaqmx.Task() as task:
            channels = "cDAQ1Mod1/ai0:1"
            task.ai_channels.add_ai_voltage_chan(channels)
            measurement = task.read()

            Vbatt = measurement[0]
            temp = thermocoupleVoltageToTemperature(measurement[1])
            print("Vbatt: ", Vbatt)

            if math.isnan(temp):
                print(f"Error al calcular la temperatura con Vth = {measurement[1]}")
                continue

            if check_temperature_limit(temp):
                print("Turning off equipment due to temperature limit.")
                mode = 0

        if mode == 0:
            supply.write(':OUTP CH2, OFF')
            load.write(':SOUR:INP:STAT OFF')
            print("All hardware is shutdown!")
            break

        voltages_window.append(Vbatt)
        temperatures_window.append(temp)
        temp_mov_avg = moving_average(temperatures_window, window_size)
        volt_mov_avg = moving_average(voltages_window, window_size)

        if mode in [1, 3]:
            I = float(load.query(':MEAS:CURR?'))
            currents_window.append(I)
            curr_mov_avg = moving_average(currents_window, window_size)
        
        if mode == 1:  # Modo CC
            Vset = float(supply.query(':MEAS:VOLT? CH2'))
            I = float(supply.query(':MEAS:CURR? CH2'))
            R = (Vset - Vbatt)/ I
            print("La resistencia es", R, "a una corriente de: ", I)
            
            if Vbatt > Vmax:
                #Vset_adjusted = Vmax + R*I
                Vset_adjusted = Vmax
                print("Vsetadj: ", Vset_adjusted)
                if R>0:
                    Vset_adjusted += R * I
                    #supply.write(":APPL CH2," + str(Vset_adjusted) + "," + str(Imax_ch))
                Vset_adjusted = min(Vset_adjusted, Vmax)  
                supply.write(":APPL CH2," + str(Vset_adjusted) + "," + str(Imax_ch))  
                print(f"Ajustando Vset a {Vset_adjusted:.2f} V para proteger la batería.")

            if I < Imin:
                supply.write(':OUTP CH2, OFF')
                mode = 0
               
            print(f"Modo CC - Vbatt: {Vbatt:.2f} V, Vbatt media móvil: {volt_mov_avg:.2f} V, Vset: {Vset:.2f} V")
            print(f"Corriente real: {I:.2f} A, Corriente mínima: {Imin:.2f} A")
        
        elif mode == 3:  # Modo de descarga
            I = -float(load.query(':MEAS:CURR?'))
            Vdis = float(load.query(':MEAS:VOLT?'))
            if Vbatt < Vmin:
                print("Se acabó la descarga")
                load.write(':SOUR:INP:STAT OFF')
                modo = 0

            print(f"Vbatt real: {Vbatt:.2f} V, Vbatt media movil: {volt_mov_avg:.2f} V")
            print(f"Corriente real: {I:.2f} A, Corriente media movil: {curr_mov_avg:.2f} A")

        elif mode == 4:  # Modo de solo medición
            print(f"Vbatt real: {Vbatt:.2f} V, Vbatt media movil: {volt_mov_avg:.2f} V")

        timestamp = time.time()
        formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

        with open(csv_filename, "a", newline="") as csv_file:
            csv_writer = csv.writer(csv_file)
            if mode != 4:
                row = [formatted_timestamp, Vbatt, I, temp, Vbatt]
            else:
                row = [formatted_timestamp, Vbatt, 'N/A', temp, Vbatt]
            csv_writer.writerow(row)

        x.append(time.time() - t0)
        yvoltajes.append(volt_mov_avg)

        line_voltage.set_data(x, yvoltajes)

        if mode in [1, 3]:
            ycorrientes.append(I)
            line_current.set_data(x, ycorrientes)

        ax1.relim()
        ax1.autoscale_view()

        if mode in [1, 3]:
            ax2.relim()
            ax2.autoscale_view()

        fig.canvas.draw()
        fig.canvas.flush_events()

        time.sleep(1)

except KeyboardInterrupt:
    print("\nInterrupción detectada. Guardando gráfica...")
    plt.ioff()
    fig.savefig(os.path.join("logs", f"graph_{current_datetime}.png"))
    plt.show()
    print("Gráfica guardada exitosamente. El programa ha terminado correctamente.")
    supply.write(':OUTP CH2, OFF')
    load.write(':SOUR:INP:STAT OFF')
    print("Equipos apagados correctamente.")