import pyvisa
import time
import os
import nidaqmx
import csv
import math
import matplotlib.pyplot as plt
from collections import deque
from datetime import datetime



def thermocoupleVoltageToTemperature(Vth):
    if Vth <= 0 or Vth >= 5:
        raise ValueError(f"Voltaje del termopar fuera del rango esperado: {Vth}")        
    R = 100 * Vth / (5 - Vth)    
    if R <= 0:
        raise ValueError(f"Resistencia calculada no válida: {R}")
    if R / 100e3 <= 0:
        raise ValueError(f"Argumento de log no válido: {R / 100e3}")        
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

N_CELLS = 1

if not os.path.exists("logs"):
    os.makedirs("logs")

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
csv_filename = os.path.join("logs", f"battery_HPPC_{current_datetime}.csv")
graph_filename = os.path.join("logs", f"battery_HPPC_test_{current_datetime}.png")

x = []
yvoltajes = []
ycorrientes = []
ytemperaturas = []

# Parameters
Vmax  = 4.2 
Vmmax = 4.4
Vmin  = 3.0
Imax_ch = 1.3
Imax = 1.3
Imin = 0.3
Imax_disch = 2.6
Tmax = 80
window_size   = 50  
sampling_time = 0.001


mode = 0  #0
t0   = time.time()

rm = pyvisa.ResourceManager()
print("Resources detected\n{}".format(rm.list_resources()))

supply = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C224204541::INSTR')
load   = rm.open_resource('USB0::0x1AB1::0x0E11::DL3C213000056::INSTR')
supply.write(':OUTP ON')
supply.write(":APPL CH3, 5, 1")
supply.write(':OUTP CH3, ON')

plt.ioff()
fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
line_voltage, = ax1.plot([], [], label="Voltage (V)", color='b')
line_current, = ax2.plot([], [], label="Current (A)", color='g')

ax1.set_ylabel("Voltage (V)", color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax2.set_xlabel("Time (seconds)")
ax2.set_ylabel("Current (A)", color='g')
ax2.tick_params(axis='y', labelcolor='g')
ax1.legend(loc='upper left')
ax2.legend(loc='upper left')

# Historial de las últimas mediciones para la media móvil
voltages_window     = deque(maxlen=window_size)
currents_window     = deque(maxlen=window_size)
temperatures_window = deque(maxlen=window_size)

def save_graph():
    plt.savefig(graph_filename)
    print(f"Graph saved as {graph_filename}")

def run_battery_test():
    global mode
    with open(csv_filename, "w", newline="") as file:
        csv_writer = csv.writer(file)
        header = ["Timestamp", "Voltage", "Current", "Temperature", "Avg Voltage", "Avg Current", "Avg Temperature"]
        csv_writer.writerow(header)
        try:
            while True:
                if mode == 0:
                    print("Reposo por 1 minuto...")
                    supply.write(':OUTP CH2, OFF')
                    load.write(':SOUR:INP:STAT OFF')
                    start_time = time.time()
                    while time.time() - start_time < 60:
                        v, c, temp = medir_voltaje_corriente()
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return 
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)                    
                        time.sleep(sampling_time)
                        
                    mode = 1

                elif mode == 1:
                    Imax_ch = Imax
                    print("Cargando en modo CC-CV...")
                    supply.write(":APPL CH2," + str(Vmax) + "," + str(Imax_ch))  # Set voltage to 4.2V and current to 1.3A
                    supply.write(':OUTP CH2, ON')    
                    time.sleep(1)            
                    start_time = time.time()
                    while True:
                        v, c, temp = medir_voltaje_corriente()                    
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t    = time.time() - t0
                        Vset = float(supply.query(':MEAS:VOLT? CH2'))
                        c    = float(supply.query(':MEAS:CURR? CH2')) 
                        R    = (Vset - v)/ c  
                        print('voltage:', v, 'current:', c, 'Vset:', Vset)
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                        if check_temperature_limit(temp):
                            print("Turning off equipment due to temperature limit.")
                            supply.write(':OUTP CH2, OFF')
                            mode = 0
                            break  
                        if Vset >= Vmax:                        
                     
                            Vlim = Vmax + R*c
                            supply.write(":APPL CH2," + str(Vlim))
                            #print('Voltaje de la batería:', v, 'Voltaje de la fuente:', Vset, 'Corriente:', c, 'Vlim:', Vlim)              
                        if c < Imin:
                            supply.write(':OUTP CH2, OFF')
                            mode = 2
                            break                 
                        time.sleep(sampling_time)
                        
                    mode = 2
                elif mode == 2:
                    print("Reposo por 40 minutos...")
                    supply.write(':OUTP CH2, OFF')
                    load.write(':SOUR:INP:STAT OFF')
                    start_time = time.time()
                    while time.time() - start_time < 2400
                    
                    
                    
                    :  #2400
                        v, c, temp = medir_voltaje_corriente()
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                       
                        time.sleep(sampling_time)

                        
                    mode = 3

                elif mode == 3:
                    print("Descarga a 2.6 A por 10 segundos...")
                    load.write(':SOUR:CURR 2.6')
                    load.write(':SOUR:INP:STAT ON')
                    #time.sleep(1)
                    c = -float(load.query(':MEAS:CURR?'))
                    start_time = time.time()
                    while time.time() - start_time < 10:
                        v, c, temp = medir_voltaje_corriente()
                        #print('Corriente:', c, 'Voltaje:', v)
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                        time.sleep(sampling_time)

                    load.write(':SOUR:INP:STAT OFF')
                    mode = 4

                elif mode == 4:
                    print("Reposo por 40 segundos...")
                    supply.write(':OUTP CH2, OFF')
                    load.write(':SOUR:INP:STAT OFF')
                    start_time = time.time()
                    while time.time() - start_time < 40:
                        v, c, temp = medir_voltaje_corriente()
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                        time.sleep(sampling_time)

                    mode = 5

                elif mode == 5:
                    print("Cargando a 2.6 A durante 10 segundos...")
                    supply.write(':APPL CH2, 4.2, 2.6')
                    supply.write(':OUTP CH2, ON')
                    time.sleep(0.6)
                    start_time = time.time()
                    c = float(supply.query(':MEAS:CURR?'))
                    while time.time() - start_time < 10:
                        v, c, temp = medir_voltaje_corriente()
                        print('Corriente:', c, 'Voltaje:', v)
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                        time.sleep(sampling_time)

                    supply.write(':OUTP CH2, OFF')
                    mode = 6
                elif mode == 6:
                    print("Reposo por 3 minutos...")
                    supply.write(':OUTP CH2, OFF')
                    load.write(':SOUR:INP:STAT OFF')
                    start_time = time.time()
                    while time.time() - start_time < 180:
                        v, c, temp = medir_voltaje_corriente()
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                        time.sleep(sampling_time)

                    mode = 7
                elif mode == 7:
                    print("Descargando a 2.6 A durante 6 minutos...")
                    load.write(':SOUR:CURR 2.6')
                    load.write(':SOUR:INP:STAT ON')
                    c = -float(load.query(':MEAS:CURR?'))
                    start_time = time.time()
                    while time.time() - start_time < 360:
                        v, c, temp = medir_voltaje_corriente()
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        t = time.time() - t0
                        actualizar_grafica(t, v, c)
                        escribir_datos_csv(csv_writer, v, c, temp, file)
                        time.sleep(sampling_time)

                    load.write(':SOUR:INP:STAT OFF')
                    mode = 8
                elif mode == 8:
                    with nidaqmx.Task() as task:
                        task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0:1", terminal_config=nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)
                        measurement = task.read()
                        v = measurement[0]
                        print("Voltage: ", v, "Corriente: ", c)
                        if v < 3.0:
                            print("Voltaje bajo detectado, terminando prueba.")
                            supply.write(':OUTP CH2, OFF')
                            load.write(':SOUR:INP:STAT OFF')
                            return
                        else:
                            mode = 2
                
        except KeyboardInterrupt:
            print("Program stopped by user.")
            mode = 0  # Cambia a modo 0 para asegurar que los equipos se apaguen
            supply.write(':OUTP CH3, OFF')  # Apaga la fuente
            supply.write(':OUTP CH2, OFF')  # Apaga la fuente
            load.write(':SOUR:INP:STAT OFF')  # Apaga la carga

            ax1.plot(x, yvoltajes, 'b-')
            ax1.set_ylabel('Voltage (V)')
            ax1.tick_params(axis='y', labelcolor='b')
            ax1.legend(loc='upper left')
    
            ax2.plot(x, ycorrientes, 'g-')
            ax2.set_xlabel('Time (seconds)')
            ax2.set_ylabel('Current (A)')
            ax2.tick_params(axis='y', labelcolor='g')
            ax2.legend(loc='upper left')
            ax2.set_ylim(min(ycorrientes) - 0.5, max(ycorrientes) + 0.5)

            plt.show()

            
        finally:
            save_graph()
            print("Exiting program.")                    

def escribir_datos_csv(csv_writer, v, c, temp, csv_file):
    voltages_window.append(v)
    currents_window.append(c)
    temperatures_window.append(temp)

    avg_voltage     = moving_average(voltages_window, window_size)
    avg_current     = moving_average(currents_window, window_size)
    avg_temperature = moving_average(temperatures_window, window_size)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    csv_writer.writerow([timestamp,v, c, temp, avg_voltage, avg_current, avg_temperature])
    csv_file.flush()

def medir_voltaje_corriente(sampling_rate=1000):
    try:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0:1")
            task.timing.cfg_samp_clk_timing(
                sampling_rate, 
                samps_per_chan=1000,
                sample_mode=nidaqmx.constants.AcquisitionType.FINITE
            )
            measurement = task.read()
            v = measurement[0] 
            temp = thermocoupleVoltageToTemperature(measurement[1]) 
            if mode in [3, 7]:
                c = -float(load.query(':MEAS:CURR?'))
            else:
                c = float(supply.query(':MEAS:CURR? CH2'))            
            return v, c, temp
    except nidaqmx.DaqError as e:
        print(f"Error en la adquisición de datos: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None, None, None

def actualizar_grafica(t, v, c):
    voltages_window.append(v)
    currents_window.append(c)
    
    v_avg = moving_average(voltages_window, window_size)
    c_avg = moving_average(currents_window, window_size)
    
    x.append(t)
    yvoltajes.append(v)
    ycorrientes.append(c)

    ax1.clear()
    ax2.clear()
    
    ax1.plot(x, yvoltajes, 'b-', label='Voltage (V)')
    ax1.set_ylabel('Voltage (V)')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.legend(loc='upper left')
    
    ax2.plot(x, ycorrientes, 'g-', label='Current (A)')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Current (A)')
    ax2.tick_params(axis='y', labelcolor='g')
    ax2.legend(loc='upper left')
    ax2.set_ylim(min(ycorrientes) - 0.5, max(ycorrientes) + 0.5)
    
    plt.pause(sampling_time)

run_battery_test()

    
