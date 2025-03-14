import pyvisa
import nidaqmx
import time
import matplotlib.pyplot as plt


rm      = pyvisa.ResourceManager()
fuente  = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C224204541::INSTR') 
carga   = rm.open_resource('USB0::0x1AB1::0x0E11::DL3C213000056::INSTR')

canal             = 2 
corriente_deseada = 2.6  
voltaje_deseado   = 4.2  
duracion_pulso    = 10  
duracion_reposo   = 30  
fuente.write(f'INST:NSEL {canal}')
fuente.write(f'APPL CH{canal},{voltaje_deseado},{corriente_deseada}')

carga.write('FUNC CURR')

carga.write('INPUT OFF')  
task = nidaqmx.Task()
task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0", terminal_config=nidaqmx.constants.TerminalConfiguration.DIFFERENTIAL)

tiempo_total = 0
frecuencia_muestreo = 100 
tiempos    = []
voltajes   = []
corrientes = []
voltaje_bateria = []

print("Pulso de carga: aplicando 2.6 A durante 10 segundos...")
fuente.write(f'OUTP CH{canal},ON')
start_time = time.time()
try:
    while time.time() - start_time < duracion_pulso:
        tiempo_actual = time.time() - start_time + tiempo_total
        voltaje   = float(fuente.query(f'MEAS:VOLT? CH{canal}'))
        corriente = float(fuente.query(f'MEAS:CURR? CH{canal}'))
        voltaje_bateria_actual = task.read()
        #print('Vbattery:', voltaje_bateria_actual)
        #print('Corriente:', corriente)
        tiempos.append(tiempo_actual)
        voltajes.append(voltaje)
        corrientes.append(corriente)
        voltaje_bateria.append(voltaje_bateria_actual)
    tiempo_total+= duracion_pulso    
    fuente.write(f'OUTP CH{canal},OFF')
    print("Pulso de carga finalizado. Canal apagado.")
    print(f"Intervalo de reposo de {duracion_reposo} segundos...")
    start_time = time.time()
    while time.time() - start_time < duracion_reposo:
        tiempo_actual = time.time() - start_time + tiempo_total
        voltaje_bateria_actual = task.read()
        #print('Vbattery:', voltaje_bateria_actual)
        corriente = float(fuente.query(f'MEAS:CURR? CH{canal}'))   
        tiempos.append(tiempo_actual)
        voltajes.append(voltaje)
        corrientes.append(corriente)     
        #print('Corriente:', corriente)
        voltaje_bateria.append(voltaje_bateria_actual)
    tiempo_total += duracion_reposo
    #print('Vbatt:', voltaje_bateria_actual)
    print("Pulso de descarga: aplicando 2.6 A durante 10 segundos...")
    carga.write('INPUT ON')
    carga.write(f'CURR {corriente_deseada}')
    start_time = time.time()
    while time.time() - start_time < duracion_pulso:
        tiempo_actual = time.time() - start_time + tiempo_total
        corriente = -float(carga.query('MEAS:CURR?'))
        voltaje_bateria_actual = task.read()
        #print('Vbatt:', voltaje_bateria_actual)
        tiempos.append(tiempo_actual)
        voltajes.append(voltaje)
        corrientes.append(corriente)
        voltaje_bateria.append(voltaje_bateria_actual)
    tiempo_total +=duracion_pulso    
    carga.write('INPUT OFF')
    print("Pulso de descarga finalizado. Carga apagada.")
    print(f"Intervalo de reposo de {duracion_reposo} segundos...")
finally:
    fuente.write(f'OUTP CH{canal},OFF')
    carga.write('INPUT OFF')
    print("Prueba finalizada, equipos apagados.")
    fuente.close()
    carga.close()
    rm.close()
    task.stop()
    task.close()
plt.figure(figsize=(12, 8))
plt.subplot(3, 1, 1)
plt.plot(tiempos, voltajes, label='Voltaje de la fuente (V)', color='b')
plt.xlabel('Tiempo (s)')
plt.ylabel('Voltaje (V)')
plt.title('Voltaje durante la prueba')
plt.grid(True)
plt.legend()

plt.subplot(3, 1, 2)
plt.plot(tiempos, corrientes, label='Corriente (A)', color='r')
plt.xlabel('Tiempo (s)')
plt.ylabel('Corriente (A)')
plt.title('Corriente durante la prueba')
plt.grid(True)
plt.legend()

plt.subplot(3, 1, 3)
plt.plot(tiempos, voltaje_bateria, label='Voltaje de la batería (V)', color='g')
plt.xlabel('Tiempo (s)')
plt.ylabel('Voltaje (V)')
plt.title('Voltaje de la batería durante la prueba')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
