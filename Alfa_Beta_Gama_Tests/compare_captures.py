import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt
import random
from collections import deque

ALPHA_AZ = 0.949
BETA_AZ = 0.267
GAMMA_AZ = 0.001
ALPHA_EL = 0.951
BETA_EL = 0.170
GAMMA_EL = 0.003

ERROR_TEST = False
REMOVE_PERCENT = 1
BURST_ERROR = True
BURST_INDEXES = 10

file_path = os.path.realpath(__file__)
script_dir = Path(file_path).parent # Get the script path
dir_path = script_dir/'tracks_test/' # Define the directory path with capture data

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
        # x_o_plus  = x_o + 360
        # x_o_minus = x_o - 360
        # if abs(x_o_plus - x_p) < abs(erro):
        #     erro = x_o_plus - x_p
        # if abs(x_o_minus - x_p) < abs(erro):
        #     erro = x_o_minus - x_p

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

def const_vel_extrapolation(x_obs, deltat, filter_arr):
    x_pred_list = []
    t_pred_list = []
    n = min(len(x_obs), len(deltat))
    if n <= 1:
        return np.array([]), np.array([]), 1e3

    last_idx = 0
    v_est = 0.0
    sum_sq_err = 0.0

    for idx in range(1, n - 2):
        dt_from_last = deltat[idx] - deltat[last_idx]
        x_p = x_obs[last_idx] + v_est * dt_from_last

        erro = x_obs[idx] - x_p
        sum_sq_err += erro ** 2

        t_pred_list.append(deltat[idx])
        x_pred_list.append(x_p)

        if filter_arr[idx]:
            if dt_from_last > 0:
                v_est = (x_obs[idx] - x_obs[last_idx]) / dt_from_last
            last_idx = idx

    rmse = np.sqrt(sum_sq_err / max(1, len(x_pred_list)))
    return np.array(t_pred_list), np.array(x_pred_list), rmse


def delayed_linear_interpolation(x_obs, deltat, filter_arr):
    """
    Interpolação linear com buffer deslizante de 2 amostras válidas (atraso de ~1 s):
    A cada passo idx, avalia o instante alvo t_target (atrasado em 1 passo em relação a idx)
    usando as duas últimas amostras válidas armazenadas no buffer.
    """
    n = min(len(x_obs), len(deltat))
    if n <= 2:
        return np.array([]), np.array([]), 1e3

    buf_t = deque(maxlen=2)
    buf_x = deque(maxlen=2)

    t_out = []
    x_out = []

    for idx in range(n - 2):
        if filter_arr[idx]:
            buf_t.append(float(deltat[idx]))
            buf_x.append(float(x_obs[idx]))

        # Instante a ser reconstruído com 1 amostra de atraso de chegada
        t_target = float(deltat[idx])

        if len(buf_t) == 2:
            t0, t1 = buf_t[-2], buf_t[-1]
            x0, x1 = buf_x[-2], buf_x[-1]

            if t1 > t0:
                # Extrapola/interpola linearmente a partir do par do buffer
                val = x0 + ((x1 - x0) / (t1 - t0)) * (t_target - t0)
            else:
                val = x1
        elif len(buf_t) == 1:
            val = buf_x[0]
        else:
            val = float(x_obs[idx])

        if idx >= 1:
            x_out.append(val)
        t_out.append(t_target)

    if not x_out:
        return np.array([]), np.array([]), 1e3

    x_out_arr = np.array(x_out)
    rmse = np.sqrt(np.mean((x_obs[2:-2] - x_out_arr[-1]) ** 2))
    return np.array(t_out[2:]), x_out_arr[:-1], rmse

def delayed_cubic_interpolation(x_obs, deltat, filter_arr):
    """
    Interpolação cúbica de Hermite com buffer deslizante de 4 amostras válidas:
    Mantém os últimos 4 pontos válidos (p0, p1, p2, p3) no buffer para calcular
    as derivadas locais e reconstruir o intervalo central/atual com suavidade.
    """
    n = min(len(x_obs), len(deltat))
    if n <= 2:
        return np.array([]), np.array([]), 1e3

    buf_t = deque(maxlen=4)
    buf_x = deque(maxlen=4)

    t_out = []
    x_out = []
    x_ref = []

    for idx in range(n - 2):
        if filter_arr[idx]:
            buf_t.append(float(deltat[idx]))
            buf_x.append(float(x_obs[idx]))

        t_target = float(deltat[idx])
        k_len = len(buf_t)

        if k_len >= 4:
            tv = list(buf_t)
            xv = list(buf_x)

            # Derivadas nos 4 pontos do buffer
            d = [0.0] * 4
            d[0] = (xv[1] - xv[0]) / max(tv[1] - tv[0], 1e-9)
            d[1] = 0.5 * (
                (xv[1] - xv[0]) / max(tv[1] - tv[0], 1e-9)
                + (xv[2] - xv[1]) / max(tv[2] - tv[1], 1e-9)
            )
            d[2] = 0.5 * (
                (xv[2] - xv[1]) / max(tv[2] - tv[1], 1e-9)
                + (xv[3] - xv[2]) / max(tv[3] - tv[2], 1e-9)
            )
            d[3] = (xv[3] - xv[2]) / max(tv[3] - tv[2], 1e-9)

            # Seleciona o segmento do buffer que contém ou precede t_target
            seg = 2
            if t_target <= tv[1]:
                seg = 0
            elif t_target <= tv[2]:
                seg = 1

            t_a, t_b = tv[seg], tv[seg + 1]
            x_a, x_b = xv[seg], xv[seg + 1]
            m_a, m_b = d[seg], d[seg + 1]

            h = t_b - t_a
            if h > 0:
                s = (t_target - t_a) / h
                s2 = s * s
                s3 = s2 * s

                h00 = 2.0 * s3 - 3.0 * s2 + 1.0
                h10 = s3 - 2.0 * s2 + s
                h01 = -2.0 * s3 + 3.0 * s2
                h11 = s3 - s2

                val = h00 * x_a + h10 * h * m_a + h01 * x_b + h11 * h * m_b
            else:
                val = x_b

        elif k_len >= 2:
            # Fallback linear no buffer enquanto há menos de 4 amostras válidas
            t0, t1 = buf_t[-2], buf_t[-1]
            x0, x1 = buf_x[-2], buf_x[-1]
            if t1 > t0:
                val = x0 + ((x1 - x0) / (t1 - t0)) * (t_target - t0)
            else:
                val = x1
        elif k_len == 1:
            val = buf_x[0]
        else:
            val = float(x_obs[idx])

        if idx >= 1:
            x_out.append(val)
            x_ref.append(float(x_obs[idx]))
        t_out.append(t_target)

    if not x_out:
        return np.array([]), np.array([]), 1e3

    x_out_arr = np.array(x_out)
    rmse = np.sqrt(np.mean((x_obs[2:-2] - x_out_arr[-1]) ** 2))
    return np.array(t_out[2:]), x_out_arr[:-1], rmse

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
    capture = 1
    show_plot = input("Mostrar plot? (s/n): ")
    abg_sum_az = 0
    vel_cte_sum_az = 0
    lin_sum_az = 0
    cub_sum_az = 0
    abg_sum_el = 0
    vel_cte_sum_el = 0
    lin_sum_el = 0
    cub_sum_el = 0
    for filename, timestamp, az_data, el_data in read_capture():
        real_tst = np.cumsum(timestamp)

        filter_arr = []
        still_burst = 0
        for k in range(len(timestamp)):
            if ERROR_TEST:
                val = random.random()
                if still_burst > 0:
                    still_burst -= 1
                    filter_arr.append(False)
                    continue
                if val < REMOVE_PERCENT / 100:
                    filter_arr.append(False)
                    if BURST_ERROR:
                        still_burst = BURST_INDEXES - 1
                else:
                    filter_arr.append(True)
            else:
                filter_arr.append(True)
        filter_arr = np.array(filter_arr, dtype=bool)
        # Garante que a primeira e a última amostra estejam disponíveis como âncoras
        filter_arr[0] = True
        filter_arr[-1] = True

        # 1. Filtro Alfa-Beta-Gama (mantendo chamada exatamente como no original)
        t_az_abg, az_abg, rmse_az_abg, _, _ = alfa_beta_gamma_filter_fast(az_data, real_tst, ALPHA_AZ, BETA_AZ, GAMMA_AZ, filter_arr)
        t_el_abg, el_abg, rmse_el_abg, _, _ = alfa_beta_gamma_filter_fast(el_data, real_tst, ALPHA_EL, BETA_EL, GAMMA_EL, filter_arr)

        # 2. Extrapolação de Velocidade Constante
        t_az_cv, az_cv, rmse_az_cv = const_vel_extrapolation(az_data, real_tst, filter_arr)
        t_el_cv, el_cv, rmse_el_cv = const_vel_extrapolation(el_data, real_tst, filter_arr)

        # 3. Interpolação Linear (atraso de 1 s)
        t_az_lin, az_lin, rmse_az_lin = delayed_linear_interpolation(az_data, real_tst, filter_arr)
        t_el_lin, el_lin, rmse_el_lin = delayed_linear_interpolation(el_data, real_tst, filter_arr)

        # 4. Interpolação Cúbica (atraso de 1 s)
        t_az_cub, az_cub, rmse_az_cub = delayed_cubic_interpolation(az_data, real_tst, filter_arr)
        t_el_cub, el_cub, rmse_el_cub = delayed_cubic_interpolation(el_data, real_tst, filter_arr)

        # 4. Posição anterior
        t_az_cub, az_cub, rmse_az_cub = delayed_cubic_interpolation(az_data, real_tst, filter_arr)
        t_el_cub, el_cub, rmse_el_cub = delayed_cubic_interpolation(el_data, real_tst, filter_arr)

        for k in range(2):
            if show_plot == 'n':
                continue
            if len(str(filename)) == 0:
                continue
            # plot and replot with new name
            # --- GRÁFICO 1: Comparação de Trajetórias (Azimute e Elevação) ---
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)

            # Subplot Azimute
            ax1.plot(real_tst[:-2], az_data[:-2], "k-", linewidth=2.2, label="SatDump / SGP4 ESP32 (Ref)")
            ax1.plot(t_az_abg, az_abg, "--", color="tab:red", linewidth=1.8, label=f"α-β-γ (RMSE: {rmse_az_abg:.3f}°)")
            ax1.plot(t_az_cv, az_cv, "-.", color="tab:orange", linewidth=1.6, label=f"Vel. Constante (RMSE: {rmse_az_cv:.3f}°)")
            ax1.plot(t_az_lin, az_lin, ":", color="tab:blue", linewidth=1.8, label=f"Interp. Linear (RMSE: {rmse_az_lin:.3f}°)")
            ax1.plot(t_az_cub, az_cub, "--", color="tab:green", linewidth=1.8, label=f"Interp. Cúbica (RMSE: {rmse_az_cub:.3f}°)")
            if ERROR_TEST:
                ax1.plot(real_tst[~filter_arr], az_data[~filter_arr], "rx", markersize=6, label="Amostra Perdida")
            ax1.set_ylabel("Azimute [º]")
            ax1.set_title(f"Comparação de Métodos de Rastreio — {filename}")
            ax1.grid(True, which="both", alpha=0.4)
            ax1.legend(loc="best", fontsize=9)

            # Subplot Elevação
            ax2.plot(real_tst[:-2], el_data[:-2], "k-", linewidth=2.2, label="SatDump / SGP4 ESP32 (Ref)")
            ax2.plot(t_el_abg, el_abg, "--", color="tab:red", linewidth=1.8, label=f"α-β-γ (RMSE: {rmse_el_abg:.3f}°)")
            ax2.plot(t_el_cv, el_cv, "-.", color="tab:orange", linewidth=1.6, label=f"Vel. Constante (RMSE: {rmse_el_cv:.3f}°)")
            ax2.plot(t_el_lin, el_lin, ":", color="tab:blue", linewidth=1.8, label=f"Interp. Linear (RMSE: {rmse_el_lin:.3f}°)")
            ax2.plot(t_el_cub, el_cub, "--", color="tab:green", linewidth=1.8, label=f"Interp. Cúbica (RMSE: {rmse_el_cub:.3f}°)")
            if ERROR_TEST:
                ax2.plot(real_tst[~filter_arr], el_data[~filter_arr], "rx", markersize=6, label="Amostra Perdida")
            ax2.set_xlabel("Tempo [s]")
            ax2.set_ylabel("Elevação [º]")
            ax2.grid(True, which="both", alpha=0.4)
            ax2.legend(loc="best", fontsize=9)

            plt.tight_layout()
            plt.show()

            if k == 0:
                filename = input("Novo título: ")

        capture += 1
        abg_sum_az += rmse_az_abg
        abg_sum_el += rmse_el_abg
        vel_cte_sum_az += rmse_az_cv
        vel_cte_sum_el += rmse_el_cv
        lin_sum_az += rmse_az_lin
        lin_sum_el += rmse_el_lin
        cub_sum_az += rmse_az_cub
        cub_sum_el += rmse_el_cub
    print(f"Total de {capture} capturas...")
    print("Cálculo RMS Médio AZ:")
    print(f"ABG: {abg_sum_az/(capture):.4f}")
    print(f"VEL CTE: {vel_cte_sum_az/(capture):.4f}")
    print(f"LIN: {lin_sum_az/(capture):.4f}")
    print(f"CUBICO: {cub_sum_az/(capture):.4f}")
    print("Cálculo RMS Médio EL:")
    print(f"ABG: {abg_sum_el/(capture):.4f}")
    print(f"VEL CTE: {vel_cte_sum_el/(capture):.4f}")
    print(f"LIN: {lin_sum_el/(capture):.4f}")
    print(f"CUBICO: {cub_sum_el/(capture):.4f}")