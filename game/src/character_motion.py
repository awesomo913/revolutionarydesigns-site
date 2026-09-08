"""Cached cutout rigs: moving limbs/wings, stable feet, no opacity flashing.

All deformation is presentation-only. The simulation owns collision rectangles.
Thirty-two poses per cycle are rendered at double resolution for small sprites.
"""
import math
from functools import lru_cache
import pygame

WALKERS={0,1,4,7,8,10,11,15,16,17,23}
FLIERS={3,6}
SPIRITS={14,18,20}

def _part(target, source, rect, pivot, angle=0, scale_y=1):
    piece=source.subsurface(rect)
    piece=pygame.transform.smoothscale(piece,(rect.w,max(1,round(rect.h*scale_y))))
    # Rotate around the top-centre attachment, not the centre of the limb.
    offset=pygame.Vector2(0,piece.get_height()/2).rotate(-angle)
    rotated=pygame.transform.rotate(piece,angle)
    target.blit(rotated,rotated.get_rect(center=(round(pivot[0]+offset.x),round(pivot[1]+offset.y))))

@lru_cache(maxsize=1024)
def rig_frame(identity, size, phase, mode='idle'):
    from journey_art import creature, panda
    is_hero=isinstance(identity,str)
    pose=int(identity.split(':')[1]) if is_hero else identity
    source=panda(pose,size) if is_hero else creature(identity,size)
    # Double-resolution parts keep rotated leg edges clean at gameplay scale.
    source=pygame.transform.smoothscale(source,(source.get_width()*2,source.get_height()*2))
    w,h=source.get_size();pad=max(8,round(max(w,h)*.14))
    target=pygame.Surface((w+pad*2,h+pad*2),pygame.SRCALPHA)
    t=phase*math.tau/32;s=math.sin(t);c=math.cos(t)
    x=pad;y=pad
    walking=mode=='walk'
    attack=mode in ('attack','windup')
    if (not is_hero and identity in FLIERS):
        # Two articulated wings fold independently around the stable torso.
        left=round(w*.36);right=round(w*.64)
        wing_scale=.52+.48*(s+1)/2
        _part(target,source,pygame.Rect(0,0,left,h),(x+left/2,y+round(h*.08*(1-s))),-12*s,wing_scale)
        _part(target,source,pygame.Rect(right,0,w-right,h),(x+right+(w-right)/2,y+round(h*.08*(1-s))),12*s,wing_scale)
        target.blit(source.subsurface((left,0,right-left,h)),(x+left,y))
    elif walking and ((not is_hero and identity in WALKERS) or is_hero):
        # Alternating attached feet; the upper body never changes silhouette.
        # Panda's cream belly extends nearly to its ankles. Splitting at the
        # generic hip height would tear that continuous patch while walking.
        hip=round(h*(.84 if is_hero else .68 if identity==1 else .74))
        divisions=(0,.24,.48,.72,1) if identity==1 else (0,.5,1)
        stride=25 if identity==1 else 20
        for i in range(len(divisions)-1):
            a=round(w*divisions[i]);b=round(w*divisions[i+1])
            swing=math.sin(t+(i%2)*math.pi+(i//2)*.7)
            _part(target,source,pygame.Rect(a,hip-4,b-a,h-hip+4),
                  (x+(a+b)/2,y+hip-4-round(max(0,swing)*h*.025)),stride*swing)
        body=source.subsurface((0,0,w,hip+3))
        body=pygame.transform.smoothscale(body,(w,hip+3-round((1-c* c)*h*.025)))
        target.blit(body,(x,y+round((1-c*c)*h*.025)))
    elif not is_hero and identity in (2,5,15,22):
        # Slimes breathe and compress; puffers/eaters visibly swell to attack.
        amount=.075 if identity in (2,5) else .04
        sy=1+amount*s+(.07 if attack else 0)
        squish=pygame.transform.smoothscale(source,(round(w*(2-sy)),round(h*sy)))
        target.blit(squish,squish.get_rect(midbottom=(x+w//2,y+h)))
    elif not is_hero and identity in SPIRITS|{9,19}:
        # Continuous body ripple for spirits/vortex; the drone gently banks.
        for row in range(h):
            sway=round(math.sin(t+row/h*math.tau)*w*.045*(row/h if identity in SPIRITS else .6))
            target.blit(source,(x+sway,y+row),pygame.Rect(0,row,w,1))
    elif not is_hero and identity==21:
        # The hammer's simulation controls its slam; its handle winds up.
        angle=(9*s if mode!='attack' else 18+4*s)
        rotated=pygame.transform.rotate(source,angle)
        target.blit(rotated,rotated.get_rect(midbottom=(x+w//2,y+h)))
    else:
        # Stable lower body with breathing/head sway (including idle panther).
        for row in range(h):
            upper=max(0,1-row/(h*.8))
            sway=round(s*w*(.022 if not attack else .055)*upper)
            target.blit(source,(x+sway,y+row),pygame.Rect(0,row,w,1))
        if not is_hero and identity==13:
            # Crystal glint moves across its face without hiding the sprite.
            gx=round(x+w*(.3+.35*(s+1)/2));gy=round(y+h*.36)
            pygame.draw.line(target,(225,246,255),(gx-2,gy),(gx+2,gy),1)
        if not is_hero and identity==12 and attack:
            jaw=source.subsurface((0,h//2,w,h-h//2))
            target.blit(jaw,(x+round(3*s),y+h//2+round(2+2*c)))
    # Continuous deformation across the whole silhouette connects the limb rig
    # to a weighted torso. Nothing blinks, and collision bounds never change.
    p=phase/31
    pulse=math.sin(math.pi*p)
    lean=0;stretch=1
    if mode=='walk':
        lean=2.5*s;stretch=1+.018*math.cos(2*t)
    elif mode=='windup':
        lean=-7*(.65+.35*p);stretch=.94-.035*p
    elif mode=='attack':
        lean=12*pulse+6*p-4*(1-p);stretch=1-.08*pulse-.025*p
    elif mode=='hurt':
        lean=-14*pulse;stretch=1-.12*pulse
    elif mode=='air':
        lean=3*s;stretch=1.035+.018*s
    else:
        stretch=1+.014*s
    # Shear around the feet: grounded sprites do not float when they breathe.
    bent=pygame.Surface(target.get_size(),pygame.SRCALPHA)
    for row in range(target.get_height()):
        offset=round(math.tan(math.radians(lean))*(y+h-row)*.55)
        bent.blit(target,(offset,row),pygame.Rect(0,row,target.get_width(),1))
    new_h=round(bent.get_height()*stretch)
    shaped=pygame.transform.smoothscale(bent,(round(bent.get_width()/stretch),new_h))
    target.fill((0,0,0,0))
    target.blit(shaped,shaped.get_rect(midbottom=(target.get_width()//2,y+h+round(pad*stretch))))
    return pygame.transform.smoothscale(target,(target.get_width()//2,target.get_height()//2)),pad//2

def creature_motion(index,size,time,mode='walk'):
    phase=min(31,int(time*32)) if mode in ('attack','hurt','windup') else int(time*32)%32
    return rig_frame(index,size,phase,mode)


def update_motion(sprite,dt,previous):
    """Distance-driven footsteps, time-driven breathing, separate action clocks."""
    distance=math.hypot(sprite.rect.x-previous.x,sprite.rect.y-previous.y)
    rate=1-math.exp(-dt*10)
    sprite.visual_speed=getattr(sprite,'visual_speed',0)+(min(900,distance/max(.001,dt))-getattr(sprite,'visual_speed',0))*rate
    sprite.visual_time=getattr(sprite,'visual_time',0)+dt*(min(2.8,max(.65,sprite.visual_speed/75)))
    state=getattr(sprite,'state','')
    if getattr(sprite,'_attack_pose',0)>0: state='attacking';sprite._attack_pose=max(0,sprite._attack_pose-dt)
    if getattr(sprite,'flash_timer',0)>0: mode='hurt'
    elif state in ('telegraph','warning'): mode='windup'
    elif state in ('attacking','striking','snapping','open','slamming','lunging','swoop','puffing','leaping'): mode='attack'
    elif sprite.visual_speed>12: mode='walk'
    else: mode='idle'
    old=getattr(sprite,'motion_mode','idle')
    sprite.action_time=(getattr(sprite,'action_time',0)+dt) if old==mode else 0
    sprite.motion_mode=mode


def enemy_motion(sprite,index):
    mode=getattr(sprite,'motion_mode','idle')
    clock=getattr(sprite,'action_time',0)/(.35 if mode!='windup' else .65) if mode in ('attack','windup','hurt') else getattr(sprite,'visual_time',0)
    return creature_motion(index,(max(30,sprite.rect.w),max(30,sprite.rect.h)),clock,mode)


class DefeatPose:
    """Short, non-colliding recoil; gameplay removes the enemy immediately."""
    def __init__(self,sprite,source_x):
        from journey_art import CAST
        self.index=CAST[type(sprite).__name__]
        self.size=(max(30,sprite.rect.w),max(30,sprite.rect.h))
        self.x,self.y=sprite.rect.midbottom
        self.direction=1 if self.x>=source_x else -1
        self.facing=getattr(sprite,'facing_right',getattr(sprite,'direction',1)>=0)
        self.age=0.0

    def draw(self,screen,cam_x,cam_y):
        progress=min(1,self.age/.38)
        art,pad=rig_frame(self.index,self.size,round(progress*31),'hurt')
        if not self.facing: art=pygame.transform.flip(art,True,False)
        art=pygame.transform.rotate(art,-self.direction*progress*22)
        # A single dissolve at the end, never alternating visibility.
        if progress>.55:
            art=art.copy();art.set_alpha(round(255*(1-progress)/.45))
        pos=(round(self.x+cam_x+self.direction*progress*30),round(self.y+cam_y-math.sin(progress*math.pi)*24+pad))
        screen.blit(art,art.get_rect(midbottom=pos))

def hero_motion(player):
    # Reuse one consistent idle face; the former two unrelated stills popped.
    if player.is_victory_dancing: pose,mode=11,'walk'
    elif player.dead or player.knockback_timer>0: pose,mode=9,'hurt'
    elif player.is_attacking: pose,mode=8,'attack'
    elif player.is_dashing: pose,mode=2,'walk'
    elif player.is_slamming: pose,mode=0,'attack'
    elif player.is_gliding: pose,mode=6,'air'
    elif not player.is_on_ground: pose,mode=(4 if player.velocity_y<0 else 5),'air'
    elif abs(player.velocity_x)>10: pose,mode=0,'walk'
    else: pose,mode=0,'idle'
    # Weapon/glider extensions may extend beyond the body's collision box.
    height=player.rect.h+3
    width=round(height*(1.55 if pose in (6,8) else 1.25))
    clock=getattr(player,'walk_time',getattr(player,'visual_time',0)) if mode=='walk' else getattr(player,'visual_time',0)*.75
    phase=int(clock*32)%32
    if player.is_attacking: phase=round(max(0,min(1,1-player.attack_timer/.25))*31)
    elif player.knockback_timer>0: phase=round(max(0,min(1,1-player.knockback_timer/.25))*31)
    art,pad=rig_frame('hero:'+str(pose),(width,height),phase,mode)
    if player.is_slamming:
        art=pygame.transform.smoothscale(art,(art.get_width(),round(art.get_height()*.84)))
        pad=round(pad*.84)
    return art,pad
