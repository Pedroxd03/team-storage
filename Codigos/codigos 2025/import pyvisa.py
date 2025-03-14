import pyvisa
from time import sleep # for delays
import os # for datalogging

rm = pyvisa.ResourceManager()
# List all connected resources
print("Resources detected\n{}\n".format(rm.list_resources()))