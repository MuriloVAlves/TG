import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import math

#SCRIPT VARIABLE
STEPS = 10
HINGESTEPS = 100
LOWBORDER = 0.1
HIGHBORDER = 0.95
LOWSIZE = 0.01
HIGHSIZE = 1.1
MAX_ANTENNA_ANGLE = 90
MIN_ANTENNA_ANGLE = 0
ANTENNA_ANGLE_TOLERANCE = 0.2
ANGLE_CORRECTION_STEP = 0.001

# Parts of the mechanism
# fixed hinge/movable hinge
ref_pole = [(0,1),(0,0)] # x/y coordinates
ref_antenna_hinge = [(0,1),(0,0)]
ref_actuator = [(0,0),(1,0)]
ref_antenna_pole = [(0,1),(0,1.1)]

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

def calcular_angulo(vetor):
    x = vetor[0][0] - vetor[1][0]
    y = vetor[0][1] - vetor[1][1]
    return (math.atan2((y),(x))*-1)

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
    print('\nIniciando programa...')
    css_colors_dict = mcolors.CSS4_COLORS
    css_color_names = list(css_colors_dict.keys())
    colors = css_color_names #['red','blue','green','orange','purple','yellow']
    antenna_params = []
    sensitivity = []
    for multiplier in np.arange(LOWSIZE,HIGHSIZE+((HIGHSIZE-LOWSIZE)/HINGESTEPS),(HIGHSIZE-LOWSIZE)/HINGESTEPS):
        print('Calculando para',multiplier)
        pole = ref_pole.copy()
        antenna_hinge = ref_antenna_hinge.copy()
        antenna_pole = ref_antenna_pole.copy()
        multiplied_tuple = tuple(item * multiplier for item in ref_pole[0])
        pole[0] = multiplied_tuple
        antenna_hinge[0] = multiplied_tuple
        antenna_pole[0] = pole[0]
        result_array = np.add(pole[0], (0,0.1)) 
        result_tuple = tuple(result_array)
        antenna_pole[1] = result_tuple
        numcolor = 0
        max_angle_value_read = -360
        max_angle_depth = 0
        max_angle_found = False
        min_angle_value_read = 360
        min_angle_depth = 0
        min_angle_found = False
        # print('pole =',calcular_tamanho(pole))
        # print('antenna_hinge =',calcular_tamanho(antenna_hinge))
        # print('antenna_pole =',calcular_tamanho(antenna_pole))
        for actuator_len in np.arange(calcular_tamanho(ref_actuator)*LOWBORDER,(calcular_tamanho(ref_actuator)*HIGHBORDER),calcular_tamanho(ref_actuator)/STEPS):
            active_actuator = [(0,0),(actuator_len,0)]
            try:
                hinge_angle = calcular_triangulo(calcular_tamanho(active_actuator),calcular_tamanho(pole),calcular_tamanho(antenna_hinge))
                actuator_angle = calcular_triangulo(calcular_tamanho(antenna_hinge),calcular_tamanho(pole),calcular_tamanho(active_actuator))
            except:
                continue
            new_hinge_pos = calcular_posicao(antenna_hinge,hinge_angle+(270*DEG2RAD))
            new_active_act_pos = calcular_posicao(active_actuator,(90*DEG2RAD)-actuator_angle)
            new_act_pos = calcular_posicao(ref_actuator,(90*DEG2RAD)-actuator_angle)
            new_antenna_pole = calcular_posicao(antenna_pole,(90*DEG2RAD)+hinge_angle)
            # Calcular sensibilidade do sistema
            # Ângulo atual da antena
            actual_angle = calcular_angulo(new_antenna_pole)/DEG2RAD
            # Ver se ângulo maior é maior que o ângulo esperado
            if actual_angle > max_angle_value_read:
                #Salvar parâmetros
                max_angle_found = True
                max_angle_depth = actuator_len
                max_angle_value_read = actual_angle
            #Ver se ele é menor que o menor ângulo maior que o esperado
            if actual_angle < min_angle_value_read:
                min_angle_found = True
                min_angle_depth = actuator_len
                min_angle_value_read = actual_angle
            # for part in [pole,new_hinge_pos,new_act_pos,new_active_act_pos,new_antenna_pole]:
            #     x_coords,y_coords = vector2matplot(part)
            #     plt.plot(x_coords, y_coords, marker='o',color=colors[numcolor%len(colors)])
            # numcolor += 1
        if max_angle_found and min_angle_found and (max_angle_value_read-min_angle_value_read != 0):
            antenna_params.append((pole,antenna_hinge,antenna_pole))
            sensitivity.append(((min_angle_depth,max_angle_depth),(min_angle_value_read,max_angle_value_read)))
        # plt.show()
    # Verificar a melhor sensibilidade
    print('Verificando os melhores parâmetros encontrados...')
    best_guess_value = (-360,360)
    best_guess_actuator = (0,0)
    best_guess_index = -1
    for i in range(len(sensitivity)):
        actuator,value = sensitivity[i]
        if actuator[0] - actuator[1] >= best_guess_actuator[0] - best_guess_actuator[1]:
            if value[1] - value[0] >= ANTENNA_ANGLE_TOLERANCE+MAX_ANTENNA_ANGLE-MIN_ANTENNA_ANGLE:
                if value[1] - value[0] <= best_guess_value[1] - best_guess_value[0]:
                    best_guess_value = value
                    best_guess_actuator = actuator
                    best_guess_index = i

    # Corrigir braço da antena
    print('Calculando correção do braço da antena...')
    best_guess_correction = 2000
    best_guess_difference = 2000
    for correc_angle in np.arange(-180,180,ANGLE_CORRECTION_STEP):
        min_val, max_val = best_guess_value
        min_val = min_val + correc_angle
        max_val = max_val + correc_angle
        if min_val < MIN_ANTENNA_ANGLE and max_val > MAX_ANTENNA_ANGLE:
            if abs(min_val-MIN_ANTENNA_ANGLE)+abs(max_val-MAX_ANTENNA_ANGLE) < best_guess_difference:
                best_guess_correction = correc_angle
                best_guess_difference = abs(min_val-MIN_ANTENNA_ANGLE)+abs(max_val-MAX_ANTENNA_ANGLE)
    # Printar parâmetros:
    print('\r--- Melhores parâmetros ---')
    best_guess_params = antenna_params[best_guess_index]
    print('pole =',calcular_tamanho(best_guess_params[0]))
    print('antenna_hinge =',calcular_tamanho(best_guess_params[1]))
    print('antenna_pole =',calcular_tamanho(best_guess_params[2]))
    print('antenna_correction = ',best_guess_correction)
    print('actuator_range = ',best_guess_actuator)

    # Resultados gráfico:
    # pole = best_guess_params[0]
    # antenna_hinge = best_guess_params[1]
    # antenna_pole = pole[0]
    # result_array = np.add(pole[0], (0,0.1)) 
    # result_tuple = tuple(result_array)
    # antenna_pole[1] = result_tuple
    # numcolor = 0
    # for actuator_len in np.arange(calcular_tamanho(ref_actuator)*LOWBORDER,(calcular_tamanho(ref_actuator)*HIGHBORDER),calcular_tamanho(ref_actuator)/STEPS):
    #     active_actuator = [(0,0),(actuator_len,0)]
    #     try:
    #         hinge_angle = calcular_triangulo(calcular_tamanho(active_actuator),calcular_tamanho(pole),calcular_tamanho(antenna_hinge))
    #         actuator_angle = calcular_triangulo(calcular_tamanho(antenna_hinge),calcular_tamanho(pole),calcular_tamanho(active_actuator))
    #     except:
    #         continue
    #     new_hinge_pos = calcular_posicao(antenna_hinge,hinge_angle+(270*DEG2RAD))
    #     new_active_act_pos = calcular_posicao(active_actuator,(90*DEG2RAD)-actuator_angle)
    #     new_act_pos = calcular_posicao(ref_actuator,(90*DEG2RAD)-actuator_angle)
    #     new_antenna_pole = calcular_posicao(antenna_pole,(90*DEG2RAD)+hinge_angle)
    #     # Calcular sensibilidade do sistema
    #     # Ângulo atual da antena
    #     actual_angle = calcular_angulo(new_antenna_pole)/DEG2RAD
    #     # Ver se ângulo maior é maior que o ângulo esperado
    #     if actual_angle > max_angle_value_read:
    #         #Salvar parâmetros
    #         max_angle_found = True
    #         max_angle_depth = actuator_len
    #         max_angle_value_read = actual_angle
    #     #Ver se ele é menor que o menor ângulo maior que o esperado
    #     if actual_angle < min_angle_value_read:
    #         min_angle_found = True
    #         min_angle_depth = actuator_len
    #         min_angle_value_read = actual_angle
    #     for part in [pole,new_hinge_pos,new_act_pos,new_active_act_pos,new_antenna_pole]:
    #         x_coords,y_coords = vector2matplot(part)
    #         plt.plot(x_coords, y_coords, marker='o',color=colors[numcolor%len(colors)])
    #     numcolor += 1
    # plt.show()



if __name__ == "__main__":
    main()