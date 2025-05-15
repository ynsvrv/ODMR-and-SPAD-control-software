import serial
import struct
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable
import time

# Plot settings
plt.rcParams.update({'font.size': 18,})
plt.rcParams.update({'figure.autolayout': True})

# Configure the serial port
serial_port = '/dev/ttyACM0'  # Change as needed for your system
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1.0)
max_attempts = 5 #Maximum number of times that the get_frame function may attempt to retrieve a frame in one call.

max_counts = 100

def get_frame():
    bytes_per_counter = 4
    collecting = False
    current_attempt = 0

    data = np.zeros((16, 16))

    #Put everything under while loop so that multiple attempts can be made at getting a good frame.
    try:
        while current_attempt < max_attempts:
            current_attempt += 1
            try:
                #print("Waiting for start-of-frame bytes.")
                flag_byte_counter = 0
                while collecting == False:
                    data_bytes = ser.read(1)
                    number = struct.unpack('B', data_bytes)[0]
                    #print(hex(number))
                    if(number == 0xFF):
                        flag_byte_counter += 1
                        if(flag_byte_counter == bytes_per_counter):
                            #This was the end of the start-of-frame signal. Begin counting!
                            flag_byte_counter = 0
                            #print("Found start-of-frame! Collecting actual data now.")
                            collecting = True
                            data_counter = 0
                    else:
                        #Not a flag byte. Reset counter
                        flag_byte_counter = 0
                
                for i in range(256):
                    data_bytes = ser.read(bytes_per_counter)
                    #Currently struct.unpack expects a defined number of bits. Change this too when changing bytes_per_counter!
                    number = struct.unpack('>I', data_bytes)[0]
                    #print(hex(number))
                    x = i % 16
                    y = i // 16
                    data[x][y] = number

                #Check if frame is ended by the next end-of-frame. Otherwise it was a bad frame, and we discard the data.
                data_bytes = ser.read(4)
                number = struct.unpack('>I', data_bytes)[0]
                if(number == 0xFFFFFFFF):
                    #Needs to be transposed because apparently x is rows and y is columns as it is now, and it should be the opposite.
                    return np.transpose(data)
                else:
                    print("Bad frame! Retrying.")
            except struct.error:
                print("No Signal! Retrying (" + str(current_attempt) + "/" + str(max_attempts) + ")")

        #If the code reaches here, maximum attempts have been reached.
        print("Maximum number of attempts reached!")
        return np.zeros((16, 16))
    except KeyboardInterrupt:
        print("Exiting.")

def main():
    fig = plt.figure()

    ax = fig.add_subplot(111)
    div = make_axes_locatable(ax)
    cax = div.append_axes('right', '5%', '5%')
    data = np.zeros((16, 16))
    im = ax.imshow(data)
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("Counts", rotation=270, fontweight ="bold", labelpad=30)
    ax.set_xlabel("column")
    ax.set_ylabel("row")
    tx = ax.set_title('Frame 0')

    def animate(i):
        cax.cla()
        data = get_frame()
        im = ax.imshow(data)
        cb = fig.colorbar(im, cax=cax)
        cb.set_label("Counts", rotation=270, fontweight ="bold", labelpad=30)
        tx.set_text('Frame {0}'.format(i))

    ani = animation.FuncAnimation(fig, animate)

    plt.show()

# Example of how to call the main function with your get_frame() function
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        ser.close()