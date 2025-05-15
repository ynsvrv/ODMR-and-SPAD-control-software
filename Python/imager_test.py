""" Test script for imager """
import numpy as np
import matplotlib.pyplot as plt
from rtcs.devices.flir.camera import SpinnakerCamera

serial_number = "23468841" #Serial number to connect with camera
#serial_number = "22301144"

camera = SpinnakerCamera(serial_number)
camera.open()
camera.start_acquisition(4, 0.2e6)
data = camera.get_image()
camera.stop_acquisition()
camera.close()

plt.figure()
plt.imshow(data)
plt.colorbar()
plt.show()