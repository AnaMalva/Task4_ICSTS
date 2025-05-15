"""
Bibliotecas

"""

import numpy as np
import os
from glob import glob
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import cv2


"""
functions

"""

from Task3.functions_Task3 import *

"""
Definição da RoI

"""

def get_data(set):

    ## Selecionar manualmente RoI Pulmão Esquerdo
    #r_left=cv2.selectROI("select the area left", image)
    #cv2.destroyWindow("select the area left")

    ## Selecionar manualmente RoI Pulmão Direito
    #r_right=cv2.selectROI("select the area right", image)
    #cv2.destroyWindow("select the area right")
    
    path_frame="C:/Users/anama/OneDrive/Ambiente de Trabalho/UNI/Semestre2/ICSTS/Task3/ICSTS_EIT_Processment/Images/set_01/trial_04/frame_027.png"

    # Coordenadas obtidas com zona anterior comentada
    r_left=220, 169, 194, 339 
    r_right=498, 169, 194, 339


    sample_image_left = apply_RoI(path_frame, r_left)
    sample_image_right = apply_RoI(path_frame, r_right)

    # Example shape from first image
    sample_array_left = np.array(sample_image_left)
    sample_array_right = np.array(sample_image_right)

    height_l, width_l, channels_l = sample_array_left.shape
    height_r, width_r, channels_r = sample_array_right.shape

    path_set_file="C:/Users/anama/OneDrive/Ambiente de Trabalho/UNI/Semestre2/ICSTS/Task3/ICSTS_EIT_Processment/Images/set_0"+str(set)

    items = os.listdir(path_set_file)
    files_num = len([item for item in items if os.path.isdir(os.path.join(path_set_file, item))])

    diff_expiration_trial=np.zeros(files_num)
    diff_inspiration_trial=np.zeros(files_num)

    for trial in range(1,files_num+1):

        print(str(trial))

        if trial > 9:
            images_file=sorted(glob("C:/Users/anama/OneDrive/Ambiente de Trabalho/UNI/Semestre2/ICSTS/Task3/ICSTS_EIT_Processment/Images/set_0"+str(set)+"/trial_"+str(trial)+'/*.png'))
        else:
            images_file=sorted(glob("C:/Users/anama/OneDrive/Ambiente de Trabalho/UNI/Semestre2/ICSTS/Task3/ICSTS_EIT_Processment/Images/set_0"+str(set)+"/trial_0"+str(trial)+'/*.png'))

        image_array_left = np.zeros((len(images_file), height_l, width_l, channels_l), dtype=np.uint8)

        image_array_right = np.zeros((len(images_file), height_r, width_r, channels_r), dtype=np.uint8)

        for image_num in range(len(images_file)):

            image_left = apply_RoI(images_file[image_num], r_left)
            image_right = apply_RoI(images_file[image_num], r_right)

            image_array_left[image_num]=image_left
            image_array_right[image_num]=image_right

        
        impedance_signal_left=impedance_calc(image_array_left)
        impedance_signal_right=impedance_calc(image_array_right)

        processed_signal_left=processing(impedance_signal_left)
        processed_signal_right=processing(impedance_signal_right)

        # Expiration
        expiration_frames=peak_detection(processed_signal_left,"expiration")
        sum=0
        
        for i in expiration_frames:
            sum=sum+abs(processed_signal_left[i]-processed_signal_right[i])

        
        diff_expiration_trial[trial-1]=sum/files_num


        # Inspiration
        inspiration_frames=peak_detection(processed_signal_left,"inspiration")
        sum=0
        
        for i in inspiration_frames:
            sum=sum+abs(processed_signal_left[i]-processed_signal_right[i])


        diff_inspiration_trial[trial-1]=sum/len(inspiration_frames)

    diff_expiration=np.sum(diff_expiration_trial)/files_num
    diff_inspiration=np.sum(diff_inspiration_trial)/files_num


    
    if diff_expiration > 0.5 or diff_inspiration > 0.5:
        print("The patient should be evaluated through other techniques of diagnosis.\n")
        diag=1
    else:
        print("The patient is healthy\n")
        diag=0

    return diff_expiration, diff_inspiration, diag



