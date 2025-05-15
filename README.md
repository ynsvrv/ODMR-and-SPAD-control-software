%====================================
This code has been developed within the Quantum Integration Technology (QIT) research group (Ishihara Lab) in TU Delft, as part of the MEP thesis of Dylan Aliberti (dylan.aliberti@gmail.com), titled \textit{"Characterization of Single-Photon Avalanche Diodes and Integration with Diamond for Quantum Bio-sensing"}, and the overall PhD research project of Ioannis Varveris (ynsvrv@gmail.com), titled \textit{"Toward a quantum biosensor based on CMOS-integrated NV centers: Quantum sensing and fabrication of color centers in diamond"}. This code is intended to be viewed and used by subsequent lab users/researchers and should not be distributed without prior permission by the authors.

\noindent The online version can be found on GitHub:\\
\href{https://github.com/Dylan-Aliberti/MEP_SPAD_quantum_bio_sensing/tree/main}{\texttt{github.com/Dylan-Aliberti/MEP\_SPAD\_quantum\_bio\_sensing/tree/main}}


\section{Overview}

The code consists of two main parts:

\begin{itemize}
  \item \textbf{Confocal‐scan control and processing}\\  
    Python scripts for 2D scans and $z$–scans:
    \begin{itemize}
      \item \texttt{ODMR\_2D.py}\quad [data acquisition for 2D scans]
      \item \texttt{ODMR\_2D\_process.py}\quad [processing and plotting of the acquired data]
      \item \texttt{z\_scan.py}\quad [$z$–scan acquisition]
    \end{itemize}
    When setting up a measurement, edit the parameter dictionary at the top of
    \\\texttt{ODMR\_2D.py}, or supply a JSON file path. Outputs are saved as \texttt{.npy} and JSON metadata.
    
    To view results, type in the terminal (example):
    \begin{verbatim}
    python3 ODMR_2D_process.py /home/user/measurements/scan1.npy
    \end{verbatim}
    
    These scripts depend on the modules:
    
    \texttt{point\_in\_triangle.py}\quad and\\
    \texttt{double\_dip\_fitter.py}

  \item \textbf{SPAD‐array readout}\\
    The control code for the SPAD array includes FPGA, Arduino, and Python modules. Readout scripts provide both full-array and single-SPAD modes, and the Arduino package offers a frame-generation test program so the Python reader can be exercised without actual FPGA or chip hardware. Since this code is tailored to the current setup, parameters will need to be adjusted when testing new SPAD or FPGA revisions. If you are interested in using this code to test new SPAD hardware, feel free to contact the author at dylan.aliberti@gmail.com.
\end{itemize}


\section{How to use the code}

This section covers only the confocal scan part; for SPAD‐array details, please contact the author.

\subsection{General procedure for a 2D scan and data viewing}

This procedure assumes the diamond is mounted on the piezo stage. Part of the workflow uses external TNO alignment code (commands prefixed \texttt{rtcs}). Valid for the setup as of December 2024; hardware or software changes may require adaptation.

\subsubsection{Launching GUI and setting up}

After mounting:
\begin{enumerate}
  \item In a terminal, run: \quad \texttt{rtcs gui}
  \item Auto-zero all piezo axes.
  \item Flip down the pellicle beamsplitter, turn on camera and LED (set LED to 12 mA).
  \item Move the piezo stage slowly in $+z$ to find the LED double‐square focus ($\pm$ surface).
\end{enumerate}


\subsubsection{Determining tilt}

Move by a few millimeters in $x$ (and separately in $y$) and note the required $\Delta z$ to refocus the LED. The tilt is $\Delta z / \Delta x$ (and $\Delta z / \Delta y$). Enter these values (in mm per mm) as \texttt{ax} and \texttt{ay} in \texttt{ODMR\_2D.py}.


\subsubsection{Finding the exact surface focus}

\begin{enumerate}
  \item Turn off LED, turn on laser.
  \item Use the camera to focus the laser spot (fine $z$ steps, $\sim$ 12 µm offset from LED focus).
  \item (Optional) Do a $z$–scan: two count‐rate maxima mark the top and back surfaces. Investigate any disagreement between camera focus and scan peaks.
  \item Record the $(x_0,y_0,z_0)$ of the laser focus point for the scan script.
  \item Turn off camera and raise the pellicle beamsplitter.
\end{enumerate}


\subsection{Checking ODMR}

In the terminal, type:
\begin{verbatim}
rtcs esr-scan --show --num-sweeps 1
\end{verbatim}
Adjust parameters as needed. Use \texttt{--help} to list available options.


\subsection{Preparing and running the measurement script}

\begin{enumerate}
  \item Open \quad\texttt{ODMR\_2D.py} 
  \item Set \quad\texttt{ax, ay, x0, y0, z0}\\
  and other parameters (steps, sweeps, \texttt{measurement\_type}, etc.).
  \item In the terminal, type: \quad\texttt{cd/home/dl-lab-pc3/Dylan/}
  \item Then, to run the measurement type: \quad\texttt{python3 ODMR\_2D.py}
  \item Monitor the runtime estimate and PL readings after each sweep.
\end{enumerate}

\subsection{Viewing acquired data}
After completion, note the output file path (e.g. \texttt{data.npy}). Then type:
\begin{verbatim}
python3 ODMR_2D_process.py   path/to/data.npy
\end{verbatim}
First, ten random pixels are shown for quick quality check; then the full 2D plots appear one by one. Close each window to advance. All figures are saved with the original filename as a prefix. Make sure the data is available locally (in the computer), in OneNote/OneDrive, and also synchronized with a data storage unit in the cloud (e.g. \texttt{U:\textbackslash QIT Research Data\textbackslash Username}).

\subsection{Customizing plots}
To change titles, fonts, units or clipping thresholds, edit the calls to \texttt{plot\_map(...)} in \texttt{ODMR\_2D\_process.py}. Update units and conversion rates consistently.
