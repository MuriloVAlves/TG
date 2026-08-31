import json
from pathlib import Path
import numpy as np
from numba import njit

MAX_ALPHA_AZ = 2
MAX_ALPHA_EL = 2
N_STEPS   = 30
ITERATIONS = 10
N_BEST_RESULTS = 1


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


def filtro_abg_otimo_fast(t_obs, x_obs, max_alpha, n_steps):
    rmse_list = []
    config_list = []

    # Converter entradas para float64 continuous arrays para o Numba
    t_obs_arr = np.ascontiguousarray(t_obs, dtype=np.float64)
    x_obs_arr = np.ascontiguousarray(x_obs, dtype=np.float64)

    step_alpha = max_alpha / n_steps
    step_grid = max_alpha / (2 * n_steps)

    for alpha in np.arange(0, max_alpha, step_alpha):
        beta_max = 4.0 - 2.0 * alpha
        for beta in np.arange(0, beta_max, step_grid):
            gamma_max = (4.0 * alpha * beta) / (2.0 - alpha) if alpha < 2.0 else 0.0
            for gamma in np.arange(0, gamma_max, step_grid):

                rmse = alfa_beta_gamma_filter_fast(
                    x_obs_arr, t_obs_arr, alpha, beta, gamma
                )

                rmse_list.append(rmse)
                config_list.append((round(alpha, 4), round(beta, 4), round(gamma, 4)))

    return config_list, rmse_list

# ==============================================================================
# PROGRAMA PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    from pathlib import Path

    # Define the directory path
    dir_path = Path('./track_test/')

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

    print("\nStarting simulations...")
    az_dict = {}
    el_dict = {}
    def adicionar_dado_az(chave, dado):
        # Se a chave não existir, inicializa com lista vazia [].
        # Em seguida, faz o append do dado.
        az_dict.setdefault(chave, []).append(dado)

    def adicionar_dado_el(chave, dado):
        # Se a chave não existir, inicializa com lista vazia [].
        # Em seguida, faz o append do dado.
        el_dict.setdefault(chave, []).append(dado)

    for stlt_pass in range(len(timestamp)):
        print(f"Pass {stlt_pass+1}/{len(timestamp)}"+" "*50)
        for iteration in range(ITERATIONS):
            print(f"ITERATION {iteration+1}"+" "*50)
            config_az, rmse_az = filtro_abg_otimo_fast(timestamp[stlt_pass],az_data[stlt_pass],MAX_ALPHA_AZ,N_STEPS)
            config_el, rmse_el = filtro_abg_otimo_fast(timestamp[stlt_pass],el_data[stlt_pass],MAX_ALPHA_EL,N_STEPS)
            for idx in range(len(config_az)):
                adicionar_dado_az(str(config_az[idx]),rmse_az[idx])
            for idx in range(len(config_el)):
                adicionar_dado_el(str(config_el[idx]),rmse_el[idx])
            # Check AZ
            list_counter = 0
            list_alpha = []
            list_comparer = []
            last_alpha = -1
            for element in range(len(config_az)):
                alpha, beta, gamma = config_az[element]
                if alpha != last_alpha:
                    if list_counter != 0:
                        list_alpha.append(last_alpha)
                        list_comparer.append(list_counter)
                    list_counter = 0
                    last_alpha = alpha
                list_counter += rmse_az[element]
            MAX_VAL = max(list_comparer)+1
            MAX_ALPHA_AZ = 0
            for k in range(N_BEST_RESULTS):
                min_val = min(list_comparer)
                min_val_idx = list_comparer.index(min_val)
                if MAX_ALPHA_AZ < list_alpha[min_val_idx]:
                    MAX_ALPHA_AZ = list_alpha[min_val_idx]
                list_comparer[min_val_idx] = MAX_VAL

            # Check EL
            list_counter = 0
            list_alpha = []
            list_comparer = []
            last_alpha = -1
            for element in range(len(config_az)):
                alpha, beta, gamma = config_el[element]
                if alpha != last_alpha:
                    if list_counter != 0:
                        list_alpha.append(last_alpha)
                        list_comparer.append(list_counter)
                    list_counter = 0
                    last_alpha = alpha
                list_counter += rmse_el[element]
            MAX_VAL = max(list_comparer)+1
            MAX_ALPHA_EL = 0
            for k in range(N_BEST_RESULTS):
                min_val = min(list_comparer)
                min_val_idx = list_comparer.index(min_val)
                if MAX_ALPHA_EL < list_alpha[min_val_idx]:
                    MAX_ALPHA_EL = list_alpha[min_val_idx]
                list_comparer[min_val_idx] = MAX_VAL

    with open("./az_dict.json", "w", encoding="utf-8") as f:
        json.dump(az_dict, f, ensure_ascii=False, indent=4)
    with open("./el_dict.json", "w", encoding="utf-8") as f:
        json.dump(el_dict, f, ensure_ascii=False, indent=4)

    # print(f"--- Configuração Ótima Encontrada ---")
    # print(f"Alpha (α): {a_opt}")
    # print(f"Beta  (β): {b_opt}")
    # print(f"Gamma (γ): {g_opt}")
    # print(f"Menor RMSE obtido: {rmse_min:.4f}")