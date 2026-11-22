import numpy as np
import math
from pathlib import Path

GRAPH_LIMITS = (1.5,1.8)

freq = []
R = []
I = []
script_path = Path(__file__)
with open(script_path.parent / "medicao_antena_s1p.txt", 'r') as arquivo:
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
freq_filter = ((freq>=GRAPH_LIMITS[0]) & (freq<=GRAPH_LIMITS[1]))
mag_log = mag_log

import matplotlib.pyplot as plt

plt.plot(freq,mag_log)
print("Largura de banda:",min(mag_log[freq_filter])+3)
plt.axhline(min(mag_log[freq_filter])+3,linestyle='--',color='r')
# plt.xlim(GRAPH_LIMITS)
plt.ylim(-25,0)
plt.title("Diagrama de Perda de Retorno")
plt.xlabel("Frequência (GHz)")
plt.ylabel("Perda de retorno (dB)")
plt.grid(True,'both','both')
plt.show()
