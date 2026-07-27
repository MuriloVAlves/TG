import numpy as np

def filtro_abg_otimo(t, x_obs, x_ref=None):
    """
    Varia alpha, beta e gamma em passos de 0.1 dentro da região de estabilidade de Jury
    e retorna o menor Erro Quadrático Médio (MSE/RMSE) e os coeficientes ótimos.
    
    :param t: Array com os instantes de tempo
    :param x_obs: Array com as posições observadas/medidas (com ruído)
    :param x_ref: Array opcional com a posição real (se conhecido). Se None, usa x_obs.
    """
    dt = t[1] - t[0] if len(t) > 1 else 1.0
    x_alvo = x_obs if x_ref is None else x_ref
    
    melhor_rmse = float('inf')
    melhor_config = None

    # Variação em passos de 0.1 dentro dos limites de Jury:
    # 0 < alpha < 2
    for alpha in np.arange(0.1, 2.0, 0.1):
        # 0 < beta < 4 - 2*alpha
        for beta in np.arange(0.1, 4.0 - 2.0 * alpha, 0.1):
            gamma_max = (4.0 * alpha * beta) / (2.0 - alpha)
            # 0 < gamma < gamma_max
            for gamma in np.arange(0.1, gamma_max, 0.1):
                
                # --- Execução rápida do Filtro ---
                x_p, v_p, a_p = x_obs[0], 0.0, 0.0
                x_s_list = []
                
                for x_o in x_obs:
                    inovacao = x_o - x_p
                    x_s = x_p + alpha * inovacao
                    v_s = v_p + (beta / dt) * inovacao
                    a_s = a_p + (gamma / (2.0 * (dt ** 2))) * inovacao
                    x_s_list.append(x_s)
                    
                    # Predição do próximo passo (k+1)
                    x_p = x_s + dt * v_s + 0.5 * (dt ** 2) * a_s
                    v_p = v_s + dt * a_s
                    a_p = a_s
                
                # --- Cálculo do Erro Médio Quadrático (RMSE) ---
                rmse = np.sqrt(np.mean((np.array(np.array(x_alvo)) - np.array(x_s_list)) ** 2))
                
                if rmse < melhor_rmse:
                    melhor_rmse = rmse
                    melhor_config = (round(alpha, 1), round(beta, 1), round(gamma, 1))

    return melhor_config, melhor_rmse

# ==============================================================================
# EXEMPLO DE USO
# ==============================================================================
if __name__ == "__main__":
    # Array de tempo
    t = np.arange(0, 100, 1.0)
    
    # Trajetória simulada com ruído
    np.random.seed(42)
    x_real = 45.0 + 0.5 * t + 0.02 * (t ** 2) - 0.0001 * (t ** 3)
    x_observado = x_real + np.random.normal(0, 1.5, size=len(t))

    # Executa a otimização comparando com a trajetória real (ou com x_observado)
    (a_opt, b_opt, g_opt), rmse_min = filtro_abg_otimo(t, x_observado, x_ref=x_real)

    print(f"--- Configuração Ótima Encontrada ---")
    print(f"Alpha (α): {a_opt}")
    print(f"Beta  (β): {b_opt}")
    print(f"Gamma (γ): {g_opt}")
    print(f"Menor RMSE obtido: {rmse_min:.4f}")