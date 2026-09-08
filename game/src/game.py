"""Bamboo Forest - Main game entry point and loop (WEB BUILD)."""

from __future__ import annotations

import asyncio
import math
import sys

import pygame

from config import (
    COL_GOLD, CRYSTAL_RADIUS, DARK_RADIUS, DOUBLE_JUMP_LEVEL,
    ENEMY_STOMP_BOUNCE, FPS, FLOOR_Y, GEYSER_LAUNCH, HEAL_AMOUNT,
    LEVEL_COUNT, PLAYER_DAMAGE, PLAYER_MAX_HP, SCREEN_HEIGHT,
    SCREEN_WIDTH, STARTING_LIVES, STOMP_SCORE, ST_GAME_OVER,
    ST_LEVEL_TRANS, ST_MENU, ST_PAUSED, ST_PLAYING, ST_VICTORY,
    SULFUR_TRAIL_DMG, THERMAL_FORCE, TITLE, BOSS_KILL_SCORE,
    # Levels 14-18
    MUSHROOM_BOUNCE, DRONE_RANGE, DRONE_PULL,
)
from audio import AudioManager
from backgrounds import BiomeBackground
from engine import Camera, ParticleSystem, ScreenShake
from levels import build_level_state, LevelState
from save import save_high_score
from physics import move_axis, top_contact, projectile_hits, moving_platform_step
import ground_ai
from journey_art import draw_sprite, LEVEL_WORLDS, relic
from journey_ui import panel, text, wrap, GOLD, CREAM, SAGE
from sprites import BambooShuriken, BambooStaff, DashBoots, GlideFeather, IceProjectile, Player
from ui import (
    DeathAnimation, GameOverScreen, HUD, LevelTransition,
    PauseOverlay, TitleScreen, VictoryScreen,
)


class Game:
    """Main game class -- owns the loop and state machine."""

    def __init__(self) -> None:
        pygame.init()
        # Web build: plain display mode -- SCALED breaks under WASM/Pyodide.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.audio = AudioManager()
        self.background: BiomeBackground = BiomeBackground("forest")
        self.shake = ScreenShake()

        self.title_screen = TitleScreen()
        self.pause_overlay = PauseOverlay()
        self.game_over_screen = GameOverScreen()
        self.victory_screen = VictoryScreen()

        self.state: str = ST_MENU
        self.player: Player | None = None
        self.level: LevelState | None = None
        self.current_level: int = 0
        self.camera: Camera | None = None
        self.particles: ParticleSystem = ParticleSystem()
        self.hud: HUD = HUD()
        self.level_transition: LevelTransition | None = None
        self.death_anim: DeathAnimation | None = None
        self.running = True
        self.practice_mode = False

        self.lives: int = STARTING_LIVES
        self.respawn_x: int = 100
        self.respawn_y: int = FLOOR_Y
        self._total_score: int = 0

        self._carry_score: int = 0
        self._carry_health: int = 0
        self._was_on_ground: bool = False
        self._is_high_score: bool = False
        self._jump_pressed: bool = False
        self._boss_warning_timer: float = 0.0
        self._fullscreen: bool = False
        self._debug_mode: bool = False
        # Tutorial hints
        self._weapon_tutorial_timer: float = 0.0
        self._weapon_used: bool = False
        self._glide_tutorial_timer: float = 0.0
        self._glide_used: bool = False
        # Glide persists across levels once collected
        self._has_glide_permanent: bool = False
        # Ice magic: unlocked on first boss kill (Level 3), persists
        self._has_ice_magic_permanent: bool = False
        self._ice_tutorial_timer: float = 0.0
        self._ice_used: bool = False
        # Hitstop: brief pause on enemy hit for impact feel
        self._hitstop_timer: float = 0.0
        # Level-end outro: Pain-da auto-runs off screen after reaching goal
        self._outro_active: bool = False
        self._outro_timer: float = 0.0
        self._outro_speed: float = 240.0
        self._sync_audio_controls()

    async def run(self) -> None:
        """Async main loop -- Pygbag/WASM requirement."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
            await asyncio.sleep(0)
        pygame.quit()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == getattr(pygame, 'WINDOWFOCUSLOST', -1):
                self._jump_pressed = False
                if self.state == ST_PLAYING:
                    self.state = ST_PAUSED
                    self.pause_overlay = PauseOverlay()
            if event.type == pygame.KEYDOWN:
                # Global toggles (work in any state)
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                    continue
                if event.key == pygame.K_F3:
                    self._debug_mode = not self._debug_mode
                    continue
                self._on_key_down(event.key)
            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self._jump_pressed = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.state == ST_MENU:
                    # Clicking a character card opens the detail popup
                    self.title_screen.handle_click(event.pos)
                    self._consume_menu_action(self.title_screen)
                elif event.button == 1 and self.state == ST_PAUSED:
                    self.pause_overlay.handle_click(event.pos)
                    self._consume_menu_action(self.pause_overlay)
                elif event.button == 1 and self.state in (ST_GAME_OVER, ST_VICTORY):
                    end = self.victory_screen if self.state == ST_VICTORY else self.game_over_screen
                    if end.handle_click(event.pos):
                        continue
                    self.state = ST_MENU
                    self.title_screen = TitleScreen()
                elif event.button == 1 and self.state == ST_PLAYING:
                    if self.player and self.player.attack():
                        self.audio.play("attack")
                        self._weapon_used = True
                        self._weapon_tutorial_timer = 0.0

    def _toggle_fullscreen(self) -> None:
        """Browser handles F11 natively; in-game F11 is a no-op."""
        pass

    def _maybe_unlock_ice_magic(self) -> None:
        """Grant ice magic on first boss defeat. Persists across levels."""
        if self._has_ice_magic_permanent:
            return
        self._has_ice_magic_permanent = True
        self.player.has_ice_magic = True
        self.player.mana = self.player.mana_max  # full mana as reward
        self._ice_tutorial_timer = 999.0
        self._ice_used = False
        self.hud.add_floating_text(
            "ICE MAGIC UNLOCKED!",
            self.player.rect.centerx, self.player.rect.top - 40,
            (140, 220, 255))
        # Big sparkle burst around player
        for _ in range(20):
            self.particles.emit_sparkle(
                self.player.rect.centerx,
                self.player.rect.centery, 1)
        self.audio.play("crystal")

    def _on_key_down(self, key: int) -> None:
        if key in (pygame.K_F7,pygame.K_F8):
            self.audio.toggle_music() if key == pygame.K_F7 else self.audio.toggle()
            self._sync_audio_controls()
            return
        if self.state in (ST_GAME_OVER, ST_VICTORY):
            end = self.victory_screen if self.state == ST_VICTORY else self.game_over_screen
            if end.handle_key(key): return
        if key == pygame.K_m:
            self.audio.toggle_music()
            self._sync_audio_controls()
            return
        if key == pygame.K_n:
            self.audio.toggle()
            self._sync_audio_controls()
            return
        if self.state == ST_MENU:
            self.title_screen.handle_key(key)
            self._consume_menu_action(self.title_screen)
        elif self.state == ST_PLAYING:
            if key == pygame.K_ESCAPE:
                # ESC in fullscreen drops to windowed first, THEN pauses
                if self._fullscreen:
                    self._toggle_fullscreen()
                self.state = ST_PAUSED
                self.pause_overlay = PauseOverlay()
                self.audio.play("menu_select")
            elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if not self._jump_pressed and self.player:
                    grounded = self.player.is_on_ground or self.player.coyote_timer > 0
                    if self.player.jump():
                        self.audio.play("jump" if grounded else "double_jump")
                    self._jump_pressed = True
            elif key in (pygame.K_e, pygame.K_x):
                if self.player and self.player.attack():
                    self.audio.play("attack")
                    self._weapon_used = True
                    self._weapon_tutorial_timer = 0.0
            elif key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                if self.player and self.player.dash():
                    self.audio.play("dash")
                    self.particles.emit_dust(
                        self.player.rect.centerx, self.player.rect.bottom)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                if self.player and self.player.slam():
                    self.audio.play("slam")
            elif key in (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_q):
                if self.player and self.player.throw_bamboo():
                    self.audio.play("throw")
            elif key == pygame.K_r:
                # Cast ice spell (requires boss-kill unlock + full mana)
                if self.player and self.player.cast_ice_spell():
                    self.audio.play("crystal")
                    self._ice_used = True
                    self._ice_tutorial_timer = 0.0
                    # Cast burst particles at player
                    for _ in range(12):
                        self.particles.emit_sparkle(
                            self.player.rect.centerx,
                            self.player.rect.centery, 1)
                    self.shake.trigger(4, 0.1)
        elif self.state == ST_PAUSED:
            self.pause_overlay.handle_key(key)
            self._consume_menu_action(self.pause_overlay)
        elif self.state in (ST_GAME_OVER, ST_VICTORY):
            if key == pygame.K_RETURN:
                self.state = ST_MENU
                self.title_screen = TitleScreen()

    # ------------------------------------------------------------------
    # Level management
    # ------------------------------------------------------------------

    def _consume_menu_action(self, menu):
        action = menu.action
        menu.action = None
        if action == 'start':
            self._start_game()
        elif action == 'resume':
            self.state = ST_PLAYING
            self._jump_pressed = False
        elif action == 'quit':
            self.state = ST_MENU
            self.title_screen = TitleScreen()
        elif action and action.startswith('practice:'):
            self._start_game(int(action.split(':')[1]), practice=True)
        if action:
            self.audio.play('menu_select')

    def _sync_audio_controls(self):
        if sys.platform == 'emscripten':
            import platform
            platform.window.setJourneyAudio(self.audio.music_enabled,self.audio.effects_enabled)

    def _start_game(self, level=0, practice=False) -> None:
        self.practice_mode = practice
        self.lives = STARTING_LIVES
        self.current_level = level
        self._total_score = 0
        self._carry_score = 0
        self._carry_health = PLAYER_MAX_HP
        self._has_ice_magic_permanent = practice
        self._has_glide_permanent = False
        self._weapon_used = self._glide_used = self._ice_used = practice
        self._weapon_tutorial_timer = self._glide_tutorial_timer = self._ice_tutorial_timer = 0
        self._hitstop_timer = 0
        self._boss_warning_timer = 0
        self._is_high_score = False
        self._spent = set()
        self.respawn_x = 100
        self.respawn_y = FLOOR_Y
        self._load_level(level)

    def _equip_practice(self):
        self.hud.practice = self.practice_mode
        self.hud.displayed_hp = self.player.health
        if self.practice_mode:
            self.player.has_bamboo_weapon = True
            self.player.weapon_time_remaining = 60
            self.player.dash_time_remaining = 60
            self.player.glide_time_remaining = 30

    def _load_level(self, level_num: int) -> None:
        self.current_level = level_num
        self._spent = set()
        from biomes import TimedGate
        TimedGate._global_timer = 0.0
        self.level = build_level_state(level_num)
        self.camera = Camera(self.level.world_width, SCREEN_HEIGHT)
        self.background = BiomeBackground(LEVEL_WORLDS[self.current_level])
        self.respawn_x = self.level.player_start[0]
        self.respawn_y = self.level.player_start[1]
        self.player = Player(self.respawn_x, self.respawn_y)
        if level_num >= DOUBLE_JUMP_LEVEL:
            self.player.has_double_jump = True
        # Glide + Dash are per-level timed pickups (not permanent).
        # Player must collect them each level to use those abilities.
        # Ice magic persists once unlocked from boss kill
        if self._has_ice_magic_permanent:
            self.player.has_ice_magic = True
            self.player.mana = self.player.mana_max
        if self.level.is_icy:
            self.player.friction_mode = "ice"
        else:
            self.player.friction_mode = "normal"
        self.player.reset_state()  # clear input locks, dash, attack flags
        self.player.score = self._total_score
        self.level.all_sprites.add(self.player)
        self.current_level = level_num
        self.particles = ParticleSystem()
        self.hud = HUD()
        self.hud.set_bamboo_count(len(self.level.bamboos))
        self.hud.lives = self.lives
        self._equip_practice()
        self.death_anim = None
        self._was_on_ground = False
        self._jump_pressed = False
        self._outro_active = False
        self._outro_timer = 0.0
        self._portal_lock = None
        self._sync_audio_controls()
        # If player already has weapon from previous level, keep tutorial hidden
        if self.player.has_bamboo_weapon:
            self._weapon_used = True
        self.state = ST_PLAYING

    def _respawn_at_checkpoint(self) -> None:
        if not self.practice_mode:
            self.lives -= 1
        if self.lives <= 0:
            self.game_over_screen = GameOverScreen()
            self.game_over_screen.offer(self._total_score,self.current_level+1,self.practice_mode)
            self.state = ST_GAME_OVER
            self.death_anim = None
            return
        self._portal_lock = None
        activated_xs = set()
        if self.level:
            for cp in self.level.checkpoints:
                if cp.activated:
                    activated_xs.add(cp.spawn_x)
        from biomes import TimedGate
        TimedGate._global_timer = 0.0
        self.level = build_level_state(self.current_level)
        if ("boss",0) in self._spent and self.level.boss:
            self.level.boss.alive_flag=False
            self.level.boss.kill()
        for group in (self.level.bamboos,self.level.enemies):
            for item in list(group):
                if item.spawn_id in self._spent: item.kill()
        self.camera = Camera(self.level.world_width, SCREEN_HEIGHT)
        self.background = BiomeBackground(LEVEL_WORLDS[self.current_level])
        for cp in self.level.checkpoints:
            if cp.spawn_x in activated_xs:
                cp.activate()
        self.player = Player(self.respawn_x, self.respawn_y)
        if self.current_level >= DOUBLE_JUMP_LEVEL:
            self.player.has_double_jump = True
        # Glide + Dash are per-level timed pickups (not permanent).
        # Player must collect them each level to use those abilities.
        # Ice magic persists once unlocked from boss kill
        if self._has_ice_magic_permanent:
            self.player.has_ice_magic = True
            self.player.mana = self.player.mana_max
        if self.level.is_icy:
            self.player.friction_mode = "ice"
        else:
            self.player.friction_mode = "normal"
        self.player.reset_state()
        self.player.score = self._total_score
        self.level.all_sprites.add(self.player)
        self.particles = ParticleSystem()
        self.hud = HUD()
        self.hud.set_bamboo_count(len(self.level.bamboos))
        self.hud.lives = self.lives
        self._equip_practice()
        self.death_anim = None
        self._was_on_ground = False
        self._jump_pressed = False
        self.state = ST_PLAYING

    def _advance_level(self) -> None:
        self._total_score = self.player.score
        next_lv = self.current_level + 1
        if next_lv >= LEVEL_COUNT:
            self.victory_screen = VictoryScreen()
            self.victory_screen.offer(self.player.score,self.current_level+1,self.practice_mode)
            self.state = ST_VICTORY
            self.audio.play("victory")
        else:
            self._carry_score = self.player.score
            self._carry_health = self.player.health
            self.level_transition = LevelTransition(next_lv + 1)
            self.state = ST_LEVEL_TRANS
            self.audio.play("menu_select")

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self, dt: float) -> None:
        in_world=self.state in (ST_PLAYING,ST_PAUSED,ST_LEVEL_TRANS)
        boss_active=bool(in_world and self.level and self.level.boss and self.level.boss.alive() and self.player and abs(self.level.boss.rect.centerx-self.player.rect.centerx)<650)
        self.audio.update(dt,self.current_level if in_world else None,boss_active,self.state!=ST_PLAYING)
        if self.state == ST_MENU:
            self.title_screen.update(dt)
        elif self.state == ST_LEVEL_TRANS:
            if self.level_transition and self.level_transition.update(dt):
                next_num = self.current_level + 1
                self._total_score = self._carry_score
                self._load_level(next_num)
                self.player.score = self._carry_score
                self.player.health = self._carry_health
        elif self.state == ST_PLAYING:
            remaining = min(dt, .05)
            while remaining > .000001 and self.state == ST_PLAYING:
                step = min(remaining, 1/60)
                self._update_gameplay(step)
                remaining -= step
        elif self.state == ST_GAME_OVER:
            self.game_over_screen.update(dt)
            self.particles.update(dt)
        elif self.state == ST_VICTORY:
            self.victory_screen.update(dt)

    def _update_gameplay(self, dt: float) -> None:
        if not self.player or not self.level or not self.camera:
            return

        # Hitstop freezes game briefly on impact for weight/juice
        if self._hitstop_timer > 0:
            self._hitstop_timer -= dt
            return

        if self._outro_active:
            self.hud.update(dt,self.player)
            self.particles.update(dt)
            before = self._outro_timer
            self._outro_timer -= dt
            if before > .75 >= self._outro_timer: self.audio.play('dance')
            self.player.is_victory_dancing = True
            if self._outro_timer <= 0:
                self._outro_active = False
                self._advance_level()
            return

        # DEFENSIVE: Never let input_locked stay stuck forever.
        # If player is on ground + not dashing + not in knockback, clear it.
        if (self.player.input_locked
                and self.player.is_on_ground
                and not self.player.is_dashing
                and self.player.knockback_timer <= 0):
            self.player.input_locked = False

        effective_dt = dt
        if self.death_anim:
            effective_dt = dt * self.death_anim.get_time_scale()
            if self.death_anim.update(dt):
                self._total_score = self.player.score
                self._respawn_at_checkpoint()
                return

        if self.death_anim:
            self.particles.update(effective_dt)
            return
        self._previous_player_rect = self.player.rect.copy()
        self.player.gravity_multiplier = next((z.get_multiplier() for z in self.level.gravity_zones if z.rect.colliderect(self.player.rect)), 1.0)

        # Platforms use the same swept terrain resolution as the player.
        for mp in self.level.moving_platforms:
            moving_platform_step(self.player, mp, effective_dt, self.level.platforms)

        # Player
        keys = pygame.key.get_pressed()
        self.player.update(effective_dt, keys, self.level.platforms)

        self.player.rect.x = max(0,min(self.level.world_width-self.player.rect.w,self.player.rect.x))
        if self.player.rect.top < -60:
            self.player.rect.top = -60
            self.player.velocity_y = max(0,self.player.velocity_y)

        if self.player.is_gliding and not getattr(self,"_was_gliding",False): self.audio.play("glide")
        self._was_gliding = self.player.is_gliding
        sliding = self.player.friction_mode == 'ice' and self.player.is_on_ground and abs(self.player.velocity_x) > 100
        if sliding and not getattr(self, '_was_ice_sliding', False): self.audio.play('ice_slide')
        self._was_ice_sliding = sliding

        # Detect glide use to dismiss tutorial
        if self.player.is_gliding and not self._glide_used:
            self._glide_used = True
            self._glide_tutorial_timer = 0.0

        # Landing dust
        if self.player.is_on_ground and not self._was_on_ground:
            self.particles.emit_dust(self.player.rect.centerx, self.player.rect.bottom)
            self.audio.play("land")
        self._was_on_ground = self.player.is_on_ground

        # Enemies
        for enemy in list(self.level.enemies):
            old_state = getattr(enemy,'state',None)
            if not ground_ai.update(enemy,effective_dt,self.level.platforms,self.player,self.current_level):
                enemy.update(effective_dt, self.level.platforms, self.player)
            if getattr(enemy,'state',None) in ('telegraph','warning') and old_state != enemy.state and abs(enemy.rect.centerx-self.player.rect.centerx)<500:
                self.audio.play('warning')

        # Boss
        if self.level.boss and self.level.boss.alive():
            old_boss_state = self.level.boss.state
            self.level.boss.update(effective_dt, self.player, self.level.platforms)
            if self.level.boss.state == 'telegraph' and old_boss_state != 'telegraph': self.audio.play('warning')

        # =============================================================
        # BIOME MECHANICS
        # =============================================================

        # --- Geysers (Level 4: Caldera) ---
        for geyser in self.level.geysers:
            geyser.update(effective_dt)
            if geyser.is_active() and pygame.sprite.collide_rect(self.player, geyser):
                self.player.velocity_y = GEYSER_LAUNCH
                self.player.is_on_ground = False
                self.player.jumps_remaining = 0
                self.particles.emit_sparkle(geyser.rect.centerx, geyser.rect.top)
                self.audio.play("geyser")

        # --- Toxic trails (Level 4: SulfurSlime) ---
        for enemy in self.level.enemies:
            if hasattr(enemy, "get_new_trails"):
                for trail in enemy.get_new_trails():
                    self.level.toxic_trails.add(trail)
                    self.level.all_sprites.add(trail)
        self.level.toxic_trails.update(effective_dt)
        for trail in pygame.sprite.spritecollide(
                self.player, self.level.toxic_trails, False):
            if self.player.take_damage(SULFUR_TRAIL_DMG):
                self.shake.trigger(4, 0.1)
                self.audio.play("hit")

        # --- Crumbling platforms (Level 5: Basalt) ---
        for cp in self.level.crumbling:
            if cp.solid and self.player.is_on_ground:
                feet = self.player.get_stomp_rect()
                test = pygame.Rect(cp.rect.x - 2, cp.rect.y - 4, cp.rect.w + 4, 8)
                if feet.colliderect(test):
                    cp.touch()
            was_solid = cp.solid
            cp.update(effective_dt, self.player.rect)
            if was_solid and not cp.solid: self.audio.play("crumble")

        # --- Wind zones (Level 6: Desert) ---
        in_wind = any(self.player.rect.colliderect(z.rect) for z in list(self.level.wind_zones)+list(self.level.updrafts))
        if in_wind and not getattr(self, '_was_in_wind', False): self.audio.play('wind')
        self._was_in_wind = in_wind
        for wz in self.level.wind_zones:
            if pygame.sprite.collide_rect(self.player, wz):
                move_axis(self.player, wz.get_push() * effective_dt, self.level.platforms, "x")
                self.player.rect.x = max(
                    0, min(self.player.rect.x,
                           self.level.world_width - self.player.rect.width))

        # --- Thermal updrafts (Level 6: Desert) ---
        for tu in self.level.updrafts:
            if pygame.sprite.collide_rect(self.player, tu):
                self.player.velocity_y = max(
                    self.player.velocity_y + (THERMAL_FORCE - 1800*self.player.gravity_multiplier) * effective_dt,
                    THERMAL_FORCE)

        # --- Projectiles (Level 6: CactusScorpion) ---
        for enemy in self.level.enemies:
            if hasattr(enemy, "get_new_projectiles"):
                for proj in enemy.get_new_projectiles():
                    self.level.projectiles.add(proj)
                    self.level.all_sprites.add(proj)
                    if abs(enemy.rect.centerx-self.player.rect.centerx)<600: self.audio.play('throw')
        for projectile in self.level.projectiles:
            projectile.previous_rect = projectile.rect.copy()
        self.level.projectiles.update(effective_dt)
        for projectile in list(self.level.projectiles):
            if any(projectile_hits(projectile,p.rect) for p in self.level.platforms):
                projectile.kill()
        # Enemy projectiles damage player. Friendly projectiles (shurikens,
        # ice shards) are thrown by player and must not hurt self.
        for proj in list(self.level.projectiles):
            if isinstance(proj, (BambooShuriken, IceProjectile)):
                continue
            if projectile_hits(proj,self.player.rect):
                if self.player.take_damage(PLAYER_DAMAGE, source_x=proj.rect.centerx):
                    self.shake.trigger()
                    self.audio.play("hit")
                proj.kill()

        # --- Crystal interaction (Level 7: Cave) ---
        for crystal in self.level.crystals:
            crystal.update(effective_dt)
            if (not crystal.is_lit()
                    and (pygame.sprite.collide_rect(self.player, crystal) or (self.player.is_attacking and self.player.get_attack_rect().colliderect(crystal.rect)))):
                crystal.strike()
                self.particles.emit_sparkle(crystal.rect.centerx, crystal.rect.centery)
                self.audio.play("crystal")

        # --- Mushroom springs (Level 14) ---
        for mush in self.level.mushrooms:
            mush.update(effective_dt)
            # Player must be descending and feet contact the cap
            if (self.player.velocity_y > 0
                    and mush.compress_timer <= 0
                    and pygame.sprite.collide_rect(self.player, mush)
                    and top_contact(self._previous_player_rect,self.player.rect,mush.rect,self.player.velocity_y>0)):
                self.player.velocity_y = MUSHROOM_BOUNCE
                self.player.is_on_ground = False
                # Reset jumps so double-jump is available mid-bounce
                self.player.jumps_remaining = 2 if self.player.has_double_jump else 1
                mush.compress()
                self.particles.emit_sparkle(
                    mush.rect.centerx, mush.rect.top, 10)
                self.audio.play("jump")

        # --- Poison spores from SporePuffers (Level 14) ---
        for enemy in self.level.enemies:
            if hasattr(enemy, "get_new_spores"):
                for spore in enemy.get_new_spores():
                    self.level.poison_spores.add(spore)
                    self.level.all_sprites.add(spore)
        self.level.poison_spores.update(effective_dt)
        for spore in pygame.sprite.spritecollide(
                self.player, self.level.poison_spores, False):
            if self.player.take_damage(spore.damage):
                self.shake.trigger(4, 0.1)
                self.audio.play("hit")
                spore.kill()

        # --- Rising lava (Level 15) ---
        if self.level.rising_lava is not None:
            if not self._outro_active: self.level.rising_lava.update(effective_dt)
            # Instant death if player's feet dip into lava
            if (self.player.rect.bottom > self.level.rising_lava.rect.top + 4
                    and not self._outro_active):
                self.player.health = 0
                self.player.dead = True
                self.audio.play("death")
                self.shake.trigger(12, 0.4)

        # --- Magma leaper projectiles handled in standard enemy update ---

        # --- Timed gates (Level 16) ---
        if len(self.level.timed_gates) > 0:
            from biomes import TimedGate
            TimedGate.tick_global(effective_dt)
            for gate in self.level.timed_gates:
                was_solid = gate.solid
                gate.update(effective_dt, self.player.rect)
                if was_solid != gate.solid and abs(gate.rect.centerx-self.player.rect.centerx)<500: self.audio.play("gate")

        # --- Teleport portals (Level 17) ---
        for portal in self.level.portals:
            portal.update(effective_dt)
        if self._portal_lock is not None and not self.player.rect.colliderect(self._portal_lock.rect):
            self._portal_lock = None
        # Check player overlap with active portals
        for portal in self.level.portals:
            if (portal.active and not self.player.dead
                    and portal is not self._portal_lock
                    and portal.partner is not None
                    and pygame.sprite.collide_rect(self.player, portal)):
                # Teleport player to partner's position
                target = portal.partner
                destination = self.player.rect.copy()
                destination.midbottom = target.rect.midbottom
                if any(destination.colliderect(p.rect) for p in self.level.platforms):
                    continue
                self.player.reset_state()
                self.player.rect = destination
                self._portal_lock = target
                self.player.jumps_remaining = 2 if self.player.has_double_jump else 1
                self.player.velocity_x = 0.0
                self.player.velocity_y = 0.0
                portal.teleport()
                target.teleport()
                self.player.invincible_timer = max(
                    self.player.invincible_timer, 0.3)
                self.particles.emit_sparkle(
                    portal.rect.centerx, portal.rect.centery, 12)
                self.particles.emit_sparkle(
                    target.rect.centerx, target.rect.centery, 12)
                self.audio.play("portal")
                break  # one teleport per frame
        for enemy in self.level.enemies:
            if type(enemy).__name__ == "PhaseWraith" and enemy.teleport_cooldown <= 0:
                for portal in self.level.portals:
                    if portal.active and portal.partner and enemy.rect.colliderect(portal.rect):
                        enemy.teleport_to(*portal.partner.rect.midbottom)
                        break

        # --- Gravity zones (Level 18) ---
        # Determine which zone the player is in (if any)
        active_multiplier = 1.0
        for gz in self.level.gravity_zones:
            if pygame.sprite.collide_rect(self.player, gz):
                active_multiplier = gz.get_multiplier()
                break
        self.player.gravity_multiplier = active_multiplier

        # --- Gravity drones: pull player toward them ---
        for enemy in self.level.enemies:
            if enemy.__class__.__name__ == "GravityDrone" and enemy.alive():
                dx = enemy.rect.centerx - self.player.rect.centerx
                dy = enemy.rect.centery - self.player.rect.centery
                dist = math.hypot(dx, dy)
                if 10 < dist < DRONE_RANGE:
                    pull_x = (dx / dist) * DRONE_PULL * effective_dt
                    pull_y = (dy / dist) * DRONE_PULL * effective_dt
                    move_axis(self.player, pull_x * .45, self.level.platforms, "x")
                    self.player.velocity_y += pull_y

        # --- ForgeHammer lethality check ---
        for enemy in self.level.enemies:
            if (enemy.__class__.__name__ == "ForgeHammer"
                    and getattr(enemy, "is_lethal", lambda: False)()):
                if pygame.sprite.collide_rect(self.player, enemy):
                    if self.player.take_damage(PLAYER_DAMAGE * 2):
                        self.shake.trigger(12, 0.3)
                        self.audio.play("hit")

        # --- VoidEater contact damage while open ---
        for enemy in self.level.enemies:
            if (enemy.__class__.__name__ == "VoidEater"
                    and getattr(enemy, "is_dangerous", lambda: False)()):
                if pygame.sprite.collide_rect(self.player, enemy):
                    if self.player.take_damage(PLAYER_DAMAGE):
                        self.shake.trigger(8, 0.2)
                        self.audio.play("hit")

        # --- Dark walls: update their solid/faded state based on nearby crystals ---
        for dw in self.level.dark_walls:
            dw.update(effective_dt, self.player.rect)

        # --- NPCs ---
        for npc in self.level.npcs:
            npc.update(effective_dt, self.player)

        # =============================================================
        # STANDARD COLLISIONS
        # =============================================================

        # Fatal world damage ends interactions before pickups or attacks.
        if self.player.dead:
            if self.death_anim is None:
                self.death_anim = DeathAnimation()
                self.audio.play('death')
            return

        # Checkpoints
        for cp in self.level.checkpoints:
            if not cp.activated and pygame.sprite.collide_rect(self.player, cp):
                if cp.activate():
                    self.respawn_x = cp.spawn_x
                    self.respawn_y = cp.spawn_y
                    self._total_score = self.player.score
                    self.hud.add_floating_text(
                        "CHECKPOINT!", cp.rect.centerx, cp.rect.top - 10,
                        (100, 255, 100))
                    self.particles.emit_sparkle(cp.rect.centerx, cp.rect.centery)
                    self.audio.play("checkpoint")

        # Bamboo
        for bamboo in pygame.sprite.spritecollide(
                self.player, self.level.bamboos, True):
            self._spent.add(bamboo.spawn_id)
            points = self.player.collect_bamboo()
            self.hud.on_bamboo_collected()
            suffix = f" x{self.player.combo_count}!" if self.player.combo_count > 1 else ""
            self.hud.add_floating_text(
                f"+{points}{suffix}", bamboo.rect.centerx, bamboo.rect.top, COL_GOLD)
            self.particles.emit_sparkle(bamboo.rect.centerx, bamboo.rect.centery)
            self.audio.play("collect")

        # Bamboo staff weapon pickup (limited duration)
        for weapon in pygame.sprite.spritecollide(
                self.player, self.level.weapons, True):
            self.player.has_bamboo_weapon = True
            self.player.weapon_time_remaining = min(60, self.player.weapon_time_remaining + 30.0)
            self._weapon_tutorial_timer = 999.0
            self._weapon_used = False
            self.hud.add_floating_text(
                "BAMBOO STAFF +30s",
                weapon.rect.centerx, weapon.rect.top - 10, (255, 220, 120))
            self.particles.emit_sparkle(weapon.rect.centerx, weapon.rect.centery, 14)
            self.audio.play("power")

        # Glide feather pickup (10-second timed buff)
        from config import GLIDE_DURATION_SEC, DASH_DURATION_SEC
        for feather in pygame.sprite.spritecollide(
                self.player, self.level.glide_pickups, True):
            self.player.glide_time_remaining = min(30, self.player.glide_time_remaining + GLIDE_DURATION_SEC)
            self._glide_tutorial_timer = 999.0
            self._glide_used = False
            self.hud.add_floating_text(
                f"GLIDE! {int(GLIDE_DURATION_SEC)}s",
                feather.rect.centerx, feather.rect.top - 10, (140, 220, 255))
            self.particles.emit_sparkle(feather.rect.centerx,
                                        feather.rect.centery, 16)
            self.audio.play("power")

        # Dash boots pickup (30-second timed buff)
        for boots in pygame.sprite.spritecollide(
                self.player, self.level.dash_pickups, True):
            self.player.dash_time_remaining = min(60, self.player.dash_time_remaining + DASH_DURATION_SEC)
            self.hud.add_floating_text(
                f"DASH! {int(DASH_DURATION_SEC)}s",
                boots.rect.centerx, boots.rect.top - 10, (255, 180, 100))
            self.particles.emit_sparkle(boots.rect.centerx,
                                        boots.rect.centery, 16)
            self.audio.play("power")

        # Update weapon sprite animations
        self.level.weapons.update(effective_dt)
        self.level.glide_pickups.update(effective_dt)
        self.level.dash_pickups.update(effective_dt)

        # Heals
        for heal in pygame.sprite.spritecollide(
                self.player, self.level.heals, True):
            restored = min(HEAL_AMOUNT, PLAYER_MAX_HP-self.player.health)
            self.player.heal(HEAL_AMOUNT)
            self.hud.add_floating_text(
                f"+{restored} HP", heal.rect.centerx, heal.rect.top,
                (100, 255, 100))
            self.particles.emit_sparkle(heal.rect.centerx, heal.rect.centery)
            self.audio.play("heal")

        # Spawn pending thrown shurikens
        if self.player.pending_throws:
            for (sx, sy, sdir) in self.player.pending_throws:
                shur = BambooShuriken(sx, sy, sdir)
                self.level.projectiles.add(shur)
                self.level.all_sprites.add(shur)
            self.player.pending_throws.clear()

        # Shuriken hits ALL enemies (including flying, false-glowworm)
        for shur in list(self.level.projectiles):
            if not isinstance(shur, BambooShuriken):
                continue
            for enemy in list(self.level.enemies):
                if (getattr(enemy, "alive_flag", True)
                        and projectile_hits(shur,enemy.rect)):
                    # Only skip true invincibles
                    if type(enemy).__name__ in ("BrineShard", "DustDevil", "ForgeHammer"):
                        continue
                    self._spent.add(getattr(enemy,"spawn_id",("runtime",id(enemy))))
                    enemy.die()
                    self.player.score += STOMP_SCORE
                    self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery)
                    self.audio.play("stomp")
                    shur.kill()
                    break

        # Spawn pending ice casts
        if self.player.pending_ice_casts:
            for (ix, iy, idir) in self.player.pending_ice_casts:
                ice = IceProjectile(ix, iy, idir)
                self.level.projectiles.add(ice)
                self.level.all_sprites.add(ice)
            self.player.pending_ice_casts.clear()

        # Ice projectile pierces all non-boss enemies (frozen shatter)
        for ice in list(self.level.projectiles):
            if not isinstance(ice, IceProjectile):
                continue
            for enemy in list(self.level.enemies):
                if (getattr(enemy, "alive_flag", True)
                        and projectile_hits(ice,enemy.rect)):
                    # Ice CAN kill invincibles -- it freezes them
                    self._spent.add(getattr(enemy,"spawn_id",("runtime",id(enemy))))
                    enemy.die()
                    # Some hazard die() implementations intentionally ignore
                    # ordinary weapons. Ice must remove them before scoring,
                    # otherwise a piercing shard awards points every frame.
                    enemy.kill()
                    if hasattr(enemy, 'alive_flag'):
                        enemy.alive_flag = False
                    self.player.score += STOMP_SCORE
                    # Big ice-shatter burst
                    for _ in range(8):
                        self.particles.emit_sparkle(
                            enemy.rect.centerx, enemy.rect.centery, 1)
                    self.particles.emit_death(
                        enemy.rect.centerx, enemy.rect.centery, 10)
                    self.audio.play("crystal")
                    # Don't kill the ice shard -- it pierces
            # Boss: deal 1 hit if stunned
            if (self.level.boss and self.level.boss.alive()
                    and self.level.boss.stunned
                    and ice.rect.colliderect(self.level.boss.rect)):
                killed = self.level.boss.take_hit()
                self.audio.play("boss_hit")
                self.shake.trigger(6, 0.15)
                if killed:
                    self._spent.add(("boss",0))
                    self.particles.emit_death(
                        self.level.boss.rect.centerx,
                        self.level.boss.rect.centery, 30)
                    self.player.score += BOSS_KILL_SCORE

        # Bamboo staff attack hits ALL enemies (even bats/flying that can't be stomped)
        # The staff is a weapon -- it damages what a foot cannot.
        if self.player.is_attacking:
            atk_rect = self.player.get_attack_rect()
            if atk_rect.width > 0:
                for enemy in list(self.level.enemies):
                    if (getattr(enemy, "alive_flag", True)
                            and atk_rect.colliderect(enemy.rect)):
                        # Some static hazards (BrineShard) are genuinely
                        # invincible -- skip those. Others (bats, glowworms)
                        # CAN be hit with the staff.
                        if type(enemy).__name__ in ("BrineShard", "DustDevil", "ForgeHammer"):
                            continue
                        self._spent.add(getattr(enemy,"spawn_id",("runtime",id(enemy))))
                        enemy.die()
                        self.player.score += STOMP_SCORE
                        self.hud.add_floating_text(
                            f"+{STOMP_SCORE}", enemy.rect.centerx,
                            enemy.rect.top, COL_GOLD)
                        self.particles.emit_death(
                            enemy.rect.centerx, enemy.rect.centery)
                        self.audio.play("stomp")
                        # Hitstop: freeze 60ms for impact punch
                        self._hitstop_timer = max(self._hitstop_timer, 0.06)
                        self.shake.trigger(5, 0.08)
                # Boss gets hit too (if stunned)
                if (self.level.boss and self.level.boss.alive()
                        and self.level.boss.stunned
                        and atk_rect.colliderect(self.level.boss.rect)):
                    killed = self.level.boss.take_hit()
                    self.audio.play("boss_hit")
                    self.shake.trigger(8, 0.2)
                    if killed:
                        self._spent.add(("boss",0))
                        self.particles.emit_death(
                            self.level.boss.rect.centerx,
                            self.level.boss.rect.centery, 30)
                        self.player.score += BOSS_KILL_SCORE
                        self._maybe_unlock_ice_magic()

        # Enemy collisions (stomp or damage)
        for enemy in pygame.sprite.spritecollide(
                self.player, self.level.enemies, False):
            if self.player.dead: break
            if not getattr(enemy, "alive_flag", True):
                continue
            kind = type(enemy).__name__
            if kind == "ForgeHammer" or (kind == "VoidEater" and not enemy.is_dangerous()) or (kind == "FalseGlowworm" and enemy.state != "snapping"):
                continue
            stomp_rect = self.player.get_stomp_rect()
            is_stompable = getattr(enemy, "is_stompable", True)
            if is_stompable and top_contact(self._previous_player_rect,self.player.rect,enemy.rect,self.player.velocity_y>0):
                self._spent.add(getattr(enemy,"spawn_id",("runtime",id(enemy))))
                enemy.die()
                self.player.velocity_y = ENEMY_STOMP_BOUNCE
                self.player.score += STOMP_SCORE
                self.hud.add_floating_text(
                    f"+{STOMP_SCORE}", enemy.rect.centerx, enemy.rect.top, COL_GOLD)
                self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery)
                self.audio.play("stomp")
            else:
                if self.player.take_damage(PLAYER_DAMAGE, source_x=enemy.rect.centerx):
                    self.shake.trigger()
                    self.particles.emit_damage(
                        self.player.rect.centerx, self.player.rect.centery)
                    self.audio.play("hit")

        # Boss collision:
        #   - Landing on head (stomp) always bounces player off, never hurts.
        #     Damage to boss ONLY applied during stunned state.
        #   - Side/below collision damages player (as before).
        if self.level.boss and self.level.boss.alive() and not self.player.dead:
            if pygame.sprite.collide_rect(self.player, self.level.boss):
                stomp_rect = self.player.get_stomp_rect()
                is_head_stomp = top_contact(self._previous_player_rect,self.player.rect,self.level.boss.rect,self.player.velocity_y>0)
                if is_head_stomp:
                    if self.level.boss.stunned:
                        # Damage boss during vulnerable window
                        self.player.velocity_y = ENEMY_STOMP_BOUNCE
                        self.player.rect.bottom = self.level.boss.rect.top
                        killed = self.level.boss.take_hit()
                        self.audio.play("boss_hit")
                        self.shake.trigger(12, 0.3)
                        if killed:
                            self._spent.add(("boss",0))
                            self.particles.emit_death(
                                self.level.boss.rect.centerx,
                                self.level.boss.rect.centery, 30)
                            self.player.score += BOSS_KILL_SCORE
                            self.hud.add_floating_text(
                                f"+{BOSS_KILL_SCORE}",
                                self.level.boss.rect.centerx,
                                self.level.boss.rect.top, COL_GOLD)
                            self._maybe_unlock_ice_magic()
                    else:
                        # NON-STUNNED head-camp: boss shakes player off with
                        # a strong sideways knockback + damage. No free ride.
                        kb_dir = 1.0 if self.player.rect.centerx >= \
                            self.level.boss.rect.centerx else -1.0
                        self.player.velocity_x = 500.0 * kb_dir
                        self.player.velocity_y = -450.0
                        self.player.rect.bottom = self.level.boss.rect.top
                        if self.player.take_damage(
                                PLAYER_DAMAGE,
                                source_x=self.level.boss.rect.centerx):
                            self.shake.trigger(10, 0.2)
                            self.particles.emit_damage(
                                self.player.rect.centerx,
                                self.player.rect.centery)
                            self.audio.play("hit")
                        self.hud.add_floating_text(
                            "!!", self.level.boss.rect.centerx,
                            self.level.boss.rect.top - 10, (255, 60, 60))
                else:
                    # Side/below hit -- boss damages player
                    if self.player.take_damage(PLAYER_DAMAGE):
                        self.shake.trigger()
                        self.particles.emit_damage(
                            self.player.rect.centerx, self.player.rect.centery)
                        self.audio.play("hit")

        # Goal -- trigger "run off screen" outro instead of instant transition
        if (self.level.goal and not self.player.dead and not self._outro_active
                and pygame.sprite.collide_rect(self.player, self.level.goal)):
            boss_blocking = (self.level.boss is not None
                             and self.level.boss.alive())
            if not boss_blocking:
                self._outro_active = True
                self._outro_timer = 1.8
                self.audio.play("level_clear")
                bonus=500 + int(self.player.health)*2
                self.player.score += bonus
                self.hud.add_floating_text(f'CHAPTER CLEAR +{bonus}',self.player.rect.centerx,self.player.rect.top-32,COL_GOLD)
                # Lock player from damage during outro + clear any bad state
                self.player.invincible_timer = 999.0
                self.player.input_locked = True
                self.player.is_dashing = False
                self.player.is_slamming = False
                self.player.is_gliding = False
                self.player.knockback_timer = 0.0
                self.player.velocity_x = 0.0
                self.player.velocity_y = 0.0
                self.player.dead = False  # can't die during outro
            else:
                # Player reached goal but boss still alive -- give feedback
                if self._boss_warning_timer <= 0:
                    self._boss_warning_timer = 2.0
                    self.hud.add_floating_text(
                        "DEFEAT THE BOSS FIRST!",
                        self.player.rect.centerx,
                        self.player.rect.top - 20,
                        (255, 80, 80))
        if self._boss_warning_timer > 0:
            self._boss_warning_timer -= effective_dt

        # Death
        # Trench death (disabled during outro -- player is invincible there)
        from config import TRENCH_DEATH_Y
        if (self.player.rect.top > TRENCH_DEATH_Y and not self.player.dead
                and not self._outro_active):
            self.player.health = 0
            self.player.dead = True
            self.player.is_falling_trench = True
        if self.player.dead and self.death_anim is None:
            self.death_anim = DeathAnimation()
            self.audio.play("death")

        # Tutorial hint timer decrement (when not persistent)
        if self._weapon_tutorial_timer < 999 and self._weapon_tutorial_timer > 0:
            self._weapon_tutorial_timer -= effective_dt

        # Camera + effects
        self.camera.update(self.player, effective_dt)
        self.shake.update(effective_dt)
        # Ambient atmosphere is owned by the painted background renderer.
        self.particles.update(effective_dt)

        self.level.bamboos.update(effective_dt)
        self.level.heals.update(effective_dt)

        self.hud.lives = self.lives
        self.hud.update(effective_dt, self.player)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        # Browser touch controls appear only during gameplay, keeping menus
        # entirely clickable. No DOM work on unchanged frames.
        if getattr(self, '_browser_state', None) != self.state:
            self._browser_state = self.state
            import sys
            if sys.platform == 'emscripten':
                import platform
                platform.window.document.body.setAttribute('data-game-state', self.state)
        if self.state == ST_MENU:
            self.title_screen.draw(self.screen)
            return
        if self.state == ST_LEVEL_TRANS:
            if self.level_transition:
                self.level_transition.draw(self.screen)
            return
        if self.state == ST_VICTORY:
            score = self.player.score if self.player else 0
            self.victory_screen.draw(self.screen, score, self._is_high_score)
            return
        if not self.player or not self.level or not self.camera:
            return

        shake_off = self.shake.update(0)
        self.background.draw(self.screen, self.camera.offset_x)

        render_cam_x = math.floor(self.camera.offset_x)
        render_cam_y = math.floor(self.camera.offset_y)
        cam_x = render_cam_x + shake_off[0]
        cam_y = render_cam_y + shake_off[1]
        visible = self.camera.get_visible_rect().inflate(100, 100)

        for dec in self.level.decorations:
            if dec.rect.colliderect(visible):
                draw_sprite(self.screen, dec, cam_x, cam_y, LEVEL_WORLDS[self.current_level])

        # Ice projectile trails (drawn BEFORE the shard itself for depth)
        for sprite in self.level.projectiles:
            if isinstance(sprite, IceProjectile) and sprite._trail:
                for idx, (tx, ty) in enumerate(sprite._trail):
                    alpha = int(180 * (idx + 1) / len(sprite._trail))
                    r = 4 + idx
                    glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (160, 220, 255, alpha),
                                      (r, r), r)
                    self.screen.blit(
                        glow,
                        (int(tx) - r + cam_x, int(ty) - r + cam_y),
                        special_flags=pygame.BLEND_RGBA_ADD)

        for sprite in self.level.all_sprites:
            if not sprite.rect.colliderect(visible):
                continue
            # The painted hurt pose replaces the old disappearing/flickering
            # panda effect. Invulnerability remains a gameplay timer only.
            draw_sprite(self.screen, sprite, cam_x, cam_y, LEVEL_WORLDS[self.current_level])

        self.particles.draw(self.screen, self.camera)

        # NPC friendly-indicator: bouncing "?" above head (universal UI affordance)
        t_ms = pygame.time.get_ticks()
        bounce = math.sin(t_ms / 200.0) * 5
        for npc in self.level.npcs:
            if not npc.rect.colliderect(visible):
                continue
            sx = npc.rect.centerx + cam_x
            sy = npc.rect.top + cam_y - 26 + bounce
            # Yellow bubble background
            bubble = pygame.Surface((20, 24), pygame.SRCALPHA)
            pygame.draw.circle(bubble, (255, 230, 80), (10, 12), 10)
            pygame.draw.circle(bubble, (255, 180, 40), (10, 12), 10, 2)
            self.screen.blit(bubble, (int(sx) - 10, int(sy) - 12))
            # "?" glyph
            from journey_ui import font as journey_font
            font = journey_font(18, True)
            q = font.render("?", True, (70, 45, 0))
            self.screen.blit(q, q.get_rect(center=(int(sx), int(sy))))

        # Sword swing arc (rotational visual + hitbox glow)
        if self.player.is_attacking:
            self._draw_sword_arc(cam_x, cam_y)

        # --- Darkness overlay (Level 7, 9, 13, 17: dark biomes) ---
        # Single-pass: one dark layer with transparent "holes" around the
        # player + each lit crystal. Crystals fade smoothly during their
        # last 1.5s of life so there's no hard on/off pop.
        if self.level.is_dark:
            from config import CRYSTAL_LIGHT_TIME
            dark_overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((4, 10, 15, 175))
            px = self.player.rect.centerx + cam_x
            py = self.player.rect.centery + cam_y
            pygame.draw.circle(
                dark_overlay, (0, 0, 0, 0), (px, py), DARK_RADIUS)
            FADE_SECONDS = 1.5
            for crystal in self.level.crystals:
                if not crystal.is_lit():
                    continue
                if crystal.light_timer < FADE_SECONDS:
                    frac = max(0.0, crystal.light_timer / FADE_SECONDS)
                else:
                    frac = 1.0
                cx = crystal.rect.centerx + cam_x
                cy = crystal.rect.centery + cam_y
                radius = int(CRYSTAL_RADIUS * (0.5 + 0.5 * frac))
                inner_r = int(radius * 0.7)
                pygame.draw.circle(
                    dark_overlay, (0, 0, 0, 0), (cx, cy), inner_r)
                if radius > inner_r:
                    ring = pygame.Surface(
                        (radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(
                        ring, (0, 0, 0, int(115 * frac)),
                        (radius + 2, radius + 2), radius)
                    pygame.draw.circle(
                        ring, (0, 0, 0, 0),
                        (radius + 2, radius + 2), inner_r)
                    dark_overlay.blit(
                        ring, (cx - radius - 2, cy - radius - 2),
                        special_flags=pygame.BLEND_RGBA_SUB)
            self.screen.blit(dark_overlay, (0, 0))

        # --- Boss HP bar (above boss, world-space) ---
        if self.level.boss and self.level.boss.alive():
            boss = self.level.boss
            bar_w = 120
            bar_h = 8
            bx = boss.rect.centerx + cam_x - bar_w // 2
            by = boss.rect.top + cam_y - 16
            # Backing
            pygame.draw.rect(self.screen, (30, 0, 0), (bx - 2, by - 2, bar_w + 4, bar_h + 4))
            pygame.draw.rect(self.screen, (80, 20, 20), (bx, by, bar_w, bar_h))
            # Fill proportional to HP
            fill = int(bar_w * (boss.hp / max(1, boss.max_hp)))
            if fill > 0:
                pygame.draw.rect(self.screen, (220, 40, 40), (bx, by, fill, bar_h))
            pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, bar_w, bar_h), 1)
            # "BOSS" label
            font = pygame.font.SysFont("consolas", 12, bold=True)
            label = font.render(f"BOSS  {boss.hp}/{boss.max_hp}", True, (255, 200, 200))
            self.screen.blit(label, (bx, by - 14))
            # STATE INDICATOR above boss head
            state_label = None
            state_color = (255, 255, 255)
            if boss.state == "chasing":
                state_label = "!"
                state_color = (255, 180, 40)
            elif boss.state == "telegraph":
                state_label = "!!! ATTACK !!!"
                state_color = (255, 60, 60)
            elif boss.state == "stunned":
                state_label = "STUN -- STOMP!"
                state_color = (80, 180, 255)
            if state_label:
                big_font = pygame.font.SysFont("consolas", 16, bold=True)
                surf = big_font.render(state_label, True, state_color)
                t_ms = pygame.time.get_ticks()
                bob = math.sin(t_ms / 150.0) * 3
                pos = surf.get_rect(center=(boss.rect.centerx + cam_x,
                                            by - 30 + bob))
                self.screen.blit(surf, pos)

        # --- Debug mode hitbox overlay ---
        if self._debug_mode:
            self._draw_debug_hitboxes(cam_x, cam_y)

        self.hud.draw(self.screen, self.player, self.current_level + 1, self.camera)

        hints = []
        if self.player.has_bamboo_weapon and not self._weapon_used:
            hints.append('Staff equipped  /  E or click to strike')
        if self.player.has_glide and not self._glide_used:
            hints.append('Leaf equipped  /  Hold jump while falling')
        if self.player.has_ice_magic and not self._ice_used:
            hints.append('Ice unlocked  /  R to cast at full mana')
        if hints:
            panel(self.screen, (294, 102, 386, 44), 225)
            text(self.screen, hints[int(pygame.time.get_ticks()/4500) % len(hints)], (487,124), 21, CREAM, True)

        # --- NPC dialog box at bottom of screen ---
        active_npc = None
        for npc in self.level.npcs:
            if npc.show_dialog:
                active_npc = npc
                break
        if active_npc is not None:
            self._draw_npc_textbox(active_npc)

        if self.state == ST_PAUSED:
            self.pause_overlay.draw(self.screen)
        elif self.state == ST_GAME_OVER:
            self.game_over_screen.draw(self.screen, self.player.score)

    def _draw_sword_arc(self, cam_x: int, cam_y: int) -> None:
        hit = self.player.get_attack_rect().move(cam_x, cam_y)
        staff = relic(2, (max(20, hit.w), 15))
        if not self.player.facing_right:
            staff = pygame.transform.flip(staff, True, False)
        self.screen.blit(staff, staff.get_rect(center=hit.center))

    def _draw_npc_textbox(self, npc) -> None:
        panel(self.screen, (257, 380, 670, 126), 245)
        text(self.screen, npc.name, (278, 394), 23, GOLD)
        wrap(self.screen, ' '.join(npc.dialog_lines), (278, 425), 624, 21, CREAM, 23)

    def _draw_debug_hitboxes(self, cam_x: int, cam_y: int) -> None:
        """Draw bright red rectangles around all hitboxes for collision verification."""
        R = (255, 0, 0)  # hitboxes
        G = (0, 255, 0)  # player
        C = (0, 255, 255)  # goal/checkpoint
        Y = (255, 255, 0)  # pickups
        # Platforms
        for p in self.level.platforms:
            pygame.draw.rect(self.screen, R,
                             p.rect.move(cam_x, cam_y), 2)
        # Enemies
        for e in self.level.enemies:
            pygame.draw.rect(self.screen, R,
                             e.rect.move(cam_x, cam_y), 2)
        # Boss
        if self.level.boss and self.level.boss.alive():
            pygame.draw.rect(self.screen, R,
                             self.level.boss.rect.move(cam_x, cam_y), 2)
        # Player (green)
        pygame.draw.rect(self.screen, G,
                         self.player.rect.move(cam_x, cam_y), 2)
        # Player stomp-rect (feet)
        pygame.draw.rect(self.screen, (255, 128, 0),
                         self.player.get_stomp_rect().move(cam_x, cam_y), 1)
        # Bamboo sword attack hitbox (during active swing)
        if self.player.is_attacking:
            atk = self.player.get_attack_rect()
            if atk.width > 0:
                pygame.draw.rect(self.screen, (255, 0, 180),
                                 atk.move(cam_x, cam_y), 2)
        # Goal
        if self.level.goal:
            pygame.draw.rect(self.screen, C,
                             self.level.goal.rect.move(cam_x, cam_y), 2)
        # Checkpoints
        for cp in self.level.checkpoints:
            pygame.draw.rect(self.screen, C,
                             cp.rect.move(cam_x, cam_y), 2)
        # Bamboos & heals
        for b in self.level.bamboos:
            pygame.draw.rect(self.screen, Y, b.rect.move(cam_x, cam_y), 1)
        for h in self.level.heals:
            pygame.draw.rect(self.screen, Y, h.rect.move(cam_x, cam_y), 1)
        # Biome: geysers, wind zones, crystals, crumbling, updrafts
        for g in self.level.geysers:
            pygame.draw.rect(self.screen, R, g.rect.move(cam_x, cam_y), 2)
        for wz in self.level.wind_zones:
            pygame.draw.rect(self.screen, (255, 0, 255),
                             wz.rect.move(cam_x, cam_y), 2)
        for tu in self.level.updrafts:
            pygame.draw.rect(self.screen, (255, 0, 255),
                             tu.rect.move(cam_x, cam_y), 2)
        for cr in self.level.crystals:
            pygame.draw.rect(self.screen, C, cr.rect.move(cam_x, cam_y), 2)
        for cp in self.level.crumbling:
            pygame.draw.rect(self.screen, (255, 165, 0),
                             cp.rect.move(cam_x, cam_y), 2)
        for np_ in self.level.npcs:
            pygame.draw.rect(self.screen, (100, 255, 255),
                             np_.rect.move(cam_x, cam_y), 2)
        # Debug overlay text
        font = pygame.font.SysFont("consolas", 14, bold=True)
        info = font.render("DEBUG [TAB] | RED=hitbox GREEN=player CYAN=goal YELLOW=pickup",
                           True, (255, 255, 255))
        info_bg = pygame.Surface((info.get_width() + 10, info.get_height() + 4),
                                pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 180))
        self.screen.blit(info_bg, (4, SCREEN_HEIGHT - 22))
        self.screen.blit(info, (8, SCREEN_HEIGHT - 20))


async def main() -> None:
    """Async entry point for Pygbag/WASM."""
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
