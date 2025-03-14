import nidaqmx
task = nidaqmx.Task()
task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0")
V = task.read()
print(V)
task.do_channels.add_do_chan("cDAQ1Mod1/do0")
task.start()
value = True
task.write(value)
task.stop
task.close()