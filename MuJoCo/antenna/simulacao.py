#!/usr/bin/env python3
import time
import math
import mujoco
import mujoco.viewer
import socket, argparse
from time import time, sleep
from datetime import datetime
import os
import threading, queue
from pathlib import Path

TIMEOUT = 1
MAX_RETRIES = 100

script_path = os.path.realpath(__file__)
script_dir = Path(script_path).parent # Get the script path

# Dummy rot capture
class rot_server():
    def threading_handle(self,status,handle):
        pass

    def main(self, queue_handle=""):
        capture_name = ""
        capture_timeout = 0
        p = argparse.ArgumentParser()
        p.add_argument("--listen-host", default="127.0.0.1")
        p.add_argument("--listen-port", type=int, default=4533)
        args = p.parse_args()

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.listen_host, args.listen_port))
        srv.listen(1)
        srv.settimeout(TIMEOUT)
        print(f"Dummy GS-232 logger on {args.listen_host}:{args.listen_port}")
        last_az = "0"
        last_el = "0"
        try:
            timeout_counter = 0
            # fake values
            az = "179.9"
            el = "53.8"
            while True:
                try:
                    conn, addr = srv.accept()
                    timeout_counter = 0
                    print(f"GPredict connected from {addr[0]}:{addr[1]}")
                    with conn:
                        while True:
                            data = conn.recv(256)
                            if not data:
                                break
                            cmd = data.decode("ascii", errors="ignore").strip()
                            print(time(),"→ GPredict:", repr(cmd))

                            if cmd == 'p':
                                resp = f"{float(last_az):.16f} {float(last_el):.16f}"
                                capture_timeout += 1
                                if capture_timeout >3:
                                    capture_name = ""
                            elif cmd[0] == 'P':
                                _,az,el = cmd.split(' ')
                                resp = f"P {az} {el}"
                                last_az = az
                                last_el = el
                                self.threading_handle(conn,(az,el))
                                capture_timeout = 0
                            elif cmd[0].upper() == 'S':
                                resp = "S0"
                            elif cmd[0].upper() == 'Q':
                                # no reply on Q, just break out
                                print("← Dummy: <closing>")
                                break
                            else:
                                # for AZ/EL set commands and others we just acknowledge
                                resp = cmd.upper()
                            print(time(),"← Dummy:", repr(resp))
                            conn.sendall((resp + "\r\n").encode("ascii"))

                    print("GPredict disconnected")
                except TimeoutError:
                    timeout_counter += 1
                    self.threading_handle(False,("NO_CON","NO_CON"))
                    print(f"\rTry: {timeout_counter} - No connection received within {TIMEOUT} seconds. Retrying...",end="")
                    if timeout_counter >= MAX_RETRIES:
                        print("Exiting program...")
                        exit(1)
        except KeyboardInterrupt:
            print("\nStopping the server manually...")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

# Configuração da fila e thread de fundo
rot_values = queue.Queue()
connection_status = queue.Queue()

rot = rot_server()

def new_handle(status,az_el):
    az, el = az_el
    connection_status.put(status)
    if az != "NO_CON" or el != "NO_CON":
        rot_values.put((az, el))

rot.threading_handle = new_handle

dummy_rot_thread = threading.Thread(
    target=rot.main, args=(rot_values,), daemon=True
)
dummy_rot_thread.start()

# Classe de Filtro Alpha-Beta-Gamma
class filter():
    def __init__(self, alfa, beta, gamma):
        self.alfa = alfa
        self.beta = beta
        self.gamma = gamma
        
        self.last_updt = time()
        
        # Estados do filtro
        self.pos = 0.0
        self.vel = 0.0
        self.accel = 0.0
        self.first_run = True

    def update(self, new_val):
        now = time()
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
        # Unwrap function for the filter
        x_o_plus  = pos_pred + 360
        x_o_minus = pos_pred - 360
        if abs(new_val - x_o_plus) < abs(r):
            r = new_val - x_o_plus
        if abs(new_val - x_o_minus) < abs(r):
            r = new_val - x_o_minus

        # 3. PASSO DE ATUALIZAÇÃO (Correção usando os ganhos alfa, beta, gamma)
        self.pos   = pos_pred   + self.alfa * r
        self.vel   = vel_pred   + (self.beta / delta) * r
        self.accel = accel_pred + (2 * self.gamma / (delta ** 2)) * r

        self.last_updt = now

    def get_info(self):
        now = time()
        delta = now - self.last_updt
        
        # Prediz a posição extrapolando no tempo atual da tela
        x_n = self.pos + (self.vel * delta) + (0.5 * self.accel * (delta ** 2))
        if delta > 10:
            self.reset_filter_parameters()
        return now, x_n

    def reset_filter_parameters(self):
        self.pos = 0.0
        self.vel = 0.0
        self.accel = 0.0
        self.first_run = True

# Ganhos do filtro
az_filter = filter(0.937, 0.298, 0.12)
el_filter = filter(1.0, 0.253, 0.122)
az_val = 0
el_val = 0
server_connected = False

def handle_thread():
    if not dummy_rot_thread.is_alive():
        print("MATANDO THREAD")
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
            global server_connected
            server_connected = connection_status.get_nowait()
            if el_value < 0:
                az_filter.reset_filter_parameters()
                el_filter.reset_filter_parameters()
            timeout_counter = 0
    except queue.Empty:
        global az_val
        global el_val
        # Se não há dados novos na fila, gera a predição atualizada
        tstmp, az_val = az_filter.get_info()
        _, el_val = el_filter.get_info()
        if el_val > 100 or el_val < -1:
            az_filter.reset_filter_parameters()
            el_filter.reset_filter_parameters()

def main():
    # 1. Carrega o modelo a partir do arquivo XML principal da cena
    model_path = str(script_dir/"scene.xml")
    
    try:
        model = mujoco.MjModel.from_xml_path(model_path)
    except Exception as e:
        print(f"Erro ao carregar o modelo XML: {e}")
        return

    data = mujoco.MjData(model)

    print("Iniciando a simulação do robô...")
    print(f"Número de atuadores encontrados: {model.nu}")

    # 2. Inicializa o visualizador interativo do MuJoCo
    with mujoco.viewer.launch_passive(model, data) as viewer:
        start_time = time()

        # Loop principal da simulação
        while viewer.is_running():
            step_start = time()

            # Tempo decorrido na simulação
            t = time() - start_time

            # 3. Controle das juntas (Azimute e Elevação)
            if model.nu >= 2:

                # Recebe dados do servidor
                handle_thread()
                # data.ctrl[0]: Azimute (movimento horizontal/rotação)
                data.ctrl[0] = az_val*math.pi/180  # radianos
                
                # data.ctrl[1]: Elevação (movimento vertical)
                data.ctrl[1] = -1*el_val*math.pi/180  # radianos

            # 4. Avança um passo na física do MuJoCo
            mujoco.mj_step(model, data)

            # 5. Sincroniza o visualizador com o estado atual da simulação
            viewer.sync()

            # Controle de tempo para manter a taxa de atualização compatível com o timestep do modelo
            time_until_next_step = model.opt.timestep - (time() - step_start)
            if time_until_next_step > 0:
                if server_connected:
                    print(f"Rot data: {az_val:.6f} {el_val:.6f}",end='\r')
                sleep(time_until_next_step)

if __name__ == "__main__":
    main()