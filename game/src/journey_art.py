"""Painted Journey art. Rendering never changes gameplay collision rectangles."""
from pathlib import Path
import math
import pygame
import pygame.mask

ART = Path(__file__).with_name('art')
CACHE = {}
CREAM = (243, 237, 214)
GOLD = (222, 184, 105)
SAGE = (179, 198, 160)
DARK = (9, 25, 22)

WORLDS = {
    'forest': ('worlds-grove.png', 3, 0), 'corrupted': ('worlds-grove.png', 3, 1),
    'lair': ('worlds-grove.png', 3, 2), 'volcanic': ('worlds-grove.png', 3, 3),
    'basalt': ('worlds-grove.png', 3, 4), 'desert': ('worlds-grove.png', 3, 5),
    'cave': ('worlds-beyond.png', 4, 0), 'salt': ('worlds-beyond.png', 4, 1),
    'mushroom': ('worlds-beyond.png', 4, 2), 'tidal': ('worlds-beyond.png', 4, 3),
    'gravity': ('worlds-beyond.png', 4, 4), 'forge': ('worlds-beyond.png', 4, 5),
    'void': ('worlds-beyond.png', 4, 6), 'geode': ('worlds-beyond.png', 4, 7),
}
LEVEL_WORLDS = ['forest', 'corrupted', 'lair', 'volcanic', 'basalt', 'desert',
                'cave', 'salt', 'cave', 'basalt', 'salt', 'forest', 'geode',
                'mushroom', 'forge', 'tidal', 'void', 'gravity']
CAST = dict(zip(['PatrolEnemy','ChaserEnemy','SlimeEnemy','FlyingEnemy','Boss',
                'SulfurSlime','AshBat','KelpCrab','BasaltGolem','DustDevil',
                'CactusScorpion','StalactiteSpider','FalseGlowworm','BrineShard',
                'ReflectionPhantom','SporePuffer','MagmaLeaper','TidalCrab',
                'PhaseWraith','GravityDrone','HomingSpecter','ForgeHammer','VoidEater','NPC'], range(24)))
GUIDE_KEYS = dict(zip(['mushroom','panther','slime','bat','boss','sulfur','ashbat',
                      'crab','golem','dust','scorp','spider','glow','brine','phantom',
                      'puffer','leaper','tidalcrab','wraith','drone','specter','hammer','voideater','npc'], range(24)))
PROPS = {'Bamboo':0,'HealingItem':1,'BambooStaff':2,'BambooShuriken':3,
         'DashBoots':4,'GlideFeather':5,'IceProjectile':6,'Crystal':6,
         'Checkpoint':7,'SafeZone':8,'MushroomSpring':9,'GrassTuft':10,'TeleportPortal':11}

def image(name):
    if name not in CACHE:
        surf = pygame.image.load(str(ART / name)).convert_alpha()
        if name in ('panda-journey.png','creatures-journey.png','relics-journey.png'):
            # Generated keyed atlases: native SDL threshold decodes the matte
            # once, including internal gaps, without eating cream fur.
            pygame.transform.threshold(surf, surf.copy(), (255,0,255,255),
                                       (85,115,85,255), (0,0,0,0), 1, None, True)
        CACHE[name] = surf
    return CACHE[name]

def cell(name, cols, rows, index, trim=True):
    key = ('cell',name,cols,rows,index,trim)
    if key not in CACHE:
        atlas = image(name)
        col, row = index % cols, index // cols
        x0,x1 = col*atlas.get_width()//cols,(col+1)*atlas.get_width()//cols
        y0,y1 = row*atlas.get_height()//rows,(row+1)*atlas.get_height()//rows
        if name=='creatures-journey.png':
            # Measured row extents preserve the king's feet and remove slivers
            # of adjacent creatures from the generated atlas.
            boundaries=(0,280,510,733,1024)
            y0,y1=(round(boundaries[row]*atlas.get_height()/1024),round(boundaries[row+1]*atlas.get_height()/1024))
        # Inset environment panels by 2px to exclude generated divider seams.
        margin = 0 if trim else 2
        surf = atlas.subsurface((x0+margin,y0+margin,x1-x0-2*margin,y1-y0-2*margin)).copy()
        if trim:
            for py in range(surf.get_height()):
                for px in range(surf.get_width()):
                    r,g,b,a=surf.get_at((px,py))
                    if a and abs(r-b)<28 and min(r,b)>max(75,g*1.5) and min(r,b)-g>55:
                        surf.set_at((px,py),(0,0,0,0))
                    elif a and (name=='panda-journey.png' or name=='creatures-journey.png' and index not in (3,14,18,20,22)) and b>g+8 and r>g+12:
                        # Remove color-key spill from dark fur edge pixels.
                        surf.set_at((px,py),(min(r,g+8),g,min(b,g+3),a))
            if name=='creatures-journey.png':
                components=pygame.mask.from_surface(surf,70).connected_components(16)
                if components:
                    bounds=max(components,key=lambda m:m.count()).get_bounding_rects()[0]
                    surf=surf.subsurface(bounds).copy()
            bounds = surf.get_bounding_rect(min_alpha=70)
            if bounds.width and bounds.height:
                surf = surf.subsurface(bounds).copy()
        CACHE[key] = surf
    return CACHE[key]

def fit(surf, size, key=None):
    cache_key = ('fit',key,size)
    if key is not None and cache_key in CACHE:
        return CACHE[cache_key]
    ratio = min(size[0]/surf.get_width(), size[1]/surf.get_height())
    result = pygame.transform.smoothscale(surf,(max(1,round(surf.get_width()*ratio)),max(1,round(surf.get_height()*ratio))))
    if key is not None:
        CACHE[cache_key] = result
    return result

def panda(index=0, size=(160,210)):
    return fit(cell('panda-journey.png',4,3,index),size,('panda',index))

def creature(index, size=(110,110)):
    return fit(cell('creatures-journey.png',6,4,index),size,('creature',index))

def relic(index, size=(40,40)):
    return fit(cell('relics-journey.png',4,4,index),size,('relic',index))

def world(biome, size=(960,540)):
    key = ('world',biome,size)
    if key not in CACHE:
        name,rows,index = WORLDS.get(biome,WORLDS['forest'])
        source = cell(name,2,rows,index,False)
        # Cover, never distort the paintings if generator aspect varies.
        ratio = max(size[0]/source.get_width(),size[1]/source.get_height())
        scaled = pygame.transform.smoothscale(source,(math.ceil(source.get_width()*ratio),math.ceil(source.get_height()*ratio)))
        target = pygame.Surface(size)
        target.blit(scaled,scaled.get_rect(center=(size[0]//2,size[1]//2)))
        CACHE[key] = target.convert()
    return CACHE[key]

class PaintedBackground:
    def __init__(self, biome='forest'):
        self.biome = biome
        self.surface = world(biome,(1120,630))

    def draw(self, screen, camera_x):
        # A slow continuous pan with finite travel avoids mirrored scenery and
        # abrupt atlas seams. The distant scene remains a coherent place.
        shift = min(160,max(0,-camera_x*.022))
        screen.blit(self.surface,(-int(shift),-35))
        t = pygame.time.get_ticks()/1000
        for i in range(15):
            x = int((i*79+t*(3+i%3)-camera_x*.008)%960)
            y = int(110+(i*43)%350+math.sin(t*.6+i)*12)
            pygame.draw.circle(screen,(184+i%3*12,177+i%3*9,107),(x,y),1)

def tile(w,h,biome='forest'):
    key=('tile',w,h,biome)
    if key not in CACHE:
        idx = 13 if biome in ('volcanic','forge') else 14 if biome in ('salt','geode') else 15 if biome in ('gravity','void','basalt') else 12
        source=cell('relics-journey.png',4,4,idx)
        # Take the front face; a collision surface must have a straight top.
        source=source.subsurface((int(source.get_width()*.06),int(source.get_height()*.27),int(source.get_width()*.88),int(source.get_height()*.67)))
        texture=pygame.transform.smoothscale(source,(128,64))
        target=pygame.Surface((w,h),pygame.SRCALPHA)
        target.fill((43,53,38) if idx==12 else (40,46,48))
        for y in range(0,h,64):
            for x in range(0,w,128):
                target.blit(texture,(x,y))
        edge = (166,186,94) if idx==12 else (212,133,73) if idx==13 else (174,220,228) if idx==14 else GOLD
        pygame.draw.line(target,edge,(0,0),(w-1,0),2)
        pygame.draw.line(target,(22,31,25),(0,h-1),(w-1,h-1),2)
        CACHE[key]=target
    return CACHE[key]

def hero_pose(player):
    if player.is_victory_dancing: return 11
    if player.dead or player.knockback_timer>0: return 9
    if player.is_attacking: return 8
    if player.is_dashing: return 7
    if player.is_slamming: return 10
    if player.is_gliding: return 6
    if not player.is_on_ground: return 4 if player.velocity_y<0 else 5
    if abs(player.velocity_x)>10: return 2+int(player.anim_timer*10+player.anim_frame)%2
    return int(player.anim_frame)%2

def draw_sprite(screen, sprite, cam_x, cam_y, biome='forest'):
    """Presentation adapter: all mechanics retain their original bounds/states."""
    kind=type(sprite).__name__
    rect=sprite.rect.move(cam_x,cam_y)
    tick=pygame.time.get_ticks()/1000
    art=None
    if kind=='Player':
        art=panda(hero_pose(sprite),(max(42,rect.w),rect.h+3))
        if not sprite.facing_right: art=pygame.transform.flip(art,True,False)
    elif kind in CAST:
        art=creature(CAST[kind],(max(30,rect.w),max(30,rect.h)))
        if kind not in ('Boss','ForgeHammer','BrineShard','BasaltGolem'):
            phase=int(tick*5+sprite.rect.x*.02)%3
            motion_key=('breathe',CAST[kind],art.get_size(),phase)
            if motion_key not in CACHE:
                CACHE[motion_key]=pygame.transform.smoothscale(art,(art.get_width(),max(1,art.get_height()-(1 if phase==1 else 0))))
            art=CACHE[motion_key]
        facing = getattr(sprite,'facing_right',getattr(sprite,'direction',getattr(sprite,'vx',1)) >= 0)
        if not facing:
            art=pygame.transform.flip(art,True,False)
        if kind=='Boss' and sprite.state=='stunned':
            art=art.copy();art.fill((95,160,210,0),special_flags=pygame.BLEND_RGBA_ADD)
        if kind=='BasaltGolem' and getattr(sprite,'state','')=='dormant':
            art=art.copy();art.fill((120,130,115,255),special_flags=pygame.BLEND_RGBA_MULT)
        if kind in ('FalseGlowworm','VoidEater','ForgeHammer','BasaltGolem') and getattr(sprite,'state','') in ('snapping','open','telegraph','striking','slamming'):
            art=art.copy();art.fill((65,22,4,0),special_flags=pygame.BLEND_RGBA_ADD)
        if kind=='ReflectionPhantom':
            art=art.copy();art.set_alpha(115+int(35*math.sin(tick*2)))
        if getattr(sprite,'frozen_timer',0)>0:
            art=art.copy();art.fill((80,130,170,0),special_flags=pygame.BLEND_RGBA_ADD)
    elif kind in PROPS:
        size=(rect.w,rect.h)
        if kind in ('Bamboo','HealingItem','DashBoots','GlideFeather','BambooStaff'):
            size=(max(24,rect.w),max(28,rect.h))
        art=relic(PROPS[kind],size)
        if kind=='Checkpoint' and not sprite.activated:
            art=art.copy();art.fill((135,150,130,255),special_flags=pygame.BLEND_RGBA_MULT)
        if kind=='Crystal' and not sprite.is_lit():
            art=art.copy();art.fill((130,155,165,255),special_flags=pygame.BLEND_RGBA_MULT)
        if kind=='BambooShuriken': art=pygame.transform.rotate(art,tick*450%360)
        if kind=='TeleportPortal' and not sprite.active:
            art=art.copy();art.set_alpha(90)
    elif kind in ('Platform','MovingPlatform','BiomePlatform','BiomeMovingPlatform','IcePlatform','CrumblingPlatform','TimedGate'):
        if kind=='CrumblingPlatform' and rect.w<=1: return
        art=tile(rect.w,rect.h,'salt' if kind=='IcePlatform' else biome)
        if kind=='TimedGate' and not sprite.solid:
            art=art.copy();art.set_alpha(48)
        elif kind=='TimedGate':
            from biomes import TimedGate
            from config import GATE_CYCLE_SEC, GATE_TELEGRAPH_SEC
            remaining=GATE_CYCLE_SEC*.5-TimedGate._global_timer%(GATE_CYCLE_SEC*.5)
            if remaining<GATE_TELEGRAPH_SEC:
                art=art.copy()
                pygame.draw.line(art,(243,189,102),(0,0),(rect.w-1,0),3)
        if kind=='CrumblingPlatform' and getattr(sprite,'touched',False):
            art=art.copy();art.fill((55,15,0,0),special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(art,rect);return
    if art is not None:
        bottom=(rect.centerx,min(rect.bottom,490+cam_y)) if kind=='SafeZone' else rect.midbottom
        target=art.get_rect(midbottom=bottom)
        screen.blit(art,target)
        if kind in CAST and getattr(sprite,'state','') in ('telegraph','warning'):
            from journey_ui import text
            text(screen,'!',(rect.centerx,rect.top-16),25,GOLD,True)
        if kind=='TeleportPortal':
            from journey_ui import text
            text(screen,chr(65+sprite.pair_id%26),(rect.centerx,rect.top-9),17,GOLD,True)
        if kind in ('FalseGlowworm','VoidEater'):
            danger=getattr(sprite,'state','') in ('snapping','open','attack')
            if danger: pygame.draw.circle(screen,(245,146,96),rect.midtop,5,2)
        return
    if kind=='DarkWall':
        wall=tile(rect.w,rect.h,'gravity').copy();wall.set_alpha(235 if sprite.solid else 40)
        screen.blit(wall,rect)
        for y in range(rect.top+16,rect.bottom-10,36):
            pygame.draw.circle(screen,(181,162,210) if sprite.solid else (92,125,104),(rect.centerx,y),5,1)
        return
    if kind in ('WindZone','ThermalUpdraft','GravityZone'):
        effect=pygame.Surface(rect.size,pygame.SRCALPHA)
        gravity_type=getattr(sprite,'gravity_type','low')
        color=(193,186,140) if kind!='GravityZone' else (174,160,208) if gravity_type!='high' else (209,153,109)
        pygame.draw.rect(effect,(*color,28),effect.get_rect(),1,border_radius=8)
        vertical=kind!='WindZone'
        for i in range(18):
            x=int((i*43+(0 if vertical else tick*42))%max(1,rect.w))
            direction=1 if kind=='GravityZone' and gravity_type=='high' else -1
            y=int((i*61+direction*tick*35 if vertical else i*61)%max(1,rect.h))
            pygame.draw.line(effect,(*color,105),(x,y),(x,y+10) if vertical else (x+13,y),1)
        screen.blit(effect,rect)
        if kind=='GravityZone':
            from journey_ui import text
            text(screen,gravity_type.upper(),(rect.centerx,rect.top+10),14,color,True)
        return
    if kind in ('ToxicTrail','PoisonSpore','ScorpionProjectile'):
        effect=pygame.Surface(rect.size,pygame.SRCALPHA)
        color=(165,183,89) if kind!='ScorpionProjectile' else (207,173,104)
        pygame.draw.ellipse(effect,(*color,135),effect.get_rect())
        pygame.draw.ellipse(effect,(*CREAM,170),effect.get_rect().inflate(-max(2,rect.w//2),-max(2,rect.h//2)))
        screen.blit(effect,rect);return
    if kind=='Geyser':
        base=tile(rect.w,12,'volcanic');screen.blit(base,(rect.x,rect.bottom-12))
        if sprite.is_active():
            effect=pygame.Surface(rect.size,pygame.SRCALPHA)
            for y in range(rect.h-12):
                width=int(8+rect.w*.65*y/max(1,rect.h))
                pygame.draw.line(effect,(233,175,110,120+int(90*y/max(1,rect.h))),(rect.w//2-width//2,y),(rect.w//2+width//2,y),1)
            screen.blit(effect,rect)
        return
    if kind=='RisingLava':
        effect=pygame.Surface(rect.size,pygame.SRCALPHA)
        effect.fill((148,59,29,235))
        for y in range(min(rect.h,25)):
            pygame.draw.line(effect,(232-y*3,174-y*4,87-y*2,245),(0,y),(rect.w,y))
        screen.blit(effect,rect);return
    screen.blit(sprite.image,rect)

def panda_frames():
    from config import PLAYER_SIZE
    def frame(i):
        surf=pygame.Surface(PLAYER_SIZE,pygame.SRCALPHA)
        art=panda(i,PLAYER_SIZE)
        surf.blit(art,art.get_rect(midbottom=(PLAYER_SIZE[0]//2,PLAYER_SIZE[1])))
        return surf
    return {'idle':[frame(0),frame(1)],'run':[frame(2),frame(3)],'jump':[frame(4)],'fall':[frame(5)]}
