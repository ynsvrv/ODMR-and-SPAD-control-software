from __future__ import print_function
#import psutil
from IPython.display import display, clear_output
#%matplotlib inline
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import numpy as np
#import matplotlib.pyplot as plt
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

from point_in_triangle import point_in_triangle
        

def main() -> int:
    settings = {
        "save_folder": "/home/dl-lab-pc3/measurements/",
        "x_steps": 40,
        "y_steps": 40,
        "z_steps": 50, #Only used for 3DPL and z scans.
        "dwell_time": 2e11, #picoseconds
        "num_measurements": 100, #Will be ignored when just doing PL
        "min_freq": 2.8e9, #Will be ignored when just doing PL
        "max_freq": 2.94e9, #Will be ignored when just doing PL
        "num_sweeps": 1, #Will be ignored when just doing PL
        "x1": -2, #mm
        "x2": -1.940,
        "y1": 3,
        "y2": 3.060,
        "z1": 0, #Only used for 3DPL and z scans.
        "z2": 0.1, #Only used for 3DPL and z scans.
        "x0": 0.0,
        "y0": 0.0,
        "z0": 4.531,
        "ax": -0.0009, #mm per mm
        "ay": -0.0001, #mm per mm
        "measurement_type": "ODMR", #choices: "PL", "ODMR", "3DPL"
        "steps_to_autozero": 1000, #Number of steps before the piezo stack performs the periodic autozero.
        "triangle": None, #Set to None if not using triangular scan. Otherwise specify the three corners
        #Warning: triangle area is not yet taken into account in time estimation. Estimate with your own calculations!
        #Also some more metadata. Note: The program cannot check these values. Make sure to update them every time!!!
        "laser_power": 2.9, #mW
        "sample": "Bonded EDP (100)",
        "Piezo scoping": """
        Laser focus: (0, 0, 4.531)
        """
    }

    settings_file = None

    if(settings_file != None):
        #Load settings from specified json file
        with open(settings_file, 'r') as f:
            settings = json.load(f)

    save_folder = settings["save_folder"]
    x_steps = settings["x_steps"]
    y_steps = settings["y_steps"]
    z_steps = settings["z_steps"]
    dwell_time = settings["dwell_time"]
    num_measurements = settings["num_measurements"]
    min_freq = settings["min_freq"]
    max_freq = settings["max_freq"]
    num_sweeps = settings["num_sweeps"]
    x1 = settings["x1"]
    x2 = settings["x2"]
    y1 = settings["y1"]
    y2 = settings["y2"]
    z1 = settings["z1"]
    z2 = settings["z2"]

    x0 = settings["x0"]
    y0 = settings["y0"]
    z0 = settings["z0"]
    ax = settings["ax"]
    ay = settings["ay"]
    measurement_type = settings["measurement_type"]
    steps_to_autozero = settings["steps_to_autozero"]
    triangle = settings["triangle"]

    #Time estimation
    ODMR_overhead_time = 0.06 #Number of seconds overhead per measurement point (determined empirically)
    piezo_overhead_time = 0.2 #Seconds for the piezo stack needed to perform movements, and thus time spent not measuring.
    #Note: Piezo overhead time depends on step size. In the limit of small steps, it seems to stay pretty close to 0.2 seconds.

    #Calculate total amount of pixels. Triangle case shortens it.
    if(triangle != None):
       #Estimate based on surface. Becomes accurate in the limit of many pixels (also reasonable with low amount of pixels)
       print("Estimating time taking into account triangle skipping.")
       #Formula: Area = 0.5 * | x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2) |
       temp1 = triangle[0][0] * (triangle[1][1] - triangle[2][1])
       temp2 = triangle[1][0] * (triangle[2][1] - triangle[0][1])
       temp3 = triangle[2][0] * (triangle[0][1] - triangle[1][1])
       triangle_area = 0.5 * abs(temp1 + temp2 + temp3)
       square_area = (x2 - x1) * (y2 - y1)
       triangle_ratio = triangle_area / square_area
       print("Triangle ratio:", triangle_ratio)
       total_xypixels = x_steps*y_steps * triangle_ratio
    else:
       print("No triangle given. Using full square.")
       total_xypixels = x_steps*y_steps

    #Calculate time based on measurement type
    if(measurement_type == "ODMR"):
      seconds_per_measurement = dwell_time*1e-12 + ODMR_overhead_time
      total_measurements = total_xypixels * num_sweeps * num_measurements
      total_time = total_measurements * seconds_per_measurement
    elif(measurement_type == "PL"):
      total_measurements = total_xypixels
      total_time = total_measurements * (dwell_time*1e-12 + piezo_overhead_time)
    elif(measurement_type == "3DPL"):
       total_measurements = total_xypixels * z_steps
       total_time = total_measurements * (dwell_time*1e-12 + piezo_overhead_time)
    else:
       print("Bruh, unknown measurement type. Exiting >:[")
       exit()
    print("Estimated time: " + str(total_time/3600) + " hours")
    estimated_finish = time.time() + total_time
    local_time = time.ctime(estimated_finish)
    print("Will finish at: ", local_time)


    # Saving the data:
    current_time = datetime.now()
    timestamp_string = str(round(current_time.timestamp()))
    #Determine preset for file name
    if(measurement_type == "ODMR"):
       scan_name = "2D_ODMR_scan_"
    elif(measurement_type == "PL"):
       scan_name = "2D_PL_scan_"
    elif(measurement_type == "3DPL"):
       scan_name = "3D_PL_scan_"
    savePath = save_folder + scan_name + timestamp_string #Without file extension yet
    settings["savePath"] = savePath
    settings["Start time"] = str(current_time)
    #settings_file_path = settings["save_folder"] + "2D ODMR scan settings" + timestamp + ".json"

    # Create a TimeTagger instance to control your hardware
    tagger = TimeTagger.createTimeTagger()
    countrate = TimeTagger.Countrate(tagger=tagger, channels=[1])   # 1 is 1



    if(measurement_type == "ODMR"):
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
    



    #Setup piezo-stack
    from rtcs.devices.physikinstrumente.pi_E873_controller import Pistage_controller
    pi_x = Pistage_controller("type=tcp;host=192.168.20.21;port=50000") #x axis
    pi_y = Pistage_controller("type=tcp;host=192.168.20.22;port=50000") #x axis
    pi_z = Pistage_controller("type=tcp;host=192.168.20.23;port=50000") #x axis

    pi_x.open()
    pi_y.open()
    pi_z.open()

    #Set velocities of piezo stack
    pi_x.send_command("VEL 1 5")
    pi_y.send_command("VEL 1 5")
    pi_z.send_command("VEL 1 5")

    def full_autozero():
      pi_z.move(0)
      pi_y.move(0)
      pi_x.move(0)
      time.sleep(3)
      pi_x.autozero()
      time.sleep(10)
      pi_y.autozero()
      time.sleep(10)
      pi_z.autozero()
      time.sleep(10)


    #Prepare arrays:
    xmove = np.linspace(x1, x2, x_steps)
    ymove = np.linspace(y1, y2, y_steps)

    #Initialization based on measurement type
    if(measurement_type == "ODMR"):
      x = np.linspace(min_freq, max_freq, num_measurements)
      osc_freq = x - center_frequency
      fit_freq = np.linspace(min_freq, max_freq, 500)
      PL = np.zeros((x_steps, y_steps, num_measurements))
      NORMALIZED = np.zeros((x_steps, y_steps, num_measurements))
    elif(measurement_type == "PL"):
      PL = np.zeros((x_steps, y_steps))
    elif(measurement_type == "3DPL"):
      zmove = np.linspace(z1, z2, z_steps)
      PL = np.zeros((x_steps, y_steps, z_steps))

    steps_since_last_autozero = 0

    # Loop for 2D Scan
    for iy in range(y_steps):
        #pi_y.move(ymove[iy])
        for ix_loop in range(x_steps):
            #Simpel implementation of serpentine scan pattern
            if(iy % 2 == 0):
               ix = ix_loop
            else:
               ix = x_steps - ix_loop - 1

            #Triangular option
            if(triangle != None):
               #Triangle specified. Skip this iteration if not inside triangle
               current_point = (xmove[ix], ymove[iy])
               if(point_in_triangle(current_point, triangle) == False):
                  print("Not in triangle. Skipping point!")
                  continue #skip this iteration
            
            #Periodic autozero
            if(steps_since_last_autozero >= steps_to_autozero):
               np.save(savePath + ".npy", PL)
               full_autozero()
               print("Performed a periodic autozero!")
               steps_since_last_autozero = 0
            steps_since_last_autozero += 1

            pi_x.move(xmove[ix])
            pi_y.move(ymove[iy])
            z = z0 + ax*(xmove[ix] - x0) + ay*(ymove[iy] - y0)

            if(measurement_type != "3DPL"):
              pi_z.move(z)

            timeout = 10 #seconds
            start_time = time.time()
            while not pi_x.get_on_target_state() or not pi_y.get_on_target_state() or not pi_z.get_on_target_state():
                time.sleep(0.005)
                if(timeout != None):
                    if(time.time() > start_time + timeout):
                        print()
                        print("Warning: Timeout passed for wait_on_target! Giving up and moving on.")
                        print("Real position: ({}, {}, {})".format(pi_x.get_real_position(), pi_y.get_real_position(), pi_z.get_real_position()))
                        print("Target: ({}, {}, {})".format(pi_x.get_target_position(), pi_y.get_target_position(), pi_z.get_target_position()))
                        #Anti stuck procedure

                        #Query stuff
                        pi_x.send_command("SVO?")
                        response = pi_x._readline()
                        print("x SVO?: " + response)
                        pi_x.send_command("ERR?")
                        response = pi_x._readline()
                        print("x ERR?: " + response)
                        pi_x.send_command("VEL?")
                        response = pi_x._readline()
                        print("x VEL?: " + response)
                        pi_x.send_command("ONT?")
                        response = pi_x._readline()
                        print("x ONT?: " + response)
                        pi_x._transport.write(b'\x05')
                        response = pi_x._readline()
                        print("x #5 (motion status): " + response)

                        pi_y.send_command("SVO?")
                        response = pi_y._readline()
                        print("y SVO?: " + response)
                        pi_y.send_command("ERR?")
                        response = pi_y._readline()
                        print("y ERR?: " + response)
                        pi_y.send_command("VEL?")
                        response = pi_y._readline()
                        print("y VEL?: " + response)
                        pi_y.send_command("ONT?")
                        response = pi_y._readline()
                        print("y ONT?: " + response)
                        pi_y._transport.write(b'\x05')
                        response = pi_y._readline()
                        print("y #5 (motion status): " + response)

                        pi_z.send_command("SVO?")
                        response = pi_z._readline()
                        print("z SVO?: " + response)
                        pi_z.send_command("ERR?")
                        response = pi_z._readline()
                        print("z ERR?: " + response)
                        pi_z.send_command("VEL?")
                        response = pi_z._readline()
                        print("z VEL?: " + response)
                        pi_z.send_command("ONT?")
                        response = pi_z._readline()
                        print("z ONT?: " + response)
                        pi_z._transport.write(b'\x05')
                        response = pi_z._readline()
                        print("z #5 (motion status): " + response)

                        np.save(savePath + ".npy", PL)
                        full_autozero()
                        pi_x.move(xmove[ix])
                        pi_y.move(ymove[iy])
                        pi_z.move(z)
                        time.sleep(3)
                        print("Real position after recovery: ({}, {}, {})".format(pi_x.get_real_position(), pi_y.get_real_position(), pi_z.get_real_position()))
                        break

            #pi_x.wait_on_target(timeout=10)
            #pi_y.wait_on_target(timeout=10)
            #pi_z.wait_on_target(timeout=10)

            if(measurement_type == "PL"):
                countrate.startFor(dwell_time)
                countrate.waitUntilFinished()
                rate = countrate.getData()[0]
                PL[ix][iy] = rate
            elif(measurement_type == "3DPL"):
               for iz in range(z_steps):
                  pi_z.move(zmove[iz])

                  #Wait for z to move, with timeout
                  timeout = 10 #seconds
                  start_time = time.time()
                  while not pi_z.get_on_target_state():
                    time.sleep(0.005)
                    if(time.time() > start_time + timeout):
                      print("WARNING: pi_z.get_on_target_state() timed out!!!" + 10*"#\n")
                      full_autozero()
                  
                  countrate.startFor(dwell_time)
                  countrate.waitUntilFinished()
                  rate = countrate.getData()[0]
                  PL[ix][iy][iz] = rate
            elif(measurement_type == "ODMR"):
              for im in range(num_measurements):
                  PL[ix][iy][im] = 0
                  for s in range(num_sweeps): #Loop to do multiple sweeps
                      osc1_frequency = osc_freq[im]
                      # Configure digital sine generator
                      device.sgchannels[channel_index].configure_sine_generation(enable = True,
                                                                              osc_index = 0,
                                                                              osc_frequency = osc1_frequency, 
                                                                              phase = 0,
                                                                              gains = gains_cw) # or use AWG.set_rf_frequency(x[n])

                      countrate.startFor(dwell_time)
                      countrate.waitUntilFinished()
                      rate = countrate.getData()[0]
                      PL[ix][iy][im] += rate / num_sweeps
              NORMALIZED[ix][iy] = PL[ix][iy] / max(PL[ix][iy])

            print("Current PL: {}, on position: x = {}, y = {}, z = {}            \r"
                .format(rate,np.round(xmove[ix],decimals = 5),np.round(ymove[iy],decimals = 5), np.round(z, decimals = 5)))
    print()
    pi_x.close()
    pi_y.close()
    pi_z.close()

    np.save(savePath + ".npy", PL)#, header=file_header)

    if(measurement_type == "PL"):
       #Also save in txt format
       np.savetxt(savePath + ".txt", PL)

    settings["End time"] = str(datetime.now())

    #Save settings in json file
    with open(savePath + ".json", 'w') as f: 
        json.dump(settings, f, indent="")
    
    print("Measurement complete!\nFile saved as: " + savePath + ".npy")


if __name__ == "__main__":
    exitcode = main()
    if exitcode != 0:
        sys.exit(exitcode)