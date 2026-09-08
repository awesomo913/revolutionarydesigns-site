"""A soft hollow bamboo pluck, with a quiet rising overtone; no samples."""
from pathlib import Path
import wave
import numpy as np

def compose(root):
    sr=22050
    t=np.arange(round(sr*.28))/sr
    # Rounded attack and damped wooden resonances replace the shrill bell pair.
    attack=1-np.exp(-t*650)
    tone=(np.sin(2*np.pi*523.25*t)*np.exp(-t*24)
          +.22*np.sin(2*np.pi*1048*t)*np.exp(-t*38)
          +.12*np.sin(2*np.pi*1465*t)*np.exp(-t*62))*attack
    later=np.maximum(0,t-.045)
    tone+=.16*np.sin(2*np.pi*783.99*later)*(1-np.exp(-later*300))*np.exp(-later*26)
    tone*=np.minimum(1,(.28-t)*100)
    tone*=.43/max(.01,np.max(np.abs(tone)))
    with wave.open(str(root/'collect.wav'),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((tone*32767).astype('<i2').tobytes())

if __name__=='__main__': compose(Path(__file__).resolve().parents[1]/'game/audio')
