import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import math

#SCRIPT VARIABLE
STEPS = 30
HINGESTEPS = 10
LOWBORDER = 0.1
HIGHBORDER = 0.95
LOWSIZE = 0.5
HIGHSIZE = 3

# Parts of the mechanism
# fixed hinge/movable hinge
pole = [(0,1),(0,0)] # x/y coordinates
antenna_hinge = [(0,1),(0,0)]
actuator = [(0,0),(1,0)]
antenna_pole = [(0,1),(0,1.1)]

DEG2RAD = math.pi/180

def calcular_tamanho(posicao):
    pos1 = posicao[0]
    pos2 = posicao[1]
    deltaX = abs(pos1[0]-pos2[0])
    deltaY = abs(pos1[1]-pos2[1])
    return math.sqrt((deltaX**2)+(deltaY**2))

def calcular_triangulo(c,a,b):
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

def main():
    #SCRIPT
    css_colors_dict = mcolors.CSS4_COLORS
    css_color_names = list(css_colors_dict.keys())
    colors = css_color_names #['red','blue','green','orange','purple','yellow']
    for multiplier in np.arange(LOWSIZE,HIGHSIZE+((HIGHSIZE-LOWSIZE)/HINGESTEPS),(HIGHSIZE-LOWSIZE)/HINGESTEPS):
        multiplied_tuple = tuple(item * multiplier for item in pole[0])
        pole[0] = multiplied_tuple
        antenna_hinge[0] = multiplied_tuple
        antenna_pole[0] = pole[0]
        result_array = np.add(pole[0], (0,0.1)) 
        result_tuple = tuple(result_array)
        antenna_pole[1] = result_tuple
        numcolor = 0
        print('pole =',calcular_tamanho(pole))
        print('antenna_hinge =',calcular_tamanho(antenna_hinge))
        print('antenna_pole =',calcular_tamanho(antenna_pole))
        for actuator_len in np.arange(calcular_tamanho(actuator)*LOWBORDER,calcular_tamanho(actuator)*HIGHBORDER+calcular_tamanho(actuator)/STEPS,calcular_tamanho(actuator)/STEPS):
            active_actuator = [(0,0),(actuator_len,0)]
            try:
                hinge_angle = calcular_triangulo(calcular_tamanho(active_actuator),calcular_tamanho(pole),calcular_tamanho(antenna_hinge))
                actuator_angle = calcular_triangulo(calcular_tamanho(antenna_hinge),calcular_tamanho(pole),calcular_tamanho(active_actuator))
            except:
                continue
            new_hinge_pos = calcular_posicao(antenna_hinge,hinge_angle+(270*DEG2RAD))
            new_active_act_pos = calcular_posicao(active_actuator,(90*DEG2RAD)-actuator_angle)
            new_act_pos = calcular_posicao(actuator,(90*DEG2RAD)-actuator_angle)
            new_antenna_pole = calcular_posicao(antenna_pole,(90*DEG2RAD)+hinge_angle)
            for part in [pole,new_hinge_pos,new_act_pos,new_active_act_pos,new_antenna_pole]:
                x_coords,y_coords = vector2matplot(part)
                plt.plot(x_coords, y_coords, marker='o',color=colors[numcolor%len(colors)])
            numcolor += 1
        plt.show()

if __name__ == "__main__":
    main()