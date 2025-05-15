""" Single SPAD ODMR script """

#General imports
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime

#Device stuff
from laboneq.simple import *
from laboneq.controller.util import *

#Local modules
from single_SPAD_reader import get_frame

#Settings
settings = {
    "save_folder": "/home/dl-lab-pc3/Dylan/",
    "min_freq": 2.85e9,
    "max_freq": 2.89e9,
    "num_measurements": 100,
    "num_sweeps": 1,
    "laser power": 0,
    "sample": "test",
    "notes": "test",
    "measurement_type": "single_ODMR"
}

save_folder = settings["save_folder"]
num_measurements = settings["num_measurements"]
min_freq = settings["min_freq"]
max_freq = settings["max_freq"]
num_sweeps = settings["num_sweeps"]


current_time = datetime.now()
timestamp_string = str(round(current_time.timestamp()))
savePath = save_folder + "Single_SPAD_ODMR_scan" + timestamp_string #Without file extension yet
settings["savePath"] = savePath
settings["Start time"] = str(current_time)

#Initialize AWG stuff
# Define the DeviceSetup from descriptor - 
# Additionally include information on the dataserver used to connect to the instruments 
server_host = "localhost" # <-- INSERT YOUR SERVER HOST HERE

descriptor = """
instruments:
  SHFSG:
    - address: DEV12120
      uid: device_shfsg
      interface: 1GbE
    
connections:     
  device_shfsg:
    - iq_signal: q0/drive_line
      ports: SGCHANNELS/0/OUTPUT
    - iq_signal: q0/drive_line_ef
      ports: SGCHANNELS/0/OUTPUT
    - iq_signal: q1/drive_line
      ports: SGCHANNELS/1/OUTPUT
    - iq_signal: q1/drive_line_ef
      ports: SGCHANNELS/1/OUTPUT
    - iq_signal: q2/drive_line
      ports: SGCHANNELS/2/OUTPUT
    - iq_signal: q2/drive_line_ef
      ports: SGCHANNELS/2/OUTPUT
    - iq_signal: q3/drive_line
      ports: SGCHANNELS/3/OUTPUT
    - iq_signal: q3/drive_line_ef
      ports: SGCHANNELS/3/OUTPUT
    - iq_signal: q4/drive_line
      ports: SGCHANNELS/4/OUTPUT
    - iq_signal: q4/drive_line_ef
      ports: SGCHANNELS/4/OUTPUT
    - iq_signal: q5/drive_line
      ports: SGCHANNELS/5/OUTPUT
    - iq_signal: q5/drive_line_ef
      ports: SGCHANNELS/5/OUTPUT
"""

my_setup = DeviceSetup.from_descriptor(
    yaml_text=descriptor,
    server_host="localhost",
    server_port='8004',
    setup_name='Setup_Name',
)


# define baseline signal calibration for a list of qubits
def define_calibration():
    
    calib = Calibration()
    
    calib[f"/logical_signal_groups/q1/drive_line"] = \
        SignalCalibration(
            oscillator = Oscillator(
                frequency =7e7,
                modulation_type=ModulationType.HARDWARE,
            ),
            local_oscillator = Oscillator(
                frequency=2.8e9,                             #center frequency Hz
            ),
            range = 0,                                      #Strength in dBm
        )     
    
    return calib
define_calibration()
my_setup.set_calibration(define_calibration())
my_session = Session(device_setup=my_setup)
#my_session.connect(do_emulation=use_emulation)
my_session.connect()

channel_index = 1          #which channel am I using   #1 is 2
output_range= 0            #leave at 0 = limit of small amp, large amp has 7 dbm but check for large amp to make sure
center_frequency = 2.8e9
rflf_path= 1
osc1_frequency= 7e7

# Configurational
instrument_serial = my_setup.instruments[0].address
device = my_session.devices[instrument_serial]

gains_cw              = (0.0, 0.95, 0.95, 0.0) #unitless

# Configure RF output
device.sgchannels[channel_index].configure_channel(enable = True, output_range = output_range, 
                                                center_frequency = center_frequency, rf_path = rflf_path)



# Configure digital sine generator
device.sgchannels[channel_index].configure_sine_generation(enable = True, 
                                                        osc_index = 0, osc_frequency = osc1_frequency, 
                                                        phase = 0, gains = gains_cw)




#Prepare variables for measurement
x = np.linspace(min_freq, max_freq, num_measurements)
osc_freq = x - center_frequency
PL = np.zeros(num_measurements)
PL_norm = np.zeros(num_measurements)

#Main loop
for im in range(num_measurements):
    for s in range(num_sweeps):
        osc1_frequency = osc_freq[im]
        # Configure digital sine generator
        device.sgchannels[channel_index].configure_sine_generation(enable = True,
                                                                osc_index = 0,
                                                                osc_frequency = osc1_frequency, 
                                                                phase = 0,
                                                                gains = gains_cw) # or use AWG.set_rf_frequency(x[n])

        PL[im] += get_frame() / num_sweeps
PL_norm[im] = PL[im] / max(PL[im])

#Save results
settings["End time"] = str(datetime.now())
np.savetxt(savePath + ".txt", PL)
with open(savePath + ".json", 'w') as f: 
    json.dump(settings, f, indent="")

#Plot results
plt.figure()
plt.plot(x*1e-9, PL_norm)
plt.xlabel("Frequency (GHz)")
plt.ylabel("Intensity (normalized)")
plt.show()