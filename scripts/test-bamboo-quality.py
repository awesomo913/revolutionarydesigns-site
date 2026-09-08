"""Gameplay regressions against the actual distributable, including all chapters."""
import os,sys,tarfile,tempfile,json,math
from pathlib import Path
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(condition,label):
    assert condition,label
    checks.append(label)
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
    with tarfile.open(ROOT/'game/web.tar.gz') as tar: tar.extractall(folder,filter='data')
    assets=Path(folder)/'assets';os.chdir(assets);sys.path.insert(0,str(assets))
    import pygame
    pygame.init();pygame.display.set_mode((960,540))
    import visual_skin;visual_skin.install()
    from game import Game
    from sprites import Player,Platform,MovingPlatform,BambooShuriken
    from biomes import TimedGate,DarkWall,Crystal,CrumblingPlatform,FalseGlowworm,ForgeHammer,VoidEater,PhaseWraith,HomingSpecter,RisingLava
    from levels import build_level_state
    from physics import move_axis,top_contact,support,projectile_hits,moving_platform_step
    from ground_ai import update as ground_update
    from config import *
    import save
    class Keys:
        def __init__(self,*keys):self.keys=keys
        def __getitem__(self,key):return key in self.keys
    none=Keys();floor=Platform(0,490,1000,50);group=pygame.sprite.Group(floor)
    p=Player(100,490);p.has_double_jump=True;p.jumps_remaining=2;p.is_on_ground=True;p.coyote_timer=.12
    check(p.jump() and p.jump() and not p.jump(),'coyote cannot grant a third jump')
    p=Player(100,490);p.is_on_ground=True;p.jump();top=490
    for _ in range(90):p.update(1/120,none,group);top=min(top,p.rect.bottom)
    check(490-top>165,'normal jump retains its specified impulse')
    p=Player(100,490);p.velocity_y=-1100
    p.update(1/60,none,group);check(p.velocity_y < -1000,'spring launches are not clamped to falling speed')
    for dt in (1/120,1/60,.05):
        p=Player(100,300);p.velocity_y=1200;p.is_slamming=True
        thin=Platform(80,330,140,4)
        for _ in range(12):p.update(dt,none,pygame.sprite.Group(thin))
        check(p.rect.bottom==330,f'slam lands on 4px platform at dt={dt}')
        wall=Platform(170,0,4,540);p=Player(100,490);p.dash_time_remaining=30;p.dash()
        for _ in range(12):p.update(dt,Keys(pygame.K_RIGHT),pygame.sprite.Group(floor,wall))
        check(p.rect.right<=170 and not p.input_locked,f'dash cannot tunnel or lock at dt={dt}')
    p=Player(100,490);wall=Platform(150,0,10,540)
    lift=MovingPlatform(80,350,140,20,axis='vertical');lift.direction=-1
    ceiling=Platform(50,280,200,20);p=Player(110,350);p.is_on_ground=True
    for _ in range(60):
        moving_platform_step(p,lift,1/60,pygame.sprite.Group(lift,ceiling))
        check(not p.rect.colliderect(lift.rect) and not p.rect.colliderect(ceiling.rect),'lift cannot crush a rider into a ceiling')
    p=Player(110,lift.rect.top);p.is_on_ground=True;p.velocity_y=-780
    before=p.rect.copy();moving_platform_step(p,lift,1/60,pygame.sprite.Group(lift))
    check(p.rect==before,'jump leaves moving platform without being recaptured')
    mover=MovingPlatform(80,400,80,20);wall=Platform(200,300,20,190)
    p=Player(160,430);p.is_on_ground=False
    for _ in range(120):
        moving_platform_step(p,mover,1/60,pygame.sprite.Group(mover,wall))
        check(not p.rect.colliderect(mover.rect) and not p.rect.colliderect(wall.rect),'horizontal mover pushes safely or reverses at obstruction')
    p=Player(100,490);wall=Platform(150,0,10,540)
    move_axis(p,200,pygame.sprite.Group(wall),'x');check(p.rect.right==150,'external wind respects walls')
    check(not top_contact(pygame.Rect(100,130,36,44),pygame.Rect(110,140,36,44),pygame.Rect(130,140,30,30),True),'side collision is not a stomp')
    p=Player(100,490);check([p.collect_bamboo() for _ in range(4)]==[100,200,300,400],'combo multiplier matches displayed reward')
    p=Player(100,490);p.dead=True;p.has_bamboo_weapon=True;p.dash_time_remaining=20;p.has_ice_magic=True;p.mana=100
    check(not any((p.jump(),p.attack(),p.dash(),p.slam(),p.throw_bamboo(),p.cast_ice_spell())),'dead player cannot use abilities')
    gates=pygame.sprite.Group();TimedGate._global_timer=0
    gate=TimedGate(100,300,100,20,'B',gates);TimedGate.tick_global(1.6);occupant=pygame.Rect(120,290,36,44)
    gate.update(.01,occupant);check(not gate.solid,'gate waits for occupant before materializing')
    gate.update(.01,pygame.Rect(0,0,10,10));check(gate.solid,'gate recovers after occupant clears')
    cp=CrumblingPlatform(100,300,100,20,gates);gates.add(cp);cp.touch();cp.update(1.1);cp.update(4.1,occupant)
    check(not cp.solid,'crumbling platform cannot respawn through player')
    cp.update(.1,pygame.Rect(0,0,10,10));check(cp.solid and cp in gates,'crumbling platform reappears safely')
    game=Game();game._start_game(0,practice=True)
    game._start_game(14,practice=True);game.player.invincible_timer=0
    game.level.rising_lava.current_y=450;game.level.rising_lava.rect.top=450
    item=next(iter(game.level.bamboos));item.rect.center=game.player.rect.center
    game._update_gameplay(.001)
    check(game.player.dead and game.death_anim is not None and item in game.level.bamboos,'fatal lava cannot collect a coincident reward')
    # Award once when the staff destroys the cave lure; never farm hammers.
    for kind,should_die in ((FalseGlowworm,True),(ForgeHammer,False)):
        game._start_game(0,practice=True);game.level.enemies.empty();e=kind(150,470);e.update=lambda *a:None;e.rect=pygame.Rect(145,451,30,30)
        game.level.enemies.add(e);game.player.rect.bottomleft=(105,490);game.player.attack();game.player.attack_timer=.15
        score=game.player.score;game._update_gameplay(.001)
        check((e not in game.level.enemies)==should_die,f'{kind.__name__} weapon behavior')
        check(game.player.score==score+(200 if should_die else 0),f'{kind.__name__} score reflects actual defeat')
    game._start_game();item=next(iter(game.level.bamboos));game.player.rect.center=item.rect.center
    game._update_gameplay(.001);score=game.player.score;identity=item.spawn_id
    game._total_score=score;game._respawn_at_checkpoint()
    check(all(x.spawn_id!=identity for x in game.level.bamboos),'checkpoint retries cannot farm collected bamboo')
    lava=RisingLava(1000)
    for _ in range(3600):lava.update(1/60)
    check(lava.current_y>=450,'forge route is not erased by unbounded lava')
    ghost=PhaseWraith(100,400);ghost.teleport_to(1500,490);ghost.update(.01,group,p)
    check(abs(ghost.rect.centerx-1500)<25,'wraith stays at destination instead of snapping to old patrol')
    specter=HomingSpecter(1400,300);p=Player(100,490);old=specter.rect.copy();specter.update(1/60,group,p)
    check(specter.rect==old,'distant specters do not converge from the entire map')
    from sprites import ChaserEnemy
    wolf=ChaserEnemy(500,490);p=Player(300,490)
    for _ in range(30):ground_update(wolf,1/60,group,p,10)
    check(wolf.rect.x<440 and wolf.rect.bottom==490,'wolf pursues across solid ground')
    # Every physical platform gets a real falling collision test. Geometry graph
    # includes alternating and moving supports; it is a route audit, not a speedrun.
    # Each biome's special interaction is exercised through the game loop.
    game._start_game(13,practice=True);game.level.enemies.empty();mush=next(iter(game.level.mushrooms))
    game.player.rect.midbottom=(mush.rect.centerx,mush.rect.top-2);game.player.velocity_y=300
    game._update_gameplay(1/60)
    check(game.player.velocity_y<=-1000,'mushroom spring launches through real gameplay loop')
    game._start_game(16,practice=True);game.level.enemies.empty();portal=next(iter(game.level.portals));target=portal.partner
    game.player.rect.midbottom=portal.rect.midbottom;game._update_gameplay(.001)
    check(abs(game.player.rect.centerx-target.rect.centerx)<3,'player portal reaches paired destination')
    for _ in range(140):game._update_gameplay(1/60)
    check(abs(game.player.rect.centerx-target.rect.centerx)<3,'standing in destination does not cause repeated teleport bounce')
    game._start_game(5,practice=True);game.level.enemies.empty();up=next(iter(game.level.updrafts))
    game.player.rect.center=up.rect.center;game.player.velocity_y=0
    for _ in range(10):game._update_gameplay(1/60)
    check(game.player.velocity_y<0,'updraft overcomes gravity rather than merely slowing fall')
    game._start_game(17,practice=True);game.level.enemies.empty();zone=next(z for z in game.level.gravity_zones if z.get_multiplier()<0)
    game.player.rect.center=zone.rect.center;game.player.velocity_y=0;game._update_gameplay(1/60)
    check(game.player.velocity_y<0,'reverse gravity applies on first physics step')
    game.player.is_on_ground=True;game.player.jumps_remaining=2;game.player.jump()
    check(game.player.velocity_y>0,'reverse-gravity jump pushes away from ceiling')
    chapter_rows=[]
    for i in range(18):
        lv=build_level_state(i);static=list(lv.platforms)+[g for g in lv.timed_gates if g not in lv.platforms]
        for platform in static:
            actor=Player(platform.rect.centerx-18,platform.rect.top-8);actor.velocity_y=500
            for _ in range(4):actor.update(1/60,none,pygame.sprite.Group(platform))
            check(actor.rect.bottom==platform.rect.top,f'chapter {i+1} platform {platform.rect.topleft} landing')
        for name in ('weapons','dash_pickups','glide_pickups'):
            check(len(getattr(lv,name))>0,f'chapter {i+1} supplies {name}')
            for item in getattr(lv,name):
                # A player body touching the item must have an unobstructed pose.
                poses=[pygame.Rect(item.rect.centerx-18+dx,item.rect.centery-22+dy,36,44) for dx in (-25,0,25) for dy in (-25,0,25)]
                check(any(r.colliderect(item.rect) and not any(r.colliderect(p.rect) for p in static) for r in poses),f'chapter {i+1} {name} has accessible contact')
        for cp in lv.checkpoints:
            pose=pygame.Rect(cp.spawn_x,cp.spawn_y-44,36,44)
            check(not any(pose.colliderect(p.rect) for p in static),f'chapter {i+1} checkpoint has clear spawn')
        # Conservative surface graph using a normal double jump with a 30px
        # horizontal landing margin. Moving/gate surfaces are candidate nodes;
        # their timing is tested separately, so this is not a full playthrough.
        surfaces=[p.rect for p in static if type(p).__name__!='DarkWall']
        reached={j for j,r in enumerate(surfaces) if r.left<=100<=r.right and r.top==490}
        def edge(a,b):
            rise=a.top-b.top
            if rise>325: return False
            gap=max(0,b.left-a.right,a.left-b.right)
            airtime=.88+math.sqrt(max(0,2*(348-rise)/1800))
            return gap+30<360*airtime
        for _ in surfaces:
            expanded=reached|{j for j,r in enumerate(surfaces) if any(edge(surfaces[k],r) for k in reached)}
            if expanded==reached:break
            reached=expanded
        check(len(reached)==len(surfaces),f'chapter {i+1} platform geometry connects from start')
        chapter_rows.append({'chapter':i+1,'platforms':len(static),'enemies':len(lv.enemies),'powers':sum(len(getattr(lv,n)) for n in ('weapons','dash_pickups','glide_pickups'))})
    # Exercise every enemy species through multiple cycles near a moving target.
    enemies={}
    for i in range(18):
        for enemy in build_level_state(i).enemies: enemies.setdefault(type(enemy).__name__,enemy)
    from ground_ai import KINDS
    arena=pygame.sprite.Group(Platform(0,490,10000,50))
    for kind,enemy in enemies.items():
        actor=Player(enemy.rect.centerx+100,490)
        for tick in range(720):
            actor.rect.x=enemy.rect.centerx+int(math.sin(tick/90)*160)
            actor.rect.bottom=490-int(max(0,math.sin(tick/60))*150)
            actor.is_on_ground=actor.rect.bottom==490
            if not ground_update(enemy,1/60,arena,actor,10): enemy.update(1/60,arena,actor)
            # Drain emissions as the game does; this also catches malformed payloads.
            for method in ('get_new_trails','get_new_projectiles','get_new_spores'):
                if hasattr(enemy,method):
                    for obj in getattr(enemy,method)(): check(isinstance(obj.rect,pygame.Rect),kind+' emits a physical object')
        check(all(math.isfinite(v) for v in enemy.rect),kind+' remains finite after 12 seconds')
    for i in range(18):
        game._start_game(i,practice=True);game.level.enemies.empty()
        if game.level.boss: game.level.boss.alive_flag=False;game.level.boss.kill()
        game.player.rect.midbottom=(game.level.goal.rect.left+30,320 if i==14 else 490)
        game.player.invincible_timer=1
        game._update_gameplay(.001)
        check(game._outro_active,f'chapter {i+1} exit starts celebration')
        score=game.player.score
        for _ in range(120):game._update(1/60)
        check(game.state in (ST_LEVEL_TRANS,ST_VICTORY),f'chapter {i+1} completes without soft lock')
        check(game.player.score==score,f'chapter {i+1} clear bonus awarded once')
    # Local top three is stable, validates input and preserves initials.
    Path(SAVE_FILE).write_text('{}')
    for score,name in ((100,'AAA'),(300,'BCD'),(200,'XYZ'),(50,'LOW')): save.save_high_score(score,3,name)
    check([s['initials'] for s in save.load_high_scores()]==['BCD','XYZ','AAA'],'top three initials sorted and persisted')
    check(not save.qualifies(100),'equal score does not displace existing third place')
    check(not save.save_high_score(-1,30,'BAD'),'malformed scores rejected')
    from journey_ui import EndScreen
    end=EndScreen();end.offer(999,18)
    for key in (pygame.K_j,pygame.K_p,pygame.K_a,pygame.K_RETURN):end.handle_key(key)
    check(save.load_high_scores()[0]['initials']=='JPA' and not end.pending,'initials entry saves once')
    check(game.audio.enabled and len(game.audio.sounds)==28,'all 28 action sounds load from archive')
    for i in range(18):game.audio.update(1,i)
    game.audio.update(1,17,True);check(game.audio._track=='boss','boss score starts')
    game.audio.toggle_music();game.audio.update(1,17);check(pygame.mixer.Channel(game.audio._channel).get_volume()==0,'music mute silences channel')
    print(json.dumps({'checks':len(checks),'chapters':chapter_rows,'result':'PASS'},indent=2))
    os.chdir(ROOT)
