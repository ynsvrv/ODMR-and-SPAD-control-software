# Quantum Bio-sensing Code

This code has been developed within the Quantum Integration Technology (QIT) research group (Ishihara Lab) at TU Delft, as part of the MEP thesis of **Dylan Aliberti** (<dylan.aliberti@gmail.com>), titled _“Characterization of Single-Photon Avalanche Diodes and Integration with Diamond for Quantum Bio-sensing”_, and the overall PhD research project of **Ioannis Varveris** (<ynsvrv@gmail.com>), titled _“Toward a quantum biosensor based on CMOS-integrated NV centers: Quantum sensing and fabrication of color centers in diamond”_. This code is intended to be viewed and used by subsequent lab users/researchers and **should not be distributed** without prior permission by the authors.

The online version can be found on GitHub:  
🔗 [https://github.com/ynsvrv/ODMR_and_SPAD_control_software](https://github.com/ynsvrv/ODMR_and_SPAD_control_software)

---

## Overview

The code consists of two main parts:

1. **Confocal-scan control and processing**  
   Python scripts for 2D scans and _z_-scans:
   - `ODMR_2D.py`  [data acquisition for 2D scans]  
   - `ODMR_2D_process.py`  [processing and plotting of the acquired data]  
   - `z_scan.py`  [_z_-scan acquisition]  

   When setting up a measurement, edit the parameter dictionary at the top of `ODMR_2D.py` or supply a JSON file path. Outputs are saved as `.npy` files plus JSON metadata.

   To view results, for example run:
   ```bash
   python3 ODMR_2D_process.py /home/user/measurements/scan1.npy


These scripts depend on the modules:

* `point_in_triangle.py`
* `double_dip_fitter.py`

2. **SPAD-array readout**
   The control code for the SPAD array includes FPGA, Arduino, and Python modules. Readout scripts provide both full-array and single-SPAD modes, and the Arduino package offers a frame-generation test program so the Python reader can be exercised without actual FPGA or chip hardware. Since this code is tailored to the current setup, parameters will need to be adjusted when testing new SPAD or FPGA revisions. If you are interested in using this code to test new SPAD hardware, feel free to contact the author at [dylan.aliberti@gmail.com](mailto:dylan.aliberti@gmail.com).

---

## How to use the code

> **Note:** This section covers only the confocal scan part; for SPAD-array details, please contact the author.

### General procedure for a 2D scan and data viewing

This procedure assumes the diamond is mounted on the piezo stage. Part of the workflow uses external TNO alignment code (commands prefixed `rtcs`). Valid for the setup as of December 2024; hardware or software changes may require adaptation.

#### Launching GUI and setting up

1. In a terminal, run:

   ```bash
   rtcs gui
   ```
2. Auto-zero all piezo axes.
3. Flip down the pellicle beamsplitter; turn on camera and LED (set LED to 12 mA).
4. Move the piezo stage slowly in `+z` to find the LED double-square focus (± surface).

#### Determining tilt

1. Move by a few millimeters in `x` (and separately in `y`) and note the required Δz to refocus the LED.
2. Tilt = Δz / Δx (and Δz / Δy).
3. Enter these values (in mm per mm) as `ax` and `ay` in `ODMR_2D.py`.

#### Finding the exact surface focus

1. Turn off LED; turn on laser.
2. Use the camera to focus the laser spot (fine `z` steps, \~12 µm offset from LED focus).
3. (Optional) Do a *z*-scan: two count-rate maxima mark the top and back surfaces. Investigate any disagreement between camera focus and scan peaks.
4. Record the `(x0, y0, z0)` of the laser focus point for the scan script.
5. Turn off camera and raise the pellicle beamsplitter.

---

### Checking ODMR

In the terminal, type:

```bash
rtcs esr-scan --show --num-sweeps 1
```

Adjust parameters as needed. Use `--help` to list available options.

---

### Preparing and running the measurement script

1. Open `ODMR_2D.py`.
2. Set `ax`, `ay`, `x0`, `y0`, `z0` and other parameters (`steps`, `sweeps`, `measurement_type`, etc.).
3. In the terminal, navigate to the code directory, e.g.:

   ```bash
   cd /home/dl-lab-pc3/Dylan/
   ```
4. Run:

   ```bash
   python3 ODMR_2D.py
   ```
5. Monitor the runtime estimate and PL readings after each sweep.

---

### Viewing acquired data

After completion, note the output file path (e.g. `data.npy`). Then run:

```bash
python3 ODMR_2D_process.py path/to/data.npy
```

* First, ten random pixels are shown for quick quality check.
* Then the full 2D plots appear one by one; close each window to advance.
* All figures are saved with the original filename as a prefix.
* Make sure the data is available locally, in OneNote/OneDrive, and synchronized with cloud storage (e.g. `U:\QIT Research Data\Username`).

---

### Customizing plots

To change titles, fonts, units or clipping thresholds, edit the calls to `plot_map(...)` in `ODMR_2D_process.py`. Update units and conversion rates consistently.

```
```
