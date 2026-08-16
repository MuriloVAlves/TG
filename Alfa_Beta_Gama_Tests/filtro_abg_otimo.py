import numpy as np
import json

def alfa_beta_gamma_filter(x_obs,alpha,beta,gamma,deltat):
    # --- Execução rápida do Filtro ---
    x_p, v_p, a_p = x_obs[0], 0.0, 0.0
    x_p_list = []

    if alpha == 1:
        pass

    for idx in range(1,min(len(x_obs),len(deltat))):
        x_o = x_obs[idx]
        dt = deltat[idx]
        erro = x_o - x_p
        x_s = x_p + alpha * erro
        v_s = v_p + (beta / dt) * erro
        a_s = a_p + ((2.0 *gamma) / (dt ** 2)) * erro
        x_p_list.append(x_p)

        # Predição do próximo passo (k+1)
        x_p = x_s + (dt * v_s) + (0.5 * (dt ** 2) * a_s)
        v_p = v_s + (dt * a_s)
        a_p = a_s

    # --- Cálculo do Erro Médio Quadrático (RMSE) ---
    rmse = np.sqrt(np.mean((np.array(np.array(x_obs[1:])) - np.array(x_p_list)) ** 2))
    return rmse

def filtro_abg_otimo(t_obs,x_obs):
    """
    Varia alpha, beta e gamma em passos de 0.1 dentro da região de estabilidade de Jury
    e retorna o menor Erro Quadrático Médio (MSE/RMSE) e os coeficientes ótimos.

    :param t: Array com os instantes de tempo
    :param x_obs: Array com as posições observadas/medidas (com ruído)
    :param x_ref: Array opcional com a posição real (se conhecido). Se None, usa x_obs.
    """

    rmse_list = []
    config_list = []

    # Variação em passos de 0.1 dentro dos limites de Jury:
    # 0 < alpha < 2
    for alpha in np.arange(0, 2.0, 0.1):
        # 0 < beta < 4 - 2*alpha
        for beta in np.arange(0, 4.0 - 2.0 * alpha, 0.05):
            gamma_max = (4.0 * alpha * beta) / (2.0 - alpha)
            # 0 < gamma < gamma_max
            for gamma in np.arange(0, gamma_max, 0.05):
                # Calcular filtro
                print(f"Alpha: {alpha}; Beta: {beta}; Gamma: {gamma}",end='\r')
                rmse = alfa_beta_gamma_filter(x_obs,alpha,beta,gamma,t_obs)

                # Salvar configuração
                rmse_list.append(rmse)
                config_list.append((round(alpha, 2), round(beta, 2), round(gamma, 2)))
    return config_list, rmse_list


# ==============================================================================
# EXEMPLO DE USO
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
        print(f"Pass {stlt_pass+1}/{len(timestamp)}"+" "*150)
        config_az, rmse_az = filtro_abg_otimo(timestamp[stlt_pass],az_data[stlt_pass])
        config_el, rmse_el = filtro_abg_otimo(timestamp[stlt_pass],el_data[stlt_pass])
        for idx in range(len(config_az)):
            adicionar_dado_az(str(config_az[idx]),rmse_az[idx])
        for idx in range(len(config_el)):
            adicionar_dado_el(str(config_el[idx]),rmse_el[idx])

    with open("./az_dict.json", "w", encoding="utf-8") as f:
        json.dump(az_dict, f, ensure_ascii=False, indent=4)
    with open("./el_dict.json", "w", encoding="utf-8") as f:
        json.dump(el_dict, f, ensure_ascii=False, indent=4)

    # print(f"--- Configuração Ótima Encontrada ---")
    # print(f"Alpha (α): {a_opt}")
    # print(f"Beta  (β): {b_opt}")
    # print(f"Gamma (γ): {g_opt}")
    # print(f"Menor RMSE obtido: {rmse_min:.4f}")