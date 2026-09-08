"""Reproducible original instrumental score and soft action foley; no samples."""
from pathlib import Path
import json
import numpy as np
import wave
import subprocess
import shutil

ROOT=Path(__file__).resolve().parents[1]/'game/audio'
ROOT.mkdir(exist_ok=True)
SR=22050
rng=np.random.default_rng(712)
def wav(path,data):
 with wave.open(str(path),'wb') as f:
  f.setnchannels(2 if data.ndim==2 else 1);f.setsampwidth(2);f.setframerate(SR)
  f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())
def voice(freq,duration,kind='bell'):
 t=np.arange(int(SR*duration))/SR
 if kind=='bell':
  y=np.sin(2*np.pi*freq*t)*np.exp(-t*5)+.27*np.sin(2*np.pi*freq*2.003*t)*np.exp(-t*9)+.1*np.sin(2*np.pi*freq*3.97*t)*np.exp(-t*15)
 elif kind=='flute':
  phase=2*np.pi*freq*t+.035*np.sin(2*np.pi*4.8*t)
  y=(np.sin(phase)+.16*np.sin(phase*2)+.04*np.sin(phase*3))*(1-np.exp(-t*18))*np.minimum(1,(duration-t)*10)
 elif kind=='pad':
  y=(np.sin(2*np.pi*freq*t)+.35*np.sin(2*np.pi*freq*1.003*t)+.1*np.sin(2*np.pi*freq*2*t))*(1-np.exp(-t*2))*np.minimum(1,(duration-t)*1.5)
 elif kind=='bass': y=np.sin(2*np.pi*freq*t)*np.exp(-t*2.5)
 else: y=rng.normal(0,1,len(t))*np.exp(-t*25)*.15+np.sin(2*np.pi*(95*t-35*t*t))*np.exp(-t*18)
 return y*np.minimum(1,t*250)*np.minimum(1,(duration-t)*100)
def hz(note): return 440*2**((note-69)/12)
themes={
 'grove':(94,60,[0,2,4,7,9],[0,7,5,0]),
 'shadow':(96,57,[0,2,3,7,10],[0,5,3,7]),
 'ember':(112,50,[0,2,3,5,7],[0,3,5,7]),
 'wind':(100,62,[0,2,5,7,9],[0,5,7,0]),
 'crystal':(82,64,[0,2,4,7,11],[0,5,2,7]),
 'tide':(90,55,[0,2,3,7,10],[0,5,3,7]),
 'gravity':(108,57,[0,2,3,6,7],[0,3,5,7]),
 'boss':(128,50,[0,2,3,5,7],[0,0,5,7]),
}
manifest={}
for name,(bpm,key,scale,chords) in themes.items():
 beat=60/bpm;length=beat*64;n=int(length*SR);mix=np.zeros((n,2))
 def add(signal,start,volume,pan=0):
  indices=(np.arange(len(signal))+int(start*SR))%n
  mix[indices,0]+=signal*volume*(.7-pan*.3);mix[indices,1]+=signal*volume*(.7+pan*.3)
 for bar in range(16):
  root=key+chords[(bar//2)%4];minor=name in ('shadow','ember','tide','gravity','boss')
  for degree in (0,3 if minor else 4,7): add(voice(hz(root+degree),beat*4,'pad'),bar*4*beat,.06,degree/7-.5)
  for b in range(4):
   add(voice(hz(root-24+(7 if b==2 else 0)),beat*.9,'bass'),(bar*4+b)*beat,.15)
   if name not in ('crystal','tide') or b in (0,2): add(voice(90,.13,'drum'),(bar*4+b)*beat,.1 if b%2==0 else .055,(-1)**b*.4)
  motif=[0,2,3,1,4,3,2,1] if bar%4<2 else [4,3,1,2,0,2,1,0]
  for j,note in enumerate(motif):
   if bar%4==3 and j in (5,7): continue
   midi=key+12+scale[(note+bar//4)%5]
   add(voice(hz(midi),beat*1.8,'bell'),(bar*4+j/2)*beat,.15,(-1)**j*.45)
  if bar%4 in (1,2):
   for j,degree in enumerate((2,4,3,0)): add(voice(hz(key+12+scale[degree]),beat*.82,'flute'),(bar*4+j)*beat,.08,.2)
 # Circular short reflections preserve the loop boundary and add depth.
 for delay,gain in ((.13,.12),(.27,.08),(.41,.045)):
  mix+=np.roll(mix,int(delay*SR),axis=0)[:,::-1]*gain
 mix=np.tanh(mix*1.3);peak=float(np.max(np.abs(mix)));mix*=.66/max(.66,peak)
 temporary=ROOT/f'{name}.wav';wav(temporary,mix)
 subprocess.run([shutil.which('ffmpeg'),'-y','-loglevel','error','-i',str(temporary),'-c:a','libvorbis','-q:a','4',str(ROOT/f'{name}.ogg')],check=True)
 temporary.unlink()
 manifest[name]={'seconds':round(length,2),'bpm':bpm,'peak':round(float(np.max(np.abs(mix))),4),'rms':round(float(np.sqrt(np.mean(mix**2))),4)}
effects={
 'jump':([64,71],.16),'double_jump':([71,76,83],.2),'land':([40],.12),
 'dash':([52,64,76],.2),'attack':([46,57],.12),'throw':([69,81],.15),
 'slam':([43,31],.24),'collect':([79,86],.2),'power':([67,71,74,79],.55),
 'heal':([72,76,79],.45),'checkpoint':([60,67,72,79],.7),'portal':([64,71,76,83,88],.6),
 'gate':([57,69],.2),'crumble':([43,38,31],.3),'hit':([50,43],.2),
 'stomp':([48,67],.19),'boss_hit':([38,55],.25),'crystal':([83,90,95],.5),
 'geyser':([48,60,72],.36),'menu_select':([76,79],.14),'level_clear':([60,64,67,72,79],1.1),
 'victory':([60,64,67,72,76,79,84],1.9),'death':([64,60,55,48],.9),
 'dance':([72,76,79,84,79,84],1.),'wind':([55,62],.4),'ice_slide':([83,76],.2),
 'glide':([67,74],.35),'warning':([55,55],.32)
}
for name,(notes,duration) in effects.items():
 n=int(SR*(duration+.25));y=np.zeros(n)
 for j,note in enumerate(notes):
  v=voice(hz(note),duration/len(notes)+.2,'bell' if name not in ('hit','land','slam','crumble') else 'drum')
  start=int(j*duration/len(notes)*SR);end=min(n,start+len(v));y[start:end]+=v[:end-start]*.45
 peak=max(.01,float(np.max(np.abs(y))));y*=.6/peak
 wav(ROOT/f'{name}.wav',y)
manifest['effects']=list(effects)
import runpy
runpy.run_path(str(Path(__file__).with_name('compose-bamboo-pickup.py')))['compose'](ROOT)
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('Composed',len(themes),'looping arrangements and',len(effects),'action sounds.')
