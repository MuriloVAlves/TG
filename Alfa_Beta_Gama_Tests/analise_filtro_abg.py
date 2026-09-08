import json
import matplotlib.pyplot as plt
import numpy as np

print("Carregando azimute...")
with open("./az_dict.json", "r") as file:
    data_az = json.load(file)

print("Carregando elevação...")
with open("./el_dict.json", "r") as file:
    data_el = json.load(file)

az_min_rms = np.inf
az_min_key = ''

for az_key in data_az.keys():
    rms_mean = np.mean(data_az[az_key])
    if rms_mean < az_min_rms:
        az_min_rms = rms_mean
        az_min_key = az_key

el_min_rms = np.inf
el_min_key = ''

for el_key in data_el.keys():
    rms_mean = np.mean(data_el[el_key])
    if rms_mean < el_min_rms:
        el_min_rms = rms_mean
        el_min_key = el_key

print("---AZIMUTE---")
print(f"Melhores valores de alfa beta gamma: {az_min_key}")
print(f"Erro médio: {az_min_rms}")

print("\n---ELEVAÇÃO---")
print(f"Melhores valores de alfa beta gamma: {el_min_key}")
print(f"Erro médio: {el_min_rms}")