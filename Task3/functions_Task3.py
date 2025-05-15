import scipy
from PIL import Image
import numpy as np
from scipy.ndimage import gaussian_filter1d
import cv2

def apply_RoI(image,r):
    
    image = Image.open(image)
    image_np = np.array(image)
    image= image_np[int(r[1]):int(r[1]+r[3]),int(r[0]):int(r[0]+r[2])] 
    
    return image

def impedance_calc(image_array):

    impedance_means = []

    for image in image_array:

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        intensity = hsv[:, :, 2] 

        mean_intensity = np.mean(intensity)
        impedance_means.append(mean_intensity)
    
    return impedance_means

def processing(signal):
    
    signal = np.array(signal)
    fps = 33
    num_seconds = len(signal) // fps
    signal_freq = signal[:num_seconds * fps].reshape(num_seconds, fps).mean(axis=1)

    normalized_signal = (signal_freq - np.mean(signal_freq)) / np.std(signal_freq)

    smoothed_signal = gaussian_filter1d(normalized_signal, sigma=2)

    processed_signal=smoothed_signal

    return processed_signal

def peak_detection(signal,type):

    if type=="expiration":
        peak_time=scipy.signal.find_peaks(signal)[0]
    elif type == "inspiration":
        peak_time=scipy.signal.find_peaks(-signal)[0]
    else:
        print("Error: Inserted Type does not exist")

    return peak_time
