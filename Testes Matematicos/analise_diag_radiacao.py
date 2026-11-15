import matplotlib.pyplot as plt
import numpy as np
import math

DEG2RAD = math.pi/180

diag_L = np.array([-26.5,-26.8,-27,-27.4,-27.3,-31.5,-33.5,-32.4,-36.7,-43.1,-44.4,-49.3,-49.8,-46,-50.1,-57.1,-43.7,-46.7,-47.4, -55.2])
diag_R = np.array([-24.9,-25.3,-25.6,-26.4,-29.2,-29.5,-32.3,-31.6,-37.2,-46.2,-44,-41.1,-45.2,-45.3,-43.3,-44.3,-44.5,-48.8,-45.4,-50.2])

# Normalize the read data
max_L = max(diag_L)
max_R = max(diag_R)
diag_L = diag_L-max_L
diag_R = diag_R-max_R

left_theta = []
right_theta = []
for k in range(0,95,5):
    # Inverted because of counter-clockwise polar plot
    left_theta.append(k)
    right_theta.append((-1)*k)
left_theta.append(110)
right_theta.append(-110)
left_theta = np.array(left_theta)
right_theta = np.array(right_theta)

# Create -3 dB line
left_idx = (np.absolute(diag_L-(-3))).argmin()
right_idx = (np.absolute(diag_R-(-3))).argmin()

# Calculate the -3dB exact point
theta_max_neg3db = [0,0]
menor, maior = (left_idx,left_idx-1)
theta_max_neg3db[0] = ((left_theta[menor]-left_theta[maior])*((-3-diag_L[maior])/(diag_L[menor]-diag_L[maior])))+left_theta[maior]
menor, maior = (right_idx,right_idx-1)
theta_max_neg3db[1] = ((right_theta[menor]-right_theta[maior])*((-3-diag_R[maior])/(diag_R[menor]-diag_R[maior])))+right_theta[maior]

line_neg3db = []
theta_neg3db = []
for t in range(0,50,1):
    val = (theta_max_neg3db[1] - theta_max_neg3db[0])/50
    theta_neg3db.append((t*val)+theta_max_neg3db[0])
    line_neg3db.append(-3)
theta_neg3db.append(theta_max_neg3db[1]) # last value
line_neg3db.append(-3)
theta_neg3db = np.array(theta_neg3db)

theta = np.append(np.flip(left_theta),right_theta)
diag = np.append(np.flip(diag_L),diag_R)

half_pwr_cone_L = np.array([min(diag),0])
half_pwr_cone_R = np.array([min(diag),0])
half_pwr_cone_theta_L = np.array([theta_max_neg3db[0],theta_max_neg3db[0]])
half_pwr_cone_theta_R = np.array([theta_max_neg3db[1],theta_max_neg3db[1]])

plt.polar(DEG2RAD*theta,diag,color='tab:blue')
plt.polar(DEG2RAD*theta_neg3db,line_neg3db,'--',color='tab:red')
plt.polar(DEG2RAD*half_pwr_cone_theta_L,half_pwr_cone_L,'--',color='tab:red')
plt.polar(DEG2RAD*half_pwr_cone_theta_R,half_pwr_cone_R,'--',color='tab:red')
plt.legend(["Potência (dB)","Cone de -3 dB"])
print("BW:",theta_max_neg3db[0]-theta_max_neg3db[1])
plt.show()