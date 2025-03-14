import matplotlib.pyplot as plt
import numpy as np
import time

# Definimos las funciones acotadas
def funcion_1(t):
    return np.sin(t)

def sinc(x):
    if x-8 == 0:
        return 1.0
    else:
        return np.sin(x-8) / (x-8)

def funcion_3(t):
    return np.tanh(t-5)

# Funciones para calcular las derivadas
def derivada(data, x):
    if len(data) >= 3:
        delta_corriente = data[-2] - data[-1]
        delta_tiempo = x[-2] - x[-1]
        derivada = delta_corriente / (delta_tiempo)
        return derivada
    else:
        return 0

x = []
y1 = []
y2 = []
y3 = []
dy1 = []
dy2 = []
dy3 = []

inicio = time.time()

plt.ion()  # interactive mode on
fig, ax = plt.subplots(3, 1)  # 3 rows for functions and their derivatives

line1, = ax[0].plot(x, y1, label='Función 1')
line_d1, = ax[0].plot(x, dy1, label='Derivada 1', linestyle='--')

line2, = ax[1].plot(x, y2, label='Función 2')
line_d2, = ax[1].plot(x, dy2, label='Derivada 2', linestyle='--')

line3, = ax[2].plot(x, y3, label='Función 3')
line_d3, = ax[2].plot(x, dy3, label='Derivada 3', linestyle='--')

for axis in ax:
    axis.legend()
    axis.set_xlabel("tiempo (s)")
    axis.set_ylabel("Valor")

plt.tight_layout()  # To ensure labels don't overlap
plt.show()

while True:
    t = time.time() - inicio

    x.append(t)
    y1.append(funcion_1(t))
    y2.append(sinc(t))
    y3.append(funcion_3(t))

    if len(y1) >= 3:
        dy1.append(derivada(y1, x))
    else:
        dy1.append(0)

    if len(y2) >= 3:
        dy2.append(derivada(y2, x))
    else:
        dy2.append(0)

    if len(y3) >= 3:
        dy3.append(derivada(y3, x))
    else:
        dy3.append(0)


    if len(x) == 300:
        x.pop(0)
        y1.pop(0)
        y2.pop(0)
        y3.pop(0)
        dy1.pop(0)
        dy2.pop(0)
        dy3.pop(0)

    line1.set_data(x, y1)
    line_d1.set_data(x, dy1)
    line2.set_data(x, y2)
    line_d2.set_data(x, dy2)
    line3.set_data(x, y3)
    line_d3.set_data(x, dy3)

    for axis in ax:
        axis.relim()
        axis.autoscale_view()

    plt.pause(1)
