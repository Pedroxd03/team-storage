import pyvisa
import time
import os
import nidaqmx
import csv
import math
import matplotlib.pyplot as plt
from datetime import datetime

def movingAverage(avg_list, new_values, n_samples):
    if not isinstance(avg_list, list):
        avg_list = [avg_list]

    if isinstance(new_values, list):
        avg_list.extend(new_values)
    else:
        avg_list.append(new_values)

    while len(avg_list) > n_samples:
        avg_list.pop(0)

    # Filtra elementos no numéricos y asegura que la lista no esté vacía
    avg_list = [value for value in avg_list if isinstance(value, (int, float))]
    
    if not avg_list:
        return avg_list, 0.0  # Evita la división por cero si la lista está vacía

    moving_avg = sum(avg_list) / len(avg_list)
    return avg_list, moving_avg

def thermocoupleVoltageToTemperature(Vth):
    R = 100 * Vth / (5 - Vth)   #Divisor de voltaje
    print("Vth es: ",Vth)
    print("R es: ",R)
    # R = 271.26 * exp(-0.038 * T)
    #T = - math.log(R / 271.26) / 0.038
    T = (298.15*3950) / (3950+math.log(R /100e3)*298.15) - 273.15  #Versión reducida de la ecc Steinhart-Hart
    print("La temperatura es: ", T)
    return T

def check_temperature_limit(temperatures):
    for cell, temp in enumerate(temperatures):
        print(f"Tmax es {Tmax}")
        if max(temp, key = abs) > Tmax:
            print(f"Temperature limit exceeded in Cell {cell + 1}!")
            return True
    return False
# LOGGING
N_CELLS = 3
N_CHANNELS = N_CELLS * 2

# Crear la carpeta "logs" si no existe
if not os.path.exists("logs"):
    os.makedirs("logs")

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = os.path.join("logs", f"battery_data_bank_3s_{current_datetime}.csv")

# Crear un nuevo archivo CSV con el nombre basado en la fecha y hora
with open(csv_filename, "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    header = ["Timestamp"]
    header.extend([f"Cell {i+1} Voltage" for i in range(N_CELLS)])
    header.extend([f"Cell {i+1} Current" for i in range(N_CELLS)])
    header.extend([f"Cell {i+1} Temp" for i in range(N_CELLS)])
    header.extend(["Vbatt"])
    csv_writer.writerow(header)

x = []
yvoltajes = [[] for _ in range(N_CELLS)]
ytemperaturas = [[] for _ in range(N_CELLS)]
ycorrientes = [[] for _ in range(N_CELLS)]
derivada_voltaje = [[] for _ in range(N_CELLS)]
derivada_corriente = [[] for _ in range(N_CELLS)]
derivada_temperatura = [[] for _ in range(N_CELLS)]

yvoltajes = []
ytemperaturas = []
ycorrientes = []
derivada_voltaje = []
derivada_corriente = []
derivada_temperatura = []

# Initialize line objects
lines = []

# Parameters
N_CYCLES = 10
R = 0.5
Vmax = 13
Vmin = 9.0
Imax_ch = 0.3
Imin = 0.09
Imax_dh = 0.5
dVmin = 0.005
Vmmin = 8.0
Vmmax = 12.6 #Voltaje de alimentación de la batería
Tmax = 80

# Initialization
n = 1
mode = -1
Tavg  = [0.0]*N_CELLS
T = [[] for _ in range(N_CELLS)]
Tread = [[] for _ in range(N_CELLS)]
Tread_avg = [[] for _ in range(N_CELLS)]
Vread = [[] for _ in range(N_CELLS)] #Listas de voltaje para cada celda
Iread = [] 
V_bank= []
Vavg_cell = [0.0]
Tavg_cell = [0.0]
Vprev = 0.0
avg_list = [ [] for _ in range(N_CELLS) ]
Tavg_list = [[] for _ in range(N_CELLS)]
t0 = time.time()
count = 0


def calculate_Vbank(measurement, n_cells):
    Vbank = sum(measurement[i] for i in range(n_cells))
    print(Vbank)
    return Vbank

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
elif mode == 3:
    load.write(":SOUR:CURR:LEV:IMM " + str(Imax_dh))
    load.write(':SOUR:INP:STAT ON')

while True:
    with nidaqmx.Task() as task:
        channels = f"cDAQ1Mod1/ai0:{2 * N_CELLS - 1}"
        print("Channels configured:", channels)
        task.ai_channels.add_ai_voltage_chan(channels)
        measurement = task.read()
        print("Length of measurement:", len(measurement))  
 
        for cell in range(N_CELLS):
            index_voltaje = cell  # Canales de voltaje están en las posiciones 0, 1, 2
            index_temperatura = cell + 3  # Canales de temperatura están en las posiciones 3, 4, 5
            Tread[cell], moving_avg = movingAverage(Tread[cell], T[cell], 5)
            Tavg_list[cell].append(moving_avg)
            print(f"Index voltaje: {index_voltaje}, Index temperatura: {index_temperatura}")
            if len(measurement) > max(index_voltaje, index_temperatura) and T[cell] is not None:
                V = measurement[index_voltaje]
                Vbank = calculate_Vbank(measurement, N_CELLS)
                V_bank.append(Vbank)
                Vread[cell].append(V)

                temp = thermocoupleVoltageToTemperature(measurement[index_temperatura])
                if math.isnan(temp):
                    print(f"Error al calcular la temperatura para la celda {cell + 1} con Vth = {measurement[index_temperatura]}")
                    continue
                if not isinstance(T[cell],list):
                    T[cell] = []
                T[cell] = temp    
                Tread[cell].append(T[cell])

        if check_temperature_limit(Tread):
            print("Turning off equipment due to temperature limit.")
            mode = 0
        
        Tavg = [sum(cell_avg_list) / len(cell_avg_list) if cell_avg_list else 0.0 for cell_avg_list in Tread_avg]
        Tread[cell], Tavg = movingAverage(Tread[cell], T[cell], 5)
        avg_list, Tavg = movingAverage(avg_list, Tavg, 5)          
        dV = Vbank - Vprev
        Vprev = Vbank
        
    if mode == 0:
        supply.write(':OUTP CH2, OFF')
        load.write(':SOUR:INP:STAT OFF')
        print("All hardware is shutdown!")
        break

    elif mode == 1:
        print("Mode 1: battery charge")
        Vset = float(supply.query(':MEAS:VOLT? CH2'))
        I = float(supply.query(':MEAS:CURR? CH2'))
        Iread, Iavg = movingAverage(Iread, I, 5)
        print(f"Vset: {Vset}, Vbank: {Vbank}, Iavg: {Iavg}")
        R = (Vset - Vbank) / Iavg
        print("R =" + str(R))
        if Vbank > Vmax:    
            Vlim = Vmax + R * Iavg
            if R > 0:
                supply.write(":APPL CH2," + str(Vlim) + "," + str(Imax_ch))
        if Iavg < Imin:
            count = count + 1
            if count >= 5:
                if n == 0:
                    print("Cycle 1 start!")
                else:
                    print('Cycle ' + str(n) + " finished!")
                    if n == N_CYCLES:
                        print("Done with success!")
                        mode = 0 
                        rm.close()
                        task.close() 
                    else:
                        n = n + 1
                        mode = 2
                        print("Switching to mode 2")
                        supply.write(':OUTP CH2, OFF')
                    count = 0
        else:
            count = 0
    elif mode == 2:
        print("Mode 2: relaxation")
        I = 0
        Iavg = 0
        print(f"Abs(dV): {abs(dV)}, dVmin: {dVmin}")
        if abs(dV) < dVmin:
            count = count + 1
            if count == 2:
                mode = 3
                load.write(":SOUR:CURR:LEV:IMM " + str(Imax_dh))
                load.write(':SOUR:INP:STAT ON')
                count = 0
        else:
            count = 0

    elif mode == 3:
        print("Mode 3: battery discharge")
        I = -float(load.query(":MEASURE:CURRENT?"))
        Iread, Iavg = movingAverage(Iread, I, 5)
        print(f"Vbank: {Vbank}, Vmin: {Vmin}")
        if Vbank < Vmin:
            mode = 4
            load.write(':SOUR:INP:STAT OFF')
    elif mode == 4:
        print("Mode 4: recovery")
        I = 0
        Iavg = 0
        print(f"Abs(dV): {abs(dV)}, dVmin: {dVmin}")
        if (abs(dV)) < dVmin:
            print(f"Abs(dV): {abs(dV)}, dVmin: {dVmin}")
            count = count + 1
            if count >= 2:
                mode = 1
                supply.write(':OUTP CH2, ON')
                supply.write(":APPL CH2," + str(Vmmax) + "," + str(Imax_ch))
                count = 0
        else:
            count = 0
    elif mode == -1:
        print("Mode -1: Just Measurement")
        print("Vbank = " + str(Vbank)  + ", T = " + str(T) + ", Tavg = " + str(Tavg))
        time.sleep(1)
        continue
    else:
        print("No mode ", mode)
        break

    print(f"Cycle number: {n}")
    print(f"V_bank = {V_bank[-1]:.2f}, ", end="")
    for cell in range(N_CELLS):
        print(f"Vcell{cell + 1} = {Vread[cell][-1]:.2f}", end=", ")
    for cell in range(N_CELLS):
        print(f"Tcell{cell + 1} = {Tread[cell][-1]:.2f}", end=", ")
    print(f"I = {I:.3f}, Tavg = {Tavg:.2f}")
    timestamp = time.time()
    formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    with open(csv_filename, "a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        voltage_data = [Vread[cell][-1] for cell in range(N_CELLS)]
        current_data = [I]*N_CELLS
        temperature_data = [Tread[cell][-1] for cell in range(N_CELLS)]
        formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        row = [formatted_timestamp] + voltage_data + current_data + temperature_data + [Vbank]
        csv_writer.writerow(row)

    x.append(time.time() - t0)
    yvoltajes.append(Vbank)
    ycorrientes.append(I)
    ytemperaturas.append(T)

    ventana_derivada = 2

    if len(ycorrientes) >= ventana_derivada and len(x) >= ventana_derivada:
        delta_corriente = ycorrientes[-1] - ycorrientes[-ventana_derivada]
        delta_tiempo = x[-1] - x[-ventana_derivada]
        derivada = delta_corriente / (delta_tiempo)
        derivada_corriente.append(derivada*10)
    else:
        derivada_corriente.append(0)

    # Calculate derivatives for voltage and temperature
    if len(yvoltajes) >= ventana_derivada and len(x) >= ventana_derivada:
        delta_voltaje = yvoltajes[-1] - yvoltajes[-ventana_derivada]
        delta_tiempo = x[-1] - x[-ventana_derivada]
        derivada_v = delta_voltaje / delta_tiempo
        derivada_voltaje.append(derivada_v * 10)
    else:
        derivada_voltaje.append(0)
# Verifica si las listas tienen elementos antes de calcular la longitud
    if not ytemperaturas or not ytemperaturas[0]:
        delta_temperatura = [0.0 for _ in range(N_CELLS)]
    else:
        delta_temperatura = [ytemperaturas[-1][cell] - ytemperaturas[-1][-ventana_derivada] for cell in range(N_CELLS)]

# Calculate derivatives for temperature
    if len(ytemperaturas) >= ventana_derivada and len(x) >= ventana_derivada:
        delta_temperatura = [ytemperaturas[-1][cell] - ytemperaturas[-1][-ventana_derivada] for cell in range(N_CELLS)]
    else:
        print("Not enough elements in ytemperaturas or x.")
        delta_temperatura = [0.0 for _ in range(N_CELLS)]
# Calculate derivatives for temperature
   
    if len(ytemperaturas) >= ventana_derivada and all(ytemp and len(ytemp) >= ventana_derivada for ytemp in ytemperaturas):
        delta_temperatura = [ytemperaturas[-1][cell] - ytemperaturas[-ventana_derivada][cell] for cell in range(N_CELLS)]
    else:
        print("Not enough elements in ytemperaturas or x.")
        delta_temperatura = [0.0 for _ in range(N_CELLS)]

# Verifica si las listas tienen elementos antes de calcular la longitud
    if not derivada_temperatura or not ytemperaturas or not ytemperaturas[0]:
        derivada_temperatura = [[] for _ in range(N_CELLS)]
        ytemperaturas = [[] for _ in range(N_CELLS)]

    if ytemperaturas and derivada_temperatura and ytemperaturas[0] and derivada_temperatura[0]:
        delta_temperatura = [ytemperaturas[-1][cell] - ytemperaturas[-ventana_derivada][cell] for cell in range(N_CELLS)]
    else:
        print("Not enough elements in ytemperaturas.")
        delta_temperatura = [0.0 for _ in range(N_CELLS)]
        print("delta_temperatura set to zeros.")
    min_len = min(len(x), len(yvoltajes), len(ycorrientes), len(ytemperaturas[0]), len(derivada_voltaje), len(derivada_corriente), len(derivada_temperatura[0]))
    x = x[-min_len:]
    yvoltajes = yvoltajes[-min_len:]
    ycorrientes = ycorrientes[-min_len:]
    ytemperaturas = [temp[-min_len:] for temp in ytemperaturas]
    derivada_voltaje = derivada_voltaje[-min_len:]
    derivada_corriente = derivada_corriente[-min_len:]
    derivada_temperatura = [temp[-min_len:] for temp in derivada_temperatura]
    time.sleep(1)
print("El programa ha terminado correctamente.")