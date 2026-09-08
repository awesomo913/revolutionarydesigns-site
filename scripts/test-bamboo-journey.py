"""Exercise the shipped archive, all chapters and critical interaction paths."""
from pathlib import Path
import argparse
import json
import os
import sys
import tarfile
import tempfile
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
parser=argparse.ArgumentParser();parser.add_argument('--preview-dir',type=Path);args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
out=args.preview_dir.resolve() if args.preview_dir else None
if out: out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='bamboo-journey-',ignore_cleanup_errors=True) as tmp:
    target=Path(tmp)
    with tarfile.open(root/'game/web.tar.gz') as tar: tar.extractall(target,filter='data')
    assets=target/'assets';os.chdir(assets);sys.path.insert(0,str(assets))
    import pygame
    pygame.init();pygame.display.set_mode((960,540))
    import visual_skin
    visual_skin.install();visual_skin.install()
    from game import Game
    from config import *
    from journey_art import image,cell,draw_sprite,CAST,PROPS,LEVEL_WORLDS,panda,creature
    from journey_ui import JourneyMenu,LevelTransition,VictoryScreen,EndScreen
    game=Game()
    def shot(name):
        if out: pygame.image.save(game.screen,str(out/(name+'.png')))
    def click(pos):
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos));game._handle_events()
    game._draw();shot('01-title')
    assert len(game.title_screen.buttons)==4
    click(game.title_screen._gallery_button_rect.center);game._draw();shot('02-field-guide')
    assert game.title_screen.page=='field'
    chars=game.title_screen.characters()
    for i,char in enumerate(chars):
        game.title_screen.selected_char=char;game._draw()
        if i in (0,5,len(chars)-1): shot(f'03-character-{i}')
    game.title_screen.activate('controls');game._draw();shot('04-abilities')
    game.title_screen.activate('chapters');game._draw();shot('05-chapters')
    for page in range(3):
        game.title_screen.page_number=page;game._draw()
        assert len([a for _,a in game.title_screen.buttons if a.startswith('practice:')])==6
    game.title_screen.activate('home');game._draw()
    click(game.title_screen.buttons[0][0].center)
    assert game.state==ST_PLAYING and game.player.rect.size==(36,44)
    for _ in range(90): game._update(1/60)
    game._draw();shot('06-grove-play')
    game._on_key_down(pygame.K_ESCAPE);game._draw();shot('07-pause')
    assert game.state==ST_PAUSED
    game.pause_overlay.activate('controls');game._draw();game._on_key_down(pygame.K_ESCAPE)
    assert game.state==ST_PAUSED
    game._on_key_down(pygame.K_ESCAPE);assert game.state==ST_PLAYING
    # Every old rendering category gets exercised over the entire level,
    # including remote hazards not visible from the spawn point.
    kinds=set();counts=[]
    for level in range(18):
        game._start_game(level,practice=True)
        assert game.player.has_ice_magic and game.player.has_bamboo_weapon
        assert game.background.biome==LEVEL_WORLDS[level]
        for _ in range(60): game._update(1/60)
        game._draw();shot(f'level-{level+1:02}')
        for sprite in game.level.all_sprites:
            kinds.add(type(sprite).__name__)
            # Isolate each sprite at its native visual size; don't change rect.
            draw_sprite(game.screen,sprite,80-sprite.rect.x,200-sprite.rect.y,LEVEL_WORLDS[level])
        counts.append(dict(level=level+1,biome=game.background.biome,sprites=len(game.level.all_sprites)))
    # Practice is not allowed to pollute scored Journey state.
    game._start_game(4,practice=True);lives=game.lives
    game._respawn_at_checkpoint();assert game.lives==lives and game.player.has_bamboo_weapon
    game._start_game();assert not game.practice_mode and not game.player.has_ice_magic
    assert not game._has_ice_magic_permanent and game.player.score==0
    assert not game._weapon_used and game.hud.displayed_hp==PLAYER_MAX_HP
    # Combat abilities and timer boundaries.
    game._start_game(0,practice=True);player=game.player
    player.is_on_ground=True;player.jumps_remaining=2
    assert player.jump();player.is_on_ground=False
    assert player.jump();assert not player.jump()
    assert player.attack();assert not player.attack()
    assert player.throw_bamboo();assert not player.throw_bamboo()
    assert player.cast_ice_spell();assert not player.cast_ice_spell()
    player.is_attacking=False;player.input_locked=False
    assert player.dash();assert not player.dash()
    player.reset_state();assert not player.input_locked and not player.is_dashing
    player.weapon_time_remaining=.01;player.dash_time_remaining=.01
    player.update(.05,pygame.key.get_pressed(),game.level.platforms)
    assert not player.has_bamboo_weapon and player.dash_time_remaining==0
    # Regressions uncovered by the visual audit: drawing loops overwrote y.
    from sprites import DashBoots, Boss, MovingPlatform
    from biomes import Geyser, TimedGate, CrumblingPlatform, Crystal, DarkWall, TeleportPortal, DustDevil
    assert DashBoots(400,490).rect.centery==468
    geyser=Geyser(700,490);assert geyser.rect.bottom==490
    geyser.erupt_remaining=1;geyser.update(.01);assert geyser.rect.bottom==490 and geyser.rect.height==200
    geyser.update(2);assert geyser.rect.bottom==490 and geyser.rect.height==24
    # Boss attacks have one damage window, not one hit per overlapping frame.
    boss=Boss(700,490);hp=boss.hp
    boss.stunned=False;assert not boss.take_hit() and boss.hp==hp
    boss.stunned=True;boss.flash_timer=0;boss.take_hit();assert boss.hp==hp-1
    boss.take_hit();assert boss.hp==hp-1
    # Timed gates and crystal walls change their collision membership.
    group=pygame.sprite.Group();TimedGate._global_timer=0
    gate=TimedGate(100,300,100,20,'A',group);gate.update(.01);assert gate.solid and gate in group
    TimedGate.tick_global(GATE_CYCLE_SEC*.5+.01);gate.update(.01);assert not gate.solid and gate not in group
    crystals=pygame.sprite.Group();crystal=Crystal(100,300);crystals.add(crystal)
    wall=DarkWall(110,280,40,120,crystals,group);assert wall in group
    crystal.strike();wall.update(.01);assert not wall.solid and wall not in group
    crystal.update(CRYSTAL_LIGHT_TIME+.1);wall.update(.01);assert wall.solid and wall in group
    portal=TeleportPortal(200,490,0);portal.teleport();assert not portal.active
    portal.update(PORTAL_COOLDOWN_SEC+.1);assert portal.active
    crumble=CrumblingPlatform(100,300,100,20,group);group.add(crumble);crumble.touch()
    crumble.update(CRUMBLE_DELAY+.01);assert not crumble.solid and crumble not in group
    crumble.update(CRUMBLE_RESPAWN+.01);assert crumble.solid and crumble in group and crumble.rect.size==(100,20)
    # Jumping away from an ascending platform must not snap the player back.
    game._start_game();mp=MovingPlatform(100,400,150,20,'vertical',100);mp.direction=-1
    game.level.platforms.add(mp);game.level.moving_platforms.add(mp);game.level.all_sprites.add(mp)
    game.player.rect.midbottom=(160,400);game.player.is_on_ground=True;game.player.jumps_remaining=2
    assert game.player.jump();game._update_gameplay(1/60)
    assert game.player.velocity_y<0 and game.player.rect.bottom<mp.rect.top-3
    # A piercing ice spell removes an invulnerable hazard and scores once.
    from sprites import IceProjectile
    game._start_game(0,practice=True)
    hazard=DustDevil(600,490,100);hazard.rect=pygame.Rect(590,390,180,110)
    hazard.update=lambda *args: None
    game.level.enemies.empty();game.level.enemies.add(hazard);game.level.all_sprites.add(hazard)
    ice=IceProjectile(620,450,1);game.level.projectiles.add(ice);game.level.all_sprites.add(ice)
    score=game.player.score;game._update_gameplay(.001)
    assert hazard not in game.level.enemies and game.player.score==score+STOMP_SCORE
    score=game.player.score;game._update_gameplay(.001);assert game.player.score==score
    # Score storage tolerates malformed data and reloads valid results.
    import save
    Path(SAVE_FILE).write_text('{broken');assert save.load_high_scores()==[]
    assert save.save_high_score(1234,8);assert save.get_best_score()==1234
    Path(SAVE_FILE).write_text('{"high_scores":[null,{"score":"bad","level":1}]}');assert save.load_high_scores()==[]
    # Death, game over, victory and chapter transitions all render and exit.
    game._start_game();game.lives=1;game._respawn_at_checkpoint();assert game.state==ST_GAME_OVER
    game._draw();shot('08-game-over');click((480,427));assert game.state==ST_MENU
    game._start_game(17,practice=True);game._advance_level();assert game.state==ST_VICTORY
    game._draw();shot('09-victory');game._on_key_down(pygame.K_RETURN);assert game.state==ST_MENU
    for i in range(1,19):
        transition=LevelTransition(i);transition.draw(game.screen)
        if i==14: shot('10-transition')
        assert transition.update(2.5)
    # Keyed atlas backgrounds decode to alpha and every subject survives.
    for name,cols,rows in [('panda-journey.png',4,3),('creatures-journey.png',6,4),('relics-journey.png',4,4)]:
        atlas=image(name);assert atlas.get_at((0,0)).a==0,name
        for i in range(cols*rows): assert cell(name,cols,rows,i).get_bounding_rect().height>5
    result=dict(chapters=counts,characters=len(chars),sprite_types=sorted(kinds),checks='menu mouse/keyboard; pause nesting; fresh-run reset; practice retries; jumps; attack/throw/dash/ice cooldowns; timers; end screens; all chapter transitions; atlas transparency')
    if out: (out/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));pygame.quit();os.chdir(root)
