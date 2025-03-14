import pyvisa
import time 
import os
import nidaqmx
import csv
#from nidaqmx.constants import (TerminalConfiguration)
from datetime import datetime
import math

def movingAverage(list, element, n_samples):
    if len(list) == n_samples:
        list.pop(0)
    list.append(element)
    return list, float(sum(list)) / max(len(list), 1)

def thermocupleVoltageToTemperature(Vth):
	R = 1e+5 * Vth / (5 - Vth) / 1000
	# R = 271.26 * exp(-0.038 * T)
	T = - math.log(R / 271.26) / 0.038
	return T

# LOGGING
N_CELLS = 1  # Cambiar con el número real de celdas

# Crear la carpeta "logs" si no existe
if not os.path.exists("logs"):
    print("que pasa")
    os.makedirs("logs")

# Obtener la ruta completa del archivo CSV
current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = os.path.join("logs", f"battery_data_{current_datetime}.csv")

# Crear un nuevo archivo CSV con el nombre basado en la fecha y hora
with open(csv_filename, "w", newline="") as csv_file:
    csv_writer = csv.writer(csv_file)
    header = ["Timestamp"]
    header.extend([f"Cell {i+1} Voltage" for i in range(N_CELLS)])
    header.extend([f"Cell {i+1} Current" for i in range(N_CELLS)])
    header.extend([f"Cell {i+1} Temp" for i in range(N_CELLS)])
    csv_writer.writerow(header)

# Parameters
N_CYCLES = 5
R = 0.027
Vmax = 4.2
Vmin = 3.0
Imin = 0.05
Imax_ch = 2.6
Imax_dh = 4*Imax_ch
dVmin = 0.00001
Vmmax = 4.5
Tmax = 80

# Initialization
i = 0
mode = 0
count = 0
Vprev = 0

Vread, Iread, dVread, Tread = ([],[],[],[])
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
elif mode == 3:
    load.write(":SOUR:CURR:LEV:IMM " + str(Imax_dh))
    load.write(':SOUR:INP:STAT ON')

while True:
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0:1")
        measurement = task.read()
        V = measurement[0]
        Vread, Vavg = movingAverage(Vread, V, 5)
        T = thermocupleVoltageToTemperature(measurement[1])
        Tread, Tavg = movingAverage(Tread, T, 5)
        dV = Vavg - Vprev
        dVread, dVavg = movingAverage(dVread, dV, 20)
        Vprev = Vavg
        if Tavg > Tmax:
            print("Dangerous temperature value!!!!")
            mode = 0

    if mode == 0:
        supply.write(':OUTP CH2, OFF')
        load.write(':SOUR:INP:STAT OFF')
        print("All hardware is shutdown!")
        break
    
    elif mode == 1:
        print("mode 1: battery charge")
        Vset = float(supply.query(':MEAS:VOLT? CH2'))
        I = float(supply.query(':MEAS:CURR? CH2'))
        Iread, Iavg = movingAverage(Iread, I, 5)
        if Vavg > Vmax:
          #R = (Vset - V)/Iset
          # print("R = " + str((Vset - V)/Iavg))
          Vlim = Vmax + R*Iavg
          if R > 0:
            supply.write(":APPL CH2," + str(Vlim) + "," + str(Imax_ch))
            # print("set Vlim = " + str(Vlim))
        if Iavg < Imin:
            count = count + 1
            if count == 5:
                if i == 0:
                    print("Cycle 1 start!")
                else:
                    print('Cycle ' + str(i) + " finished!")
                if i == N_CYCLES:
                    print("Done with success!")
                    mode = 0
                    break
                i = i + 1
                mode = 2 # relajación
                print("paso a modo 2")
                supply.write(':OUTP CH2, OFF')
                count = 0
                # aquí falta abrir el relé de la fuente
        else:
            count = 0

    elif mode == 2:
        print("mode 2: relaxation")
        I = 0
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
        print("mode 3: battery discharge")
        I = -float(load.query(":MEASURE:CURRENT?"))
        Iread, Iavg = movingAverage(Iread, I, 5)

        if Vavg < Vmin:
            mode = 4
            load.write(':SOUR:INP:STAT OFF')
            # abrir relé carga

    elif mode == 4:
        print("mode 4: recovery")
        I = 0
        if abs(dVavg) < dVmin:
            count = count + 1
            if count == 5:
                # print("-----------------------------------")
                # i = i + 1
                # print('Cycle ' + str(i) + " finished!")
                # if i == N_CYCLES:
                #     print("Done with success!")
                #     break
                mode = 1
                supply.write(':OUTP CH2, ON')
                supply.write(":APPL CH2," + str(Vmmax) + "," + str(Imax_ch))
                # aquí falta cerrar el relé de la fuente
        else:
            count = 0

    else:
        print("No mode ", mode)
        break
    
    print("Cycle number: ", i)
    print("V = " + str(V) + ", Vavg = " + str(Vavg) + ", I = " + str(I) + ", Iavg = " + str(Iavg) + ", T = " + str(T) + ", Tavg = " + str(Tavg))

    # Generar valores aleatorios para las mediciones
    timestamp = time.time()
    voltage = [V]
    current = [I]
    temperature = [T]

    # Formatear el timestamp como una cadena de fecha y hora legible
    formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    # Guardar los datos en el archivo CSV
    with open(csv_filename, "a", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([formatted_timestamp]+ voltage + current + temperature)
    time.sleep(1)