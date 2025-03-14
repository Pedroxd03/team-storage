import pyvisa
import time
import os
import nidaqmx
import csv
import math
import matplotlib.pyplot as plt
from datetime import datetime
#from nidaqmx.constants import (TerminalConfiguration)

def movingAverage(list, element, n_samples):
    if len(list) == n_samples:
        list.pop(0)
    list.append(element)
    return list, float(sum(list)) / max(len(list), 1)

def thermocoupleVoltageToTemperature(Vth):
    R = 1e+5 * Vth / (5 - Vth) / 1000
    # R = 271.26 * exp(-0.038 * T)
    T = - math.log(R / 271.26) / 0.038
    return T

# LOGGING
N_CELLS = 3

# Crear la carpeta "logs" si no existe
if not os.path.exists("logs"):
    os.makedirs("logs")

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = os.path.join("logs", f"battery_data_sustrend_III_{current_datetime}.csv")

# Crear un nuevo archivo CSV con el nombre basado en la fecha y hora
with open(csv_filename, "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    header = ["Timestamp"]
    header.extend([f"Cell {i+1} Voltage" for i in range(N_CELLS)])
    header.extend([f"Cell {i+1} Current" for i in range(N_CELLS)])
    header.extend([f"Cell {i+1} Temp" for i in range(N_CELLS)])
    csv_writer.writerow(header)

x = []
yvoltajes = []
ytemperaturas = []
ycorrientes = []
derivada_voltaje = []
derivada_corriente = []
derivada_temperatura = []


# Initialize line objects
lines = []

# Parameters
N_CYCLES = 4
R = 0.027
Vmax = 4.8
Vmin = 2
Imax_ch = 1.0
#Imax_load = 1.0
Imin = 0.3
Imax_dh = 0.5
dVmin = 0.00001
Vmmin = 1.0
Vmmax = 5.0
Tmax = 80

# Initialization
n = 1
mode =-1
count = 0
Vprev = 0
Vread, Iread, dVread, Tread = ([],[],[],[])
Rread=([])
t0 = time.time()

if mode != -1:
    plt.ion()
    fig, ax = plt.subplots(3, 2, figsize=(10, 12))  
    plt.xlabel("Time (s)")

    ax[0][0].set_title('Voltage')
    ax[0][1].set_title('Derivative of Voltage')
    ax[1][0].set_title('Current')
    ax[1][1].set_title('Derivative of Current')
    ax[2][0].set_title('Temperature')
    ax[2][1].set_title('Derivative of Temperature')

    for i in range(3):
        line, = ax[i][0].plot(x, [0]*len(x))
        lines.append(line)

    for i in range(3):
        line, = ax[i][1].plot(x, [0]*len(x))
        lines.append(line)

    for row in ax:
        for axis in row:
            axis.set_ylabel("Value")


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
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0:3")
        measurement = task.read()
        V = measurement[0]
        V2 = measurement[2]
        Vread, Vavg = movingAverage(Vread, V, 5)
        Vread2, Vavg2 = movingAverage(Vread, V2, 5)
        T = thermocoupleVoltageToTemperature(measurement[1])
        Tread, Tavg = movingAverage(Tread, T, 5)
        dV = Vavg - Vprev
        dVread, dVavg = movingAverage(dVread, dV, 20)
        Vprev = Vavg
        
    
    if Tavg > Tmax or Vavg < Vmmin:
        print("Dangerous temperature or voltage value!!!!")
        print("T = " + str(T) + ", V = " + str(Vavg))
        mode = 0

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
        if Vavg > Vmax:
            #R = (Vset - V)/Iset
            # print("R = " + str((Vset - V)/Iavg))     
            Vlim = Vmax + R * Iavg
            if R > 0:
                supply.write(":APPL CH2," + str(Vlim) + "," + str(Imax_ch))
                # print("set Vlim = " + str(Vlim))
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
        if abs(dVavg) < dVmin:
            count = count + 1
            if count == 5:
                mode = 3
                load.write(":SOUR:CURR:LEV:IMM " + str(Imax_dh))
                load.write(':SOUR:INP:STAT ON')
                count = 0
            # cerrar relé carga
        else:
            count = 0

    elif mode == 3:
        print("Mode 3: battery discharge")
        I = -float(load.query(":MEASURE:CURRENT?"))
        Iread, Iavg = movingAverage(Iread, I, 5)

        if Vavg < Vmin:
            mode = 4
            load.write(':SOUR:INP:STAT OFF')
            # abrir relé carga

    elif mode == 4:
        print("Mode 4: recovery")
        I = 0
        Iavg = 0
        if abs(dVavg) < dVmin:
            count = count + 1
            if count >= 5:
                # print("-----------------------------------")
                # i = i + 1
                # print('Cycle ' + str(i) + " finished!")
                # if i == N_CYCLES:
                #     print("Done with success!")
                #     break
                mode = 1
                supply.write(':OUTP CH2, ON')
                supply.write(":APPL CH2," + str(Vmmax) + "," + str(Imax_ch))
                count = 0
        else:
            count = 0
    elif mode == -1:

        Vset = float(supply.query(':MEAS:VOLT? CH2'))
                     
        print("Mode -1: Just Measurement")
        print("V = " + str(V) + ", Vavg = " + str(Vavg) + ", T = " + str(T) + ", Tavg = " + str(Tavg)  )
        I = float(supply.query(":MEASURE:CURRENT?"))
        Iread, Iavg = movingAverage(Iread, I, 5)
      
        #print((Vset-Vavg)/I )
        print("R = " + str((Vset-(V+V2) )/Iavg))  
      

       
        time.sleep(1)
        continue

    else:
        print("No mode ", mode)
        break

    print("Cycle number: ", n)
    print("V = " + str(V) + ", Vavg = " + str(Vavg) + ", I = " + str(I) + ", Iavg = " + str(Iavg) + ", T = " + str(T) + ", Tavg = " + str(Tavg))

    # Generate random values for the measurements
    timestamp = time.time()
    voltage = [V]
    current = [I]
    temperature = [T]

    # Format the timestamp as a readable date and time string
    formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    # Save the data in the CSV file
    with open(csv_filename, "a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([formatted_timestamp] + voltage + current + temperature)

    x.append(time.time() - t0)
    yvoltajes.append(V)
    ycorrientes.append(I)
    ytemperaturas.append(Tavg)

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
        derivada_v = delta_voltaje / (delta_tiempo)
        derivada_voltaje.append(derivada_v*10)
    else:
        derivada_voltaje.append(0)

    if len(ytemperaturas) >= ventana_derivada and len(x) >= ventana_derivada:
        delta_temperatura = ytemperaturas[-1] - ytemperaturas[-ventana_derivada]
        delta_tiempo = x[-1] - x[-ventana_derivada]
        derivada_t = delta_temperatura / (delta_tiempo)
        derivada_temperatura.append(derivada_t*10)
    else:
        derivada_temperatura.append(0)

    # Update the plots
    lines[0].set_data(x, yvoltajes)
    lines[1].set_data(x, ycorrientes)
    lines[2].set_data(x, ytemperaturas)
    lines[3].set_data(x, derivada_voltaje)
    lines[4].set_data(x, derivada_corriente)
    lines[5].set_data(x, derivada_temperatura)

    for axis_row in ax:
        for axis in axis_row:
            axis.relim()
            axis.autoscale_view()

    """
    if len(x) == 10:
        x.pop(0)
        yvoltajes.pop(0)
        ycorrientes.pop(0)
        ytemperaturas.pop(0)
        derivada_voltaje.pop(0)
        derivada_corriente.pop(0)
        derivada_temperatura.pop(0)"""

    plt.pause(0.001)
    time.sleep(1)
