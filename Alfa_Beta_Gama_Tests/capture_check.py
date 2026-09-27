import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt
import random

ALPHA_AZ = 0.937
BETA_AZ = 0.3
GAMMA_AZ = 0.1
ALPHA_EL = 0.939
BETA_EL = 0.17
GAMMA_EL = 0.0

ERROR_TEST = False
REMOVE_PERCENT = 10
BURST_ERROR = True
BURST_INDEXES = 5

file_path = os.path.realpath(__file__)
script_dir = Path(file_path).parent # Get the script path
dir_path = script_dir/'tracks/' # Define the directory path with capture data

def alfa_beta_gamma_filter_fast(x_obs, deltat, alpha, beta, gamma, filter_arr):
    x_prediction = []
    t_prediction = []
    t_smoothed = []
    x_smoothed = []
    n = min(len(x_obs), len(deltat))
    if n <= 1:
        return 1e3

    x_p = x_obs[0]
    x_s = x_obs[0]
    v_p = v_s = 0.0
    a_p = a_s = 0.0

    sum_sq_err = 0.0
    sum_delta_t = 0.0
    last_idx = 0

    for idx in range(1, n-2):
        x_o = x_obs[idx]
        dt = deltat[idx] - deltat[last_idx]

        erro = x_o - x_p
        # Unwrap function for the filter
        x_o_plus  = x_o + 360
        x_o_minus = x_o - 360
        if abs(x_o_plus - x_p) < abs(erro):
            erro = x_o_plus - x_p
        if abs(x_o_minus - x_p) < abs(erro):
            erro = x_o_minus - x_p

        sum_sq_err += (x_o - x_p) ** 2

        if filter_arr[idx]:
            x_s = x_p + alpha * erro
            v_s = v_p + (beta / dt) * erro
            a_s = a_p + ((2.0 * gamma) / (dt**2)) * erro
            last_idx = idx

        # Predição para k
        x_prediction.append(x_p)
        t_prediction.append(deltat[idx])

        # Predição para k+1
        x_p = x_s + (dt * v_s) + (0.5 * (dt**2) * a_s)
        v_p = v_s + (dt * a_s)
        a_p = a_s
        t_smoothed.append(deltat[idx])
        x_smoothed.append(x_s)

    rmse = np.sqrt(sum_sq_err / (n - 1))
    return t_prediction, x_prediction, rmse, t_smoothed, x_smoothed

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
        still_burst = 0
        for k in range(len(timestamp)):
            if ERROR_TEST:
                val = random.random()
                if still_burst > 0:
                    still_burst -= 1
                    filter_arr.append(False)
                    continue
                if val < REMOVE_PERCENT/100:
                    filter_arr.append(False)
                    if BURST_ERROR:
                        still_burst = BURST_INDEXES-1
                else:
                    filter_arr.append(True)
            else:
                filter_arr.append(True)
        filter_arr = np.array(filter_arr)
        t_az,az_filter, rmse_az, pred_t_az, pred_val_az = alfa_beta_gamma_filter_fast(az_data,real_tst,ALPHA_EL,BETA_EL,GAMMA_EL,filter_arr)
        t_el,el_filter, rmse_el, pred_t_el, pred_val_el = alfa_beta_gamma_filter_fast(el_data,real_tst,ALPHA_AZ,BETA_AZ,GAMMA_AZ,filter_arr)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(real_tst[:-2],az_data[:-2],'-',color="tab:blue")
        ax.plot(real_tst[:-2],el_data[:-2],'-',color="tab:orange")
        ax.plot(t_az,az_filter,'-.',color="tab:red")
        ax.plot(t_el,el_filter,'-.',color="tab:green")
        if ERROR_TEST:
            ax.plot(pred_t_az,pred_val_az,'.',color="tab:purple")
            ax.plot(pred_t_el,pred_val_el,'.',color="tab:cyan")
            ax.plot(real_tst[~filter_arr],az_data[~filter_arr],'x',color='r')
            ax.plot(real_tst[~filter_arr],el_data[~filter_arr],'x',color='r')
        # plt.title(f"{k}/{len(os.listdir(dir_path))} {filename} - rmse: {rmse_az:.2f} {rmse_el:.2f}")
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        # Bottom Left
        # ax.text(0.05,0.05,f"RMS AZ: {rmse_az:.2f}\nRMS EL:{rmse_el:.2f}",bbox=props, horizontalalignment='left',verticalalignment='bottom',transform = ax.transAxes)
        # center Left
        ax.text(0.05,0.5,f"RMS AZ: {rmse_az:.2f}\nRMS EL:{rmse_el:.2f}",bbox=props, horizontalalignment='left',verticalalignment='center',transform = ax.transAxes)
        # Top Right
        # ax.text(0.95,0.90,f"RMS AZ: {rmse_az:.2f}\nRMS EL:{rmse_el:.2f}",bbox=props, horizontalalignment='right',verticalalignment='top',transform = ax.transAxes)
        ax.set_title("Ângulo do Satélite X Tempo")
        ax.set_xlabel("Tempo [s]")
        ax.set_ylabel("Ângulo [º]")
        ax.grid(True,'both')
        ax.legend(["Real AZ", "Real EL", "Pred AZ", "Pred EL"])
        plt.show()
        k += 1