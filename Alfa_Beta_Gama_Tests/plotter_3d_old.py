import numpy as np
import matplotlib.pyplot as plt

class PlotterFiltroABG:
    """
    Classe responsável por mapear o erro (RMSE) nas regiões de estabilidade de Jury
    e plotar os resultados para os coeficientes alpha, beta e gamma.
    """
    def __init__(self, t, x_obs, x_ref=None):
        self.t = np.array(t)
        self.x_obs = np.array(x_obs)
        self.x_ref = np.array(x_ref) if x_ref is not None else self.x_obs
        self.dt = self.t[1] - self.t[0] if len(self.t) > 1 else 1.0

    def _executar_filtro(self, alpha, beta, gamma):
        """Executa uma passagem rápida do filtro para um conjunto de parâmetros."""
        x_p, v_p, a_p = self.x_obs[0], 0.0, 0.0
        x_s_list = []
        
        for x_o in self.x_obs:
            inovacao = x_o - x_p
            x_s = x_p + alpha * inovacao
            v_s = v_p + (beta / self.dt) * inovacao
            a_s = a_p + (gamma / (2.0 * (self.dt ** 2))) * inovacao
            x_s_list.append(x_s)
            
            # Predição (k+1)
            x_p = x_s + self.dt * v_s + 0.5 * (self.dt ** 2) * a_s
            v_p = v_s + self.dt * a_s
            a_p = a_s
            
        return np.array(x_s_list)

    def plot_superficie_erro(self, passo=0.1):
        """
        Calcula o RMSE de todas as combinações estáveis e plota o mapa de dispersão 3D
        dos coeficientes (alpha, beta, gamma) coloridos pelo valor do Erro Mínimo Quadrático.
        """
        alphas, betas, gammas, rmses = [], [], [], []

        for a in np.arange(passo, 2.0, passo):
            for b in np.arange(passo, 4.0 - 2.0 * a, passo):
                gamma_max = (4.0 * a * b) / (2.0 - a)
                for g in np.arange(passo, gamma_max, passo):
                    x_s = self._executar_filtro(a, b, g)
                    rmse = np.sqrt(np.mean((self.x_ref - x_s) ** 2))
                    
                    alphas.append(a)
                    betas.append(b)
                    gammas.append(g)
                    rmses.append(rmse)

        # Plot 3D da Região de Estabilidade x Erro
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        
        sc = ax.scatter(alphas, betas, gammas, c=rmses, cmap='viridis_r', marker='o', alpha=0.8)
        
        cbar = fig.colorbar(sc, ax=ax, pad=0.1)
        cbar.set_label('RMSE (Erro Mínimo Quadrático)', rotation=270, labelpad=15)
        
        # Destaque do ponto mínimo
        min_idx = np.argmin(rmses)
        ax.scatter([alphas[min_idx]], [betas[min_idx]], [gammas[min_idx]], 
                   color='red', s=100, label=f'Mínimo (α={alphas[min_idx]:.1f}, β={betas[min_idx]:.1f}, γ={gammas[min_idx]:.1f})')

        ax.set_xlabel('Alpha (α)')
        ax.set_ylabel('Beta (β)')
        ax.set_zlabel('Gamma (γ)')
        ax.set_title('Mapeamento do Erro nas Regiões Estáveis de Jury')
        ax.legend()
        plt.tight_layout()
        plt.show()

    def plot_comparacao_resultado(self, params_otimos, params_comparacao=(0.8, 0.5, 0.2)):
        """
        Plota a trajetória resultante comparando os parâmetros ótimos
        com parâmetros não ajustados e o sinal de referência/observado.
        """
        a_opt, b_opt, g_opt = params_otimos
        x_opt = self._executar_filtro(a_opt, b_opt, g_opt)
        rmse_opt = np.sqrt(np.mean((self.x_ref - x_opt) ** 2))

        a_comp, b_comp, g_comp = params_comparacao
        x_comp = self._executar_filtro(a_comp, b_comp, g_comp)
        rmse_comp = np.sqrt(np.mean((self.x_ref - x_comp) ** 2))

        plt.figure(figsize=(12, 6))
        plt.plot(self.t, self.x_obs, 'r.', alpha=0.4, label='Observações (x_o)')
        plt.plot(self.t, self.x_ref, 'k--', label='Referência Real', linewidth=1.5)
        plt.plot(self.t, x_opt, 'g-', label=f'Ótimo (α={a_opt}, β={b_opt}, γ={g_opt}) | RMSE = {rmse_opt:.3f}', linewidth=2)
        plt.plot(self.t, x_comp, 'b:', label=f'Não Otimizado (α={a_comp}, β={b_comp}, γ={g_comp}) | RMSE = {rmse_comp:.3f}', linewidth=2)

        plt.title('Comparação do Rastreio: Filtro Ótimo vs. Não Ajustado')
        plt.xlabel('Tempo (s)')
        plt.ylabel('Posição')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()


# ==============================================================================
# EXEMPLO INTEGRADO DE USO
# ==============================================================================
if __name__ == "__main__":
    from filtro_otimo import filtro_abg_otimo  # Importa a função da resposta anterior

    # 1. Dados de Teste
    t = np.arange(0, 100, 1.0)
    np.random.seed(42)
    x_real = 45.0 + 0.5 * t + 0.02 * (t ** 2) - 0.0001 * (t ** 3)
    x_observado = x_real + np.random.normal(0, 1.5, size=len(t))

    # 2. Busca dos Parâmetros Ótimos
    params_otimos, rmse_min = filtro_abg_otimo(t, x_observado, x_ref=x_real)

    # 3. Instancia a Classe de Plotagem e Gera os Gráficos
    plotter = PlotterFiltroABG(t, x_observado, x_ref=x_real)
    
    # Gráfico 1: Espaço 3D dos coeficientes de Jury mapeando o erro por cor
    plotter.plot_superficie_erro(passo=0.1)
    
    # Gráfico 2: Desempenho do rastreio com os coeficientes ótimos encontrados
    plotter.plot_comparacao_resultado(params_otimos)