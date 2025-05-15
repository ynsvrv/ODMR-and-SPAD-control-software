from __future__ import print_function
#import psutil
from IPython.display import display, clear_output
#%matplotlib inline
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
#import zhinst.utils
#import Pyro5.api
#import TimeTagger as TT
# convenience import for all LabOne Q software functionality
from laboneq.simple import *
from laboneq.controller.util import *
from time import sleep
import TimeTagger
from scipy.optimize import curve_fit
import time
from datetime import date, datetime
import scipy as scipy
#from scipy import optimize
import os
#from pipython import GCSDevice, pitools
#import argparse
import sys
#import h5py
#logging.disable(logging.DEBUG)
#from rtcs.measurements.esr_scan import single_dip_esr_fit as single_fit
#from rtcs.measurements.esr_scan import triple_dip_esr_fit as triple_fit
import json

plt.rcParams.update({'font.size': 24,})

def main() -> int:
    settings = {
        "save_folder": "/home/dl-lab-pc3/measurements/",
        "z_steps": 140,
        "dwell_time": 2e11, #picoseconds
        "x0": 0.0,
        "y0": 0.0,
        "z1": 4.520,
        "z2": 4.660,
        "laser_power": 2.9, #mW
        "sample": "Bonded EDP (100)"
    }

    settings_file = None

    if(settings_file != None):
        #Load settings from specified json file
        with open(settings_file, 'r') as f:
            settings = json.load(f)

    save_folder = settings["save_folder"]
    z_steps = settings["z_steps"]
    dwell_time = settings["dwell_time"]
    z1 = settings["z1"]
    z2 = settings["z2"]
    x0 = settings["x0"]
    y0 = settings["y0"]

    #Time estimation
    total_time = z_steps * (dwell_time*1e-12 + 0.2) #0.2 seconds is the overhead time for movement of the piezo stack
    print("Estimated time: " + str(total_time/3600) + " hours")
    estimated_finish = time.time() + total_time
    local_time = time.ctime(estimated_finish)
    print("Will finish at: ", local_time)


    # Saving the data:
    current_time = datetime.now()
    timestamp_string = str(round(current_time.timestamp()))
    savePath = save_folder + "z_scan_" + timestamp_string #Without file extension yet
    settings["savePath"] = savePath
    settings["Start time"] = str(current_time)
    #settings_file_path = settings["save_folder"] + "2D ODMR scan settings" + timestamp + ".json"

    # Create a TimeTagger instance to control your hardware
    tagger = TimeTagger.createTimeTagger()
    countrate = TimeTagger.Countrate(tagger=tagger, channels=[1])   # 1 is 1


    #Setup piezo-stack
    from rtcs.devices.physikinstrumente.pi_E873_controller import Pistage_controller
    pi_x = Pistage_controller("type=tcp;host=192.168.20.21;port=50000") #x axis
    pi_y = Pistage_controller("type=tcp;host=192.168.20.22;port=50000") #x axis
    pi_z = Pistage_controller("type=tcp;host=192.168.20.23;port=50000") #x axis

    pi_x.open()
    pi_y.open()

    #Move to the right spot
    pi_x.move(x0)
    pi_y.move(y0)
    time.sleep(1)

    pi_x.close()
    pi_y.close()

    pi_z.open()

    #Set velocities of piezo stack
    pi_z.send_command("VEL 1 5")

    zmove = np.linspace(z1, z2, z_steps)
    PL = np.zeros(z_steps)

    for iz in range(z_steps):
        pi_z.move(zmove[iz])
        pi_z.wait_on_target()
        countrate.startFor(dwell_time)
        countrate.waitUntilFinished()
        rate = countrate.getData()[0]
        PL[iz] = rate

    np.save(savePath + ".npy", PL)
    np.savetxt(savePath + ".txt", PL)

    settings["End time"] = str(datetime.now())

    #Save settings in json file
    with open(savePath + ".json", 'w') as f: 
        json.dump(settings, f, indent="")
    
    print("Measurement complete!\nFile saved as: " + savePath + ".npy")

    pi_z.close()


if __name__ == "__main__":
    exitcode = main()
    if exitcode != 0:
        sys.exit(exitcode)
