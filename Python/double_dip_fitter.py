import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
from torch import nn, optim

plt.rcParams.update({'font.size': 15})

def double_dip_func(f, I0, A, width, f_center, f_delta):
    '''Double Lorentzian dip.'''
    return I0 - A/(1 + ((f_center - 0.5*f_delta - f)/width)**2) - A/(1 + ((f_center + 0.5*f_delta - f)/width)**2)

class DoubleLorentzianModel(nn.Module):
    def __init__(self, I0, A, width, f_center, f_delta):
        super(DoubleLorentzianModel, self).__init__()
        """self.I0 = nn.Parameter(I0)
        self.A = nn.Parameter(A)
        self.width = nn.Parameter(width)
        self.f_center = nn.Parameter(f_center)
        self.f_delta = nn.Parameter(f_delta)"""
        # Use a log transformation to enforce positivity
        self.log_I0 = nn.Parameter(torch.log(I0.view(-1, 1)))
        self.log_A = nn.Parameter(torch.log(A.view(-1, 1)))
        self.log_width = nn.Parameter(torch.log(width.view(-1, 1)))
        self.log_f_center = nn.Parameter(torch.log(f_center.view(-1, 1)))
        self.log_f_delta = nn.Parameter(torch.log(f_delta.view(-1, 1)))

    def forward(self, f):
        # Apply the exponential to get the actual parameters
        I0 = torch.exp(self.log_I0)
        A = torch.exp(self.log_A)
        width = torch.exp(self.log_width)
        f_center = torch.exp(self.log_f_center)
        f_delta = torch.exp(self.log_f_delta)
        
        # Reshape f (frequency tensor) to 2D: (batch_size, F)
        f = f.reshape(-1, f.shape[-1])  # Flatten (M, N, F) to (M*N, F) if using full data, or (batch_size, F) in batch
        
        # f has shape (batch_size, F) where F is the frequency range
        # Parameters are broadcasted to match the (batch_size, F) shape
        
        """lorentzian1 = self.A.unsqueeze(2) / (1 + ((self.f_center.unsqueeze(2) - 0.5 * self.f_delta.unsqueeze(2) - f) / self.width.unsqueeze(2)) ** 2)
        lorentzian2 = self.A.unsqueeze(2) / (1 + ((self.f_center.unsqueeze(2) + 0.5 * self.f_delta.unsqueeze(2) - f) / self.width.unsqueeze(2)) ** 2)
        return self.I0.unsqueeze(2) - (lorentzian1 + lorentzian2)"""
        lorentzian1 = A / (1 + ((f_center - 0.5 * f_delta - f) / width) ** 2)
        lorentzian2 = A / (1 + ((f_center + 0.5 * f_delta - f) / width) ** 2)
        return I0 - (lorentzian1 + lorentzian2)

def fit_double_lorentzian(data, freq, lr=0.0005, epochs=10000, tail=5, thresholds=[3, 5], error_threshold=0.1, default_values=None, batch_size=300000):
    '''
    Fits the double Lorentzian model to the (M, N, F) shaped input data.
    
    Arguments:
    - data: numpy array of shape (M, N, F) with the intensity values
    - freq: numpy array of shape (F,) with the frequency values
    - lr: learning rate for the optimizer
    - epochs: number of epochs for the optimization
    - tail: number of pixels to take from the side as a sample for baseline and noise
    - thresholds: relative values used to detect dips

    Returns:
    - A dictionary containing five (M, N) numpy arrays for the fitted parameters: I0, A, width, f_center, f_delta.
    '''
    M, N, F = data.shape
    freq_tensor = torch.tensor(freq, dtype=torch.float32).cuda().unsqueeze(0).unsqueeze(0).repeat(M, N, 1)
    intensity = torch.tensor(data, dtype=torch.float32).cuda()

    # Initialize arrays for initial guesses
    I0_est = np.zeros((M, N))
    A_est = np.zeros((M, N))
    width_est = np.zeros((M, N))
    f_center_est = np.zeros((M, N))
    f_delta_est = np.zeros((M, N))
    
    #Batch management
    total_pixels = M * N
    batch_size = min(batch_size, total_pixels)
    
    print("Starting initial guesses")

    for m in tqdm(range(M)):
        for n in range(N):
            # Get the intensity data for the current pixel
            intens = data[m, n, :]

            # Estimate noise level
            tail_values = np.concatenate((intens[:tail], intens[-tail:]))
            noise_std = np.std(tail_values)
            I0_est[m, n] = np.average(tail_values)
            A_est[m, n] = np.max(intens) - np.min(intens) - 2*noise_std

            dips = []
            dip_start = 0
            in_dip = False
            
            # Calculate absolute threshold positions
            #threshold_low = I0_est[m, n] - (1 - thresholds[0])*A_est[m, n]
            #threshold_high = I0_est[m, n] - (1 - thresholds[1])*A_est[m, n]
            threshold_low = np.min(intens) + thresholds[0]*noise_std
            threshold_high = np.min(intens) + thresholds[1]*noise_std

            for i in range(F):
                if in_dip:
                    if intens[i] >= threshold_high:
                        dips.append((dip_start, i))
                        in_dip = False
                else:
                    if intens[i] <= threshold_low:
                        dip_start = i
                        in_dip = True

            if len(dips) == 0:
                #print("Warning: somehow zero dips?")
                #There's almost nothing we can do with this :(
                width_est[m, n] = 1
                f_center_est[m, n] = np.average(freq)
                f_delta_est[m, n] = (np.max(freq) - np.min(freq)) / 4
            elif len(dips) == 1:
                f_dip_start = freq[dips[0][0]]
                f_dip_finish = freq[dips[0][1]]
                width_est[m, n] = 0.5 * (f_dip_finish - f_dip_start)
                f_center_est[m, n] = 0.5 * (f_dip_start + f_dip_finish)
                f_delta_est[m, n] = 0.003 #Assume the nuclear splitting as the only splitting 
                A_est[m, n] *= 0.5
            elif len(dips) == 2:
                f_dip_start_1 = freq[dips[0][0]]
                f_dip_finish_1 = freq[dips[0][1]]
                f_dip_start_2 = freq[dips[1][0]]
                f_dip_finish_2 = freq[dips[1][1]]
                width_est[m, n] = 0.25 * (f_dip_finish_1 + f_dip_finish_2 - f_dip_start_1 - f_dip_start_2)
                middle_1 = 0.5 * (f_dip_finish_1 + f_dip_start_1) 
                middle_2 = 0.5 * (f_dip_finish_2 + f_dip_start_2) 
                f_center_est[m, n] = 0.5 * (middle_1 + middle_2)
                f_delta_est[m, n] = middle_2 - middle_1
            else:
                #In this case, multiple "dips" were found, and it's not clear where the two peaks are located, or if it's even two peaks.
                #With the information we have, we try as best as possible to give reasonable first estimates, and hope the optimizer will take care of it.
                
                #Base width estimate on average of all "dips"
                width_est[m, n] = 0
                for i in range(len(dips)):
                    f_dip_start = freq[dips[i][0]]
                    f_dip_finish = freq[dips[i][1]]
                    width_est[m, n] += 0.5 * (f_dip_finish - f_dip_start)
                width_est[m, n] /= len(dips)
                
                #For center frequency, just take the middle of all the "dips"
                f_center_est[m, n] = 0
                for i in range(len(dips)):
                    f_dip_start = freq[dips[i][0]]
                    f_dip_finish = freq[dips[i][1]]
                    f_center_est[m, n] += 0.5 * (f_dip_finish + f_dip_start)
                f_center_est[m, n] /= len(dips)
                
                #Estimating f_delta is the hardest part with multiple "dips". One reasonable measure would be the standard deviation of the middels of each "dip"
                middles = np.zeros(len(dips))
                for i in range(len(dips)):
                    f_dip_start = freq[dips[i][0]]
                    f_dip_finish = freq[dips[i][1]]
                    middles[i] = 0.5 * (f_dip_finish - f_dip_start)
                f_delta_est[m, n] = np.std(middles)

    print("Initial guess done! Now invoking optimizer.")
    
    # Prepare storage for fitted parameters
    fitted_params = {
        "I0": np.zeros((M, N)),
        "A": np.zeros((M, N)),
        "width": np.zeros((M, N)),
        "f_center": np.zeros((M, N)),
        "f_delta": np.zeros((M, N)),
    }
    
    # Flatten data for easier batching
    data = data.reshape(-1, F)
    num_batches = (total_pixels + batch_size - 1) // batch_size  # Number of batches
    
    I0_est_flat = I0_est.reshape(-1)
    A_est_flat = A_est.reshape(-1)
    width_est_flat = width_est.reshape(-1)
    f_center_est_flat = f_center_est.reshape(-1)
    f_delta_est_flat = f_delta_est.reshape(-1)
    
    for batch_idx in range(num_batches):
        print("batch_idx:", batch_idx)
        
        start = batch_idx * batch_size
        end = min(start + batch_size, total_pixels)
        current_batch_size = end - start  # Current batch size, which may vary
        
        # Select the batch of data and convert to PyTorch tensor
        batch_data = data[start:end]
        batch_data = torch.tensor(batch_data, dtype=torch.float32).cuda()
    
        # Convert initial guesses to torch tensors
        I0 = torch.tensor(I0_est_flat[start:end], dtype=torch.float32).cuda()
        A = torch.tensor(A_est_flat[start:end], dtype=torch.float32).cuda()
        width = torch.tensor(width_est_flat[start:end], dtype=torch.float32).cuda()
        f_center = torch.tensor(f_center_est_flat[start:end], dtype=torch.float32).cuda()
        f_delta = torch.tensor(f_delta_est_flat[start:end], dtype=torch.float32).cuda()
        
        # Ensure the frequency tensor has the correct shape for broadcasting
        freq_tensor = torch.tensor(freq, dtype=torch.float32).cuda().unsqueeze(0).expand(current_batch_size, -1)

        # Initialize the model with different initial guesses for each pixel
        model = DoubleLorentzianModel(I0, A, width, f_center, f_delta).cuda()

        # Define the loss function (mean squared error)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=lr)

        # Optimization loop
        for epoch in range(epochs):
            optimizer.zero_grad()
            output = model(freq_tensor)
            
            # Get the batch-specific target intensity for loss calculation
            batch_target = intensity.view(-1, F)[start:end]  # Reshape and slice intensity for the batch
            loss = criterion(output, batch_target)
            loss.backward()
            optimizer.step()

            if epoch % 1000 == 0:
                print(f'Epoch {epoch}, Loss: {loss.item()}')

        # Extract the optimized parameters
        """fitted_params = {
            "I0": model.I0.data.cpu().numpy(),
            "A": model.A.data.cpu().numpy(),
            "width": model.width.data.cpu().numpy(),
            "f_center": model.f_center.data.cpu().numpy(),
            "f_delta": model.f_delta.data.cpu().numpy(),
        }"""
        batch_fitted_params = {
        "I0": torch.exp(model.log_I0).data.cpu().numpy(),
        "A": torch.exp(model.log_A).data.cpu().numpy(),
        "width": torch.exp(model.log_width).data.cpu().numpy(),
        "f_center": torch.exp(model.log_f_center).data.cpu().numpy(),
        "f_delta": torch.exp(model.log_f_delta).data.cpu().numpy(),
        }
        
        # Place batch results into the final storage array
        for param in fitted_params:
            fitted_params[param].reshape(-1)[start:end] = batch_fitted_params[param].reshape(-1)
        
        #This batch is done. Now emptyy cache.
        torch.cuda.empty_cache()
    
    # Reshape the final storage arrays back to (M, N)
    for param in fitted_params:
        fitted_params[param] = fitted_params[param].reshape(M, N)
    
    # Check for high MSE and replace with default values where needed
    if default_values is None:
        default_values = {"I0": 1.0, "A": 0, "width": 1.0, "f_center": 2.87, "f_delta": 0.0}
    
    failed_pixels = (loss > error_threshold).cpu().numpy()  # Boolean mask of failed pixels
    for param in fitted_params:
        fitted_params[param][failed_pixels] = default_values[param]
        
    return fitted_params

def inspect_initial_and_final_fit(data, freq, m, n, tail=5, thresholds=[3, 5], lr=0.0005, epochs=10000):
    """
    Generates two plots for inspection:
    - Initial guessed parameters with thresholds and dip regions
    - Final fit after optimization
    
    Arguments:
    - data: numpy array of shape (M, N, F) with intensity values
    - freq: numpy array of shape (F,) with the frequency values
    - m, n: indices of the pixel to inspect
    - tail: number of points to use for baseline noise estimation
    - thresholds: thresholds for detecting dips
    - lr: learning rate for optimizer
    - epochs: number of epochs for fitting
    """
    intens = data[m, n, :]
    F = len(freq)

    # Estimate initial parameters
    tail_values = np.concatenate((intens[:tail], intens[-tail:]))
    noise_std = np.std(tail_values)
    I0_est = np.average(tail_values)
    A_est = np.max(intens) - np.min(intens) - 2 * noise_std

    # Determine dips based on thresholds
    dips = []
    dip_start = 0
    in_dip = False
    threshold_low = np.min(intens) + thresholds[0] * noise_std
    threshold_high = np.min(intens) + thresholds[1] * noise_std

    for i in range(F):
        if in_dip:
            if intens[i] >= threshold_high:
                dips.append((dip_start, i))
                in_dip = False
        else:
            if intens[i] <= threshold_low:
                dip_start = i
                in_dip = True

    # Initial estimates for parameters
    if len(dips) == 0:
        width_est = 1
        f_center_est = np.average(freq)
        f_delta_est = (np.max(freq) - np.min(freq)) / 4
    elif len(dips) == 1:
        f_dip_start = freq[dips[0][0]]
        f_dip_finish = freq[dips[0][1]]
        width_est = 0.5 * (f_dip_finish - f_dip_start)
        f_center_est = 0.5 * (f_dip_start + f_dip_finish)
        f_delta_est = 0.003
        A_est *= 0.5
    elif len(dips) == 2:
        f_dip_start_1 = freq[dips[0][0]]
        f_dip_finish_1 = freq[dips[0][1]]
        f_dip_start_2 = freq[dips[1][0]]
        f_dip_finish_2 = freq[dips[1][1]]
        width_est = 0.25 * (f_dip_finish_1 + f_dip_finish_2 - f_dip_start_1 - f_dip_start_2)
        f_center_est = 0.5 * (f_dip_finish_1 + f_dip_start_1 + f_dip_finish_2 + f_dip_start_2) / 2
        f_delta_est = f_dip_finish_2 - f_dip_start_1
    else:
        width_est = 1
        f_center_est = np.mean([freq[d[0]] for d in dips])
        f_delta_est = np.std([freq[d[0]] for d in dips])

    # Plot initial guess with thresholds and dips
    initial_guess = double_dip_func(freq, I0_est, A_est, width_est, f_center_est, f_delta_est)
    plt.figure()
    plt.plot(freq, intens, label="Data", marker='.')
    plt.plot(freq, initial_guess, label="Initial Guess")
    plt.axhline(threshold_low, color="orange", linestyle="--", label="Low Threshold")
    plt.axhline(threshold_high, color="green", linestyle="--", label="High Threshold")
    
    # Highlight dip regions
    for (start, end) in dips:
        plt.axvspan(freq[start], freq[end], color="magenta", alpha=0.3)
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("Intensity")
    plt.title("Initial Guess with Thresholds and Dips")
    plt.legend()
    plt.show()

    # Fine-tune parameters with the model
    I0 = torch.tensor([I0_est], dtype=torch.float32, requires_grad=True).cuda()
    A = torch.tensor([A_est], dtype=torch.float32, requires_grad=True).cuda()
    width = torch.tensor([width_est], dtype=torch.float32, requires_grad=True).cuda()
    f_center = torch.tensor([f_center_est], dtype=torch.float32, requires_grad=True).cuda()
    f_delta = torch.tensor([f_delta_est], dtype=torch.float32, requires_grad=True).cuda()
    freq_tensor = torch.tensor(freq, dtype=torch.float32).unsqueeze(0).cuda()

    model = DoubleLorentzianModel(I0, A, width, f_center, f_delta).cuda()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()
    target_data = torch.tensor(intens, dtype=torch.float32).unsqueeze(0).cuda()

    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(freq_tensor)
        loss = criterion(output, target_data)
        loss.backward()
        optimizer.step()

        if epoch % 1000 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item()}")

    # Extract optimized parameters
    fitted_params = {
        "I0": torch.exp(model.log_I0).item(),
        "A": torch.exp(model.log_A).item(),
        "width": torch.exp(model.log_width).item(),
        "f_center": torch.exp(model.log_f_center).item(),
        "f_delta": torch.exp(model.log_f_delta).item(),
    }
    final_fit = double_dip_func(freq, **fitted_params)

    # Plot final fit
    plt.figure()
    plt.plot(freq, intens, label="Data", marker='.')
    plt.plot(freq, final_fit, label="Final Fit", color="red")
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("Intensity")
    plt.title("Final Fit after Optimization")
    plt.legend()
    plt.show()



if __name__ == "__main__":
    M, N, F = 50, 50, 100  # Example dimensions
    freq = np.linspace(2.85, 2.89, F)

    # Generate synthetic data with two dips
    intensity = np.zeros((M, N, F))
    for m in range(M):
        for n in range(N):
            intensity[m, n, :] = double_dip_func(freq, 1, 0.15, np.random.uniform(0.001, 0.004), 2.87, np.random.uniform(0.0, 0.010))
            intensity[m, n, :] += np.random.normal(0, 0.005, F)

    inspect_initial_and_final_fit(intensity, freq, 0, 0)
    exit()
    
    # Call the fitting function
    fitted_params = fit_double_lorentzian(intensity, freq)

    # Fitted parameters are now stored in fitted_params dictionary
    
    #print(fitted_params["I0"][0, 0])  # Example: print I0 for the first pixel
    
    #A couple of randomly selected ODMR graphs
    num_graphs = 10
    for i in range(num_graphs):
        x = np.random.randint(0, M, 1)[0]
        y = np.random.randint(0, N, 1)[0]
        fit = double_dip_func(freq,
                            fitted_params["I0"][x][y],
                            fitted_params["A"][x][y],
                            fitted_params["width"][x][y],
                            fitted_params["f_center"][x][y],
                            fitted_params["f_delta"][x][y]
                            )
        plt.figure()
        plt.plot(freq, intensity[x][y], '.')
        plt.plot(freq, fit)
        plt.title("(" + str(x) + ", " + str(y) + ")")
        plt.xlabel("Frequency")
        plt.ylabel("Intensity")
        plt.show()
    
    
    #Show plots with the processed results
    for key in fitted_params.keys():
        plt.figure()
        im = plt.imshow(fitted_params[key])
        plt.xlabel("X (pixels)")
        plt.ylabel("Y (pixels)")
        plt.title(key)
        cb = plt.colorbar(im)
        cb.set_label("Value", rotation=270, fontweight ="bold", labelpad=30)
        plt.show()