import dummyrotcapture as rot
import threading, queue
import time
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# Configuração da fila e thread de fundo
rot_values = queue.Queue()

def new_handle(az_el):
    az, el = az_el
    rot_values.put((az, el))

rot.threading_handle = new_handle

dummy_rot_thread = threading.Thread(
    target=rot.main, args=(rot_values,), daemon=True
)
dummy_rot_thread.start()

# Classe de Filtro Alpha-Beta-Gamma corrigida
class filter():
    def __init__(self, alfa, beta, gamma):
        self.alfa = alfa
        self.beta = beta
        self.gamma = gamma
        
        self.last_updt = time.time()
        
        # Estados do filtro
        self.pos = 0.0
        self.vel = 0.0
        self.accel = 0.0
        self.first_run = True

    def update(self, new_val):
        now = time.time()
        delta = now - self.last_updt
        
        if self.first_run:
            self.pos = new_val
            self.last_updt = now
            self.first_run = False
            return

        if delta <= 0: 
            delta = 0.001

        # 1. PASSO DE PREDIÇÃO (Onde o estado deveria estar baseado no tempo)
        pos_pred = self.pos + (self.vel * delta) + (0.5 * self.accel * (delta ** 2))
        vel_pred = self.vel + (self.accel * delta)
        accel_pred = self.accel

        # 2. CÁLCULO DO ERRO (Resíduo da medição real vs predita)
        r = new_val - pos_pred

        # 3. PASSO DE ATUALIZAÇÃO (Correção usando os ganhos alfa, beta, gamma)
        self.pos   = pos_pred   + self.alfa * r
        self.vel   = vel_pred   + (self.beta / delta) * r
        self.accel = accel_pred + (2 * self.gamma / (delta ** 2)) * r

        self.last_updt = now

    def get_info(self):
        now = time.time()
        delta = now - self.last_updt
        
        # Prediz a posição extrapolando no tempo atual da tela
        x_n = self.pos + (self.vel * delta) + (0.5 * self.accel * (delta ** 2))
        return now, x_n

# Interface Gráfica Tkinter
root = tk.Tk()
root.title("Visualização em Tempo Real - Azimuth & Elevação")
root.geometry("800x600")

# Criação dos Gráficos com Matplotlib
fig = Figure(figsize=(8, 6), dpi=100)

# Subplot 1: Azimuth (Dados Reais vs Preditos)
ax_az = fig.add_subplot(2, 1, 1)
line_az_real, = ax_az.plot([], [], 'r-', label="Az Real")
line_az_pred, = ax_az.plot([], [], 'b--', label="Az Predito")
ax_az.set_title("Filtro de Azimuth")
ax_az.set_ylabel("Graus")
ax_az.legend(loc="upper left")

# Subplot 2: Elevação (Dados Reais vs Preditos)
ax_el = fig.add_subplot(2, 1, 2)
line_el_real, = ax_el.plot([], [], 'r-', label="El Real")
line_el_pred, = ax_el.plot([], [], 'b--', label="El Predito")
ax_el.set_title("Filtro de Elevação")
ax_el.set_xlabel("Tempo (Timestamp)")
ax_el.set_ylabel("Graus")
ax_el.legend(loc="upper left")

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Ganhos do filtro
az_filter = filter(0.4, 0.05, 0.005)
el_filter = filter(0.4, 0.05, 0.005)

# Histórico de dados
real_tm, real_az, real_el = [], [], []
pred_tm, pred_az, pred_el = [], [], []

def handle_thread():
    if not dummy_rot_thread.is_alive():
        import sys
        sys.exit(0)
    
    try:
        # Pega todos os dados pendentes na fila de uma vez para não atrasar
        while True:
            latest_info = rot_values.get_nowait()
            az_value = float(latest_info[0])
            el_value = float(latest_info[1])
            
            az_filter.update(az_value)
            el_filter.update(el_value)
            
            real_tm.append(az_filter.last_updt)
            real_az.append(az_value)
            real_el.append(el_value)
    except queue.Empty:
        # Se não há dados novos na fila, gera a predição atualizada
        tstmp, az_val = az_filter.get_info()
        _, el_val = el_filter.get_info()
        
        pred_tm.append(tstmp)
        pred_az.append(az_val)
        pred_el.append(el_val)

def update_plot():
    handle_thread()
    
    # Limita o histórico visual aos últimos 50 pontos
    slice_size = -50
    
    if real_tm:
        line_az_real.set_data(real_tm[slice_size:], real_az[slice_size:])
        line_el_real.set_data(real_tm[slice_size:], real_el[slice_size:])
        
    if pred_tm:
        line_az_pred.set_data(pred_tm[slice_size:], pred_az[slice_size:])
        line_el_pred.set_data(pred_tm[slice_size:], pred_el[slice_size:])

    # Auto-ajuste dos eixos (Essencial para os dados aparecerem)
    for ax in [ax_az, ax_el]:
        ax.relim()
        ax.autoscale_view()

    canvas.draw()
    root.after(50, update_plot) # Frequência de atualização de 50ms para maior fluidez

try:
    update_plot()
    root.mainloop()
except KeyboardInterrupt:
    print("Encerrando o programa.")