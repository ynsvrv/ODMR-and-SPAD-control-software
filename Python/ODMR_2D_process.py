import numpy as np
import matplotlib.pyplot as plt
import sys
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import json
import argparse

#Local modules
#from rtcs.measurements.esr_scan import triple_dip_esr_fit as triple_fit
#from rtcs.measurements.esr_scan import double_dip_esr_fit as double_fit
from double_dip_fitter import fit_double_lorentzian, double_dip_func

#Plot settings
plt.rcParams.update({'font.size': 24,})
plt.rcParams.update({'figure.autolayout': True})
PL_color = "inferno"
contrast_color = "plasma"
ps_color = "viridis"
fshift_color = "cividis"
interpolation = "nearest"

#Strain constants
d_perp = 0.8e9 #Hz
d_axial = 1.54e9 #Hz


def Lorentzian(x, I, x0, gamma):
    """Three-parameter Lorentzian.
    I = height of peak
    x0 = location of peak
    gamma = half-width at half-maximum (HWHM) of the peak"""
    return I * (gamma**2 / ( (x - x0)**2 + gamma**2) )

def double_dip(x, height, distance, center, gamma, max_value):
    """Fitting function for inverted Lorentzian.
    max_value = value of the function outside of the peaks (around 1 in a normalized graph)
    height = height of the peak (corresponds to contrast in a normalized graph)
    center = middle between the two peaks. The peaks will be placed symmetrically around this point.
    gamma = gamma parameter in the Lorentzian (half-width at half maximum of each peak).
    distance = distance between the two peaks (thus half the distance from each peak to the specified center).
    Note: width is de width of the peaks themselves, and distance is between the peak centers. Both peaks will be at half this distance from the center."""
    loc1 = center - 0.5*distance
    loc2 = center + 0.5*distance
    peak1 = Lorentzian(x, height, loc1, gamma)
    peak2 = Lorentzian(x, height, loc2, gamma)
    return max_value - peak1 - peak2

def fit_double_dip(x, PL_graph):
    """Fits a double dip on a normalized PL map
    x: Array of frequencies
    PL_graph: The data to be fitted"""
    popt, pcov = curve_fit(double_dip, x, PL_graph, p0=[0.1, 4e7, 2.87e9, 2e7, 1], bounds=([0, 0, 2.8e9, 0, 0.5], [1.5, 1e8, 3.0e9, 1e8, 1.5]))
    return popt


def plot_random_ODMR_samples(PL_normalized, settings, random_sampling_margin=0, num_random_samples=10):
    """Takes a couple random pixels of the 2D ODMR data and plots their corresponding ODMR graphs. For testing whether ODMR is actually working."""
    x_steps = settings["x_steps"]
    y_steps = settings["y_steps"]
    x = np.linspace(settings["min_freq"], settings["max_freq"], settings["num_measurements"])
    fit_freq = np.linspace(settings["min_freq"], settings["max_freq"], 500)

    ix_arr = np.random.randint(random_sampling_margin, x_steps - random_sampling_margin, num_random_samples)
    iy_arr = np.random.randint(random_sampling_margin, y_steps - random_sampling_margin, num_random_samples)
    for k in range(num_random_samples):
        fit_double_dip = double_fit.fit_double_dip_esr(x, PL_normalized[ix_arr[k]][iy_arr[k]])
        localminima = -fit_double_dip(fit_freq)
        peakyboo, _ = find_peaks(localminima, prominence=0.003)
        if(len(peakyboo) > 0):
            plt.figure()
            plt.title("x step = " + str(ix_arr[k]) + ", y step = " + str(iy_arr[k]))
            plt.plot(x, PL_normalized[ix_arr[k]][iy_arr[k]])
            plt.plot(fit_freq, fit_double_dip(fit_freq), "r-")
            plt.plot(fit_freq[peakyboo], fit_double_dip(fit_freq)[peakyboo], "xb", label = "Peaks, difference = {}" 
            .format(np.abs(max(fit_double_dip(fit_freq)[peakyboo])-min(fit_double_dip(fit_freq)[peakyboo]))))
            plt.show()


def plot_map(data, settings, color_label, unit_conversion_factor=1, title=None, suffix="out.png", filename_base="", cmap="Inferno"):
    """Data[x][y]
    color label: What comes to display on the color bar (include a unit!)
    unit conversion factor: By which factor does the data need to be multiplied to match the label.
    suffix: Added at the end of the file name. INCLUDE A FILE EXTENSION!"""

    # Colour plot of diamond surface
    plt.figure(figsize=(12,8))
    #imshow is (y, x) instead of (x, y) as we have our PL data in, so transpose PL
    pos = plt.imshow(data.T * unit_conversion_factor, cmap=cmap, interpolation = interpolation, extent = [settings["x1"], settings["x2"], settings["y1"], settings["y2"]], origin="lower")
    if(title != None):
        plt.title(title)
    plt.xlabel("x (mm)", fontweight ="bold")
    plt.ylabel("y (mm)", fontweight ="bold")
    cb = plt.colorbar(pos)
    cb.set_label(color_label, rotation=270, fontweight ="bold", labelpad=30)
    plt.savefig(filename_base + suffix, dpi = 100, transparent=False)
    plt.show()


def main() -> int:
    parser = argparse.ArgumentParser(description="Perform an ESR scan measurement.")
    parser.add_argument('filename', help="Path to the file to be processed. Expects a .npy file. Settings will be taken from a .json file with exactly the same name.")
    args = parser.parse_args()
    filename = args.filename
    filename_base = filename[:-4]
    settings_file = filename_base + ".json" #Remove .npy and add .json


    PL = np.load(filename)
    with open(settings_file, 'r') as f:
        settings = json.load(f)
        
    #Temporary for making a graph. When you read this, you can remove these lines up to and including the exit statement
    #freq = np.linspace(settings["min_freq"], settings["max_freq"], settings["num_measurements"])
    #freq_GHz = freq * 1e-9
    #plt.figure()
    #plt.plot(freq_GHz, PL[11][20])
    #plt.xlabel("Frequency (GHz)")
    #plt.ylabel("Intensity (counts)")
    #plt.show()
    #np.savetxt("test_PL.txt", PL[11][20])
    #np.savetxt("test_freq.txt", freq)
    #exit()

    #TODO integrate the following if-elif statement in the measurement_type stack underneath
    if(len(PL.shape) == 1):
        #This is a z scan. Show graph.
        zmove = np.linspace(settings["z1"], settings["z2"], settings["z_steps"])
        plt.figure()
        plt.plot(zmove, PL)
        plt.xlabel("Z (mm)")
        plt.ylabel("I (counts/s)")
        plt.savefig(filename_base + "_plot.png", dpi = 100, transparent=False, bbox_inches="tight")
        plt.show()
        return 0
    elif(len(PL.shape)==2):
        #2D PL map.
        plot_map(PL, settings, "counts/s", 1, title="PL map", suffix="plot_PL.png", filename_base=filename_base, cmap=PL_color)
        plot_map(np.log10(PL), settings, "log PL ($_{10}$log counts/s)", 1, title="PL map", suffix="plot_log_PL.png", filename_base=filename_base, cmap=PL_color)
        return 0
    
    if(settings["measurement_type"] ==  "3DPL"):
        #Take some random pixels and plot their graph
        num_random_samples = 0
        x_steps = settings["x_steps"]
        y_steps = settings["y_steps"]
        z_steps = settings["z_steps"]
        z_arr = np.linspace(settings["z1"], settings["z2"], settings["z_steps"])
        ix_arr = np.random.randint(0, x_steps, num_random_samples)
        iy_arr = np.random.randint(0, y_steps, num_random_samples)
        #First show a couple random graphs
        for k in range(num_random_samples):
            plt.figure()
            plt.title("x step = " + str(ix_arr[k]) + ", y step = " + str(iy_arr[k]))
            plt.plot(z_arr, PL[ix_arr[k]][iy_arr[k]])
            plt.xlabel("Z (mm)")
            plt.ylabel("I (counts/s)")
            plt.show()
        
        #Now compute the heightmaps
        count_threshold = 1000 #All places with more counts per second will be considered diamond.
        top_surface = np.zeros((x_steps, y_steps))
        back_surface = np.zeros((x_steps, y_steps))
        xmove = np.linspace(settings["x1"], settings["x2"], settings["x_steps"])
        ymove = np.linspace(settings["y1"], settings["y2"], settings["y_steps"])
        for ix in range(x_steps):
            for iy in range(y_steps):
                #Loop through z values until first point above threshold
                for iz in range(z_steps):
                    if(PL[ix][iy][iz] > count_threshold):
                        top_surface[ix][iy] = z_arr[iz]
                        break
                #Now do the same from the back
                for iz in range(z_steps-1, -1, -1):
                    if(PL[ix][iy][iz] > count_threshold):
                        back_surface[ix][iy] = z_arr[iz]
                        break
        thickness_map = abs(top_surface - back_surface)

        #Also make a PL plot. A simple way to do this is to average through z.
        #PL_averaged = np.average(PL, axis=2)
        
        #Fit planes on top and back surface, so that PL can be plotted on those.
        def plane_z(xy, z0, ax, ay):
            """xy format [x, y].
            Or for fitting: [[x1, x2, x3, ...], [y1, y2, y3, ...]]"""
            return z0 + ax*xy[0] + ay*xy[1]
        
        xfit = np.zeros(0)
        yfit = np.zeros(0)
        zfit = np.zeros(0)
        for ix in range(x_steps):
            for iy in range(y_steps):
                if(np.average(PL[ix][iy]) > count_threshold): #If not above threshold, ignore it. Probably background
                    xfit = np.append(xfit, xmove[ix])
                    yfit = np.append(yfit, ymove[iy])
                    zfit = np.append(zfit, top_surface[ix][iy])
        popt, pcov = curve_fit(plane_z, [xfit, yfit], zfit)
        z0 = popt[0]
        ax = popt[1]
        ay = popt[2]
        print("Top surface: z0:", z0, ". ax:", ax, ". ay:", ay)

        PL_top_surface = np.zeros((x_steps, y_steps))
        for ix in range(x_steps):
            for iy in range(y_steps):
                z_plane = plane_z([xmove[ix], ymove[iy]], z0, ax, ay)
                if(z_plane > z_arr[0] and z_plane < z_arr[-1]):
                    #Z is within measurement range. Take closest point.
                    closest_iz = 0
                    for iz in range(z_steps):
                        if(abs(z_arr[iz] - z_plane) < abs(z_arr[closest_iz] - z_plane)):
                            #Found closer index
                            closest_iz = iz
                    PL_top_surface[ix][iy] = PL[ix][iy][closest_iz]

        #Do the same for the back surface
        xfit = np.zeros(0)
        yfit = np.zeros(0)
        zfit = np.zeros(0)
        for ix in range(x_steps):
            for iy in range(y_steps):
                if(np.average(PL[ix][iy]) > count_threshold): #If not above threshold, ignore it. Probably background
                    xfit = np.append(xfit, xmove[ix])
                    yfit = np.append(yfit, ymove[iy])
                    zfit = np.append(zfit, back_surface[ix][iy])
        popt, pcov = curve_fit(plane_z, [xfit, yfit], zfit)
        z0 = popt[0]
        ax = popt[1]
        ay = popt[2]
        print("Back surface: z0:", z0, ". ax:", ax, ". ay:", ay)

        PL_back_surface = np.zeros((x_steps, y_steps))
        for ix in range(x_steps):
            for iy in range(y_steps):
                z_plane = plane_z([xmove[ix], ymove[iy]], z0, ax, ay)
                if(z_plane > z_arr[0] and z_plane < z_arr[-1]):
                    #Z is within measurement range. Take closest point.
                    closest_iz = 0
                    for iz in range(z_steps):
                        if(abs(z_arr[iz] - z_plane) < abs(z_arr[closest_iz] - z_plane)):
                            #Found closer index
                            closest_iz = iz
                    PL_back_surface[ix][iy] = PL[ix][iy][closest_iz]

        #Now plot results
        plot_map(np.clip(top_surface, a_min=z_arr[0], a_max=z_arr[-1]), settings, "z (um)", 1000, title="Top surface height map", suffix="plot_3DPL_top.png", filename_base=filename_base, cmap=PL_color)
        plot_map(np.clip(back_surface, a_min=z_arr[0], a_max=z_arr[-1]), settings, "z (um)", 1000, title="Back surface height map", suffix="plot_3DPL_back.png", filename_base=filename_base, cmap=PL_color)
        plot_map(thickness_map, settings, "Δz (um)", 1000, title="Observed diamond thickness", suffix="plot_3DPL_thickness.png", filename_base=filename_base, cmap=PL_color)
        #plot_map(PL_averaged, settings, "counts/s", 1, title="PL map z-averaged", suffix="plot_3DPL_z_averaged.png", filename_base=filename_base, cmap=PL_color)
        #plot_map(np.log10(PL_averaged), settings, "log PL ($_{10}$log counts/s)", 1, title="PL map z-averaged", suffix="plot_log_3DPL_averaged.png", filename_base=filename_base, cmap=PL_color)
        plot_map(PL_top_surface, settings, "counts/s", 1, title="PL map fitted top surface", suffix="plot_3DPL_PL_top_surface.png", filename_base=filename_base, cmap=PL_color)
        plot_map(np.log10(PL_top_surface), settings, "log PL ($_{10}$log counts/s)", 1, title="PL map fitted top surface", suffix="plot_log_3DPL_PL_top_surface.png", filename_base=filename_base, cmap=PL_color)
        plot_map(PL_back_surface, settings, "counts/s", 1, title="PL map fitted back surface", suffix="plot_3DPL_PL_back_surface.png", filename_base=filename_base, cmap=PL_color)
        plot_map(np.log10(PL_back_surface), settings, "log PL ($_{10}$log counts/s)", 1, title="PL map fitted back surface", suffix="plot_log_3DPL_PL_back_surface.png", filename_base=filename_base, cmap=PL_color)

        return 0

    PL_normalized = np.zeros(PL.shape)
    for ix in range(PL.shape[0]):
        for iy in range(PL.shape[1]):
            PL_normalized[ix][iy] = PL[ix][iy] / max(PL[ix][iy])

    #plot_random_ODMR_samples(PL_normalized, settings)

    if(len(PL.shape)==3):
        print("Processing double dip fits")
        x_steps = settings["x_steps"]
        y_steps = settings["y_steps"]

        contrast_fit = np.zeros((x_steps, y_steps))
        contrast_raw = np.zeros((x_steps, y_steps))
        peak_splitting = np.zeros((x_steps, y_steps))
        frequency_shift = np.zeros((x_steps, y_steps))

        x = np.linspace(settings["min_freq"], settings["max_freq"], settings["num_measurements"])
        fit_freq = np.linspace(settings["min_freq"], settings["max_freq"], 500)
        freq_GHz = x * 1e-9
        
        """
        for ix in range(x_steps):
            for iy in range(y_steps):
                #If number of counts is too low, ignore pixel
                if(np.mean(PL_normalized[ix][iy])):
                    fit_double_dip = double_fit.fit_double_dip_esr(x, PL_normalized[ix][iy])
                    localminima = -fit_double_dip(fit_freq)
                    peakyboo, _ = find_peaks(localminima, prominence=0.003)
                    if(len(peakyboo) == 2):
                        fs = max(fit_freq[peakyboo]) - min(fit_freq[peakyboo])
                        center_freq = ( max(fit_freq[peakyboo]) + min(fit_freq[peakyboo]) ) / 2
                        contr = (max(fit_double_dip(fit_freq))-min(fit_double_dip(fit_freq)[peakyboo]))
                        contrast_raw[ix][iy] = np.max(PL_normalized[ix][iy]) - np.min(PL_normalized[ix][iy]) #scale 0 to 1
                        contrast_fit[ix][iy] = contr #scale 0 to 1
                        peak_splitting[ix][iy] = fs #Hz
                        frequency_shift[ix][iy] = center_freq - 2.87e9 #Hz
        """
        
        #Calculate contrast_raw
        for ix in range(x_steps):
            for iy in range(y_steps):
                contrast_raw[ix][iy] = np.max(PL_normalized[ix][iy]) - np.min(PL_normalized[ix][iy]) #scale 0 to 1
        
        #Use the improved fitting module
        #Note: Everything here will be with GHz as frequency unit
        fitted_params = fit_double_lorentzian(PL_normalized, freq_GHz)
        contrast_fit = fitted_params["A"]
        peak_splitting = fitted_params["f_delta"]
        frequency_shift = fitted_params["f_center"] - 2.87 #Yes, in GHz
        
        #Show a few random plots to check whether stuff went well
        num_graphs = 10
        for i in range(num_graphs):
            x = np.random.randint(0, x_steps, 1)[0]
            y = np.random.randint(0, y_steps, 1)[0]
            fit = double_dip_func(freq_GHz,
                                fitted_params["I0"][x][y],
                                fitted_params["A"][x][y],
                                fitted_params["width"][x][y],
                                fitted_params["f_center"][x][y],
                                fitted_params["f_delta"][x][y]
                                )
            plt.figure()
            plt.plot(freq_GHz, PL_normalized[x][y], '.')
            plt.plot(freq_GHz, fit)
            plt.title("(" + str(x) + ", " + str(y) + ")")
            plt.xlabel("Frequency (GHz)")
            plt.ylabel("Intensity (normalized)")
            plt.show()
        

        plot_map(np.mean(PL, axis=2), settings, "PL (kcounts/s)", 1e-3, title="Photoluminescence", suffix="plot_PL.png", filename_base=filename_base, cmap=PL_color)
        plot_map(np.clip(contrast_raw, a_min=None, a_max=0.3), settings, "Raw contrast (%)", 100, title="Raw contrast (clipped to max 30%)", suffix="plot_contrast_raw.png", filename_base=filename_base, cmap=contrast_color)
        plot_map(np.clip(contrast_fit, a_min=None, a_max=0.3), settings, "Fit contrast (%)", 100, title="Fit contrast (clipped to max 30%)", suffix="plot_contrast_fit.png", filename_base=filename_base, cmap=contrast_color)
        plot_map(np.clip(peak_splitting, a_min=0.025, a_max=None), settings, "Peak splitting (MHz)", 1e3, title="Peak splitting (clipped above 25 MHz)", suffix="plot_peak_splitting.png", filename_base=filename_base, cmap=ps_color)
        print("Average peak splitting (GHz): ", np.mean(np.clip(peak_splitting, a_min=0.025, a_max=0.035)))
        print("Standard deviation peak splitting (GHz): ", np.std(np.clip(peak_splitting, a_min=0.025, a_max=0.035)))
        plot_map(np.clip(frequency_shift, a_min=-0.005, a_max=0.005), settings, "Frequency shift (MHz)", 1e3, title="Frequency shift (clipped at 5 MHz)", suffix="plot_frequency_shift.png", filename_base=filename_base, cmap=fshift_color)

        #Strain maps (Only valid when measurement is takin in zero field)
        #Reminder: perpendicular ~ peak splitting. Axial ~ frequency shift.
        #plot_map(np.abs(peak_splitting), settings, "$\epsilon_{perp}$ (%)", 2*np.pi / d_perp * 100, title="Perpendicular strain", suffix="plot_strain_perp.png", filename_base=filename_base, cmap=ps_color)
        #plot_map(np.abs(frequency_shift), settings, "$\epsilon_{axial}$ (%)", 2*np.pi / d_axial * 100, title="Axial strain", suffix="plot_strain_axial.png", filename_base=filename_base, cmap=fshift_color)

if __name__ == "__main__":
    exitcode = main()
    if exitcode != 0:
        sys.exit(exitcode)