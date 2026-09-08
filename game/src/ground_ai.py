"""Ground opponents share terrain rules while keeping distinct attacks."""
import math
import pygame
from physics import ground_move, support

KINDS={'PatrolEnemy','ChaserEnemy','SlimeEnemy','SulfurSlime','KelpCrab','CactusScorpion','ReflectionPhantom','StalactiteSpider','BasaltGolem','TidalCrab'}

def update(enemy,dt,platforms,player,chapter=0):
    kind=type(enemy).__name__
    if kind not in KINDS: return False
    if not getattr(enemy,'alive_flag',True): return True
    dx=player.rect.centerx-enemy.rect.centerx
    dy=player.rect.bottom-enemy.rect.bottom
    grounded=support(enemy,platforms) is not None
    direction=getattr(enemy,'direction',1.)
    speed={'PatrolEnemy':100,'SlimeEnemy':125,'SulfurSlime':60,'KelpCrab':80,'CactusScorpion':60,'ReflectionPhantom':100,'TidalCrab':90,'StalactiteSpider':85}.get(kind,0)
    enemy._ai_timer=getattr(enemy,'_ai_timer',0)+dt
    if kind=='ChaserEnemy':
        enemy._jump_wait=max(0,getattr(enemy,'_jump_wait',0)-dt)
        active=abs(dx)<500 and abs(dy)<240
        direction=1 if dx>0 else -1
        speed=(185+min(chapter,17)*2.5) if active and abs(dx)>7 else 0
        obstacle=pygame.Rect(enemy.rect.centerx+direction*(enemy.rect.w//2+12),enemy.rect.bottom-42,5,36)
        wall=any(obstacle.colliderect(p.rect) for p in platforms)
        # Jump only towards a real landing surface, never blindly into a pit.
        landing=any(30 < direction*(p.rect.centerx-enemy.rect.centerx)<210 and -145< p.rect.top-enemy.rect.bottom<45 for p in platforms)
        if active and grounded and enemy._jump_wait<=0 and (wall or dy < -45) and landing:
            enemy.velocity_y=-650;enemy._jump_wait=1.15
        enemy.facing_right=direction>0
    elif kind=='BasaltGolem':
        enemy.state_timer-=dt
        if enemy.state=='dormant' and abs(dx)<100 and abs(dy)<80:
            enemy.state='telegraph';enemy.state_timer=.45;enemy.strike_dir=1 if dx>0 else -1
        elif enemy.state=='telegraph' and enemy.state_timer<=0:
            enemy.state='striking';enemy.state_timer=.4
        elif enemy.state=='striking' and enemy.state_timer<=0:
            enemy.state='cooldown';enemy.state_timer=2
        elif enemy.state=='cooldown' and enemy.state_timer<=0: enemy.state='dormant'
        speed=250 if enemy.state=='striking' else 65 if enemy.state=='cooldown' and abs(enemy.rect.x-enemy.origin_x)>4 else 0
        direction=enemy.strike_dir if enemy.state=='striking' else (1 if enemy.origin_x>enemy.rect.x else -1)
    elif kind=='StalactiteSpider':
        if enemy.state=='hanging':
            if abs(dx)<100 and dy>40: enemy.state='warning';enemy._drop_wait=.35
            return True
        if enemy.state=='warning':
            enemy._drop_wait-=dt
            if enemy._drop_wait<=0: enemy.state='dropping'
            return True
        if enemy.state=='dropping':
            speed=0
            if grounded: enemy.state='grounded';enemy.origin_x=enemy.rect.x
    origin=getattr(enemy,'origin_x',getattr(enemy,'start_x',enemy.rect.x))
    if kind!='ChaserEnemy' and kind!='BasaltGolem':
        width=getattr(enemy,'patrol_width',80)
        if enemy.rect.x>=origin+width: direction=-1
        elif enemy.rect.x<=origin-width: direction=1
    enemy.direction=direction
    if kind=='SlimeEnemy':
        enemy.hop_timer+=dt
        if grounded and enemy.hop_timer>=.85: enemy.velocity_y=-350;enemy.hop_timer=0
    ground_move(enemy,speed*direction,dt,platforms)
    if kind=='SulfurSlime':
        from biomes import ToxicTrail
        enemy._pending_trails.clear();enemy.trail_timer+=dt
        if enemy.trail_timer>=.65 and grounded:
            enemy.trail_timer=0;enemy._pending_trails.append(ToxicTrail(enemy.rect.centerx-10,enemy.rect.bottom))
    if kind=='CactusScorpion':
        from biomes import ScorpionProjectile
        enemy._pending_proj.clear();enemy.fire_timer-=dt
        if enemy.fire_timer<=0 and abs(dx)<480 and abs(dy)<220:
            enemy.fire_timer=2.1
            enemy._pending_proj.append(ScorpionProjectile(enemy.rect.centerx,enemy.rect.top,1 if dx>0 else -1))
    if hasattr(enemy,'_frames'):
        frames=enemy._frames
        enemy.image=frames[int(enemy._ai_timer*5)%len(frames)]
        if direction<0: enemy.image=pygame.transform.flip(enemy.image,True,False)
    if enemy.rect.top>620: enemy.kill();enemy.alive_flag=False
    return True
