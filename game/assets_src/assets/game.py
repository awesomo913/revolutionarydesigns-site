"""Bamboo Forest - Main game entry point and loop."""

from __future__ import annotations

import asyncio
import math
import random
import sys
from pathlib import Path

# Crash / diagnostic logger (required per workspace rules)
sys.path.insert(0, str(Path.home() / ".claude" / "scripts"))
try:
    from crash_logger import install, log_event
    install(project_root=Path(__file__).parent)
except Exception:
    # Safe fallback in restricted envs (web / no scripts)
    def log_event(*a, **k): pass

import pygame

from config import (
    COL_GOLD, CRYSTAL_RADIUS, DARK_RADIUS, DOUBLE_JUMP_LEVEL,
    ENEMY_STOMP_BOUNCE, FPS, FLOOR_Y, GEYSER_LAUNCH, HEAL_AMOUNT,
    LEVEL_COUNT, PLAYER_DAMAGE, PLAYER_MAX_HP, SCREEN_HEIGHT,
    SCREEN_WIDTH, STARTING_LIVES, STOMP_SCORE, ST_GAME_OVER,
    ST_LEVEL_TRANS, ST_MENU, ST_PAUSED, ST_PLAYING, ST_VICTORY, ST_GROVE,
    SULFUR_TRAIL_DMG, THERMAL_FORCE, TITLE, BOSS_KILL_SCORE,
    # Levels 14-18
    MUSHROOM_BOUNCE, DRONE_RANGE, DRONE_PULL,
    GHOST_SAMPLE_INTERVAL, GHOST_ALPHA,
    DEFAULT_ACCESSIBILITY, ACCESSIBILITY_RANGES, GLIDE_DURATION_SEC, DASH_DURATION_SEC,
    TRENCH_DEATH_Y,
    CHRONO_SLOW_FACTOR, CHRONO_SLOW_DASH_SEC, CHRONO_SLOW_STAFF_SEC,
)
from audio import AudioManager
from backgrounds import BiomeBackground
from engine import Camera, ParticleSystem, ScreenShake
from levels import build_level_state, LevelState, build_overgrown_state
from save import (
    save_high_score, save_best_run, get_best_ghost, load_best_time,
    add_essence, load_grafts, load_unlocks, save_unlock, save_unlocks,
    save_settings,
    load_essences, unlock_overgrown, has_overgrown_mastery, mark_overgrown_mastery, is_overgrown_mastered,
    update_perfect_streak, get_perfect_streak,
)
from sprites import BambooShuriken, IceProjectile, Player, generate_panda_frames, GhostPanda
from ui import (
    DeathAnimation, GameOverScreen, GroveUI, HUD, LevelTransition,
    PauseOverlay, TitleScreen, VictoryScreen, AccessibilityOptions, set_text_scale,
    get_font,
)
from biomes import GravityDrone, PhaseWraith, ForgeHammer, VoidEater, TimedGate, BrineShard, DustDevil


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
        self.grove_ui = GroveUI()
        self._grove_return_state: str = ST_MENU
        self._grafts: list[str] = load_grafts()

        # Accessibility settings (merged)
        try:
            from save import load_settings
            self.settings: dict = load_settings()
        except Exception as e:
            log_event("warning", f"settings load failed, using defaults: {type(e).__name__}")
            self.settings = DEFAULT_ACCESSIBILITY.copy()

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
        self._glow_cache: dict[int, pygame.Surface] = {}  # perf: reused small glows for ice trails etc.
        self._dark_overlay: pygame.Surface | None = None  # cached for dark biome levels (perf)

        diff = self.settings.get("difficulty", "normal")
        self.lives: int = 5 if diff == "easy" else STARTING_LIVES
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
        # Glide / Ice loaded from persistent save (survive deaths + level wins)
        unlocks = load_unlocks()
        self._has_glide_permanent: bool = bool(unlocks.get("glide", False))
        self._has_ice_magic_permanent: bool = bool(unlocks.get("ice", False))
        self._ice_tutorial_timer: float = 0.0
        self._ice_used: bool = False
        # Hitstop: brief pause on enemy hit for impact feel
        self._hitstop_timer: float = 0.0
        # Accessibility / Options (basic: particle/ shake / text / reduced)
        self.settings: dict = load_settings()
        self.options_open: bool = False
        self.options_overlay = AccessibilityOptions()
        self.particles.set_intensity(self.settings.get("particle_density", 1.0))
        self.particles.set_reduced_motion(self.settings.get("reduced_motion", False))
        self.shake.set_scale(self.settings.get("shake_intensity", 1.0))
        try:
            set_text_scale(self.settings.get("text_scale", 1.0))
        except Exception as e:
            log_event("warning", f"text scale init failed: {type(e).__name__}")
        try:
            self.audio.set_master_volume(self.settings.get("volume", 0.8))
        except Exception as e:
            log_event("warning", f"volume init failed: {type(e).__name__}")
        self._fullscreen = bool(self.settings.get("fullscreen", False))
        # Level-end outro: Pain-da auto-runs off screen after reaching goal
        self._outro_active: bool = False
        self._outro_timer: float = 0.0
        self._outro_speed: float = 240.0
        self._took_damage_this_run: bool = False  # for perfect no-hit bell on victory
        # Speedrun mode + lightweight ghosts (t, x, y, facing_right)
        self.speedrun_mode: bool = False
        self.run_timer: float = 0.0
        self._last_ghost_sample: float = 0.0
        self.ghost_record: list[list] = []
        self.best_ghost: list[list] | None = None
        self._pending_best_time: float | None = None
        self._pending_best_ghost: list | None = None
        self._victory_ghost: list | None = None
        self.ghost_replay_timer: float = 0.0
        self.ghost: GhostPanda | None = None
        self._replay_cam_x: float = 0.0
        self._replay_cam_y: float = -40.0
        self._panda_frames: dict = generate_panda_frames()
        # Daily seed for challenge variety (plan vision / Feature #3)
        try:
            import datetime
            self.daily_seed = int(datetime.date.today().strftime("%Y%m%d"))
        except Exception as e:
            log_event("warning", f"daily seed failed, using 0: {type(e).__name__}")
            self.daily_seed = 0
        self._today_seed = self.daily_seed  # canonical today's seed; never overwritten by custom (N9)
        self.daily_mode: bool = False
        self.daily_timer: float = 0.0  # full-run time attack for daily
        self.custom_daily_seed: int = 0
        self._custom_seed_input: str = ""  # for shareable/custom seed entry (prototype)
        # Grove meta (initialized earlier)

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
            if event.type == pygame.KEYDOWN:
                # Global toggles (work in any state)
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                    continue
                if event.key == pygame.K_TAB:
                    self._debug_mode = not self._debug_mode
                    continue
                self._on_key_down(event.key)
                # Note: touch overlay (web/) injects synthetic KEYDOWN/UP for arrows/shift/e/space/grove + ArrowDown (joy pull-down for slam).
                # These reach here the same as real kb; get_pressed() + event.key both work for parity.
                # Joystick down-pull added for full action coverage/smooth mobile play.
            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self._jump_pressed = False
                    # NOTE: variable cut (JUMP_CUT) handled in Player.update via !jump_held check (single source of truth)
                    # removed here to avoid 0.55*0.55 on release frame; polled state is consistent
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.options_open:
                    # Accessibility overlay is modal + keyboard-driven; swallow clicks
                    # so they don't hit the hidden menu buttons underneath it. (#1)
                    pass
                elif event.button == 1 and self.state == ST_MENU:
                    # Menu buttons / gallery cards (mouse + touch)
                    self.title_screen.handle_click(event.pos)
                    self._consume_title_action()
                elif event.button == 1 and self.state == ST_PLAYING:
                    if self.player and self.player.attack(audio=self.audio):
                        self.audio.play("attack")
                        self._weapon_used = True
                        self._weapon_tutorial_timer = 0.0

    def _toggle_fullscreen(self) -> None:
        """Browser handles F11 natively; in-game F11 is a no-op."""
        pass

    def _consume_title_action(self) -> None:
        """Act on the title menu's reported intent (mouse/touch/keys)."""
        act = getattr(self.title_screen, "action", None)
        if not act:
            return
        self.title_screen.action = None
        if act == "start":
            self._start_game()
            self.audio.play("menu_select")
        elif act == "accessibility":
            self._open_accessibility()

    def _open_accessibility(self) -> None:
        if self.state in (ST_MENU, ST_PAUSED):
            self.options_open = True
            self.options_overlay.selected = 0
            self.audio.play("menu_select")

    def _close_accessibility(self) -> None:
        self.options_open = False
        save_settings(self.settings)
        if hasattr(self, 'particles'):
            self.particles.set_intensity(self.settings.get('particle_density', 1.0))
            self.particles.set_reduced_motion(self.settings.get('reduced_motion', False))
        if hasattr(self, 'shake'):
            self.shake.set_scale(self.settings.get('shake_intensity', 1.0))
        try:
            set_text_scale(self.settings.get('text_scale', 1.0))
        except Exception as e:
            log_event("warning", f"text scale apply failed: {type(e).__name__}")
        try:
            if hasattr(self, 'audio'):
                self.audio.set_master_volume(self.settings.get('volume', 0.8))
        except Exception as e:
            log_event("failure", f"volume restore failed: {type(e).__name__}")

    def _scaled_damage(self, dmg: int) -> int:
        if self.settings.get("difficulty") == "easy":
            return max(1, dmg // 2)
        return dmg

    def _adjust_option(self, delta: int) -> None:
        if not self.options_open:
            return
        key = self.options_overlay.OPTION_KEYS[self.options_overlay.selected]
        ranges = ACCESSIBILITY_RANGES.get(key, [1.0])
        current = self.settings.get(key, ranges[0])
        try:
            idx = ranges.index(current) if current in ranges else 0
        except Exception:
            idx = 0
        new_idx = max(0, min(len(ranges) - 1, idx + delta))
        self.settings[key] = ranges[new_idx]
        if key == "particle_density":
            self.particles.set_intensity(self.settings[key])
        elif key == "shake_intensity":
            self.shake.set_scale(self.settings[key])
        elif key == "text_scale":
            set_text_scale(self.settings[key])
        elif key == "reduced_motion":
            self.particles.set_reduced_motion(self.settings[key])
        elif key == "volume":
            try:
                self.audio.set_master_volume(self.settings[key])
            except Exception:
                pass
        # game_speed, color_filter, difficulty: applied live in dt/draw/_scaled_damage or on next start; no special here
        # live persist on every adjust (roundtrip safe)
        save_settings(self.settings)

    def _maybe_unlock_ice_magic(self) -> None:
        """Grant ice magic on first boss defeat. Persists across levels."""
        if self._has_ice_magic_permanent:
            return
        self._has_ice_magic_permanent = True
        self.player.has_ice_magic = True
        self.player.mana = self.player.mana_max  # full mana as reward
        self._ice_tutorial_timer = 999.0
        self._ice_used = False
        if not save_unlock("ice"):
            log_event("failure", "ice unlock not persisted")
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
        # Global: allow saving a just-completed speedrun ghost for the level (even mid-trans after non-final level)
        if key in (pygame.K_y, pygame.K_z) and getattr(self, 'speedrun_mode', False):
            g = self._victory_ghost or self._pending_best_ghost
            t = self._pending_best_time
            if g and t is not None:
                splits = getattr(self, 'splits', None)
                saved = save_best_run(self.current_level, t, g, splits)
                if saved:
                    self.audio.play("victory", pitch=0.82)
                    self.audio.play("ghost_whoosh")  # delta whoosh on save_best success
                    self.hud.add_floating_text("BEAT YOUR BEST!", SCREEN_WIDTH // 2, 68, (90, 255, 140))
                    # particle burst celebration on improved save
                    self.particles.emit_graft_leaves(SCREEN_WIDTH // 2, 70, 24)
                    self.particles.emit_ghost_beat_pop(SCREEN_WIDTH // 2 + random.uniform(-15, 15), 52)
                    log_event("state", "ghost_beat_pop")
                    if self.camera and hasattr(self.camera, 'trigger_squash'):
                        self.camera.trigger_squash(0.18, 0.22)  # stronger squash
                    for _ in range(26):
                        self.particles.emit_sparkle(SCREEN_WIDTH // 2 + random.uniform(-40, 40), 55 + random.uniform(-8, 8), 1)
                    if self.player:
                        self.particles.emit_ice_trail(self.player.rect.centerx, self.player.rect.centery - 10, 0)
                    # update live for immediate replay draw in gameplay
                    self.best_ghost = get_best_ghost(self.current_level)
                    self.ghost = GhostPanda(self.best_ghost, is_best=True) if self.best_ghost else None
                    if self.ghost:
                        self.ghost.reset()
                        self.ghost._pidx = 0
                    # Pro: load stored splits or compute
                    try:
                        from save import get_ghost_splits
                        self.ghost_splits = get_ghost_splits(self.current_level)
                    except Exception as e:
                        log_event("warning", f"ghost splits load failed: {type(e).__name__}")
                        self.ghost_splits = self._compute_ghost_splits(self.best_ghost) if self.best_ghost else []
                self._pending_best_time = None
                self._pending_best_ghost = None
                # Pro ghost library: also save personal run
                try:
                    from save import save_ghost_to_library
                    save_ghost_to_library(self.current_level, t, g)
                except Exception as e:
                    log_event("failure", f"ghost library save failed: {type(e).__name__}")
                return
        # Accessibility options overlay must win over the state handlers: it can be
        # opened from the title menu (state stays ST_MENU), so check it FIRST or the
        # menu eats the keys (arrows move the hidden menu; ESC would quit the game). (#1)
        if self.options_open:
            if key in (pygame.K_ESCAPE, pygame.K_o):
                self._close_accessibility()
                return
            keys = self.options_overlay.OPTION_KEYS
            n = len(keys)
            if key == pygame.K_UP:
                self.options_overlay.selected = (self.options_overlay.selected - 1) % n
            elif key == pygame.K_DOWN:
                self.options_overlay.selected = (self.options_overlay.selected + 1) % n
            elif key in (pygame.K_LEFT, pygame.K_RIGHT):
                self._adjust_option(1 if key == pygame.K_RIGHT else -1)
            return
        if self.state == ST_MENU:
            # Menu consumed the key (nav / toggle / gallery / start / options intent)
            if self.title_screen.handle_key(key):
                self._consume_title_action()
                return
            if key == pygame.K_RETURN:
                self._start_game()
                self.audio.play("menu_select")
            elif key == pygame.K_ESCAPE:
                self.running = False
            elif key == pygame.K_o:
                self._open_accessibility()
            elif key == pygame.K_g:
                self._grove_return_state = ST_MENU
                self.grove_ui.refresh()
                self.state = ST_GROVE
                self.audio.play("menu_select")
            elif key == pygame.K_l:
                # Simple ghost load/select from title (full system): ensure speedrun + ghosts auto per-level on start
                if hasattr(self.title_screen, "speedrun_mode"):
                    self.title_screen.speedrun_mode = True
            # Shareable/custom daily seed entry (prototype for richer daily)
            if self.state == ST_MENU and self.daily_mode:
                if pygame.K_0 <= key <= pygame.K_9:
                    self._custom_seed_input = (self._custom_seed_input + chr(key))[-8:]
                elif key == pygame.K_RETURN and self._custom_seed_input:
                    try:
                        self.custom_daily_seed = int(self._custom_seed_input)
                    except Exception as e:
                        log_event("warning", f"bad custom daily seed input: {type(e).__name__}")
                    self._custom_seed_input = ""
                elif key == pygame.K_BACKSPACE:
                    self._custom_seed_input = self._custom_seed_input[:-1]
                elif key == pygame.K_c:  # clear custom
                    self.custom_daily_seed = 0
                    self._custom_seed_input = ""
        elif self.state == ST_PLAYING:
            if key == pygame.K_ESCAPE:
                # ESC in fullscreen drops to windowed first, THEN pauses
                if self._fullscreen:
                    self._toggle_fullscreen()
                self.state = ST_PAUSED
                self.audio.play("menu_select")
            elif key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                if not self._jump_pressed and self.player:
                    if self.player.jump(audio=self.audio):
                        self.audio.play("jump")
                    self._jump_pressed = True
            elif key in (pygame.K_e, pygame.K_x):
                if self.player and self.player.attack(audio=self.audio):
                    self.audio.play("attack")
                    self._weapon_used = True
                    self._weapon_tutorial_timer = 0.0
            elif key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                if self.player and self.player.dash(audio=self.audio):
                    self.audio.play("dash")
                    self._dash_used = True
                    self._dash_tutorial_timer = 0.0
                    self.particles.emit_dust(
                        self.player.rect.centerx, self.player.rect.bottom, 8)
                    self.particles.emit_leaf_burst(self.player.rect.centerx, self.player.rect.bottom - 4, 6)
                    self.particles.emit_sparkle(self.player.rect.centerx + random.uniform(-8,8), self.player.rect.centery, 4)
                    # extra dash trail for start whoosh
                    if self.particles:
                        td = -1.0 if self.player.facing_right else 1.0
                        self.particles.emit_dash_trail(self.player.rect.centerx + td*12, self.player.rect.centery, td)
                    # Leaf burst on dash in forest biomes
                    if self.level and self.level.biome in ("forest", "corrupted"):
                        for _ in range(3):
                            self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
                    # Echo step deeper mastery: spawn echo visual on dash
                    if "echo_step" in getattr(self.player, "grafts", []):
                        self.particles.emit_sparkle(self.player.rect.centerx + 20, self.player.rect.centery, 6)
                        self.particles.emit_leaf_burst(self.player.rect.centerx - 30, self.player.rect.centery, 3)
                    # camera y-nudge + squash on dash launch (hard move feel)
                    if self.camera and hasattr(self.camera, 'trigger_squash'):
                        self.camera.trigger_squash(0.055, 0.09, y_nudge=6)
            elif key == pygame.K_DOWN or key == pygame.K_s:
                if self.player and self.player.slam():
                    self.audio.play("stomp")
            elif key in (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_q):
                if self.player and self.player.throw_bamboo():
                    self.audio.play("stomp")
            elif key == pygame.K_r:
                # Cast ice spell (requires boss-kill unlock + full mana)
                if self.player and self.player.cast_ice_spell():
                    self.audio.play("crystal")
                    self._ice_used = True
                    self._ice_tutorial_timer = 0.0
                    # Cast burst particles at player + ice trail feedback
                    for _ in range(12):
                        self.particles.emit_sparkle(
                            self.player.rect.centerx,
                            self.player.rect.centery, 1)
                    self.particles.emit_ice_trail(self.player.rect.centerx, self.player.rect.centery, -1 if self.player.facing_right else 1)
                    self.shake.trigger(4, 0.1)
        elif self.state == ST_PAUSED:
            if key == pygame.K_ESCAPE:
                self.state = ST_PLAYING
            elif key == pygame.K_q:
                self.state = ST_MENU
                self.title_screen = TitleScreen()
            elif key == pygame.K_g:
                self._grove_return_state = ST_PAUSED
                self.grove_ui.refresh()
                self.state = ST_GROVE
                self.audio.play("menu_select")
            elif key == pygame.K_o:
                self._open_accessibility()
            elif key == pygame.K_l and getattr(self, 'speedrun_mode', False):
                # Pro ghost library: cycle through saved ghosts (best + personal)
                lib = []
                try:
                    from save import get_ghost_library, get_best_ghost
                    lib = get_ghost_library(self.current_level)
                except Exception as e:
                    log_event("warning", f"ghost library load failed: {type(e).__name__}")
                    lib = []
                best = get_best_ghost(self.current_level)
                ghosts = [best] if best else []
                for entry in lib:
                    if entry and len(entry) > 1:
                        ghosts.append(entry[1])
                if not ghosts:
                    self.hud.add_floating_text("NO GHOST YET", SCREEN_WIDTH // 2, 120, (140, 140, 140))
                    return
                self._ghost_lib = ghosts
                if not hasattr(self, '_ghost_lib_idx'):
                    self._ghost_lib_idx = 0
                self._ghost_lib_idx = (self._ghost_lib_idx + 1) % len(ghosts)
                g = ghosts[self._ghost_lib_idx]
                self.best_ghost = g
                is_best_ghost = (self._ghost_lib_idx == 0)
                self._ghost_variant = "best" if is_best_ghost else "personal"
                self.ghost = GhostPanda(g, is_best=is_best_ghost)
                if self.ghost:
                    self.ghost.reset()
                    self.ghost._pidx = 0
                try:
                    from save import get_ghost_splits
                    self.ghost_splits = get_ghost_splits(self.current_level)
                except Exception as e:
                    log_event("warning", f"ghost splits load failed: {type(e).__name__}")
                    self.ghost_splits = self._compute_ghost_splits(g) if g else []
                self.audio.play("crystal", pitch=0.6)
                self.audio.play("ghost")
                if self.particles:
                    self.particles.emit_sparkle(self.player.rect.centerx, self.player.rect.centery, 6)
                t = g[-1][0] if g else 0
                self.hud.add_floating_text(f"GHOST {self._ghost_lib_idx+1}/{len(ghosts)}", SCREEN_WIDTH // 2, 120, (170, 200, 220))
                self.audio.play("menu_select")
        elif self.state == ST_GROVE:
            action = self.grove_ui.handle_key(key)
            if action == "exit":
                self.state = self._grove_return_state
                self._grafts = load_grafts()
            elif action == "crafted":
                self._grafts = load_grafts()
                if len(self._grafts) >= 5:
                    self.audio.play("graft", pitch=1.32)
                elif len(self._grafts) >= 3:
                    self.audio.play("graft", pitch=1.18)
                else:
                    self.audio.play("graft")
                if self.player:
                    self.player.apply_grafts(self._grafts, audio=self.audio)
                    if self.player:
                        self.particles.emit_graft_leaves(self.player.rect.centerx, self.player.rect.centery - 8, 12)
                        # extra craft success juice (sparkles for mastery pop)
                        for _ in range(6):
                            self.particles.emit_sparkle(
                                self.player.rect.centerx + random.uniform(-10, 10),
                                self.player.rect.centery - 4, 1)
                        if len(self._grafts) >= 5:
                            self.particles.emit_mastery_storm(self.player.rect.centerx, self.player.rect.centery - 6, 14)
                            self.particles.emit_golden_shower(self.player.rect.centerx, self.player.rect.centery - 4, 8)
                        self.shake.trigger(3, 0.08)
                        if self.camera and hasattr(self.camera, 'trigger_squash'):
                            self.camera.trigger_squash(0.08, 0.1, y_nudge=5 if len(self._grafts)>=5 else 0)
        elif self.state in (ST_GAME_OVER, ST_VICTORY):
            if key == pygame.K_RETURN:
                self.state = ST_MENU
                self.title_screen = TitleScreen()
            elif key == pygame.K_g and self.state == ST_VICTORY:
                # Enter light Grove overlay from victory (Feature #2)
                self._grove_return_state = ST_VICTORY
                self.grove_ui.refresh()
                self.state = ST_GROVE
                self.audio.play("menu_select")
            elif key == pygame.K_r and getattr(self, 'speedrun_mode', False) and self.state == ST_VICTORY:
                # Replay best ghost on victory for premium speedrun feel
                g = getattr(self, '_victory_ghost', None) or getattr(self, 'best_ghost', None)
                if g:
                    self.ghost_replay_timer = 0.0
                    self.ghost = GhostPanda(g, is_best=True)
                    self._replay_cam_x = 0.0
                    self._replay_cam_y = -40.0
                    if self.ghost:
                        self.ghost._pidx = 0
                    self.audio.play("ice", pitch=0.5)
                    self.audio.play("ghost")
                    self.audio.play("menu_select")
            elif key in (pygame.K_o, pygame.K_O) and self.state == ST_VICTORY:
                try:
                    from save import is_overgrown_unlocked
                    if is_overgrown_unlocked():
                        # Direct entry to overgrown from victory screen
                        self.title_screen = TitleScreen()
                        self.title_screen.overgrown_mode = True
                        self._start_game()
                        self.audio.play("menu_select")
                except Exception as e:
                    log_event("warning", f"overgrown entry failed: {type(e).__name__}")

    # ------------------------------------------------------------------
    # Level management
    # ------------------------------------------------------------------

    def _start_game(self) -> None:
        self.lives = STARTING_LIVES
        self.current_level = 0
        self._total_score = 0
        self.respawn_x = 100
        self.respawn_y = FLOOR_Y
        # Pull speedrun mode choice from title (menu option / flag)
        self.speedrun_mode = bool(getattr(self.title_screen, "speedrun_mode", False))
        # Daily mode from title 'Daily' button (Feature #3)
        self.daily_mode = bool(getattr(self.title_screen, "daily_mode", False))
        # Overgrown post-game challenge from title if unlocked (plan vision)
        self.overgrown_mode = bool(getattr(self.title_screen, "overgrown_mode", False))
        # Seed RNG ONLY for daily (YYYYMMDD) -- normal play stays unseeded for variety.
        # Restore the canonical today's seed first so a prior custom-seed run can't
        # permanently overwrite it for the rest of the session (N9).
        if getattr(self, '_today_seed', 0):
            self.daily_seed = self._today_seed
        if self.daily_mode and getattr(self, 'daily_seed', 0):
            use_seed = self.custom_daily_seed or self.daily_seed
            old_state = random.getstate()
            random.seed(use_seed)
            if self.custom_daily_seed:
                self.daily_seed = self.custom_daily_seed
                self.custom_daily_seed = 0  # one-shot: next daily auto-returns to today's seed (N9)
            self._daily_rng_state = old_state  # stash; restore after build (see below)
        if self.daily_mode:
            self.daily_timer = 0.0
            self.audio.play("crystal", pitch=0.85)
        self._took_damage_this_run = False
        self._load_level(0)
        if hasattr(self, '_daily_rng_state'):
            try:
                random.setstate(self._daily_rng_state)
            except Exception:
                pass

    def _compute_ghost_splits(self, ghost_replay):
        """Pro-level: compute split times for a ghost by scanning when it passed each checkpoint x."""
        if not ghost_replay or not self.level or not getattr(self.level, 'checkpoints', None):
            return []
        splits = []
        cps = sorted(self.level.checkpoints, key=lambda c: c.spawn_x)
        for i, cp in enumerate(cps):
            target_x = cp.spawn_x
            for s in ghost_replay:
                if s[1] >= target_x:
                    splits.append((i, s[0]))
                    break
        return splits

    def _load_level(self, level_num: int) -> None:
        if getattr(self, 'overgrown_mode', False):
            bloom = False
            try:
                from save import has_overgrown_mastery
                bloom = has_overgrown_mastery()
            except Exception:
                log_event("warning", "has_overgrown_mastery failed, defaulting to visible bloom")
                bloom = True  # default visible bloom
            self.level = build_overgrown_state(bloom=bloom)
            eff_level_num = 99
            self._heart_collected = False
            # Prototype ambitious Bloom feature: extra lush "bloom" feel on load (living overgrown)
            if self.particles:
                vis = self.camera.get_visible_rect() if self.camera else pygame.Rect(0,0,960,540)
                self.particles.emit_dense_foliage(vis, 30)
                for _ in range(12):
                    self.particles.emit_overgrowth_aura(400 + _ * 30, 280, 2)
        else:
            self.level = build_level_state(level_num, daily_seed=(self.daily_seed if self.daily_mode else 0))
            eff_level_num = level_num
            # Apply richer daily modifiers (low grav, fast enemies, bonus bamboo)
            if getattr(self.level, 'low_gravity', False) and self.player:
                self.player.gravity_multiplier = 0.55
            if getattr(self.level, 'fast_enemies', False):
                for e in getattr(self.level, 'enemies', []):
                    if hasattr(e, 'speed'):
                        e.speed = getattr(e, 'speed', 1.0) * 1.35
            if getattr(self.level, 'bonus_bamboo', False):
                self._daily_bonus_bamboo = True
        self.camera = Camera(self.level.world_width, SCREEN_HEIGHT)
        self.background = BiomeBackground(self.level.biome)
        if getattr(self, 'speedrun_mode', False):
            self.camera.set_speedrun_lead(1.75)
        else:
            self.camera.set_speedrun_lead(1.0)
        # Perf: pre-allocate reusable dark overlay for dark biomes instead of new full-screen Surface every frame
        if getattr(self.level, "is_dark", False):
            self._dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        else:
            self._dark_overlay = None
        self.respawn_x = self.level.player_start[0]
        self.respawn_y = self.level.player_start[1]
        self.player = Player(self.respawn_x, self.respawn_y)
        if eff_level_num >= DOUBLE_JUMP_LEVEL:
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
        self.player.apply_grafts(self._grafts, audio=self.audio)
        if self.particles:
            self.particles.emit_graft_leaves(self.player.rect.centerx, self.player.rect.centery - 10, 8)
        if len(self._grafts) >= 5:
            self.audio.play("graft", pitch=1.32)
            self.audio.play("mastery_chime", pitch=1.28)  # mastery storm chimes on 5 graft
            # mastery 5-graft juice pop + high-impact storm
            self.particles.emit_graft_leaves(self.player.rect.centerx, self.player.rect.centery - 10, 18)
            self.particles.emit_golden_shower(self.player.rect.centerx, self.player.rect.centery - 12, 12)
            self.particles.emit_mastery_storm(self.player.rect.centerx, self.player.rect.centery - 8, 16)
            log_event("state", "mastery_5_golden_shower", {"x": self.player.rect.centerx})
            if self.camera and hasattr(self.camera, 'trigger_squash'):
                self.camera.trigger_squash(0.12, 0.18, y_nudge=8)
        elif len(self._grafts) >= 3:
            self.audio.play("graft", pitch=1.18)
        else:
            self.audio.play("graft")
        self.player.score = self._total_score
        self.level.all_sprites.add(self.player)
        self.current_level = eff_level_num
        self.particles = ParticleSystem()
        if getattr(self, 'daily_mode', False):
            self._daily_score_mult = 1.2  # daily bonus (plan)
        else:
            self._daily_score_mult = 1.0
        if hasattr(self, 'settings'):
            self.particles.set_intensity(self.settings.get("particle_density", 1.0))
            self.particles.set_reduced_motion(self.settings.get("reduced_motion", False))
        self.hud = HUD()
        self.hud.set_bamboo_count(len(self.level.bamboos))
        self.hud.lives = self.lives
        self.death_anim = None
        self._was_on_ground = False
        self._was_dashing = False
        self._jump_pressed = False
        self._outro_active = False
        self._outro_timer = 0.0
        self._took_damage_this_run = False  # reset per level load (full run no-hit tracks cumulative via damage)
        # Speedrun reset + load best ghost for this level (per-biome best via level key)
        if getattr(self, 'speedrun_mode', False):
            self.run_timer = 0.0
            self._last_ghost_sample = 0.0
            self.ghost_record = []
            self._pending_best_time = None
            self._pending_best_ghost = None
            self._victory_ghost = None
            self.ghost_replay_timer = 0.0
            self._replay_cam_x = 0.0
            self._last_ghost_beaten = False
            best_data = get_best_ghost(level_num)
            self.best_ghost = best_data
            self.ghost = GhostPanda(best_data, is_best=True) if best_data else None
            if self.ghost:
                self.ghost.reset()
                self.ghost._pidx = 0
            if self.ghost and self.particles:
                self.particles.emit_sparkle(self.player.rect.centerx, self.player.rect.centery, 4)
            # seed first sample immediately for clean replay start
            if self.player:
                self.ghost_record.append([0.0, self.player.rect.x, self.player.rect.y, self.player.facing_right])
                self._last_ghost_sample = 0.0
        # If player already has weapon from previous level, keep tutorial hidden
        if self.player.has_bamboo_weapon:
            self._weapon_used = True
        self.state = ST_PLAYING

    def _respawn_at_checkpoint(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            if not save_high_score(self._total_score, self.current_level + 1):
                log_event("failure", "high score not persisted on game over")
            if not save_unlocks({"ice": self._has_ice_magic_permanent, "glide": self._has_glide_permanent}):
                log_event("failure", "unlocks not persisted on game over")
            # Extend essence: award for current biome on run end (game over) + daily source
            if self.level:
                b = getattr(self.level, "biome", "forest")
                add_essence(b)
                if getattr(self, "daily_mode", False):
                    add_essence(b)
            self.game_over_screen = GameOverScreen()
            self.state = ST_GAME_OVER
            self.death_anim = None
            return
        activated_xs = set()
        if self.level:
            for cp in self.level.checkpoints:
                if cp.activated:
                    activated_xs.add(cp.spawn_x)
        if getattr(self, 'overgrown_mode', False):
            bloom = False
            try:
                from save import has_overgrown_mastery
                bloom = has_overgrown_mastery()
            except Exception:
                log_event("warning", "has_overgrown_mastery failed, defaulting to visible bloom")
                bloom = True  # default visible bloom
            self.level = build_overgrown_state(bloom=bloom)
            self._heart_collected = False
            # Prototype ambitious Bloom feature: extra lush "bloom" feel on load (living overgrown)
            if self.particles:
                vis = self.camera.get_visible_rect() if self.camera else pygame.Rect(0,0,960,540)
                self.particles.emit_dense_foliage(vis, 30)
                for _ in range(12):
                    self.particles.emit_overgrowth_aura(400 + _ * 30, 280, 2)
        else:
            self.level = build_level_state(self.current_level, daily_seed=(self.daily_seed if self.daily_mode else 0))
        self.camera = Camera(self.level.world_width, SCREEN_HEIGHT)
        self.background = BiomeBackground(self.level.biome)
        if getattr(self, 'speedrun_mode', False):
            self.camera.set_speedrun_lead(1.75)
        else:
            self.camera.set_speedrun_lead(1.0)
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
        # Brief spawn-protection so a nearby chaser/hazard can't instantly re-hit
        # the player on respawn (mirrors the portal/dash i-frame grants). (N1)
        self.player.invincible_timer = max(self.player.invincible_timer, 1.0)
        self.player.apply_grafts(self._grafts, audio=self.audio)
        if self.particles:
            self.particles.emit_graft_leaves(self.player.rect.centerx, self.player.rect.centery - 10, 8)
        if len(self._grafts) >= 5:
            self.audio.play("graft", pitch=1.32)
            self.audio.play("mastery_chime", pitch=1.28)  # mastery storm chimes on 5 graft
            self.particles.emit_graft_leaves(self.player.rect.centerx, self.player.rect.centery - 10, 18)
            self.particles.emit_golden_shower(self.player.rect.centerx, self.player.rect.centery - 12, 12)
            self.particles.emit_mastery_storm(self.player.rect.centerx, self.player.rect.centery - 8, 16)
            log_event("state", "mastery_5_golden_shower", {"x": self.player.rect.centerx})
            if self.camera and hasattr(self.camera, 'trigger_squash'):
                self.camera.trigger_squash(0.12, 0.18, y_nudge=8)
        elif len(self._grafts) >= 3:
            self.audio.play("graft", pitch=1.18)
            self.audio.play("mastery_chime", pitch=1.05)  # chimes on 3+ graft
        else:
            self.audio.play("graft")
        self.player.score = self._total_score
        self.level.all_sprites.add(self.player)
        self.particles = ParticleSystem()
        if hasattr(self, 'settings'):
            self.particles.set_intensity(self.settings.get("particle_density", 1.0))
            self.particles.set_reduced_motion(self.settings.get("reduced_motion", False))
        self.hud = HUD()
        self.hud.set_bamboo_count(len(self.level.bamboos))
        self.hud.lives = self.lives
        self.death_anim = None
        self._was_on_ground = False
        self._was_dashing = False
        self._jump_pressed = False
        if getattr(self, 'speedrun_mode', False):
            self.run_timer = 0.0
            self._last_ghost_sample = 0.0
            self.ghost_record = []
            self._replay_cam_x = 0.0
            self._last_ghost_beaten = False
            if self.ghost:
                self.ghost.reset()
        self.state = ST_PLAYING

    def _advance_level(self) -> None:
        self._total_score = self.player.score
        # Award essence for the biome just cleared (Grove meta)
        if self.level:
            biome = getattr(self.level, "biome", "forest")
            add_essence(biome)
            if getattr(self, "daily_mode", False) or getattr(self.level, 'daily_bonus_essence', False):
                add_essence(biome)
                add_essence(biome)  # stronger daily bonus source: double + extra
            if biome == "overgrown":
                # special post-game essence feel (wild growth) -- richer source
                add_essence("forest")
                add_essence("gravity")
                add_essence("mushroom")
                add_essence("void")
            self.audio.play("essence", pitch=1.2)

        next_lv = self.current_level + 1
        if next_lv >= LEVEL_COUNT:
            self._is_high_score = save_high_score(
                self.player.score, self.current_level + 1)
            if not save_unlocks({"ice": self._has_ice_magic_permanent, "glide": self._has_glide_permanent}):
                log_event("failure", "unlocks not persisted on final victory")
            self.victory_screen = VictoryScreen()
            self.state = ST_VICTORY
            self.audio.play("victory")
            # perfect run bell on no-hit victory (full health or no damage flag this run)
            try:
                is_perfect = (not getattr(self, '_took_damage_this_run', False)) or (getattr(self.player, 'health', 0) >= PLAYER_MAX_HP)
                if is_perfect:
                    self.audio.play("perfect_bell")
            except Exception as e:
                log_event("warning", f"perfect bell play failed: {type(e).__name__}")
            if self.camera:
                self.camera.set_victory_zoom(1.065)  # subtle focus zoom juice on win
            # Mark daily complete if in daily mode (Feature #3)
            if getattr(self, "daily_mode", False) and getattr(self, "daily_seed", 0):
                try:
                    from save import mark_daily_complete, save_daily_best, update_daily_streak
                    if not mark_daily_complete(self.daily_seed):
                        log_event("failure", "daily complete not persisted")
                    update_daily_streak(self.daily_seed)
                    # Perfect daily: full health + (if bonus bamboo or no damage tracked)
                    is_perfect = (getattr(self.player, 'health', 0) >= PLAYER_MAX_HP)
                    if is_perfect:
                        # bonus essence for perfect
                        add_essence(getattr(self.level, "biome", "forest"))
                        self.hud.add_floating_text("PERFECT DAILY!", SCREEN_WIDTH // 2, 140, (255, 220, 120))
                        if self.particles:
                            self.particles.emit_golden_shower(SCREEN_WIDTH // 2, 120, 8)
                            if len(getattr(self, '_grafts', [])) >= 5:
                                self.particles.emit_mastery_storm(SCREEN_WIDTH // 2, 100, 6)
                        if self.camera and hasattr(self.camera, 'trigger_squash'):
                            self.camera.trigger_squash(0.06, 0.1)
                    # perfects streaks (rich daily polish)
                    try:
                        update_perfect_streak(self.daily_seed, is_perfect)
                    except Exception as e:
                        log_event("warning", f"perfect streak update failed: {type(e).__name__}")
                    # always update best time for the full daily run
                    if not save_daily_best(self.daily_seed, self.daily_timer or self.run_timer):
                        log_event("warning", "daily best not updated (may not be new record)")
                except Exception as e:
                    log_event("warning", f"daily mark failed: {type(e).__name__}")
            # Overgrown unlock: L18 victory if has mastery (grafts/ess) OR high essence -- set flag + offer in victory
            if getattr(self, "current_level", -1) == 17:
                try:
                    ess = load_essences() or {}
                    total_ess = sum(ess.values()) if ess else 0
                    high_essence = total_ess >= 18
                    if has_overgrown_mastery() or high_essence:
                        unlock_overgrown()
                        self.hud.add_floating_text("OVERGROWN UNLOCKED!", SCREEN_WIDTH // 2, 90, (80, 200, 120))
                except Exception as e:
                    log_event("warning", f"overgrown unlock failed: {type(e).__name__}")
            # Mastery clear feedback for overgrown runs (win condition)
            if getattr(self, "overgrown_mode", False) or biome == "overgrown":
                try:
                    if not mark_overgrown_mastery():
                        log_event("failure", "overgrown mastery not persisted")
                    self.hud.add_floating_text("OVERGROWN MASTERED!", SCREEN_WIDTH // 2, 70, (120, 255, 140))
                except Exception as e:
                    log_event("warning", f"overgrown mastery mark failed: {type(e).__name__}")
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
        if self.state == ST_MENU:
            self.title_screen.update(dt)
        elif self.state == ST_GROVE:
            self.grove_ui.update(dt)
        elif self.state == ST_LEVEL_TRANS:
            if self.level_transition and self.level_transition.update(dt):
                next_num = self.current_level + 1
                self._total_score = self._carry_score
                self._load_level(next_num)
                self.player.score = self._carry_score
                self.player.health = self._carry_health
        elif self.state == ST_PLAYING:
            self._update_gameplay(dt)
        elif self.state == ST_GAME_OVER:
            self.game_over_screen.update(dt)
            self.particles.update(dt)
        elif self.state == ST_VICTORY:
            self.victory_screen.update(dt)
            # Victory particles + text option for overgrown mastery booster (if unlocked)
            try:
                from save import is_overgrown_unlocked
                if is_overgrown_unlocked():
                    if random.random() < 0.8:
                        self.particles.emit_graft_leaves(SCREEN_WIDTH // 2 + random.uniform(-60, 60), 95 + random.uniform(-10, 10), 2)
                    if random.random() < 0.35:
                        self.particles.emit_dense_foliage(self.camera.get_visible_rect() if self.camera else pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)
            except Exception as e:
                log_event("warning", f"overgrown victory particles failed: {type(e).__name__}")
            # Advance ghost replay timer for R-replay in speedrun mode (premium feel)
            if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost', None):
                self.ghost_replay_timer += dt
                self.ghost.update(dt, self.ghost_replay_timer)
                # Better camera follow during replay: use GhostPanda's interpolated rect (smooth, no snap to raw samples)
                # tighter centering + responsive lerp for pro replay feel (follows the ghost path naturally)
                if self.ghost and hasattr(self.ghost, 'rect'):
                    gx = self.ghost.rect.centerx
                    gy = self.ghost.rect.centery
                    target = gx - SCREEN_WIDTH * 0.42  # slightly ahead centering for path visibility
                    prev = getattr(self, '_replay_cam_x', target)
                    self._replay_cam_x = prev * 0.58 + target * 0.42  # snappier yet smooth
                    # improved y: track ghost vertical pos for levels with height variation
                    y_target = gy - SCREEN_HEIGHT * 0.52
                    if hasattr(self, '_replay_cam_y'):
                        self._replay_cam_y = getattr(self, '_replay_cam_y', y_target) * 0.6 + y_target * 0.4
                    else:
                        self._replay_cam_y = y_target

    def _update_gameplay(self, dt: float) -> None:
        # HOTPATH: core per-frame gameplay (player physics, collisions, biomes, particles).
        # Keep allocations low; most work is in Player.update + Level groups.
        if not self.player or not self.level or not self.camera:
            return

        # Game speed multiplier (accessibility) -- scale simulation dt
        speed_mult = self.settings.get("game_speed", 1.0)
        dt = dt * speed_mult

        # Hitstop freezes game briefly on impact for weight/juice
        if self._hitstop_timer > 0:
            self._hitstop_timer -= dt
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

        # Chrono graft: delightful time-slow. Player keeps full speed (power fantasy),
        # world (enemies/hazards/proj/plats) runs slow while chrono_slow_timer > 0.
        # Countdown uses full player dt in sprites so duration is wall time.
        chrono_active = bool(getattr(self.player, "chrono_slow_timer", 0) > 0)
        player_dt = effective_dt
        world_dt = effective_dt * CHRONO_SLOW_FACTOR if chrono_active else effective_dt

        # Moving platforms -- player inherits platform velocity when standing on it.
        # Detect riding BEFORE the platform moves, then SNAP player after.
        # Wider tolerance for vertical platforms where gravity can push
        # the player below the surface between frames.
        self._moving_plat_riding = []
        for mp in self.level.moving_platforms:
            old_mx, old_my = mp.rect.x, mp.rect.y
            feet_y = self.player.rect.bottom
            plat_top = old_my
            # Wider horizontal overlap: 8px tolerance prevents edge slip-off
            horiz_overlap = (self.player.rect.right > old_mx - 8
                             and self.player.rect.left < old_mx + mp.rect.w + 8)
            # Much wider vertical tolerance: 20px catches gravity drift AND
            # vertical platform speed that moves >10px in one frame
            was_riding = (horiz_overlap and -20 <= (feet_y - plat_top) <= 12)
            mp.update_moving(world_dt)
            # CRITICAL: only snap to platform if player is NOT jumping up.
            # Active upward velocity (velocity_y < 0) means the player just
            # pressed jump -- we must not drag them back down.
            dx = mp.rect.x - old_mx
            dy = mp.rect.y - old_my
            if was_riding:
                # For vertical platforms moving UP, snap player UP even if
                # velocity_y is negative (player just jumped) -- the platform
                # carries them upward. Only skip if player jumped strongly
                # enough to leave the platform (velocity_y < platform_move_y).
                # Let a real jump escape an ascending vertical platform instead of
                # eating it: snap only when the player is NOT rising faster than the
                # platform. platform_vy = dy/world_dt (px/s, negative = up). (#3)
                platform_vy = (dy / world_dt) if world_dt > 0 else 0.0
                escaping_up = self.player.velocity_y < 0 and self.player.velocity_y <= platform_vy
                if (self.player.velocity_y >= 0 or dy < 0) and not escaping_up:
                    self.player.rect.x += dx
                    self.player.rect.bottom = mp.rect.top
                    self.player.velocity_y = 0
                    self.player.is_on_ground = True
                    # Re-check horizontal overlap at NEW position to detect
                    # edge-of-platform carries
                    if (self.player.rect.right <= old_mx or
                        self.player.rect.left >= old_mx + mp.rect.w):
                        # Player slid off edge during horizontal move -- still
                        # carry them by dx so they don't phase through
                        pass
                # Track riding status for post-update platform push
                self._moving_plat_riding.append((mp, dx))
            elif (horiz_overlap and
                  self.player.rect.bottom <= mp.rect.top + 4 and
                  self.player.rect.bottom >= mp.rect.top - 4 and
                  self.player.velocity_y >= 0):
                # Extra narrow snap: if player feet are between old and new
                # platform top (high-tolerance already caught them above),
                # snap them onto the moved platform
                self.player.rect.x += dx
                self.player.rect.bottom = mp.rect.top
                self.player.velocity_y = 0
                self.player.is_on_ground = True

        # Player
        keys = pygame.key.get_pressed()
        self.player.update(player_dt, keys, self.level.platforms)
        if self.ghost:
            prev_gidx = getattr(self.ghost, '_pidx', self.ghost.idx)
            self.ghost.update(effective_dt, self.run_timer)
            # Polish: ghost 'echo' particles on beat (sample advance = rhythmic pulse feel)
            if self.ghost.idx > prev_gidx and self.particles:
                try:
                    ex, ey = self.ghost.rect.centerx, self.ghost.rect.centery
                    self.particles.emit_sparkle(ex, ey - 6, 2)
                    if random.random() < 0.6:
                        self.particles.emit_ghost_beat_pop(ex + random.uniform(-4,4), ey - 3)
                except Exception as e:
                    log_event("glitch", f"ghost beat particle failed: {type(e).__name__}")
            self.ghost._pidx = self.ghost.idx

        # Lane 5 ultra depth polish: wild_weave passive vine lash on moves (visual + squash)
        grafts = getattr(self.player, "grafts", []) or []
        if "wild_weave" in grafts:
            wvt = getattr(self.player, "_wild_vine_timer", 0.0)
            if wvt <= 0 and (abs(getattr(self.player, "velocity_x", 0)) > 10 or not getattr(self.player, "is_on_ground", True)):
                self.player._wild_vine_timer = 0.7
                if self.particles:
                    self.particles.emit_vine_snag_pop(self.player.rect.centerx, self.player.rect.centery - 4, 4)
                    # high-impact vine bloom pop on weave (lush on move/vine action)
                    if len(grafts) >= 3:
                        self.particles.emit_vine_bloom_pop(self.player.rect.centerx + random.uniform(-6,6), self.player.rect.centery - 2, 8)
                if self.camera and hasattr(self.camera, "trigger_squash"):
                    self.camera.trigger_squash(0.03, 0.06, y_nudge=4 if len(grafts)>=3 else 0)
            # "Passed your ghost" satisfaction pop for next-level speedrun feel
            if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost', None) and getattr(self.ghost, 'rect', None):
                try:
                    gx = self.ghost.rect.centerx
                    px = self.player.rect.centerx
                    vx = getattr(self.player, 'velocity_x', 0)
                    beaten = getattr(self, '_last_ghost_beaten', False)
                    if vx > 5 and px > gx and not beaten:
                        self.particles.emit_sparkle(gx, self.ghost.rect.centery, 5)
                        if self.camera and hasattr(self.camera, 'trigger_squash'):
                            self.camera.trigger_squash(0.04, 0.1)
                        self._last_ghost_beaten = True
                    elif vx < -5 and px < gx and not beaten:
                        self.particles.emit_sparkle(gx, self.ghost.rect.centery, 5)
                        if self.camera and hasattr(self.camera, 'trigger_squash'):
                            self.camera.trigger_squash(0.04, 0.1)
                        self._last_ghost_beaten = True
                    if abs(px - gx) > 90:
                        self._last_ghost_beaten = False
                    # crossed detection for next-level "PASSED" feedback
                    prev_px = getattr(self, '_prev_ghost_px', px)
                    crossed = (prev_px < gx <= px) or (prev_px > gx >= px)
                    if crossed:
                        self.particles.emit_sparkle(gx, self.player.rect.centery - 4, 10)
                        self.hud.add_floating_text("PASSED", SCREEN_WIDTH // 2, 95, (180, 255, 200))
                        if self.camera and hasattr(self.camera, 'trigger_squash'):
                            self.camera.trigger_squash(0.06, 0.12)
                        log_event("state", "ghost_passed")
                    self._prev_ghost_px = px
                except Exception as e:
                    log_event("warning", f"speedrun ghost beat pop failed: {type(e).__name__}")
        # Wild ghosts in overgrown climax (hostile replay feel)
        if getattr(self, 'overgrown_mode', False) and getattr(self, 'ghost', None) and getattr(self.ghost, 'rect', None) and self.ghost.rect.colliderect(self.player.rect):
            self.player.velocity_x *= 0.7
            self.particles.emit_sparkle(self.ghost.rect.centerx, self.ghost.rect.centery, 3)
            log_event("state", "wild_ghost_touch")

        # Buffer success juice: tiny sparkle + dust when jump buffer catches a landing.
        # Makes the smoothed controls *feel* satisfying and premium ("yes, it read my input!").
        # Coyote+buffer tuned more generous (0.16/0.12) for lane 5/16 feel but not floaty (still crisp <10 frames).
        if getattr(self.player, "_consumed_buffered_jump", False):
            bx = self.player.rect.centerx
            by = self.player.rect.bottom - 4
            self.particles.emit_sparkle(bx, by, 5)
            self.particles.emit_impact_dust(bx, by, 6)
            self.particles.emit_leaf_burst(bx, by - 2, 4)
            # extra small juice squash on perfect buffer land for satisfying "got it" feel + tiny y
            if self.camera and hasattr(self.camera, 'trigger_squash'):
                self.camera.trigger_squash(0.07, 0.1, y_nudge=3)

        # Jump cut juice: small leaf wisp on release for variable height premium feedback. More pop for responsive cut feel.
        if getattr(self.player, "_just_cut", False):
            cx = self.player.rect.centerx
            cy = self.player.rect.centery - 10
            self.particles.emit_glide_wisp(cx, cy)
            self.particles.emit_sparkle(cx, cy, 7)
            self.particles.emit_leaf_burst(cx, cy + 4, 7)
            self.particles.emit_impact_dust(cx, cy + 6, 5)
            # hitstop feel on skilled cut (weight)
            self._hitstop_timer = max(getattr(self, '_hitstop_timer', 0), 0.035)
            self.particles.emit_hitstop_flash(cx, cy, 3)
            # stronger camera squash + y-nudge pop on skilled cut (premium snap feel)
            if self.camera and hasattr(self.camera, 'trigger_squash'):
                self.camera.trigger_squash(0.13, 0.14, y_nudge=5)

        # --- Speedrun timer + lightweight ghost sampling (every GHOST_SAMPLE_INTERVAL) ---
        if getattr(self, 'speedrun_mode', False):
            self.run_timer += effective_dt
            if (self.run_timer - self._last_ghost_sample) >= GHOST_SAMPLE_INTERVAL:
                self.ghost_record.append([
                    self.run_timer,
                    self.player.rect.x,
                    self.player.rect.y,
                    self.player.facing_right,
                ])
                self._last_ghost_sample = self.run_timer

        # Daily full-run time attack timer (accumulates across all levels in the daily seed run)
        if getattr(self, 'daily_mode', False):
            self.daily_timer += effective_dt

        # Dash trail particles (snappy visual lock + speed lines) -- juicy whoosh
        if self.player.is_dashing:
            trail_dir = -1.0 if self.player.dash_direction > 0 else 1.0
            for _ in range(2):
                ox = self.player.rect.centerx + trail_dir * 8
                oy = self.player.rect.centery + (self.player.rect.height * 0.1)
                self.particles.emit_dash_trail(ox, oy, trail_dir)
            # Ice dash gets frost too
            if getattr(self.player, "friction_mode", "") == "ice":
                for _ in range(1):
                    self.particles.emit_ice_trail(ox, oy, trail_dir)

        # Speedrun-specific motion trail (extra variety for high-speed visibility juice)
        if getattr(self, 'speedrun_mode', False) and abs(self.player.velocity_x) > 180:
            tr_dir = -1.0 if self.player.velocity_x > 0 else 1.0
            self.particles.emit_speedrun_trail(
                self.player.rect.centerx - (self.player.velocity_x * 0.025),
                self.player.rect.centery + random.uniform(-3, 3),
                tr_dir
            )

        # Glide visuals: soft rising air wisps + leaf flecks while actively gliding
        if self.player.is_gliding:
            for _ in range(1):
                gx = self.player.rect.centerx + random.uniform(-6, 6)
                gy = self.player.rect.bottom - 2
                self.particles.emit_glide_wisp(gx, gy)
            # Extra leaf pop on glide for forest juice
            if self.level and self.level.biome in ("forest", "corrupted", "mushroom"):
                if random.random() < 0.5:
                    self.particles.emit_graft_leaves(gx, gy - 8, 1)

        # Passive graft aura particles (subtle mastery visual feedback when not gliding)
        # Low rate for perf, uses existing emitters. Different cues per graft type.
        # + boosted leaves/aura when many grafts (>=3) for mastery indicator.
        grafts = getattr(self.player, "grafts", None) or []
        if grafts and random.random() < 0.06:
            gx = self.player.rect.centerx + random.uniform(-4, 4)
            gy = self.player.rect.centery + random.uniform(-6, 6)
            if any(g in grafts for g in ("glide_efficiency", "weak_glide")):
                self.particles.emit_graft_leaves(gx, gy + 6, 1)
            if "lava_resist" in grafts and random.random() < 0.7:
                self.particles.emit_sparkle(gx, gy - 8, 1)
            if "ice_armor" in grafts and random.random() < 0.4:
                self.particles.emit_ice_trail(gx, gy + 8, 0)
            if "dash_mastery" in grafts and random.random() < 0.5:
                self.particles.emit_speedrun_trail(gx - 4, gy, -1 if self.player.facing_right else 1)
            if "root_ward" in grafts and random.random() < 0.5:
                self.particles.emit_mushroom_puff(gx, gy + 4, 2)
            if "echo_step" in grafts and random.random() < 0.4:
                self.particles.emit_sparkle(gx - 10, gy, 2)
            if "wind_ward" in grafts and random.random() < 0.5:
                self.particles.emit_wind_drift(gx, gy, 1.0 if self.player.facing_right else -1.0, 1)
            # Mastery: extra leaf particles when 3+ grafts equipped (visible mastery)
            if len(grafts) >= 3 and random.random() < 0.4:
                self.particles.emit_graft_leaves(gx, gy - 12, 2)
            # Small mastery visual payoff (5+): occasional golden mote for "overgrown" delight
            if len(grafts) >= 5 and random.random() < 0.25:
                self.particles.emit_sparkle(gx + random.uniform(-8, 8), gy - 18, 1)
            # Unique overgrowth aura reward (5th graft slot on overgrown clear)
            if getattr(self, '_has_overgrowth_mastery_reward', False) or "overgrowth_aura" in grafts:
                if random.random() < 0.18:
                    self.particles.emit_overgrowth_aura(gx, gy - 6, 3)

        # Ice slide trail motes (visual feedback on ice biome)
        if getattr(self.player, "friction_mode", "") == "ice" and abs(self.player.velocity_x) > 60:
            if random.random() < 0.45:
                self.particles.emit_ice_trail(
                    self.player.rect.centerx - (self.player.velocity_x * 0.03),
                    self.player.rect.bottom - 4,
                    -1.0 if self.player.velocity_x > 0 else 1.0
                )
            if random.random() < 0.08:
                self.audio.play("ice_slide")  # whoosh cue, rate limited in AudioManager

        # Detect glide use to dismiss tutorial
        if self.player.is_gliding and not self._glide_used:
            self._glide_used = True
            self._glide_tutorial_timer = 0.0

        # Landing dust + leaf burst
        if self.player.is_on_ground and not self._was_on_ground:
            vy_land = abs(getattr(self.player, "velocity_y", 0))
            hard = vy_land > 280
            self.particles.emit_impact_dust(self.player.rect.centerx, self.player.rect.bottom, 7 if not hard else 11)
            self.particles.emit_leaf_burst(self.player.rect.centerx, self.player.rect.bottom - 6, 5 if not hard else 9)
            if hard:
                self.particles.emit_sparkle(self.player.rect.centerx, self.player.rect.bottom - 8, 5)
            # Extra lush landing: leaves in foresty biomes
            if self.level.biome in ("forest", "corrupted"):
                for _ in range(4 if not hard else 7):
                    self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
            # softer squash on skilled/gentle lands (low impact vertical = good landing); hard gets y-nudge + stronger
            if self.camera and hasattr(self.camera, "trigger_squash"):
                if hard:
                    self.camera.trigger_squash(0.09, 0.13, y_nudge=10)
                    self._hitstop_timer = max(getattr(self, '_hitstop_timer', 0), 0.045)
                elif vy_land < 220:
                    self.camera.trigger_squash(0.035, 0.09)
            self.audio.play("land")
            if not (self.level and getattr(self.level, 'is_icy', False)):
                try:
                    self.audio.play("grass_rustle")  # subtle grass on non-ice land
                except Exception:
                    pass
        self._was_on_ground = self.player.is_on_ground

        # Dash start dust (when SHIFT pressed and dash begins)
        # Dash end dust burst for brake feel
        if self._was_dashing and not self.player.is_dashing:
            self.particles.emit_dust(self.player.rect.centerx, self.player.rect.bottom, 8)
            self.particles.emit_impact_dust(self.player.rect.centerx, self.player.rect.bottom, 4)
            self._hitstop_timer = max(getattr(self, '_hitstop_timer', 0), 0.03)
            self.shake.trigger(3, 0.06)
            if self.camera and hasattr(self.camera, 'trigger_squash'):
                self.camera.trigger_squash(0.04, 0.07, y_nudge=4)
        self._was_dashing = self.player.is_dashing

        # Enemies
        ed = world_dt
        if getattr(self, "daily_mode", False):
            ed *= 1.18  # higher enemy speed (or count) modifier for daily challenge
        for enemy in list(self.level.enemies):
            enemy.update(ed, self.level.platforms, self.player)

        # Boss (also faster in daily for pressure)
        bd = world_dt
        if getattr(self, "daily_mode", False):
            bd *= 1.12
        if self.level.boss and self.level.boss.alive():
            self.level.boss.update(bd, self.player, self.level.platforms)

        # =============================================================
        # BIOME MECHANICS
        # =============================================================

        # --- Geysers (Level 4: Caldera) ---
        for geyser in self.level.geysers:
            geyser.update(world_dt)
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
        self.level.toxic_trails.update(world_dt)
        for trail in pygame.sprite.spritecollide(
                self.player, self.level.toxic_trails, False):
            if self.player.take_damage(self._scaled_damage(SULFUR_TRAIL_DMG), source_x=trail.rect.centerx):
                self._took_damage_this_run = True
                self.shake.trigger(4, 0.1)
                self.audio.play("hit")

        # --- Crumbling platforms (Level 5: Basalt) ---
        for cp in self.level.crumbling:
            if cp.solid and self.player.is_on_ground:
                feet = self.player.get_stomp_rect()
                test = pygame.Rect(cp.rect.x - 2, cp.rect.y - 4, cp.rect.w + 4, 8)
                if feet.colliderect(test):
                    cp.touch()
            cp.update(world_dt)

        # --- Wind zones (Level 6: Desert) ---
        # Velocity-based: let player collision resolver handle walls/ice
        in_wind = False
        for wz in self.level.wind_zones:
            if pygame.sprite.collide_rect(self.player, wz):
                push = wz.get_push() * effective_dt
                if "wind_ward" in getattr(self.player, "grafts", []):
                    push *= 0.4  # delightful wind_ward resistance + control
                    # fun leaf drift trail for elevation (more reliable juicy feel)
                    self.particles.emit_leaf_burst(self.player.rect.centerx, self.player.rect.centery, 2)
                    if random.random() < 0.6:
                        self.particles.emit_sparkle(self.player.rect.centerx + random.uniform(-4,4), self.player.rect.centery - 2, 1)
                    try:
                        self.audio.play("wind_gust")  # wind gust layer for wind_ward
                    except Exception:
                        pass
                # Synergy depth: wind_chrono (glide+ dash + chrono) gives stronger wind control + tiny chrono feel
                if "wind_chrono" in getattr(self.player, "active_synergies", set()):
                    push *= 0.6  # extra resist on top of ward if present
                    if random.random() < 0.4:
                        self.particles.emit_sparkle(self.player.rect.centerx + random.uniform(-6,6), self.player.rect.centery - 4, 2)
                    # light chrono flavor on wind gusts
                    if random.random() < 0.3:
                        self.player.chrono_slow_timer = max(getattr(self.player, "chrono_slow_timer", 0.0), 0.15)
                self.player.velocity_x += push
                in_wind = True
            if random.random() < 0.35:
                self.particles.emit_wind_drift(wz.rect.centerx, wz.rect.centery, wz.direction, 2)
        if in_wind and random.random() < 0.06:
            self.audio.play("wind")

        # --- Thermal updrafts (Level 6: Desert) ---
        for tu in self.level.updrafts:
            if pygame.sprite.collide_rect(self.player, tu):
                self.player.velocity_y = max(
                    self.player.velocity_y + THERMAL_FORCE * effective_dt,
                    THERMAL_FORCE)

        # --- Projectiles (Level 6: CactusScorpion) ---
        for enemy in self.level.enemies:
            if hasattr(enemy, "get_new_projectiles"):
                for proj in enemy.get_new_projectiles():
                    self.level.projectiles.add(proj)
                    self.level.all_sprites.add(proj)
        self.level.projectiles.update(world_dt)
        # Enemy projectiles damage player. Friendly projectiles (shurikens,
        # ice shards) are thrown by player and must not hurt self.
        for proj in list(self.level.projectiles):
            if isinstance(proj, (BambooShuriken, IceProjectile)):
                continue
            if proj.rect.colliderect(self.player.rect):
                if self.player.take_damage(PLAYER_DAMAGE, source_x=proj.rect.centerx):
                    self.shake.trigger()
                    self.audio.play("hit")
                proj.kill()

        # --- Crystal interaction (Level 7: Cave) ---
        for crystal in self.level.crystals:
            crystal.update(effective_dt)
            if (not crystal.is_lit()
                    and pygame.sprite.collide_rect(self.player, crystal)):
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
                    and self.player.rect.bottom < mush.rect.centery + 10):
                self.player.velocity_y = MUSHROOM_BOUNCE
                self.player.is_on_ground = False
                # Reset jumps so double-jump is available mid-bounce
                self.player.jumps_remaining = 2 if self.player.has_double_jump else 1
                mush.compress()
                self.particles.emit_sparkle(
                    mush.rect.centerx, mush.rect.top, 10)
                self.particles.emit_mushroom_puff(
                    mush.rect.centerx, mush.rect.top, 12)
                self.shake.trigger(4, 0.1)
                self.audio.play("jump")

        # --- Poison spores from SporePuffers (Level 14) ---
        for enemy in self.level.enemies:
            if hasattr(enemy, "get_new_spores"):
                for spore in enemy.get_new_spores():
                    self.level.poison_spores.add(spore)
                    self.level.all_sprites.add(spore)
        self.level.poison_spores.update(world_dt)
        for spore in pygame.sprite.spritecollide(
                self.player, self.level.poison_spores, False):
            if self.player.take_damage(self._scaled_damage(spore.damage), source_x=spore.rect.centerx):
                self._took_damage_this_run = True
                self.shake.trigger(4, 0.1)
                self.audio.play("hit")
                spore.kill()

        # --- Rising lava (Level 15) ---
        if self.level.rising_lava is not None:
            self.level.rising_lava.update(world_dt)
            # Instant death if player's feet dip into lava (lava_resist graft turns into heavy damage)
            if (self.player.rect.bottom > self.level.rising_lava.rect.top + 4
                    and self.player.invincible_timer <= 0
                    and not getattr(self.player, 'dead', False)):
                if "lava_resist" in getattr(self.player, 'grafts', []):
                    if self.player.take_damage(PLAYER_MAX_HP // 2 + 10):
                        self._took_damage_this_run = True
                        self.shake.trigger(6, 0.2)
                        self.audio.play("hit")
                        self.player.invincible_timer = max(self.player.invincible_timer, 0.8)
                else:
                    self.player.health = 0
                    self.player.dead = True
                    self.audio.play("death")
                    self.shake.trigger(12, 0.4)

        # --- Magma leaper projectiles handled in standard enemy update ---

        # --- Timed gates (Level 16) ---
        if len(self.level.timed_gates) > 0:
            TimedGate.tick_global(world_dt)
            for gate in self.level.timed_gates:
                gate.update(world_dt)

        # --- Teleport portals (Level 17) ---
        for portal in self.level.portals:
            portal.update(world_dt)
        for gz in self.level.gravity_zones:
            if hasattr(gz, "update"):
                gz.update(world_dt)
        # Check player overlap with active portals
        for portal in self.level.portals:
            if (portal.active
                    and portal.partner is not None
                    and pygame.sprite.collide_rect(self.player, portal)):
                # Teleport player to partner's position
                target = portal.partner
                self.player.rect.midbottom = target.rect.midbottom
                self.player.velocity_x = 0.0
                self.player.velocity_y = 0.0
                portal.teleport()
                target.teleport()
                self.player.invincible_timer = max(
                    self.player.invincible_timer, 0.3)
                self.particles.emit_portal_warp(portal.rect.centerx, portal.rect.centery, 10)
                self.particles.emit_portal_warp(target.rect.centerx, target.rect.centery, 8)
                self.particles.emit_sparkle(
                    portal.rect.centerx, portal.rect.centery, 6)
                self.player.score += 20
                self.hud.add_floating_text("WARP!", portal.rect.centerx, portal.rect.top - 14, (140, 220, 255))
                log_event("state", "portal_warp", {"x": portal.rect.centerx})
                self.audio.play("portal")
                if self.camera and hasattr(self.camera, "trigger_squash"):
                    self.camera.trigger_squash(0.05, 0.12)
                break  # one teleport per frame

        # --- PhaseWraith portal teleport (Level 17) ---
        # Wraiths that walk into an active portal teleport to the partner exit.
        for enemy in self.level.enemies:
            if (isinstance(enemy, PhaseWraith)
                    and getattr(enemy, "alive_flag", True)
                    and getattr(enemy, "teleport_cooldown", 1.0) <= 0):
                for portal in self.level.portals:
                    if (portal.active and portal.partner is not None
                            and pygame.sprite.collide_rect(enemy, portal)):
                        target = portal.partner
                        enemy.teleport_to(target.rect.centerx, target.rect.bottom)
                        portal.teleport()
                        target.teleport()
                        self.particles.emit_sparkle(
                            portal.rect.centerx, portal.rect.centery, 6)
                        break

        # --- Gravity zones (Level 18 + overgrown chaotic pulses) ---
        # Determine which zone the player is in (if any)
        prev_mult = getattr(self.player, "gravity_multiplier", 1.0)
        active_multiplier = 1.0
        flip_zone = None
        for gz in self.level.gravity_zones:
            if pygame.sprite.collide_rect(self.player, gz):
                active_multiplier = gz.get_multiplier()
                flip_zone = gz
                if random.random() < 0.4:
                    self.particles.emit_gravity_motes(gz.rect.centerx, gz.rect.centery, 3)
                break
        self.player.gravity_multiplier = active_multiplier
        # Chaotic grav flip ambush sync (overgrown only): denser late feel on pulse
        if active_multiplier != prev_mult and flip_zone is not None:
            if getattr(self, 'overgrown_mode', False) or getattr(getattr(self, 'level', None), 'biome', '') == "overgrown":
                self.shake.trigger(5, 0.18)
                if random.random() < 0.6:
                    self.audio.play("crumble", pitch=0.8)
                self.particles.emit_gravity_motes(self.player.rect.centerx, self.player.rect.centery, 8)
                # Synced ambush signal: flash/boost feel on late enemies near player (no enemy code change)
                for e in list(getattr(self.level, 'enemies', [])):
                    if getattr(e, 'alive', lambda: True)() and abs(e.rect.centerx - self.player.rect.centerx) < 420:
                        if hasattr(e, 'flash'):
                            e.flash = max(getattr(e, 'flash', 0), 0.45)
                        # light visual cue only (feels ambush without new logic)
                        if random.random() < 0.3:
                            self.particles.emit_sparkle(e.rect.centerx, e.rect.centery - 8, 2)

        # --- Overgrown vines (post-L18): varied hazards sway+pull/spike/snap (dense theme) ---
        if getattr(self.level, "vines", None):
            for v in self.level.vines:
                if pygame.sprite.collide_rect(self.player, v):
                    if hasattr(v, "apply_entangle"):
                        v.apply_entangle(self.player)
                    # audio + multi-sensory juice on vine snag (from audio agent + this drive)
                    if random.random() < 0.7:
                        try:
                            self.audio.play("vine")
                            self.audio.play("vine_snap")  # richer snap/creak layer on vine interaction
                        except Exception as e:
                            log_event("warning", f"vine audio failed, fallback crumble: {type(e).__name__}")
                            self.audio.play("crumble", pitch=random.uniform(0.65, 0.85))
                        squash_amt = 0.09 if "root_ward" in grafts else 0.07
                        if self.camera and hasattr(self.camera, "trigger_squash"):
                            self.camera.trigger_squash(squash_amt, 0.08)
                    if random.random() < 0.4:
                        self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
                    self.particles.emit_vine_snag_pop(self.player.rect.centerx, self.player.rect.centery - 4, 5)
                    if "root_ward" in grafts:
                        self.particles.emit_mushroom_puff(self.player.rect.centerx, self.player.rect.centery, 3)
                    log_event("state", "vine_snag_pop")
                    break
            # Premium: sway the vines as slow moving hazards every frame
            for v in self.level.vines:
                if hasattr(v, "update"):
                    v.update(world_dt)
                # Dynamic vines in overgrown (storm lash, more alive for climax)
                if getattr(self.level, "biome", "") == "overgrown" and hasattr(v, "sway_amp"):
                    v.sway_amp = getattr(v, "sway_amp", 8) * 1.4  # wilder movement in storm climax

        # Wild Heart climax collect (architect premium climax for overgrown)
        if getattr(self.level, "biome", "") == "overgrown" and not getattr(self, '_heart_collected', False):
            hx, hy = 7720, 255  # climax spot before final goal, high for drama
            hr = pygame.Rect(hx - 18, hy - 18, 36, 36)
            if hr.colliderect(self.player.rect):
                self._heart_collected = True
                self.hud.add_floating_text("WILD HEART CLAIMED!", SCREEN_WIDTH // 2, 95, (90, 220, 130))
                self.particles.emit_dense_foliage(self.camera.get_visible_rect(), 50)
                for _ in range(25):
                    self.particles.emit_overgrowth_aura(7600 + random.uniform(-150, 150), 260 + random.uniform(-80, 80), 4)
                if len(getattr(self, '_grafts', [])) >= 5:
                    self.particles.emit_mastery_storm(SCREEN_WIDTH // 2, 80, 10)
                    self.camera.trigger_squash(0.12, 0.2, y_nudge=8) if self.camera else None
                self.shake.trigger(9, 0.3)
                self.audio.play("victory", pitch=0.85)
                self.audio.play("crystal")
                self._has_overgrowth_mastery_reward = True
                if "overgrowth_aura" not in (getattr(self, '_grafts', None) or []):
                    self._grafts = (getattr(self, '_grafts', None) or []) + ["overgrowth_aura"]
                self.hud.add_floating_text("5TH GRAFT SLOT + OVERGROWTH AURA!", SCREEN_WIDTH // 2, 120, (120, 255, 160))
                try:
                    if not mark_overgrown_mastery():
                        log_event("failure", "overgrown mastery not persisted (climax)")
                except Exception as e:
                    log_event("warning", f"overgrown mastery mark failed: {type(e).__name__}")
                log_event("state", "wild_heart_climax_collect")

        # Denser foliage via particles for overgrown (wild post-game lush)
        if getattr(self, 'overgrown_mode', False) or getattr(getattr(self, 'level', None), 'biome', '') == "overgrown":
            if random.random() < 0.92:
                self.particles.emit_dense_foliage(self.camera.get_visible_rect(), 16)
            if random.random() < 0.78:
                self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
            # Storms (premium climax weather): occasional lash + shake + leaf burst
            storm_chance = 0.015
            if getattr(self.level, 'stormy', False) or getattr(self, 'daily_mode', False):
                storm_chance = 0.035  # richer daily + stormy mod elevation makes storms visible more
            if random.random() < storm_chance:
                self.shake.trigger(4, 0.12)
                self.particles.emit_dense_foliage(self.camera.get_visible_rect(), 22)
                try:
                    self.audio.play("crumble", pitch=random.uniform(0.5, 0.7))
                except Exception as e:
                    log_event("warning", f"storm audio failed: {type(e).__name__}")
                log_event("state", "overgrown_storm")
            if random.random() < 0.35:
                self.particles.emit_dense_foliage(self.camera.get_visible_rect(), 7)

        # --- Gravity drones: pull player toward them ---
        for enemy in self.level.enemies:
            if isinstance(enemy, GravityDrone) and enemy.alive():
                dx = enemy.rect.centerx - self.player.rect.centerx
                dy = enemy.rect.centery - self.player.rect.centery
                dist = math.hypot(dx, dy)
                if 10 < dist < DRONE_RANGE:
                    pull_x = (dx / dist) * DRONE_PULL * effective_dt
                    pull_y = (dy / dist) * DRONE_PULL * effective_dt
                    self.player.velocity_x += pull_x
                    self.player.velocity_y += pull_y

        # --- ForgeHammer lethality check ---
        for enemy in self.level.enemies:
            if (isinstance(enemy, ForgeHammer)
                    and getattr(enemy, "is_lethal", lambda: False)()):
                if pygame.sprite.collide_rect(self.player, enemy):
                    if self.player.take_damage(PLAYER_DAMAGE * 2):
                        self._took_damage_this_run = True
                        self.shake.trigger(14, 0.35)
                        self.audio.play("hit")

        # --- VoidEater contact damage while open ---
        for enemy in self.level.enemies:
            if (isinstance(enemy, VoidEater)
                    and getattr(enemy, "is_dangerous", lambda: False)()):
                if pygame.sprite.collide_rect(self.player, enemy):
                    if self.player.take_damage(PLAYER_DAMAGE):
                        self._took_damage_this_run = True
                        self.shake.trigger(8, 0.2)
                        self.audio.play("hit")

        # --- Dark walls: update their solid/faded state based on nearby crystals ---
        for dw in self.level.dark_walls:
            dw.update(effective_dt)

        # --- NPCs ---
        for npc in self.level.npcs:
            npc.update(effective_dt, self.player)

        # =============================================================
        # STANDARD COLLISIONS
        # =============================================================

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
                    self.shake.trigger(3, 0.07)
                    self.audio.play("collect")
                    if getattr(self, 'speedrun_mode', False):
                        self.ghost_record.append([self.run_timer, cp.spawn_x, cp.spawn_y, self.player.facing_right])
                        # Record split for pro-level ghost comparison
                        if not hasattr(self, 'splits'):
                            self.splits = []
                        self.splits.append((len(self.splits), self.run_timer))

        # Bamboo
        for bamboo in pygame.sprite.spritecollide(
                self.player, self.level.bamboos, True):
            points = self.player.collect_bamboo()
            self.hud.on_bamboo_collected()
            suffix = f" x{self.player.combo_count}!" if self.player.combo_count > 1 else ""
            self.hud.add_floating_text(
                f"+{points}{suffix}", bamboo.rect.centerx, bamboo.rect.top, COL_GOLD)
            # Juicy bamboo collect pop + essence sparkle (gold pop for meta reward)
            self.particles.emit_sparkle(bamboo.rect.centerx, bamboo.rect.centery, 14)
            self.particles.emit_bamboo_glitter(bamboo.rect.centerx, bamboo.rect.centery, 8)
            for _ in range(3):
                self.particles.emit_sparkle(
                    bamboo.rect.centerx + random.uniform(-6, 6),
                    bamboo.rect.top - 4, 2)
            self.audio.play("collect")
            self.audio.play("essence")
            self.audio.play("break", pitch=random.uniform(0.92, 1.08))
            self.shake.trigger(2, 0.035)
            # Grove meta: collect essence per-biome tag on bamboo
            biome = getattr(self.level, "biome", "forest") if self.level else "forest"
            add_essence(biome)
            daily_flag = getattr(self.level, 'daily_bonus_essence', False) or getattr(self, "daily_mode", False)
            if daily_flag:
                add_essence(biome)  # stronger daily bonus source: guaranteed extra on pick
                if random.random() < 0.4:
                    add_essence(biome)
            # juice: sparkles extra on daily essence bonus
            if daily_flag and random.random() < 0.3:
                self.particles.emit_sparkle(bamboo.rect.centerx + 4, bamboo.rect.top - 8, 2)
            # essence_magnet source bonus
            if self.player and "essence_magnet" in getattr(self.player, "grafts", []):
                if random.random() < 0.5:
                    add_essence(biome)

        # Bamboo staff weapon pickup (limited duration)
        for weapon in pygame.sprite.spritecollide(
                self.player, self.level.weapons, True):
            self.player.has_bamboo_weapon = True
            self.player.weapon_time_remaining = 30.0  # 30 seconds
            self._weapon_tutorial_timer = 999.0
            self._weapon_used = False
            self.hud.add_floating_text(
                "BAMBOO STAFF! 30s",
                weapon.rect.centerx, weapon.rect.top - 10, (255, 220, 120))
            self.particles.emit_sparkle(weapon.rect.centerx, weapon.rect.centery, 14)
            self.audio.play("collect")

        # Glide feather pickup (10-second timed buff)
        for feather in pygame.sprite.spritecollide(
                self.player, self.level.glide_pickups, True):
            self.player.glide_time_remaining = GLIDE_DURATION_SEC
            self._glide_tutorial_timer = 999.0
            self._glide_used = False
            # Make glide permanent on first collection (as documented)
            if not self._has_glide_permanent:
                self._has_glide_permanent = True
                if not save_unlock("glide"):
                    log_event("failure", "glide unlock not persisted")
            self.hud.add_floating_text(
                f"GLIDE! {int(GLIDE_DURATION_SEC)}s",
                feather.rect.centerx, feather.rect.top - 10, (140, 220, 255))
            self.particles.emit_sparkle(feather.rect.centerx,
                                        feather.rect.centery, 16)
            self.audio.play("collect")

        # Dash boots pickup (30-second timed buff)
        for boots in pygame.sprite.spritecollide(
                self.player, self.level.dash_pickups, True):
            self.player.dash_time_remaining = DASH_DURATION_SEC
            self._dash_tutorial_timer = 999.0
            self._dash_used = False
            self.hud.add_floating_text(
                f"DASH! {int(DASH_DURATION_SEC)}s",
                boots.rect.centerx, boots.rect.top - 10, (255, 180, 100))
            self.particles.emit_sparkle(boots.rect.centerx,
                                        boots.rect.centery, 16)
            self.audio.play("collect")

        # Update weapon sprite animations
        self.level.weapons.update(world_dt)
        self.level.glide_pickups.update(world_dt)
        self.level.dash_pickups.update(world_dt)

        # Heals
        for heal in pygame.sprite.spritecollide(
                self.player, self.level.heals, True):
            self.player.heal(HEAL_AMOUNT)
            self.hud.add_floating_text(
                f"+{HEAL_AMOUNT} HP", heal.rect.centerx, heal.rect.top,
                (100, 255, 100))
            self.particles.emit_sparkle(heal.rect.centerx, heal.rect.centery)
            self.audio.play("collect")

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
                        and shur.rect.colliderect(enemy.rect)):
                    # Only skip true invincibles
                    if isinstance(enemy, (BrineShard, DustDevil)):
                        continue
                    enemy.die()
                    mult = getattr(self, '_daily_score_mult', 1.0)
                    self.player.score += int(STOMP_SCORE * mult)
                    self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery)
                    if self.level.biome in ("forest", "corrupted"):
                        self.particles.emit_mushroom_puff(enemy.rect.centerx, enemy.rect.centery, 4)
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
                        and ice.rect.colliderect(enemy.rect)):
                    # Ice CAN kill invincibles -- it freezes them
                    enemy.die()
                    mult = getattr(self, '_daily_score_mult', 1.0)
                    self.player.score += int(STOMP_SCORE * mult)
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
                self.shake.trigger(8, 0.18)
                if killed:
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
                        if isinstance(enemy, (BrineShard, DustDevil)):
                            continue
                        enemy.die()
                        mult = getattr(self, '_daily_score_mult', 1.0)
                        self.player.score += int(STOMP_SCORE * mult)
                        self.hud.add_floating_text(
                            f"+{STOMP_SCORE}", enemy.rect.centerx,
                            enemy.rect.top, COL_GOLD)
                        self.particles.emit_death(
                            enemy.rect.centerx, enemy.rect.centery)
                        self.particles.emit_leaf_burst(enemy.rect.centerx, enemy.rect.centery - 2, 4)
                        self.particles.emit_sparkle(enemy.rect.centerx, enemy.rect.top - 2, 3)
                        self.audio.play("stomp")
                        # Hitstop: freeze 60ms for impact punch
                        self._hitstop_timer = max(self._hitstop_timer, 0.06)
                        self.particles.emit_hitstop_flash(enemy.rect.centerx, enemy.rect.centery - 4, 5)
                        self.shake.trigger(5, 0.08)
                        # Chrono graft: staff hit briefly slows time (delightful counter window)
                        if "chrono_step" in getattr(self.player, "grafts", []):
                            self.player.chrono_slow_timer = max(getattr(self.player, "chrono_slow_timer", 0.0), CHRONO_SLOW_STAFF_SEC)
                        # Prototype synergy: thorn_spore on vine_whip hit -> spore puff counter nearby
                        if "thorn_spore" in getattr(self.player, "active_synergies", set()):
                            self.particles.emit_spore_puff(enemy.rect.centerx, enemy.rect.centery, 4)
                            # light area slow/damage to other close enemies (ambitious feel)
                            for near in list(self.level.enemies):
                                if near is not enemy and getattr(near, "alive_flag", True) and abs(near.rect.centerx - enemy.rect.centerx) < 80:
                                    if hasattr(near, "velocity_x"):
                                        near.velocity_x *= 0.4
                                    self.particles.emit_spore_puff(near.rect.centerx, near.rect.centery, 2)
                # Boss gets hit too (if stunned)
                if (self.level.boss and self.level.boss.alive()
                        and self.level.boss.stunned
                        and atk_rect.colliderect(self.level.boss.rect)):
                    killed = self.level.boss.take_hit()
                    self.audio.play("boss_hit")
                    self.shake.trigger(10, 0.22)
                    if "chrono_step" in getattr(self.player, "grafts", []):
                        self.player.chrono_slow_timer = max(getattr(self.player, "chrono_slow_timer", 0.0), CHRONO_SLOW_STAFF_SEC)
                    if killed:
                        self.particles.emit_death(
                            self.level.boss.rect.centerx,
                            self.level.boss.rect.centery, 30)
                        self.player.score += BOSS_KILL_SCORE
                        self._maybe_unlock_ice_magic()

        # Enemy collisions (stomp or damage)
        for enemy in pygame.sprite.spritecollide(
                self.player, self.level.enemies, False):
            if not getattr(enemy, "alive_flag", True):
                continue
            # Skip enemies with dedicated collision handlers (they deal damage via their own paths)
            if getattr(enemy, "has_custom_collision", False):
                continue
            stomp_rect = self.player.get_stomp_rect()
            is_stompable = getattr(enemy, "is_stompable", True)
            if (is_stompable and self.player.velocity_y > 0
                    and stomp_rect.colliderect(enemy.rect)):
                enemy.die()
                self.player.velocity_y = ENEMY_STOMP_BOUNCE
                self.player.score += STOMP_SCORE
                self.hud.add_floating_text(
                    f"+{STOMP_SCORE}", enemy.rect.centerx, enemy.rect.top, COL_GOLD)
                self.particles.emit_death(enemy.rect.centerx, enemy.rect.centery)
                if self.level.biome in ("forest", "corrupted"):
                    self.particles.emit_mushroom_puff(enemy.rect.centerx, enemy.rect.centery, 3)
                self.audio.play("stomp")
                self.particles.emit_hitstop_flash(enemy.rect.centerx, enemy.rect.centery, 3)
                self._hitstop_timer = max(self._hitstop_timer, 0.05)
                if self.camera and hasattr(self.camera, "trigger_squash"):
                    self.camera.trigger_squash(0.08, 0.1, y_nudge=6)
            else:
                if self.player.take_damage(PLAYER_DAMAGE, source_x=enemy.rect.centerx):
                    self._took_damage_this_run = True
                    self.shake.trigger()
                    self.particles.emit_damage(
                        self.player.rect.centerx, self.player.rect.centery)
                    self.audio.play("hit")

        # Boss collision:
        #   - Landing on head (stomp) always bounces player off, never hurts.
        #     Damage to boss ONLY applied during stunned state.
        #   - Side/below collision damages player (as before).
        if self.level.boss and self.level.boss.alive():
            if pygame.sprite.collide_rect(self.player, self.level.boss):
                stomp_rect = self.player.get_stomp_rect()
                is_head_stomp = (self.player.velocity_y > 0
                                 and stomp_rect.colliderect(self.level.boss.rect))
                if is_head_stomp:
                    if self.level.boss.stunned:
                        # Damage boss during vulnerable window
                        self.player.velocity_y = ENEMY_STOMP_BOUNCE
                        self.player.rect.bottom = self.level.boss.rect.top
                        killed = self.level.boss.take_hit()
                        self.audio.play("boss_hit")
                        self.shake.trigger(14, 0.32)
                        if killed:
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
                            self._took_damage_this_run = True
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
                        self._took_damage_this_run = True
                        self.shake.trigger()
                        self.particles.emit_damage(
                            self.player.rect.centerx, self.player.rect.centery)
                        self.audio.play("hit")

        # Goal -- trigger "run off screen" outro instead of instant transition
        if (self.level.goal and not self._outro_active
                and pygame.sprite.collide_rect(self.player, self.level.goal)):
            boss_blocking = (self.level.boss is not None
                             and self.level.boss.alive())
            if not boss_blocking:
                self._outro_active = True
                self._outro_timer = 3.0
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
        if (self.player.rect.top > TRENCH_DEATH_Y and not self.player.dead
                and not self._outro_active):
            self.player.health = 0
            self.player.dead = True
            self.player.is_falling_trench = True
        if self.player.dead and self.death_anim is None:
            self.death_anim = DeathAnimation()
            self.audio.play("death")
            # Extra death juice burst (leaves + death particles for pop)
            self.particles.emit_death(self.player.rect.centerx, self.player.rect.centery, 22)
            if self.level and self.level.biome in ("forest", "corrupted"):
                self.particles.emit_graft_leaves(self.player.rect.centerx, self.player.rect.centery, 6)

        # --- Level end outro: victory dance then advance ---
        # Player is LOCKED in place during dance -- no walking off screen.
        if self._outro_active:
            # Play dance sound ONCE at the start of the dance
            if (self._outro_timer > 1.4 and not self.player.is_victory_dancing):
                self.audio.play("dance")
                self.shake.trigger(5, 0.09)
                # Remember dance anchor so player doesn't drift
                self._outro_anchor_x = self.player.rect.x
            self._outro_timer -= effective_dt
            if self._outro_timer > 1.4:
                # Active dance: lock player in place, play anim + JUICY sparkles/leaves (make dance as fun as gameplay)
                self.player.is_victory_dancing = True
                self.player.velocity_x = 0
                self.player.velocity_y = min(self.player.velocity_y, 0)
                # Snap back to anchor to prevent sliding
                if hasattr(self, '_outro_anchor_x'):
                    self.player.rect.x = self._outro_anchor_x
                if random.random() < 0.6:
                    self.particles.emit_sparkle(
                        self.player.rect.centerx + random.uniform(-8, 8),
                        self.player.rect.centery - 12, 4
                    )
                if random.random() < 0.4:
                    self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
            else:
                # Dance done -- small triumphant bounce in place, then advance
                self.player.is_victory_dancing = False
                self.player.velocity_x = 0
                if hasattr(self, '_outro_anchor_x'):
                    self.player.rect.x = self._outro_anchor_x
            if self._outro_timer <= 0:
                self._outro_active = False
                self.player.is_victory_dancing = False
                if getattr(self, 'speedrun_mode', False):
                    # Record final sample on level complete (per task: t,x,y,facing at interval)
                    if self.player:
                        self.ghost_record.append([self.run_timer, float(self.player.rect.x), float(self.player.rect.y), bool(self.player.facing_right)])
                    # Save best time + ghost on victory (per level / biome). Only persists if better.
                    if self.ghost_record:
                        try:
                            splits = getattr(self, 'splits', None)
                            saved = save_best_run(self.current_level, self.run_timer, list(self.ghost_record), splits)
                            if saved:
                                # refresh live ghost from the new best
                                self.best_ghost = get_best_ghost(self.current_level)
                                self.ghost = GhostPanda(self.best_ghost, is_best=True) if self.best_ghost else None
                                if self.ghost:
                                    self.ghost.reset()
                                    self.ghost._pidx = 0
                                # 'beat your best' celebration text + particle burst on improved save
                                self.hud.add_floating_text("BEAT YOUR BEST!", SCREEN_WIDTH // 2, 68, (90, 255, 140))
                                self.particles.emit_graft_leaves(SCREEN_WIDTH // 2, 60, 24)
                                self.particles.emit_ghost_beat_pop(SCREEN_WIDTH // 2 + random.uniform(-10, 10), 55)
                                if len(getattr(self, '_grafts', [])) >= 5:
                                    self.particles.emit_mastery_storm(SCREEN_WIDTH // 2, 55, 12)
                                if self.camera and hasattr(self.camera, 'trigger_squash'):
                                    yn = 10 if len(getattr(self, '_grafts', [])) >= 5 else 0
                                    self.camera.trigger_squash(0.09, 0.14, y_nudge=yn)
                                self.audio.play("ghost")
                                self.audio.play("ghost_whoosh")  # delta whoosh on save_best success
                        except Exception as e:
                            log_event("failure", f"ghost save failed on victory: {type(e).__name__}")
                            if self.camera and hasattr(self.camera, 'trigger_squash'):
                                self.camera.trigger_squash(0.18, 0.22)  # stronger squash juice
                            self.audio.play("victory", pitch=0.82)  # encouraging sound cue
                            for _ in range(28):
                                self.particles.emit_sparkle(
                                    SCREEN_WIDTH // 2 + random.uniform(-50, 50),
                                    58 + random.uniform(-12, 12), 2)
                    self._pending_best_time = self.run_timer
                    self._pending_best_ghost = list(self.ghost_record)
                    self._victory_ghost = list(self.ghost_record)
                # Premium win condition feedback for overgrown (post-game)
                if self.level and getattr(self.level, "biome", "") == "overgrown":
                    self.hud.add_floating_text("WILD HEART CLAIMED!", SCREEN_WIDTH // 2, 95, (90, 220, 130))
                    self.particles.emit_dense_foliage(self.camera.get_visible_rect(), 24)
                    for _ in range(14):
                        self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
                    # Special mastery reward on clear: 5th graft slot + unique overgrowth aura (visual + session)
                    self._has_overgrowth_mastery_reward = True
                    if "overgrowth_aura" not in (self._grafts or []):
                        self._grafts = (self._grafts or []) + ["overgrowth_aura"]
                    self.hud.add_floating_text("5TH GRAFT SLOT + OVERGROWTH AURA!", SCREEN_WIDTH // 2, 120, (120, 255, 160))
                    if self.particles:
                        self.particles.emit_overgrowth_aura(SCREEN_WIDTH // 2, 80, 22)
                    try:
                        add_essence("forest")
                        add_essence("gravity")
                    except Exception as e:
                        log_event("warning", f"mastery essence award failed: {type(e).__name__}")
                    try:
                        # subtle re-apply for any aura-aware (keeps unlock flow intact)
                        if self.player:
                            self.player.apply_grafts(self._grafts, audio=self.audio)
                    except Exception as e:
                        log_event("warning", f"mastery re-apply grafts failed: {type(e).__name__}")
                self._advance_level()

        # Tutorial hint timer decrement (when not persistent)
        if self._weapon_tutorial_timer < 999 and self._weapon_tutorial_timer > 0:
            self._weapon_tutorial_timer -= effective_dt

        # Camera + effects
        self.camera.update(self.player, effective_dt, self.level)
        # Ghosts / speedrun elevator: subtle chase camera bias toward ghost when ahead
        # gives premium "hunting your ghost" framing without stealing control
        if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost', None) and self.ghost:
            try:
                gcx = self.ghost.rect.centerx
                pcx = self.player.rect.centerx
                if abs(gcx - pcx) > 40:
                    # Bounded nudge toward ghost-biased framing, then re-clamp to world
                    # bounds (the old expression algebraically cancelled to a ~0px no-op
                    # and skipped the world-bound clamp). (N7)
                    bias = max(-120.0, min(120.0, (gcx - pcx) * 0.07))
                    self.camera.offset_x += bias * 0.05
                    self.camera.offset_x = max(-(self.level.world_width - SCREEN_WIDTH),
                                               min(0.0, self.camera.offset_x))
            except Exception as e:
                log_event("glitch", f"ghost chase camera bias failed: {type(e).__name__}")
        self.shake.update(effective_dt)
        self.particles.emit_ambient_leaves(self.camera.get_visible_rect())
        self.particles.update(effective_dt)

        self.level.bamboos.update(effective_dt)
        self.level.heals.update(effective_dt)

        self.hud.lives = self.lives
        self.hud.update(effective_dt, self.player)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        if self.state == ST_MENU:
            self.title_screen.draw(self.screen)
            return
        if self.state == ST_GROVE:
            self.grove_ui.draw(self.screen)
            return
        if self.state == ST_LEVEL_TRANS:
            if self.level_transition:
                self.level_transition.draw(self.screen)
            return
        if self.state == ST_VICTORY:
            score = self.player.score if self.player else 0
            bt = load_best_time(self.current_level) if getattr(self, 'speedrun_mode', False) else None
            # Mastery stats for end screen (grafts + essences + cleared)
            try:
                gc = len(load_grafts())
                et = sum(load_essences().values())
                om = bool(getattr(self, 'overgrown_mode', False)) or is_overgrown_mastered()
            except Exception as e:
                log_event("warning", f"victory mastery stats load failed: {type(e).__name__}")
                gc, et, om = None, None, False
            self.victory_screen.draw(self.screen, score, self._is_high_score,
                                     speedrun_time=getattr(self, '_pending_best_time', None),
                                     best_time=bt,
                                     has_ghost=bool(getattr(self, '_victory_ghost', None) or getattr(self, 'best_ghost', None)),
                                     graft_count=gc, essence_total=et, overgrown_mastered=om,
                                     splits=getattr(self, 'splits', None))
            # Replay ghost visually using GhostPanda (semi-transparent following path) when R pressed in speedrun
            if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost', None):
                g = getattr(self, '_victory_ghost', None) or getattr(self, 'best_ghost', None)
                if g and len(g) > 1:
                    t = getattr(self, 'ghost_replay_timer', 0.0)
                    # find current sample
                    sample = None
                    for s in g:
                        if s[0] <= t:
                            sample = s
                        else:
                            break
                    if sample is None:
                        sample = g[0]
                    _, gx, gy, _ = sample
                    # use improved responsive replay cam follow (now using ghost-interp driven values set in update)
                    off_x = int(getattr(self, '_replay_cam_x', gx - SCREEN_WIDTH * 0.42))
                    off_y = int(getattr(self, '_replay_cam_y', gy - SCREEN_HEIGHT * 0.52))
                    # Path overlay in victory replay -- more visible hints + split dots + progressive
                    g = getattr(self, '_victory_ghost', None) or getattr(self, 'best_ghost', None)
                    if g and len(g) > 1:
                        curr_t = getattr(self, 'ghost_replay_timer', 0.0)
                        is_pers = getattr(self, '_ghost_variant', 'best') == 'personal'
                        pcol = (85, 165, 115) if is_pers else (70, 115, 175)
                        hl = (160, 225, 175) if is_pers else (160, 200, 255)
                        for i in range(len(g)-1):
                            if g[i][0] > curr_t + 0.05:
                                break
                            x1 = int(g[i][1] + off_x)
                            y1 = int(g[i][2] + off_y)
                            x2 = int(g[i+1][1] + off_x)
                            y2 = int(g[i+1][2] + off_y)
                            pygame.draw.line(self.screen, pcol, (x1, y1), (x2, y2), 2)
                            if i % 2 == 0:
                                pygame.draw.line(self.screen, hl, (x1, y1), (x2, y2), 1)
                        # split markers on replay path too
                        gspl = getattr(self, 'ghost_splits', None) or []
                        for si, _st in gspl:
                            if si < len(g):
                                sxp = int(g[si][1] + off_x)
                                syp = int(g[si][2] + off_y)
                                pygame.draw.circle(self.screen, (255, 250, 180), (sxp, syp - 2), 3)
                    self.ghost.draw(self.screen, camera=None, offset_x=off_x, offset_y=off_y)
                    try:
                        from ui import draw_text
                        draw_text(self.screen, "GHOST REPLAY (R)", 12, (170, 190, 210), SCREEN_WIDTH // 2, SCREEN_HEIGHT - 38)
                    except Exception as e:
                        log_event("glitch", f"victory ghost replay text failed: {type(e).__name__}")
            return
        if not self.player or not self.level or not self.camera:
            return

        shake_off = self.shake.update(0)
        self.background.draw(self.screen, self.camera.offset_x)

        # Hitstop visual flash (brief bright pop for impact feedback, pairs with freeze)
        if self._hitstop_timer > 0 and self.state == ST_PLAYING:
            a = int(38 * min(1.0, self._hitstop_timer / 0.07))
            if a > 3:
                hs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                hs.fill((255, 254, 245, a))
                self.screen.blit(hs, (0, 0))

        # Chrono slow-mo tint feedback (simple, delightful world-freeze visual)
        chrono_active_draw = bool(self.player and getattr(self.player, "chrono_slow_timer", 0) > 0)
        if chrono_active_draw and self.state == ST_PLAYING:
            tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            tint.fill((120, 90, 200, 28))  # soft purple time-dilated veil
            self.screen.blit(tint, (0, 0))
            # extra juice ripple lines
            if random.random() < 0.6:
                self.particles.emit_sparkle(self.player.rect.centerx, self.player.rect.centery - 10, 3)

        render_cam_x = math.floor(self.camera.offset_x)
        render_cam_y = math.floor(self.camera.offset_y)
        cam_x = render_cam_x + shake_off[0]
        cam_y = render_cam_y + shake_off[1]
        visible = self.camera.get_visible_rect().inflate(100, 100)

        for dec in self.level.decorations:
            if dec.rect.colliderect(visible):
                self.screen.blit(dec.image, dec.rect.move(cam_x, cam_y))

        # Ice projectile trails (drawn BEFORE the shard itself for depth)
        # Perf: reuse small cached glow surfaces instead of allocating every frame
        for sprite in self.level.projectiles:
            if isinstance(sprite, IceProjectile) and sprite._trail:
                for idx, (tx, ty) in enumerate(sprite._trail):
                    alpha = int(180 * (idx + 1) / len(sprite._trail))
                    r = 4 + idx
                    glow = self._get_cached_glow(r)
                    if glow is not None:
                        # set/restore so cache entry not mutated for other uses this frame (correctness + no hidden state)
                        prev_a = glow.get_alpha()
                        glow.set_alpha(alpha)
                        self.screen.blit(
                            glow,
                            (int(tx) - r + cam_x, int(ty) - r + cam_y),
                            special_flags=pygame.BLEND_RGBA_ADD)
                        if prev_a is not None:
                            glow.set_alpha(prev_a)

        for sprite in self.level.all_sprites:
            if not sprite.rect.colliderect(visible):
                continue
            # I-frame blink for combat ONLY. Skip during level-end outro
            # (invincible_timer is set to 999s there to block damage but we
            # don't want the player flickering during the victory dance).
            if (sprite is self.player and self.player.invincible_timer > 0
                    and not self._outro_active
                    and not self.player.is_victory_dancing
                    and int(self.player.invincible_timer * 10) % 2):
                continue
            self.screen.blit(sprite.image, sprite.rect.move(cam_x, cam_y))

        # Draw best ghost (non-interacting GhostPanda sprite, semi-transparent panda frames)
        # Full system: always use GhostPanda instance for time-synced playback when best_ghost present for level
        if getattr(self, 'speedrun_mode', False) and getattr(self, 'best_ghost', None) and not getattr(self, 'ghost', None):
            self.ghost = GhostPanda(self.best_ghost, is_best=True)
            if self.ghost:
                self.ghost.reset()
                self.ghost._pidx = 0
        if getattr(self, 'ghost', None):
            # More visible path hints: thicker progressive path + split markers + distinction
            # Perf: the ghost-path hint used to draw EVERY sample's line segment
            # every frame (O(all samples)) -- the main speedrun FPS killer. Now:
            # skip entirely under reduced_motion, and cull segments/dots that fall
            # fully off-screen so the work is O(visible), not O(whole run). Output
            # is visually identical (culled draws were invisible anyway).
            if (getattr(self, 'speedrun_mode', False) and self.best_ghost
                    and len(self.best_ghost) > 1
                    and not getattr(self.particles, 'reduced_motion', False)):
                pts = self.best_ghost
                is_pers = getattr(self, '_ghost_variant', 'best') == 'personal'
                pcol = (85, 165, 115) if is_pers else (70, 115, 175)
                hlcol = (160, 225, 175) if is_pers else (160, 200, 255)
                sw, sh = SCREEN_WIDTH, SCREEN_HEIGHT
                for i in range(len(pts)-1):
                    x1 = int(pts[i][1] + cam_x)
                    y1 = int(pts[i][2] + cam_y)
                    x2 = int(pts[i+1][1] + cam_x)
                    y2 = int(pts[i+1][2] + cam_y)
                    # both endpoints past the same screen edge, with a 2px margin
                    # for the width-2 stroke (pygame extends a thick line +/-1px
                    # perpendicular) -> segment cannot paint any on-screen pixel
                    if ((x1 < -2 and x2 < -2) or (x1 > sw + 2 and x2 > sw + 2)
                            or (y1 < -2 and y2 < -2) or (y1 > sh + 2 and y2 > sh + 2)):
                        continue
                    pygame.draw.line(self.screen, pcol, (x1, y1), (x2, y2), 2)
                    if i % 2 == 0:
                        pygame.draw.line(self.screen, hlcol, (x1, y1), (x2, y2), 1)
                # visible split time hints along path (brighter dots at ghost split xs)
                if getattr(self, 'ghost_splits', None):
                    for si, st in getattr(self, 'ghost_splits', []):
                        if si < len(pts):
                            sxp = int(pts[si][1] + cam_x)
                            syp = int(pts[si][2] + cam_y)
                            if -8 <= sxp <= sw + 8 and -8 <= syp <= sh + 8:
                                pygame.draw.circle(self.screen, (255, 255, 200), (sxp, syp - 3), 3)
            self.ghost.draw(self.screen, self.camera)
            # Wild ghost visual flair in overgrown climax
            if getattr(self, 'overgrown_mode', False):
                self.particles.emit_overgrowth_aura(self.ghost.rect.centerx + cam_x, self.ghost.rect.centery + cam_y - 8, 1)
        if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost', None):
            try:
                from ui import draw_text
                g_label = "WILD GHOST" if getattr(self, 'overgrown_mode', False) else ("DAILY GHOST" if getattr(self, 'daily_mode', False) else "GHOST")
                draw_text(self.screen, g_label, 10, (200, 120, 160) if getattr(self, 'overgrown_mode', False) else (160, 180, 200), SCREEN_WIDTH // 2 + 78, 30)
            except Exception as e:
                log_event("glitch", f"ghost label HUD failed: {type(e).__name__}")

        self.particles.draw(self.screen, self.camera)

        # NPC friendly-indicator: bouncing "?" above head (universal UI affordance)

        # Wild Heart visual in overgrown climax (premium collect target)
        if getattr(self.level, "biome", "") == "overgrown" and not getattr(self, '_heart_collected', False):
            hx, hy = 7720, 255
            cx = int(hx + cam_x)
            cy = int(hy + cam_y)
            # Pulsing heart glow (climax feel)
            t = pygame.time.get_ticks() / 180.0
            r = 14 + int(4 * math.sin(t))
            pygame.draw.circle(self.screen, (255, 180, 200), (cx, cy), r)
            pygame.draw.circle(self.screen, (255, 80, 130), (cx, cy), r - 4)
            # core
            pygame.draw.circle(self.screen, (255, 220, 230), (cx, cy), 5)
        t_ms = pygame.time.get_ticks()
        for npc in self.level.npcs:
            if not npc.rect.colliderect(visible):
                continue
            # Per-NPC phase so multiple ? don't bob in lockstep
            phase = (npc.rect.x * 0.013) % (2 * math.pi)
            bounce = math.sin((t_ms / 200.0) + phase) * 5
            sx = npc.rect.centerx + cam_x
            sy = npc.rect.top + cam_y - 26 + bounce
            # Yellow bubble background (cached for perf)
            if not hasattr(self, "_npc_bubble"):
                self._npc_bubble = pygame.Surface((20, 24), pygame.SRCALPHA)
                pygame.draw.circle(self._npc_bubble, (255, 230, 80), (10, 12), 10)
                pygame.draw.circle(self._npc_bubble, (255, 180, 40), (10, 12), 10, 2)
            self.screen.blit(self._npc_bubble, (int(sx) - 10, int(sy) - 12))
            # "?" glyph
            font = get_font(18, bold=True)
            q = font.render("?", True, (70, 45, 0))
            self.screen.blit(q, q.get_rect(center=(int(sx), int(sy))))

        # Sword swing arc (rotational visual + hitbox glow)
        if self.player.is_attacking:
            self._draw_sword_arc(cam_x, cam_y)

        # Bamboo leaf parasol while gliding (juice visual)
        if self.player.is_gliding:
            self._draw_glide_leaf(cam_x, cam_y)

        # Dash afterimage trail (speed feel)
        if self.player.is_dashing:
            self._draw_dash_trail(cam_x, cam_y)

        # --- Darkness overlay (Level 7, 9, 13, 17: dark biomes) ---
        # Single-pass: one dark layer with transparent "holes" around the
        # player + each lit crystal. Crystals fade smoothly during their
        # last 1.5s of life so there's no hard on/off pop.
        if self.level.is_dark and self._dark_overlay is not None:
            dark_overlay = self._dark_overlay
            dark_overlay.fill((0, 0, 0, 230))
        elif self.level.is_dark:
            # fallback if cache not set
            dark_overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 230))
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
                    ring = self._get_cached_ring(radius, frac)
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
            font = get_font(12, bold=True)
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
                big_font = get_font(16, bold=True)
                surf = big_font.render(state_label, True, state_color)
                t_ms = pygame.time.get_ticks()
                bob = math.sin(t_ms / 150.0) * 3
                pos = surf.get_rect(center=(boss.rect.centerx + cam_x,
                                            by - 30 + bob))
                self.screen.blit(surf, pos)

        # --- Debug mode hitbox overlay ---
        if self._debug_mode:
            self._draw_debug_hitboxes(cam_x, cam_y)

        bt = None
        if getattr(self, 'best_ghost', None) and len(self.best_ghost) > 0:
            bt = self.best_ghost[-1][0]
        self.hud.draw(self.screen, self.player, self.current_level + 1, self.camera, getattr(self, 'run_timer', 0.0),
                      daily_seed=(self.daily_seed if self.daily_mode else 0),
                      best_time=bt,
                      splits=getattr(self, 'splits', None),
                      ghost_splits=getattr(self, 'ghost_splits', None))

        # Speedrun timer (top-center, large) + best + ghost chase indicator.
        if getattr(self, 'speedrun_mode', False):
            from ui import draw_text_shadow, draw_text
            t = getattr(self, 'run_timer', 0.0)
            m = int(t // 60)
            s = t % 60
            txt = f"{m}:{s:05.2f}" if m else f"{s:05.2f}"
            draw_text_shadow(self.screen, txt, 28, COL_GOLD, SCREEN_WIDTH // 2, 28, bold=True)
            bt = load_best_time(self.current_level)
            if bt is not None:
                bm = int(bt // 60)
                bs = bt % 60
                btxt = f"best {bm}:{bs:05.2f}" if bm else f"best {bs:05.2f}"
                draw_text(self.screen, btxt, 14, (200, 200, 160), SCREEN_WIDTH // 2, 46)
            # delta vs ghost time (live pace when racing best ghost) -- ensure still works
            if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost', None) and getattr(self.ghost, 'replay', None):
                try:
                    g = self.ghost
                    if g.idx < len(g.replay):
                        gt = g.replay[g.idx][0]
                        d = self.run_timer - gt
                        ahead = d <= 0.02
                        dcol = (70, 255, 130) if ahead else (255, 120, 120)
                        dstr = f"Δ{d:+.2f}" + (" AHEAD!" if ahead else "")
                        draw_text(self.screen, dstr, 13, dcol, SCREEN_WIDTH // 2 + 108, 46)
                except Exception:
                    pass
            # split times on HUD for pro visibility (current vs ghost split deltas)
            if getattr(self, 'speedrun_mode', False) and getattr(self, 'ghost_splits', None) and getattr(self, 'splits', None):
                try:
                    gs = self.ghost_splits
                    ss = getattr(self, 'splits', [])
                    if gs and ss:
                        last_i = min(len(gs)-1, len(ss)-1)
                        gi, gt = gs[last_i]
                        _, st = ss[last_i]
                        sd = st - gt
                        scol = (80, 255, 140) if sd <= 0.01 else (255, 140, 140)
                        draw_text(self.screen, f"S{last_i} Δ{sd:+.2f}", 11, scol, SCREEN_WIDTH // 2 + 185, 46)
                except Exception:
                    pass
            if getattr(self, 'best_ghost', None):
                g_label = "DAILY GHOST" if getattr(self, 'daily_mode', False) else "GHOST"
                draw_text(self.screen, g_label, 11, (160, 180, 200), SCREEN_WIDTH // 2 + 78, 30)

        # Weapon tutorial hint -- persistent banner until first use
        if (self.player.has_bamboo_weapon and not self._weapon_used):
            self._draw_weapon_hint()

        # Glide tutorial hint -- persistent banner until first glide
        if (self.player.has_glide and not self._glide_used):
            self._draw_glide_hint()

        # Ice magic tutorial hint -- persistent until first cast
        if (self.player.has_ice_magic and not self._ice_used):
            self._draw_ice_hint()

        # Dash tutorial hint -- persistent banner until first dash (#4)
        if (self.player.dash_time_remaining > 0 and not getattr(self, '_dash_used', True)):
            self._draw_dash_hint()

        # --- NPC dialog box at bottom of screen ---
        active_npc = None
        for npc in self.level.npcs:
            if npc.show_dialog:
                active_npc = npc
                break
        if active_npc is not None:
            self._draw_npc_textbox(active_npc)

        if self.state == ST_PAUSED:
            self.pause_overlay.draw(self.screen, getattr(self.player, "grafts", None),
                                    daily_seed=(self.daily_seed if self.daily_mode else 0),
                                    daily_mode=getattr(self, 'daily_mode', False))
        elif self.state == ST_GAME_OVER:
            self.game_over_screen.draw(self.screen, self.player.score)

        if self.options_open:
            self.options_overlay.draw(self.screen, self.settings)

        # Simple color filter (accessibility) -- after main scene
        self._apply_color_filter()

    def _draw_ghost(self, cam_x: int, cam_y: int) -> None:
        """Playback best ghost as semi-transparent panda. Step sampling. Uses frames from generate_panda_frames."""
        if not getattr(self, 'best_ghost', None) or not getattr(self, '_panda_frames', None):
            return
        t = getattr(self, 'run_timer', 0.0)
        sample = None
        for s in self.best_ghost:
            if s[0] <= t:
                sample = s
            else:
                break
        if sample is None:
            sample = self.best_ghost[0]
        _, gx, gy, facing = sample
        frames = self._panda_frames
        state = "run" if len(self.best_ghost) > 3 and abs(self.best_ghost[-1][1] - self.best_ghost[0][1]) > 25 else "idle"
        lst = frames.get(state, frames.get("idle", []))
        if not lst:
            return
        # Light animation from Player frames (use time for frame index) -- reuses Player art exactly
        frame_idx = int(t * (10 if state == "run" else 2)) % len(lst)
        frame = lst[frame_idx]
        if not facing:
            frame = pygame.transform.flip(frame, True, False)
        ghost = frame.copy()
        ghost.set_alpha(GHOST_ALPHA)
        self.screen.blit(ghost, (int(gx + cam_x), int(gy + cam_y)))

    def _draw_victory_ghost(self) -> None:
        """Replay the completed ghost run during victory (follow-cam + animated alpha panda using Player frames)."""
        g = getattr(self, '_victory_ghost', None) or getattr(self, 'best_ghost', None)
        if not g or not getattr(self, '_panda_frames', None):
            return
        t = getattr(self, 'ghost_replay_timer', 0.0)
        sample = None
        for s in g:
            if s[0] <= t:
                sample = s
            else:
                break
        if sample is None:
            sample = g[0]
        _, gx, gy, facing = sample
        cam_x = int(gx) - int(SCREEN_WIDTH * 0.38)
        cam_y = -40
        frames = self._panda_frames
        span = abs(g[-1][1] - g[0][1]) if len(g) > 1 else 0
        state = "run" if span > 25 else "idle"
        lst = frames.get(state, frames.get("idle", []))
        if not lst:
            return
        frame_idx = int(t * (10 if state == "run" else 2)) % len(lst)
        frame = lst[frame_idx]
        if not facing:
            frame = pygame.transform.flip(frame, True, False)
        ghost = frame.copy()
        ghost.set_alpha(GHOST_ALPHA)
        self.screen.blit(ghost, (int(gx + cam_x), int(gy + cam_y)))
        try:
            from ui import draw_text
            draw_text(self.screen, "GHOST REPLAY", 12, (170, 190, 210), SCREEN_WIDTH // 2, SCREEN_HEIGHT - 38)
        except Exception as e:
            log_event("glitch", f"victory ghost replay text failed: {type(e).__name__}")

    def _make_dummy_ghost(self) -> list[list]:
        """Generate a simple straight-line dummy ghost for testing the feature without a prior saved run."""
        dummy: list[list] = []
        start_x = 80
        y = FLOOR_Y - 4
        for i in range(16):
            t = i * 0.2
            x = start_x + i * 55
            dummy.append([t, float(x), float(y), True])
        return dummy

    def _draw_sword_arc(self, cam_x: int, cam_y: int) -> None:
        """Bamboo sword STAB: horizontal thrust forward then retract."""
        total = 0.25
        t = 1.0 - (self.player.attack_timer / total)
        t = max(0.0, min(1.0, t))

        # Stab motion: fast out, hold max, quick retract
        if t < 0.2:
            reach = t / 0.2
        elif t < 0.7:
            reach = 1.0
        else:
            reach = 1.0 - (t - 0.7) / 0.3
        thrust_px = int(36 * reach)

        # Build sword-shaped surface (horizontal, katana)
        SW, SH = 90, 18
        sword = pygame.Surface((SW, SH), pygame.SRCALPHA)
        # Pommel (dark brown ball)
        pygame.draw.circle(sword, (60, 35, 20), (5, SH // 2), 5)
        # Handle (wrapped dark red / diamond pattern)
        pygame.draw.rect(sword, (120, 45, 35), (8, 6, 20, 6))
        for i in range(10, 28, 3):
            pygame.draw.line(sword, (60, 20, 15), (i, 6), (i, 12), 1)
        # Guard (tsuba) -- round gold disk
        pygame.draw.circle(sword, (200, 170, 70), (30, SH // 2), 7)
        pygame.draw.circle(sword, (240, 210, 110), (30, SH // 2), 5)
        pygame.draw.circle(sword, (140, 100, 30), (30, SH // 2), 7, 1)
        # Blade (bright bamboo-green, tapered katana shape)
        blade_pts = [
            (36, 6),             # base top
            (SW - 10, 3),        # tip top
            (SW - 2, SH // 2),   # sharp tip
            (SW - 10, SH - 4),   # tip bottom
            (36, SH - 6),        # base bottom
        ]
        pygame.draw.polygon(sword, (150, 220, 110), blade_pts)
        # Blade highlight stripe (gives the "shine")
        pygame.draw.polygon(sword, (220, 255, 180), [
            (36, 7), (SW - 12, 5), (SW - 4, SH // 2 - 1), (36, SH // 2 - 1)])
        # Blade dark edge
        pygame.draw.polygon(sword, (80, 150, 60), [
            (36, SH // 2 + 1), (SW - 4, SH // 2 + 1),
            (SW - 12, SH - 5), (36, SH - 7)])
        # Bamboo joint rings on blade (every 15px)
        for jx in range(46, SW - 10, 14):
            pygame.draw.line(sword, (70, 140, 50),
                             (jx, 6), (jx, SH - 6), 1)
        # Leaf flourish at tip
        pygame.draw.polygon(sword, (80, 160, 55),
                            [(SW - 4, SH // 2 - 3),
                             (SW - 10, SH // 2 - 8),
                             (SW - 14, SH // 2 - 1)])

        # Horizontal stab: sword held level, extends outward from body
        if not self.player.facing_right:
            sword = pygame.transform.flip(sword, True, False)
        # Slight downward tilt so it looks like a thrust, not a pole
        sword_img = pygame.transform.rotate(sword, -5 if self.player.facing_right else 5)
        # Position: sword base at player's hand, extending by thrust_px
        sw, sh = sword_img.get_size()
        if self.player.facing_right:
            # Sword extends to the right from hand
            sx = self.player.rect.right + cam_x + thrust_px - 8
            sy = self.player.rect.centery + cam_y - sh // 2
        else:
            # Sword extends to the left from hand
            sx = self.player.rect.left + cam_x - sw - thrust_px + 8
            sy = self.player.rect.centery + cam_y - sh // 2
        self.screen.blit(sword_img, (sx, sy))

        # Speed streak during the thrust-out phase (t < 0.5)
        if t < 0.5 and thrust_px > 8:
            streak = pygame.Surface((thrust_px + 16, 4), pygame.SRCALPHA)
            streak.fill((255, 250, 200, 180))
            if self.player.facing_right:
                stx = self.player.rect.right + cam_x - 4
            else:
                stx = self.player.rect.left + cam_x - thrust_px - 12
            sty = self.player.rect.centery + cam_y - 2
            self.screen.blit(streak, (stx, sty))

        # Impact sparkle at tip at max reach
        if 0.4 < t < 0.6:
            if self.player.facing_right:
                tip_x = sx + sw - 6
            else:
                tip_x = sx + 6
            tip_y = sy + sh // 2
            for _ in range(3):
                px = tip_x + random.randint(-4, 4)
                py = tip_y + random.randint(-4, 4)
                pygame.draw.circle(self.screen, (255, 255, 180), (px, py), 2)

    def _draw_weapon_hint(self) -> None:
        """Persistent banner teaching the player how to attack."""
        # Pulsing alpha to draw attention
        t = pygame.time.get_ticks() / 200.0
        alpha = int(180 + 55 * math.sin(t))
        font_big = get_font(22, bold=True)
        font_small = get_font(14)
        title = font_big.render("BAMBOO STAFF EQUIPPED!", True, (255, 230, 120))
        hint = font_small.render("Press  [ E ]  or  LEFT CLICK  to swing",
                                 True, (230, 230, 230))
        w = max(title.get_width(), hint.get_width()) + 32
        h = 58
        bx = (SCREEN_WIDTH - w) // 2
        by = 96
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((20, 20, 30, alpha))
        pygame.draw.rect(bg, (255, 220, 120), (0, 0, w, h), 3, border_radius=6)
        self.screen.blit(bg, (bx, by))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, by + 18)))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, by + 42)))

    def _draw_glide_hint(self) -> None:
        """Persistent banner teaching the player how to glide."""
        t = pygame.time.get_ticks() / 200.0
        alpha = int(180 + 55 * math.sin(t))
        font_big = get_font(22, bold=True)
        font_small = get_font(14)
        title = font_big.render("GLIDE UNLOCKED!", True, (140, 220, 255))
        hint = font_small.render(
            "Hold  [ JUMP ]  while falling to glide!", True, (230, 230, 230))
        w = max(title.get_width(), hint.get_width()) + 32
        h = 58
        bx = (SCREEN_WIDTH - w) // 2
        # Stack below weapon hint if both are showing
        by = 160 if (self.player.has_bamboo_weapon
                     and not self._weapon_used) else 96
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((15, 25, 40, alpha))
        pygame.draw.rect(bg, (140, 220, 255), (0, 0, w, h), 3, border_radius=6)
        self.screen.blit(bg, (bx, by))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, by + 18)))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, by + 42)))

    def _draw_ice_hint(self) -> None:
        """Persistent banner teaching the player how to cast ice."""
        t = pygame.time.get_ticks() / 200.0
        alpha = int(180 + 55 * math.sin(t))
        font_big = get_font(22, bold=True)
        font_small = get_font(14)
        title = font_big.render("ICE MAGIC UNLOCKED!", True, (140, 220, 255))
        hint = font_small.render(
            "Press  [ R ]  to cast Ice Shard  (10s cooldown)",
            True, (230, 230, 230))
        w = max(title.get_width(), hint.get_width()) + 32
        h = 58
        bx = (SCREEN_WIDTH - w) // 2
        # Stack below other hints if showing
        offset = 0
        if self.player.has_bamboo_weapon and not self._weapon_used:
            offset += 64
        if self.player.has_glide and not self._glide_used:
            offset += 64
        by = 96 + offset
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((15, 25, 40, alpha))
        pygame.draw.rect(bg, (140, 220, 255), (0, 0, w, h), 3, border_radius=6)
        self.screen.blit(bg, (bx, by))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, by + 18)))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, by + 42)))

    def _draw_dash_hint(self) -> None:
        """Persistent banner teaching the player how to dash (Shift)."""
        t = pygame.time.get_ticks() / 200.0
        alpha = int(180 + 55 * math.sin(t))
        font_big = get_font(22, bold=True)
        font_small = get_font(14)
        title = font_big.render("DASH BOOTS!", True, (255, 180, 100))
        hint = font_small.render("Press  [ SHIFT ]  to dash", True, (230, 230, 230))
        w = max(title.get_width(), hint.get_width()) + 32
        h = 58
        bx = (SCREEN_WIDTH - w) // 2
        # Stack below any other hints currently showing
        offset = 0
        if self.player.has_bamboo_weapon and not self._weapon_used:
            offset += 64
        if self.player.has_glide and not self._glide_used:
            offset += 64
        if self.player.has_ice_magic and not self._ice_used:
            offset += 64
        by = 96 + offset
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((30, 22, 15, alpha))
        pygame.draw.rect(bg, (255, 180, 100), (0, 0, w, h), 3, border_radius=6)
        self.screen.blit(bg, (bx, by))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, by + 18)))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, by + 42)))

    def _draw_glide_leaf(self, cam_x: int, cam_y: int) -> None:
        """Draw a large bamboo leaf parasol above the panda while gliding."""
        px = self.player.rect.centerx + cam_x
        py = self.player.rect.top + cam_y - 6
        t = pygame.time.get_ticks() / 400.0
        sway = math.sin(t) * 8
        # Leaf shape: wide ellipse with stem
        LW, LH = 52, 18
        leaf = pygame.Surface((LW, LH + 6), pygame.SRCALPHA)
        # Main leaf body
        pygame.draw.ellipse(leaf, (70, 160, 50), (0, 0, LW, LH))
        pygame.draw.ellipse(leaf, (90, 190, 65), (4, 2, LW - 8, LH - 4))
        # Central vein
        pygame.draw.line(leaf, (50, 120, 35), (LW // 2, 2), (LW // 2, LH - 2), 2)
        # Side veins
        for i in range(3):
            vx = 10 + i * 10
            pygame.draw.line(leaf, (55, 130, 40),
                             (LW // 2, 4 + i * 4), (vx, LH - 4), 1)
            pygame.draw.line(leaf, (55, 130, 40),
                             (LW // 2, 4 + i * 4), (LW - vx, LH - 4), 1)
        # Stem connecting to panda
        pygame.draw.line(leaf, (80, 130, 40),
                         (LW // 2, LH), (LW // 2, LH + 6), 2)
        # Sway rotation
        angle = sway * 0.6
        rotated = pygame.transform.rotate(leaf, angle)
        rw, rh = rotated.get_size()
        self.screen.blit(rotated, (int(px - rw // 2 + sway * 0.5),
                                   int(py - rh)))

    def _draw_dash_trail(self, cam_x: int, cam_y: int) -> None:
        """Draw speed afterimages behind the panda while dashing."""
        if not self.player.image:
            return
        direction = self.player.dash_direction
        for i in range(3):
            offset_x = int(-direction * (16 + i * 14))
            alpha = 120 - i * 40
            ghost = self.player.image.copy()
            # Tint green for bamboo-chi feel
            tint = pygame.Surface(ghost.get_size(), pygame.SRCALPHA)
            tint.fill((80, 200, 80, alpha))
            ghost.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            gx = self.player.rect.x + cam_x + offset_x
            gy = self.player.rect.y + cam_y
            self.screen.blit(ghost, (gx, gy))
        # Speed lines
        for i in range(4):
            ly = self.player.rect.centery + cam_y + random.randint(-12, 12)
            lx = self.player.rect.centerx + cam_x - int(direction * 20)
            llen = random.randint(10, 25)
            streak = pygame.Surface((llen, 2), pygame.SRCALPHA)
            streak.fill((180, 255, 140, 140))
            self.screen.blit(streak, (lx - int(direction * llen), ly))

    def _draw_npc_textbox(self, npc) -> None:
        """Full-width text box at bottom of screen for NPC dialog."""
        box_h = 90
        box_y = SCREEN_HEIGHT - box_h - 8
        box_x = 20
        box_w = SCREEN_WIDTH - 40
        # Background panel with border
        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((15, 15, 25, 230))
        pygame.draw.rect(bg, (255, 220, 120, 200), (0, 0, box_w, box_h), 3,
                         border_radius=8)
        self.screen.blit(bg, (box_x, box_y))
        # Name tab in corner
        name_font = get_font(18, bold=True)
        name_surf = name_font.render(npc.name, True, (255, 220, 120))
        name_bg = pygame.Surface((name_surf.get_width() + 20, 24), pygame.SRCALPHA)
        name_bg.fill((40, 30, 20, 240))
        pygame.draw.rect(name_bg, (255, 220, 120),
                        (0, 0, name_bg.get_width(), 24), 2, border_radius=4)
        self.screen.blit(name_bg, (box_x + 12, box_y - 12))
        self.screen.blit(name_surf, (box_x + 22, box_y - 8))
        # Dialog text (render all lines stacked)
        text_font = get_font(16)
        for i, line in enumerate(npc.dialog_lines):
            line_surf = text_font.render(line, True, (235, 235, 235))
            self.screen.blit(line_surf, (box_x + 24, box_y + 22 + i * 22))

    def _get_cached_glow(self, r: int) -> pygame.Surface | None:
        """Perf cache: small reusable SRCALPHA glow surfaces for trails (ice, etc.)."""
        if r not in self._glow_cache:
            sz = max(2, int(r * 2))
            s = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(s, (160, 220, 255, 255), (r, r), r)
            self._glow_cache[r] = s
        return self._glow_cache.get(r)

    def _get_cached_ring(self, radius: int, frac: float) -> pygame.Surface:
        """Perf: cache ring surfaces for dark biome crystal fade (avoid alloc per fading crystal per frame)."""
        key = (radius, int(frac * 10))
        if key not in self._glow_cache:  # reuse glow dict to avoid new attr; value is ring
            # store under negative or separate, but simple: use a side dict if needed. for min change use dedicated
            pass
        # use dedicated to not collide keys
        if not hasattr(self, '_ring_cache'):
            self._ring_cache = {}
        if key not in self._ring_cache:
            rs = max(4, int(radius * 2 + 4))
            ring = pygame.Surface((rs, rs), pygame.SRCALPHA)
            pygame.draw.circle(ring, (0, 0, 0, int(115 * frac)), (radius + 2, radius + 2), radius)
            pygame.draw.circle(ring, (0, 0, 0, 0), (radius + 2, radius + 2), int(radius * 0.7))
            self._ring_cache[key] = ring
        return self._ring_cache[key]

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
        font = get_font(14, bold=True)
        info = font.render("DEBUG [TAB] | RED=hitbox GREEN=player CYAN=goal YELLOW=pickup",
                           True, (255, 255, 255))
        info_bg = pygame.Surface((info.get_width() + 10, info.get_height() + 4),
                                pygame.SRCALPHA)
        info_bg.fill((0, 0, 0, 180))
        self.screen.blit(info_bg, (4, SCREEN_HEIGHT - 22))
        self.screen.blit(info, (8, SCREEN_HEIGHT - 20))

    def _apply_color_filter(self) -> None:
        """Simple post-draw color filter for accessibility (low risk blend)."""
        if self.options_open:
            return  # don't tint the menu
        filt = self.settings.get("color_filter", 0)
        if filt == 0:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        if filt == 1:  # grayscale-ish
            overlay.fill((180, 180, 180, 45))
            self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        elif filt == 2:  # warm
            overlay.fill((255, 210, 160, 35))
            self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        elif filt == 3:  # high contrast rough
            overlay.fill((0, 0, 0, 20))
            self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            overlay.fill((255, 255, 255, 25))
            self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


async def main() -> None:
    """Async entry point for Pygbag/WASM."""
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
