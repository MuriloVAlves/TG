import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt
import random

ALPHA_AZ = 0.933
BETA_AZ = 0.0333
GAMMA_AZ = 0.0
ALPHA_EL = 0.933
BETA_EL = 0.2
GAMMA_EL = 0.0

RANDOM_TEST = False
REMOVE_PERCENT = 5

file_path = os.path.realpath(__file__)
script_dir = Path(file_path).parent # Get the script path
dir_path = script_dir/'tracks/' # Define the directory path with capture data

def alfa_beta_gamma_filter_fast(x_obs, deltat, alpha, beta, gamma):
    x_prediction = []
    t_prediction = []
    n = min(len(x_obs), len(deltat))
    if n <= 1:
        return 1e3

    x_p = x_obs[0]
    v_p = 0.0
    a_p = 0.0

    sum_sq_err = 0.0
    sum_delta_t = 0.0

    for idx in range(1, n):
        x_o = x_obs[idx]
        dt = deltat[idx] - deltat[idx-1]

        erro = x_o - x_p
        # Unwrap function for the filter
        x_o_plus  = x_o + 360
        x_o_minus = x_o - 360
        if abs(x_o_plus - x_p) < abs(erro):
            erro = x_o_plus - x_p
        if abs(x_o_minus - x_p) < abs(erro):
            erro = x_o_minus - x_p

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
        x_prediction.append(x_p)
        sum_delta_t += dt
        t_prediction.append(sum_delta_t)

    rmse = np.sqrt(sum_sq_err / (n - 1))
    return t_prediction, x_prediction, rmse

def read_capture():
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
                filename = (file_path.name)
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
            # Unwrap values
            az_unwrapped = []
            x_p = az[0]
            for x_o in az:
                x_o_plus  = x_o + 360
                x_o_minus = x_o - 360
                x_pred = x_o
                erro = x_o - x_p
                if abs(x_o_plus - x_p) < abs(erro):
                    erro = x_o_plus - x_p
                    x_pred = x_o_plus
                if abs(x_o_minus - x_p) < abs(erro):
                    erro = x_o_minus - x_p
                    x_pred = x_o_minus
                az_unwrapped.append(x_pred)
                x_p = x_pred
        yield (np.array(filename),np.array(tst),np.array(az_unwrapped),np.array(el))
if __name__ == "__main__":
    k = 1
    for filename,timestamp,az_data,el_data in read_capture():
        real_tst = []
        tst_change = 0
        for t in timestamp:
            tst_change += t
            real_tst.append(tst_change)
        real_tst = np.array(real_tst)
        filter_arr = []
        for k in range(len(timestamp)):
            if RANDOM_TEST:
                val = random.random()
                if val < REMOVE_PERCENT/100:
                    filter_arr.append(False)
                else:
                    filter_arr.append(True)
            else:
                filter_arr.append(True)
        t_az,az_filter, rmse_az = alfa_beta_gamma_filter_fast(az_data[filter_arr],real_tst[filter_arr],ALPHA_EL,BETA_EL,GAMMA_EL)
        t_el,el_filter, rmse_el = alfa_beta_gamma_filter_fast(el_data[filter_arr],real_tst[filter_arr],ALPHA_AZ,BETA_AZ,GAMMA_AZ)
        plt.plot(real_tst,az_data,'.',color="tab:blue")
        plt.plot(real_tst,el_data,'.',color="tab:orange")
        plt.plot(t_az,az_filter,'-.',color="tab:red")
        plt.plot(t_el,el_filter,'-.',color="tab:green")
        # plt.title(f"{k}/{len(os.listdir(dir_path))} {filename} - rmse: {rmse_az:.2f} {rmse_el:.2f}")
        plt.title(f"Erro : {rmse_az:.2f} {rmse_el:.2f}")
        plt.xlabel("Tempo [s]")
        plt.ylabel("Ângulo [º]")
        plt.legend(["Real AZ", "Real EL", "Pred AZ", "Pred EL"])
        plt.show()
        k += 1