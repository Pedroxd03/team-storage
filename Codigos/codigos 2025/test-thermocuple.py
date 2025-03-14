import math
import nidaqmx
import time

def thermocupleVoltageToTemperature(Vth):
	R = 1e+5 * Vth / (5 - Vth) / 1000
	print("R = " + str(R))
	# R = 271.26 * exp(-0.038 * T)
	T = - math.log(R / 271.26) / 0.038
	return T

def movingAverage(list, element, n_samples):
    if len(list) == n_samples:
        list.pop(0)
    list.append(element)
    return list, float(sum(list)) / max(len(list), 1)

Vread, Tread = ([],[])

while True:
	with nidaqmx.Task() as task:
		task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0:1")
		measurement = task.read()
		V = measurement[0]
		Vread, Vavg = movingAverage(Vread, V, 5)
		Vth = measurement[1]
		print("Vth = " + str(Vth))
		T = thermocupleVoltageToTemperature(Vth)
		Tread, Tavg = movingAverage(Tread, T, 5)
	print("V = " + str(V) + ", Vavg = " + str(Vavg) + ", T = " + str(T) + ", Tavg = " + str(Tavg))
	time.sleep(1)