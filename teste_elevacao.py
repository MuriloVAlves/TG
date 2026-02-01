import matplotlib.pyplot as plt
import numpy as np
import math

#Script variables
STEPS = 3

# Parts of the mechanism
# fixed hinge/movable hinge
pole = [(0,1),(0,0)] # x/y coordinates
antenna_hinge = [(0,1),(0,0)]
actuator = [(0,0),(1,0)]

deg2rad = math.pi/180

def calcular_tamanho(posicao):
    pos1 = posicao[0]
    pos2 = posicao[1]
    deltaX = abs(pos1[0]-pos2[0])
    deltaY = abs(pos1[1]-pos2[1])
    return math.sqrt((deltaX**2)+(deltaY**2))

def calcular_angulo(c,a,b):
    sqr_triang = (c**2)-((a**2)+(b**2))
    cos_multiplier = -(2*a*b)
    return math.acos(sqr_triang/cos_multiplier)

def calcular_posicao(parte,angulo):
    tamanho = calcular_tamanho(parte)
    x = tamanho*math.cos(angulo)
    y = tamanho*math.sin(angulo)
    novo_tamanho = [parte[0],(parte[0][0]+x,parte[0][1]+y)]
    return novo_tamanho

def vector2matplot(membro):
    x_coords = []
    y_coords = []
    x_coords.append(membro[0][0])
    y_coords.append(membro[0][1])
    x_coords.append(membro[1][0])
    y_coords.append(membro[1][1])
    return x_coords,y_coords

#SCRIPT
colors = ['red','blue','green','orange','purple']
numcolor = 0
STEPS = len(colors)
for actuator_len in np.arange(0.1,calcular_tamanho(actuator),calcular_tamanho(actuator)/STEPS):
    active_actuator = [(0,0),(actuator_len,0)]
    hinge_angle = calcular_angulo(calcular_tamanho(active_actuator),calcular_tamanho(pole),calcular_tamanho(antenna_hinge))
    actuator_angle = calcular_angulo(calcular_tamanho(antenna_hinge),calcular_tamanho(pole),calcular_tamanho(active_actuator))
    new_hinge_pos = calcular_posicao(antenna_hinge,hinge_angle+(270*deg2rad))
    new_active_act_pos = calcular_posicao(active_actuator,(90*deg2rad)-actuator_angle)
    new_act_pos = calcular_posicao(actuator,(90*deg2rad)-actuator_angle)
    
    for part in [pole,new_hinge_pos,new_act_pos,new_active_act_pos]:
        x_coords,y_coords = vector2matplot(part)
        plt.plot(x_coords, y_coords, marker='o',color=colors[numcolor])
    numcolor += 1
plt.show()


# # Plot the line
# plt.plot(x_coords, y_coords)

# # Optional: Add markers to see the exact points
# plt.plot(x_coords, y_coords, marker='o')

# # Display the plot
# plt.show()
