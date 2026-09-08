"""Regressions for reported grounding flicker and static painted characters."""
import os,sys,tarfile,tempfile,hashlib
from pathlib import Path
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
    with tarfile.open(ROOT/'game/web.tar.gz') as tar: tar.extractall(folder,filter='data')
    os.chdir(Path(folder)/'assets');sys.path.insert(0,str(Path.cwd()))
    import pygame
    pygame.init();pygame.display.set_mode((960,540))
    import visual_skin;visual_skin.install()
    from sprites import Player,Platform,MovingPlatform
    from biomes import BiomeMovingPlatform
    from physics import moving_platform_step
    from character_motion import rig_frame,hero_motion
    from journey_art import draw_sprite
    class Keys:
        def __getitem__(self,key):return False
    keys=Keys()
    for dt in (1/30,1/60,1/120,1/240):
        floor=Platform(0,490,1000,50);p=Player(100,490)
        for frame in range(300):
            p.update(dt,keys,pygame.sprite.Group(floor))
            assert p.is_on_ground and p.velocity_y==0 and p.anim_state=='idle',(dt,frame,'resting contact flickers')
        for cls in (MovingPlatform,BiomeMovingPlatform):
            for axis in ('horizontal','vertical'):
                lift=cls(100,300,160,20,axis=axis,distance=60)
                other=MovingPlatform(700,100,100,20)
                group=pygame.sprite.Group(lift,other)
                p=Player(155,300);p.update(dt,keys,group)
                p.has_double_jump=True
                for frame in range(600):
                    moving_platform_step(p,lift,dt,group)
                    moving_platform_step(p,other,dt,group)
                    p.update(dt,keys,group)
                    assert p.is_on_ground and p.rect.bottom==lift.rect.top and p.anim_state=='idle',(cls,axis,dt,frame,'rider loses contact')
                    assert p.jumps_remaining==2 and p.velocity_y==0
                assert p.jump()
                for frame in range(3):
                    moving_platform_step(p,lift,dt,group)
                    moving_platform_step(p,other,dt,group)
                    p.update(dt,keys,group)
                    assert not p.is_on_ground and p.rect.bottom<lift.rect.top,'jump was recaptured'
                assert p.jump() and not p.jump(),'jump counts changed by platform'
    # Every painted enemy has real changing pixels in all rendered cycles.
    for index in range(24):
        for mode in ('idle','walk','attack'):
            frames=[rig_frame(index,(56,64),phase,mode)[0] for phase in range(16)]
            hashes={hashlib.sha256(pygame.image.tobytes(f,'RGBA')).digest() for f in frames}
            assert len(hashes)>=4,(index,mode,'static animation')
            masses=[pygame.mask.from_surface(f).count() for f in frames]
            assert min(masses)>.6*max(masses),(index,mode,'opacity flash or lost body')
    p=Player(100,490);p.is_on_ground=True
    sizes=[]
    for frame in range(120):
        p.visual_time=frame/60;p.invincible_timer=2-frame/60
        art,pad=hero_motion(p);sizes.append(pygame.mask.from_surface(art).count())
        bounds=p.rect.copy();canvas=pygame.Surface((960,540),pygame.SRCALPHA)
        draw_sprite(canvas,p,0,0)
        assert p.rect==bounds and pygame.mask.from_surface(canvas).count()>100
    assert min(sizes)>.95*max(sizes),'idle/invulnerability changes body opacity'
    # Brown baked-in slam debris and the legacy dash streak are never used.
    from unittest.mock import patch
    p.is_slamming=True
    with patch('character_motion.rig_frame',wraps=rig_frame) as render:
        hero_motion(p);assert render.call_args.args[0]=='hero:0'
    from game import Game
    game=Game();game._start_game(practice=True)
    with patch.object(game.particles,'emit_dust') as dust:
        game._on_key_down(pygame.K_LSHIFT)
        for _ in range(90):game._update(1/60)
        assert not dust.called,'old brown foot particles returned'
    print('PASS: 4 frame rates; both platform classes and axes; ride/reverse/jump; all 24 animated cast members; no hero flashing or brown foot effect.')
    os.chdir(ROOT)
