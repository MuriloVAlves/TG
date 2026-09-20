import numpy as np

ALPHA_AZ = 1
BETA_AZ = 0.05
GAMMA_AZ = 0.0
ALPHA_EL = 1
BETA_EL = 0.55
GAMMA_EL = 0.1

def alfa_beta_gamma_filter_fast(x_obs, deltat, alpha, beta, gamma):
    x_prediction = []
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
        x_prediction.append(x_p)

    rmse = np.sqrt(sum_sq_err / (n - 1))
    return x_prediction, rmse

if __name__ == "__main__":
    from pathlib import Path

    # Define the directory path
    dir_path = Path('./tracks/')

    timestamp = []
    az_data = []
    el_data = []
    filename = []

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
                filename.append(file_path.name)
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
    import matplotlib.pyplot as plt
    for k in range(len(filename)):
        real_tst = []
        tst_change = 0
        for t in timestamp[k]:
            tst_change += t
            real_tst.append(tst_change)
        az_filter, rmse_az = alfa_beta_gamma_filter_fast(el_data[k],timestamp[k],ALPHA_EL,BETA_EL,GAMMA_EL)
        el_filter, rmse_el = alfa_beta_gamma_filter_fast(az_data[k],timestamp[k],ALPHA_AZ,BETA_AZ,GAMMA_AZ)
        plt.plot(real_tst,az_data[k])
        plt.plot(real_tst,el_data[k])
        plt.plot(real_tst[1:],az_filter,'--')
        plt.plot(real_tst[1:],el_filter,'--')
        plt.title(f"{k+1}/{len(filename)} {filename[k]} - rmse: {rmse_az:.2f} {rmse_el:.2f}")
        plt.show()