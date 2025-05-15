'''Module that provides an improved double Lorentzian fitting.'''

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def double_dip_func(f, I0, A, width, f_center, f_delta):
    '''Double Lorentzian dip.
    f = frequency
    I0 = base intensity
    A = amplitude of dip
    f_center = center frequency
    f_delta = difference in frequency between the two dips.'''
    return I0 - A/(1 + ((f_center - 0.5*f_delta - f)/width)**2) - A/(1 + ((f_center + 0.5*f_delta - f)/width)**2)

def fit_double_dip(freq, intensity, tail=5, thresholds=[0.3, 0.5]):
    '''Fits the double dip function to the intensity vs frequency data.
    freq and intensity are the x and y data
    tail = number of pixels to take from the side as a sample for baseline and noise
    thresholds = values which have to be trespassed to count as dip. These are relative values with respect to baseline, counted from I0-A upwards.'''\
    #Checks:
    if(len(freq) != len(intensity)):
        raise Exception("ERROR: Frequency and intensity data not of same length!")
    if(len(freq) < 2*tail):
        raise Exception("ERROR: length of data must be at least two times tail length!")
    if(thresholds[0] > thresholds[1]):
        raise Exception("ERROR: First threshold must be lower than second threshold!")
    if(thresholds[0] < 0 or thresholds[0] > 1):
        raise Exception("ERROR: (First threshold) Thresholds must be between 0 and 1!")
    if(thresholds[1] < 0 or thresholds[1] > 1):
        raise Exception("ERROR: (Second threshold) Thresholds must be between 0 and 1!")
        
    #First estimates:
    #Estimate noise level
    tail_values = np.concatenate((intensity[:tail], intensity[-tail:]))
    noise_std = np.std(tail_values)
    I0_est = np.average(tail_values)
    A_est = np.max(intensity) - np.min(intensity) - 2*noise_std
    dips = []
    dip_start = 0
    in_dip = False
    
    #Calculate absolute threshold positions
    threshold_low = I0_est - (1 - thresholds[0])*A_est
    threshold_high = I0_est - (1 - thresholds[1])*A_est
    print(threshold_high)
    print(threshold_low)
    for i in range(len(freq)):
        if(in_dip):
            if(intensity[i] >= threshold_high):
                #Reached end of dip
                dips += [[dip_start, i]]
                in_dip = False
        else:
            if(intensity[i] <= threshold_low):
                #Reached start of dip
                dip_start = i
                in_dip = True
                
    print(dips)
    
    #Check number of dips found
    if(len(dips) == 0):
        #This shouldn't be possible. No dips found in this case.
        raise Exception("ERROR: Fucked up the fit, no dips found!")
    elif(len(dips) == 1):
        print("Found one dip!")
        f_dip_start = freq[dips[0][0]]
        f_dip_finish = freq[dips[0][1]]
        width_est =  (f_dip_finish - f_dip_start) * 0.5 #the 0.5 is because the width parameter is half the FWHM of the dip
        f_center_est = ( f_dip_start + f_dip_finish) * 0.5 #(Average)
        f_delta_est = 0
        #The dips are (mostly) stacked oneachother, so our previous estimation for amplitude should be half!
        A_est *= 0.5
    elif(len(dips) == 2):
        print("Found two dips!")
        f_dip_start_1 = freq[dips[0][0]]
        f_dip_finish_1 = freq[dips[0][1]]
        f_dip_start_2 = freq[dips[1][0]]
        f_dip_finish_2 = freq[dips[1][1]]
        width_est = 0.25 * (f_dip_finish_1 + f_dip_finish_2 - f_dip_start_1 - f_dip_start_2) #(Average of both widths, and divided by 2 to go from FWHM to width parameter)
        middle_1 = 0.5 * (f_dip_finish_1 + f_dip_start_1) 
        middle_2 = 0.5 * (f_dip_finish_2 + f_dip_start_2) 
        f_center_est = 0.5 * (middle_1 + middle_2) #Average of both regions
        f_delta_est = middle_2 - middle_1
    else:
        print("WARNING: I was not made for this >:[")
        width_est = 1
        f_center_est = 0
        f_delta_est = 0
    
    #Initial estimates
    p0 = [I0_est, A_est, width_est, f_center_est, f_delta_est]
    print("First estimates:", p0)
    
    #Now it's time to finetune this rough graph.
    popt, pcov = curve_fit(double_dip_func, freq, intensity, p0=p0, bounds=([0.5, 0, 0, 0, 0], [1.5, 1, np.inf, np.inf, np.inf]))
    print("Finetuned estimates:", popt)
    return popt

if __name__ == "__main__":
    noise = 0.02
    num_points = 100
    freq = np.linspace(2.85, 2.89, num_points)
    #intens = double_dip_func(freq, 1, 0.15, 0.005, 2.87, 0.007)
    intens = double_dip_func(freq, 1, 0.15, 0.003, 2.87, 0.005)
    intens += np.random.normal(0, noise, num_points)
    param = fit_double_dip(freq, intens)
    fitted_graph = double_dip_func(freq, param[0], param[1], param[2], param[3], param[4])
    
    print(param)
    
    plt.figure()
    plt.plot(freq, intens, '.')
    plt.plot(freq, fitted_graph)
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("Intensity")
    plt.show()
    