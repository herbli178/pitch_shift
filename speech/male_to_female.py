from wsola import WSOLA 
import os
import pdb; 
from os.path import dirname, join as pjoin
from scipy.io import wavfile
import scipy.io
from scipy.signal import firwin, lfilter, resample, filtfilt
import numpy as np
import pyworld
import wave
from pyaudio import PyAudio,paInt16
import sys
framerate=16000
NUM_SAMPLES=2000
channels=1
sampwidth=2
TIME=5

try: 
    # just_recording = sys.argv[1]
    saving_folder = sys.argv[1]
    alexa_command = sys.argv[2]
    just_recording = sys.argv[3]
except:
    print("Please specify whether just_recording or saving_folder")


def low_cut_filter(x, fs, cutoff=70):
    """Low cut filter

    Parameters
    ---------
    x : array, shape(`samples`)
        Waveform sequence
    fs: array, int
        Sampling frequency
    cutoff : float, optional
        Cutoff frequency of low cut filter
        Default set to 70 [Hz]

    Returns
    ---------
    lcf_x : array, shape(`samples`)
        Low cut filtered waveform sequence
    """

    nyquist = fs // 2
    norm_cutoff = cutoff / nyquist

    # low cut filter
    fil = firwin(255, norm_cutoff, pass_zero=False)
    lcf_x = lfilter(fil, 1, x)

    return lcf_x


def high_frequency_completion(x, transformed, f0rate, par):
     x = np.array(x, dtype = np.float)

     f0, time_axis = pyworld.harvest(x, par['fs'], f0_floor=par['minf0'], f0_ceil=par['maxf0'], frame_period=par['shiftms'])
     spc = pyworld.cheaptrick(x, f0, time_axis, par['fs'], fft_size=par['fft1'])
     ap = pyworld.d4c(x, f0, time_axis, par['fs'], fft_size=par['fft1'])

     uf0 = np.zeros(len(f0))
     unvoice_anasyn = pyworld.synthesize(uf0, spc, ap, par['fs'], frame_period=par['shiftms'])
     fil = firwin(255, f0rate, pass_zero=False)
     HPFed_unvoice_anasyn = filtfilt(fil, 1, unvoice_anasyn)

     if len(HPFed_unvoice_anasyn) > len(transformed):
          return transformed + HPFed_unvoice_anasyn[:len(transformed)]
     else:
          transformed[:len(HPFed_unvoice_anasyn)] += HPFed_unvoice_anasyn
          return transformed


def transform_f0(x, f0rate, config):
     if f0rate < 1.0:
          completion = True
     else: 
          completion = False
     
     fs = config["fs"]
     x = low_cut_filter(x, fs, cutoff=70)

     wsola = WSOLA(config["fs"], 1 / f0rate, shiftms=10)
     wsolaed = wsola.duration_modification(x)

     xlen = len(x)
     transformed = resample(wsolaed, xlen)

     if completion:
          transformed = high_frequency_completion(x, transformed, f0rate, config)
     
     return transformed

def save_wave_file(filename,data):
    '''save the data to the wavfile'''
    wf=wave.open(filename,'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b"".join(data))
    wf.close()

# def my_record():
#     pa=PyAudio()
#     stream=pa.open(format = paInt16,channels=1,
#                    rate=framerate,input=True,
#                    frames_per_buffer=NUM_SAMPLES)
#     my_buf=[]
#     count=0
#     while count<TIME*8:#控制录音时间
#         string_audio_data = stream.read(NUM_SAMPLES)
#         my_buf.append(string_audio_data)
#         count+=1
#         print('.')
#     save_wave_file('01.wav',my_buf)
#     stream.close()

def my_record():
    pa=PyAudio()
    stream=pa.open(format = paInt16,channels=1,
                   rate=framerate,input=True,
                   frames_per_buffer=NUM_SAMPLES)
    my_buf=[]
    count=0
    while count<TIME*8:#控制录音时间
        string_audio_data = stream.read(NUM_SAMPLES)
        my_buf.append(string_audio_data)
        count+=1
        print('.')
    save_wave_file(alexa_command,my_buf)
    # save_wave_file('alexa.wav',my_buf)
    stream.close()

chunk=2014
def play(path):
    # wf=wave.open(r"alexa.wav",'rb')
    wf=wave.open(path)
    p=PyAudio()
    stream=p.open(format=p.get_format_from_width(wf.getsampwidth()),channels=
    wf.getnchannels(),rate=wf.getframerate(),output=True)
    # while True:
    #     data=wf.readframes(chunk)
    #     if data=="":break
    #     stream.write(data)
    data = wf.readframes(wf.getsampwidth())
    while len(data):
        data=wf.readframes(chunk)
        # if data=="":break
        stream.write(data)
    stream.close()
    p.terminate()
    
    return 0
 
if __name__ == "__main__":
    if just_recording == "Yes":
        my_record()
    else:
        wav_male = pjoin(alexa_command)
        # wav_male = pjoin("100008.wav")
        fs, x = wavfile.read(wav_male)
        x = np.array(x, dtype=np.float)
        
        if x.ndim == 2:
            x = x[:, 0]
        

        # print("shape of x is ", x.shape)

        config = {}
        config["fs"] = fs
        config["minf0"] = 70
        config["maxf0"] = 700
        config["shiftms"] = 10
        config["fft1"] = 1024

        # wav_slow = transform_f0(x, 0.5, config)
        # wavfile.write("siri_slow.wav", fs, wav_slow.astype(np.int16))
        # wavfile.write("tmp.wav", fs, wav_slow.astype(np.int16))
        
        pitch_shifts = []
        for i in range(30):
            pitch_shifts.append(0.5+i*0.05)
        
        for pitch in pitch_shifts:
            print("The pitch now is -------------------------- ", pitch)
            wav_fast = transform_f0(x, pitch, config)
            file_name = saving_folder + "/" + str(pitch) + alexa_command
            wavfile.write(file_name, fs, wav_fast.astype(np.int16))
            # wavfile.write()
            play(file_name)
        # sys.exit()
