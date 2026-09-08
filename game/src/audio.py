"""Original layered score, short action cues, separate controls and crossfades."""
from pathlib import Path
import pygame

LEVEL_TRACKS=['grove','shadow','shadow','ember','tide','wind','crystal','tide','tide','wind','crystal','grove','crystal','grove','ember','tide','shadow','gravity']
class AudioManager:
    def __init__(self):
        self.enabled=False;self.music_enabled=True;self.effects_enabled=True
        self.sounds={};self._last_play_time={};self._tracks={};self._track=None
        self._channel=0;self._fade=1.
        self.root=Path(__file__).resolve().parent/'audio'
        try:
            if not pygame.mixer.get_init(): pygame.mixer.init(22050,-16,2,512)
            pygame.mixer.set_num_channels(18);pygame.mixer.set_reserved(2)
            for path in self.root.glob('*.wav'):
                self.sounds[path.stem]=pygame.mixer.Sound(str(path))
            self.enabled=True
        except Exception:
            self.enabled=False
        try:
            import json
            from save import _storage
            storage=_storage()
            raw=storage.getItem('bamboo-forest.audio.v1') if storage is not None else (self.root.parent/'audio-settings.json').read_text()
            prefs=json.loads(str(raw)) if raw else {}
            self.music_enabled=prefs.get('music',True) is not False
            self.effects_enabled=prefs.get('effects',True) is not False
        except Exception: pass
    def play(self,name):
        if not self.enabled or not self.effects_enabled or name not in self.sounds: return
        now=pygame.time.get_ticks()/1000
        gap={'land':.12,'collect':.055,'warning':.6,'crumble':.35,'gate':.3,'hit':.15,'geyser':.35}.get(name,.08)
        if now-self._last_play_time.get(name,-999)<gap: return
        channel=pygame.mixer.find_channel()
        if channel:
            channel.set_volume(.38 if name not in ('warning','wind') else .22)
            channel.play(self.sounds[name]);self._last_play_time[name]=now
    def update(self,dt,level=None,boss=False,paused=False):
        if not self.enabled: return
        name='boss' if boss else LEVEL_TRACKS[level] if level is not None else 'grove'
        if self.music_enabled and name!=self._track:
            try:
                if name not in self._tracks: self._tracks[name]=pygame.mixer.Sound(str(self.root/(name+'.ogg')))
                self._channel=1-self._channel
                pygame.mixer.Channel(self._channel).play(self._tracks[name],loops=-1)
                self._track=name;self._fade=0
                self._tracks={name:self._tracks[name]}
            except Exception: return
        self._fade=min(1,self._fade+dt/.9)
        volume=(.10 if paused else .22) if self.music_enabled else 0
        pygame.mixer.Channel(self._channel).set_volume(volume*self._fade)
        pygame.mixer.Channel(1-self._channel).set_volume(volume*(1-self._fade))
        if self._fade>=1: pygame.mixer.Channel(1-self._channel).stop()
    def toggle(self):
        self.effects_enabled=not self.effects_enabled
        self._save_preferences()
    def toggle_music(self):
        self.music_enabled=not self.music_enabled
        self._save_preferences()
        if self.enabled and not self.music_enabled:
            pygame.mixer.Channel(0).set_volume(0);pygame.mixer.Channel(1).set_volume(0)
    def _save_preferences(self):
        try:
            import json
            from save import _storage
            raw=json.dumps({'music':self.music_enabled,'effects':self.effects_enabled})
            storage=_storage()
            if storage is not None: storage.setItem('bamboo-forest.audio.v1',raw)
            else: (self.root.parent/'audio-settings.json').write_text(raw)
        except Exception: pass
