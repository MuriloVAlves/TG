import json
from pathlib import Path
import numpy as np
import time
from numba import njit

MAX_ALPHA = 2
N_STEPS   = 30
ITERATIONS = 1
N_BEST_RESULTS = 10


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

# ==============================================================================
# PROGRAMA PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    from pathlib import Path

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

    def lazy_alpha_beta_gamma(max_alpha,n_steps):
        step_alpha = max_alpha / n_steps
        step_grid = max_alpha / (2 * n_steps)
        for alpha in np.arange(0, max_alpha, step_alpha):
            beta_max = 4.0 - 2.0 * alpha
            for beta in np.arange(0, beta_max, step_grid):
                gamma_max = (4.0 * alpha * beta) / (2.0 - alpha) if alpha < 2.0 else 0.0
                for gamma in np.arange(0, gamma_max, step_grid):
                    yield (alpha,beta,gamma)

    test_filter   = lazy_alpha_beta_gamma(MAX_ALPHA,N_STEPS)
    print("Verificando o número máximo de filtros encontrados...")
    max_filters = 0
    for filtro in test_filter:
        max_filters += 1
    filter_params = lazy_alpha_beta_gamma(MAX_ALPHA,N_STEPS)
    init = time.time()
    elapsed = 0
    counter = 0
    ETA_time = 0
    for alpha, beta, gamma in filter_params:
        counter += 1
        for stlt_pass in range(len(timestamp)):
            if (time.time()-elapsed) > 1:
                ETA_time = (max_filters-counter)*((time.time()-init)/counter)
                elapsed = time.time()
            print(f"[ETA: {ETA_time//60:.0f}:{int(ETA_time%60):02d}] Filtro {counter}/{max_filters}: Pass {stlt_pass+1}/{len(timestamp)} ", end='\r')
            config_az, rmse_az = filtro_abg_otimo_fast(timestamp[stlt_pass],az_data[stlt_pass], alpha, beta, gamma)
            config_el, rmse_el = filtro_abg_otimo_fast(timestamp[stlt_pass],el_data[stlt_pass], alpha, beta, gamma)
            for idx in range(len(config_az)):
                adicionar_dado_az(str(config_az),rmse_az)
            for idx in range(len(config_el)):
                adicionar_dado_el(str(config_el),rmse_el)
    print("Gravando dados em arquivos...")
    with open("./az_dict.json", "w", encoding="utf-8") as f:
        json.dump(az_dict, f, ensure_ascii=False, indent=4)
    with open("./el_dict.json", "w", encoding="utf-8") as f:
        json.dump(el_dict, f, ensure_ascii=False, indent=4)

    # print(f"--- Configuração Ótima Encontrada ---")
    # print(f"Alpha (α): {a_opt}")
    # print(f"Beta  (β): {b_opt}")
    # print(f"Gamma (γ): {g_opt}")
    # print(f"Menor RMSE obtido: {rmse_min:.4f}")