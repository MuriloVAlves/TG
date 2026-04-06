import scipy.optimize as scp
import numpy as np
import matplotlib.pyplot as plt

pid_val = [0,20,40,60,80,100]
rpm_val = [0,44,375.684,612.77,760.91,929.63]

plt.scatter(pid_val,rpm_val)
plt.show()