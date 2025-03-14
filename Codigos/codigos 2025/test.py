import pyvisa


rm = pyvisa.ResourceManager()
print("Resources detected\n{}".format(rm.list_resources()))