import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import numpy as np
from numba import njit
import ast

STEP = 0.001

with open("./az_dict.json", "r") as file:
    data_az = json.load(file)

with open("./el_dict.json", "r") as file:
    data_el = json.load(file)

@njit
def alfa_beta_gamma_filter_fast(x_obs, deltat, alpha, beta, gamma):
    n = min(len(x_obs), len(deltat))
    if n <= 1:
        return 1e3

    x_p = x_obs[0]
    v_p = 0.0
    a_p = 0.0

    sum_sq_err = 0.0

    for idx in range(1, n):
        x_o = x_obs[idx]
        dt = deltat[idx]

        erro = x_o - x_p
        if erro > 1e3:
            return 1e3

        x_s = x_p + alpha * erro
        v_s = v_p + (beta / dt) * erro
        a_s = a_p + ((2.0 * gamma) / (dt**2)) * erro

        sum_sq_err += (x_o - x_p) ** 2

        # Predição para k+1
        x_p = x_s + (dt * v_s) + (0.5 * (dt**2) * a_s)
        v_p = v_s + (dt * a_s)
        a_p = a_s

    rmse = np.sqrt(sum_sq_err / (n - 1))
    return rmse

def filtro_abg_otimo_fast(t_obs, x_obs, alpha, beta, gamma):
    # Converter entradas para float64 continuous arrays para o Numba
    t_obs_arr = np.ascontiguousarray(t_obs, dtype=np.float64)
    x_obs_arr = np.ascontiguousarray(x_obs, dtype=np.float64)

    rmse = alfa_beta_gamma_filter_fast(
        x_obs_arr, t_obs_arr, alpha, beta, gamma
    )
    return (round(alpha, 4), round(beta, 4), round(gamma, 4)), rmse

az_min_rms = np.inf
az_min_key = ''

for az_key in data_az.keys():
    rms_mean = np.mean(data_az[az_key])
    if rms_mean < az_min_rms:
        az_min_rms = rms_mean
        az_min_key = az_key

el_min_rms = np.inf
el_min_key = ''

for el_key in data_el.keys():
    rms_mean = np.mean(data_el[el_key])
    if rms_mean < el_min_rms:
        el_min_rms = rms_mean
        el_min_key = el_key

print("---AZIMUTE---")
print(f"Melhores valores de alfa beta gamma: {az_min_key}")
print(f"Erro médio: {az_min_rms}")

print("\n---ELEVAÇÃO---")
print(f"Melhores valores de alfa beta gamma: {el_min_key}")
print(f"Erro médio: {el_min_rms}")

print("Carregando valores das passagens...")
# Define the directory path
dir_path = Path('./tracks/')

timestamp = []
az_data = []
el_data = []

# Loop through all files in the immediate folder
for file_path in dir_path.iterdir():
    if file_path.is_file():
        print(f"--- Reading: {file_path.name} ---",end='\r')
        tst = []
        az = []
        el = []
        # Open and read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            lines =  file.readlines()
            if len(lines) == 1:
                continue
            got_init_time = False
            init_time = 0
            for content in lines:
                data = content.replace('\n','').split('P')
                if not got_init_time:
                    tst.append(0)
                    init_time = float(data[0].strip())
                    got_init_time = True
                else:
                    actual_time = float(data[0].strip())
                    tst.append(actual_time-init_time)
                    init_time = actual_time
                az.append(float(data[1].strip().split(' ')[0]))
                el.append(float(data[1].strip().split(' ')[1]))
        timestamp.append(tst)
        az_data.append(az)
        el_data.append(el)


print("Procurando melhores valores para o Azimute...")
searching = True
retry = 0
alpha_min, beta_min, gamma_min = ast.literal_eval(az_min_key)
step = STEP
new_alpha, new_beta, new_gamma = (0,0,0)
while searching:
    changed = False
    print(f"Trying with: Alpha = {alpha_min}, Beta = {beta_min}, Gamma = {gamma_min}")
    for alpha_search in [alpha_min,alpha_min+step,alpha_min-step]:
        for beta_search in [beta_min,beta_min+step,beta_min-step]:
            for gamma_search in [gamma_min,gamma_min+step,gamma_min-step]:
                test_list = []
                for stlt_pass in range(len(timestamp)):
                    _, rmse_az = filtro_abg_otimo_fast(timestamp[stlt_pass],az_data[stlt_pass], alpha_search, beta_search, gamma_search) # config_el, rmse_el = filtro_abg_otimo_fast(timestamp[stlt_pass],el_data[stlt_pass], alpha_search, beta_search, gamma_search)
                    test_list.append(rmse_az)
                mean_rmse = np.mean(test_list)
                if mean_rmse < az_min_rms:
                    az_min_rms = mean_rmse
                    changed = True
                    new_alpha = alpha_search if alpha_search > 0 else 0
                    new_beta  = beta_search if beta_search > 0 else 0
                    new_gamma = gamma_search if gamma_search > 0 else 0
    if not changed:
        if retry >= 3:
            searching = False
        else:
            retry +=1
            step = step/2
    else:
        retry = 0
        alpha_min = new_alpha
        beta_min  = new_beta
        gamma_min = new_gamma

print("Procurando melhores valores para a Elevação...")
searching = True
retry = 0
alpha_min, beta_min, gamma_min = ast.literal_eval(el_min_key)
step = STEP
new_alpha, new_beta, new_gamma = (0,0,0)
while searching:
    changed = False
    print(f"Trying with: Alpha = {alpha_min}, Beta = {beta_min}, Gamma = {gamma_min}")
    for alpha_search in [alpha_min,alpha_min+step,alpha_min-step]:
        for beta_search in [beta_min,beta_min+step,beta_min-step]:
            for gamma_search in [gamma_min,gamma_min+step,gamma_min-step]:
                test_list = []
                for stlt_pass in range(len(timestamp)):
                    _, rmse_el = filtro_abg_otimo_fast(timestamp[stlt_pass],el_data[stlt_pass], alpha_search, beta_search, gamma_search) # config_el, rmse_el = filtro_abg_otimo_fast(timestamp[stlt_pass],el_data[stlt_pass], alpha_search, beta_search, gamma_search)
                    test_list.append(rmse_el)
                mean_rmse = np.mean(test_list)
                if mean_rmse < el_min_rms:
                    el_min_rms = mean_rmse
                    changed = True
                    new_alpha = alpha_search if alpha_search > 0 else 0
                    new_beta  = beta_search if beta_search > 0 else 0
                    new_gamma = gamma_search if gamma_search > 0 else 0
    if not changed:
        if retry >= 3:
            searching = False
        else:
            retry +=1
            step = step/2
    else:
        retry = 0
        alpha_min = new_alpha
        beta_min  = new_beta
        gamma_min = new_gamma

print(f"Best value AZ: Alpha = {alpha_min}, Beta = {beta_min}, Gamma = {gamma_min}, rmse = {az_min_rms}")
print(f"Best value EL: Alpha = {alpha_min}, Beta = {beta_min}, Gamma = {gamma_min}, rmse = {el_min_rms}")