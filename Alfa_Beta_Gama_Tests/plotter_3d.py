import ast
import json
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

# Carregar os dados (utilize json.loads se estiver lendo de um arquivo .json)
with open("./az_dict.json", "r") as file:
    data_az = json.load(file)

# 2. Processamento dos dados
p1_list = []
p2_list = []
p3_list = []
mean_errors = []

for key_str, errors in data_az.items():
    # Converte a chave no formato de string "(0.1, 0.1, 0.0)" em uma tupla numérica (0.1, 0.1, 0.0)
    p1, p2, p3 = ast.literal_eval(key_str)

    # Calcula a média dos erros
    erro_medio = np.mean(errors)

    if erro_medio > 100:
        pass

    p1_list.append(p1)
    p2_list.append(p2)
    p3_list.append(p3)
    mean_errors.append(erro_medio)

# 3. Criação do Gráfico 3D
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Plot do tipo Scatter 3D
# As coordenadas X, Y, Z são p1, p2, p3 e a cor 'c' representa o erro médio
scatter = ax.scatter(
    p1_list,
    p2_list,
    p3_list,
    c=mean_errors,
    cmap="viridis",
    norm=LogNorm(vmin=max(min(mean_errors), 1e-3), vmax=min(max(mean_errors), 1e5)), # vmin evita log(0)
    s=35,           # Tamanho do ponto levemente reduzido
    linewidths=0.2, # Borda mais fina para não poluir
    edgecolor="k",
    alpha=0.85,
)

# Adiciona a barra de cores para indicar a intensidade do erro
cbar = fig.colorbar(scatter, ax=ax, pad=0.1)
cbar.set_label("Erro Médio", fontsize=11)

# Rótulos dos eixos e título
ax.set_xlabel('Alpha (α)')
ax.set_ylabel('Beta (β)')
ax.set_zlabel('Gamma (γ)')
ax.set_title("Distribuição 3D do Erro Médio para o Azimute", fontsize=14, pad=15)

idx = np.argmin(mean_errors)
alfa = p1_list[idx]
beta = p2_list[idx]
gama = p3_list[idx]
min_error = mean_errors[idx]

print(f"Melhor valor AZ: {alfa}, {beta}, {gama}, {min_error}")

# Exibe o gráfico
plt.tight_layout()
plt.show()

# Carregar os dados (utilize json.loads se estiver lendo de um arquivo .json)
with open("./az_dict.json", "r") as file:
    data_az = json.load(file)

# 2. Processamento dos dados
p1_list = []
p2_list = []
p3_list = []
mean_errors = []

for key_str, errors in data_az.items():
    # Converte a chave no formato de string "(0.1, 0.1, 0.0)" em uma tupla numérica (0.1, 0.1, 0.0)
    p1, p2, p3 = ast.literal_eval(key_str)

    # Calcula a média dos erros
    erro_medio = np.mean(errors)

    p1_list.append(p1)
    p2_list.append(p2)
    p3_list.append(p3)
    mean_errors.append(erro_medio)

# 3. Criação do Gráfico 3D
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Plot do tipo Scatter 3D
# As coordenadas X, Y, Z são p1, p2, p3 e a cor 'c' representa o erro médio
scatter = ax.scatter(
    p1_list,
    p2_list,
    p3_list,
    c=mean_errors,
    cmap="viridis",
    norm=LogNorm(vmin=max(min(mean_errors), 1e-3), vmax=min(max(mean_errors), 1e5)), # vmin evita log(0)
    s=35,           # Tamanho do ponto levemente reduzido
    linewidths=0.2, # Borda mais fina para não poluir
    edgecolor="k",
    alpha=0.85,
)

# Adiciona a barra de cores para indicar a intensidade do erro
cbar = fig.colorbar(scatter, ax=ax, pad=0.1)
cbar.set_label("Erro Médio", fontsize=11)

# Rótulos dos eixos e título
ax.set_xlabel('Alpha (α)')
ax.set_ylabel('Beta (β)')
ax.set_zlabel('Gamma (γ)')
ax.set_title("Distribuição 3D do Erro Médio para a Elevação", fontsize=14, pad=15)

idx = np.argmin(mean_errors)
alfa = p1_list[idx]
beta = p2_list[idx]
gama = p3_list[idx]
min_error = mean_errors[idx]

print(f"Melhor valor EL: {alfa}, {beta}, {gama}, {min_error}")

# Exibe o gráfico
plt.tight_layout()
plt.show()