import time
import numpy as np
from Task2.bitalino import BITalino
import matplotlib.pyplot as plt

def get_signals():

    # Criar e inicializar variáceis necessárias
    macAdress="00:21:08:35:15:17"

    running_time = 120

    batteryThreshold = 30
    acqChannels = [0,1]
    samplingRate = 100
    nSamples = 500
    digitalOutput_on = [1, 1]
    digitalOutput_off = [0, 0]

    # Conestar ao BITalino
    device = BITalino(macAdress)

    # Definir threshold da bateria
    device.battery(batteryThreshold)

    # Começar Aquisição
    device.start(samplingRate, acqChannels)

    # Aquisição
    start = time.time()
    end = time.time()

    all_data=[]

    while (end - start) < running_time:
        # Read samples
        data=device.read(nSamples)
        all_data.append(data)  # Append the data to the list
        end = time.time()

    all_data = np.concatenate(all_data, axis=0)

    # Plot da data adquirida através de Oximetria
    plt.plot(all_data[:,-2])
    plt.show()

    # Plot da data adquirida através de Oximetria em um intervalo mais curto para facilitar a visualização do sinal
    plt.plot(all_data[0:1000,-2])
    plt.show()

    # Plot da data adquirida através de EMG
    plt.plot(all_data[:,-1])
    plt.show()

    # Parar acquisição
    device.stop()

    # Desconectar Bitalino
    device.close()