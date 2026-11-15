import numpy as np
import math

freq = []
R = []
I = []
with open("medicao_antena_s1p.txt", 'r') as arquivo:
    for line in arquivo:
        if ('#' in line) or ('!' in line):
            # Config or comment
            continue
        f, r, i = line.split(" ") # Splits line into frequency, real and imaginary part
        freq.append(float(f))
        R.append(float(r))
        I.append(float(i))

# np array and handling of values
freq = np.array(freq)/(1e9)
R = np.array(R)**2
I = np.array(I)**2 

mag_2 = (R+I)**(1/2)
mag_log = 10*np.log(mag_2)
mag_log = mag_log-max(mag_log)

import matplotlib.pyplot as plt

plt.plot(freq,mag_log)
plt.xlim(1.5,1.8)
plt.title("Diagrama de Perda de Retorno")
plt.xlabel("Frequência (GHz)")
plt.ylabel("Perda de retorno (dB)")
plt.show()
