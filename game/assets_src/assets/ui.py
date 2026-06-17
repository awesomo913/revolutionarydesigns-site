"""Title screen, HUD, transitions, and overlays."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from config import (
    COL_BAMBOO, COL_BLACK, COL_GOLD, COL_HP_GREEN, COL_HP_RED, COL_HUD_BG,
    COL_MENU_BG, COL_RED, COL_WHITE, LEVEL_NAMES, SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from save import get_best_score

if TYPE_CHECKING:
    from engine import Camera
    from sprites import Player

# ---------------------------------------------------------------------------
# Font cache
# ---------------------------------------------------------------------------

_font_cache: dict[tuple[int, bool], pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return _font_cache[key]


def draw_text(screen: pygame.Surface, text: str, size: int,
              color: tuple, cx: int, cy: int, bold: bool = False) -> None:
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=(cx, cy)))


def draw_text_shadow(screen: pygame.Surface, text: str, size: int,
                     color: tuple, cx: int, cy: int, bold: bool = False) -> None:
    draw_text(screen, text, size, (0, 0, 0), cx + 2, cy + 2, bold)
    draw_text(screen, text, size, color, cx, cy, bold)


def draw_text_left(screen: pygame.Surface, text: str, size: int,
                   color: tuple, x: int, cy: int, bold: bool = False) -> None:
    font = get_font(size, bold)
    surf = font.render(text, True, color)
    screen.blit(surf, surf.get_rect(midleft=(x, cy)))


# ---------------------------------------------------------------------------
# Mini bamboo icon for HUD
# ---------------------------------------------------------------------------

def _draw_bamboo_icon(screen: pygame.Surface, x: int, y: int,
                      checked: bool = False) -> None:
    """Small 10x16 bamboo with optional checkmark."""
    c = COL_BAMBOO if not checked else (180, 180, 180)
    pygame.draw.rect(screen, c, (x + 3, y, 4, 16))
    pygame.draw.rect(screen, (50, 120, 0), (x + 2, y + 5, 6, 2))
    pygame.draw.rect(screen, (50, 120, 0), (x + 2, y + 11, 6, 2))
    if checked:
        # Green checkmark overlay
        pygame.draw.line(screen, (50, 220, 50), (x + 1, y + 8), (x + 4, y + 12), 2)
        pygame.draw.line(screen, (50, 220, 50), (x + 4, y + 12), (x + 9, y + 3), 2)


# ---------------------------------------------------------------------------
# Floating score text
# ---------------------------------------------------------------------------

class FloatingText:
    def __init__(self, text: str, x: float, y: float, color: tuple) -> None:
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life: float = 1.0
        self.max_life: float = 1.0

    def update(self, dt: float) -> bool:
        self.y -= 60 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        sx, sy = camera.apply_pos(self.x, self.y)
        alpha = max(0, int(255 * (self.life / self.max_life)))
        font = get_font(22, bold=True)
        surf = font.render(self.text, True, self.color)
        alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        alpha_surf.blit(surf, (0, 0))
        alpha_surf.set_alpha(alpha)
        screen.blit(alpha_surf, alpha_surf.get_rect(center=(int(sx), int(sy))))


# ---------------------------------------------------------------------------
# HUD with bamboo counter
# ---------------------------------------------------------------------------

class HUD:
    def __init__(self) -> None:
        self.displayed_hp: float = 100.0
        self.floating_texts: list[FloatingText] = []
        self.combo_display_timer: float = 0.0
        self.combo_scale: float = 1.0
        self.total_bamboos: int = 0
        self.collected_bamboos: int = 0
        self.lives: int = 3

    def set_bamboo_count(self, total: int) -> None:
        self.total_bamboos = total
        self.collected_bamboos = 0

    def on_bamboo_collected(self) -> None:
        self.collected_bamboos += 1

    def update(self, dt: float, player: Player) -> None:
        diff = player.health - self.displayed_hp
        self.displayed_hp += diff * min(1.0, 6 * dt)
        if self.combo_display_timer > 0:
            self.combo_display_timer -= dt
        self.combo_scale = max(1.0, self.combo_scale - 2 * dt)
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

    def draw(self, screen: pygame.Surface, player: Player,
             level_num: int, camera: Camera) -> None:
        # HUD backing (tall if mana bar visible)
        hud_h = 100 if player.has_ice_magic else 85
        hud_surf = pygame.Surface((260, hud_h), pygame.SRCALPHA)
        hud_surf.fill((*COL_HUD_BG, 190))
        pygame.draw.rect(hud_surf, (60, 60, 60, 100),
                        (0, 0, 260, hud_h), 2, border_radius=8)
        screen.blit(hud_surf, (8, 8))

        # HP label + bar
        draw_text(screen, "HP", 18, COL_WHITE, 30, 28)
        pygame.draw.rect(screen, COL_HP_RED, (48, 20, 150, 14), border_radius=4)
        fill_w = max(0, int(self.displayed_hp * 1.5))
        if fill_w > 0:
            pygame.draw.rect(screen, COL_HP_GREEN, (48, 20, fill_w, 14), border_radius=4)
        # HP text
        draw_text(screen, f"{int(self.displayed_hp)}", 14, COL_WHITE, 123, 28)

        # Mana bar (only shown if player has ice magic unlocked)
        if player.has_ice_magic:
            draw_text(screen, "MP", 14, COL_WHITE, 30, 44)
            # Background
            pygame.draw.rect(screen, (40, 40, 70), (48, 40, 150, 10),
                            border_radius=3)
            mana_w = max(0, int(player.mana * 1.5))
            if mana_w > 0:
                # Cyan gradient
                col = (80, 180, 240) if player.mana >= player.mana_max else (60, 140, 200)
                pygame.draw.rect(screen, col, (48, 40, mana_w, 10),
                                border_radius=3)
                # Bright edge highlight
                pygame.draw.rect(screen, (180, 230, 255),
                                (48, 40, mana_w, 2), border_radius=2)
            # "READY" indicator when full
            if player.mana >= player.mana_max:
                t = pygame.time.get_ticks() / 200.0
                pulse = 0.7 + 0.3 * math.sin(t)
                pygame.draw.circle(screen,
                                  (int(255 * pulse), 255, int(255 * pulse)),
                                  (207, 45), 3)

        # Score (shift down if mana bar visible)
        score_y = 65 if player.has_ice_magic else 50
        draw_text(screen, f"SCORE: {player.score}", 20, COL_GOLD, 138, score_y, bold=True)

        # Bamboo counter with checkmark icons
        bx = 22
        by = 80 if player.has_ice_magic else 65
        for i in range(min(self.total_bamboos, 12)):
            checked = i < self.collected_bamboos
            _draw_bamboo_icon(screen, bx + i * 14, by, checked)
        if self.total_bamboos > 12:
            draw_text(screen, f"{self.collected_bamboos}/{self.total_bamboos}",
                      14, COL_BAMBOO, bx + 12 * 14 + 20, by + 8)
        else:
            draw_text(screen, f"{self.collected_bamboos}/{self.total_bamboos}",
                      14, (150, 220, 150), bx + self.total_bamboos * 14 + 15, by + 8)

        # Level indicator
        draw_text_shadow(screen, f"LEVEL {level_num}", 20, COL_WHITE,
                         SCREEN_WIDTH - 60, 25)

        # Lives display (panda head icons)
        lives_x = SCREEN_WIDTH - 100
        lives_y = 45
        draw_text(screen, "LIVES:", 14, (180, 180, 180), lives_x - 5, lives_y)
        for li in range(self.lives):
            lx = lives_x + 28 + li * 20
            pygame.draw.circle(screen, (240, 240, 235), (lx, lives_y), 7)
            pygame.draw.circle(screen, (30, 30, 30), (lx - 2, lives_y - 1), 2)
            pygame.draw.circle(screen, (30, 30, 30), (lx + 2, lives_y - 1), 2)

        # Power-up indicators (below lives) -- show countdown timers
        pwr_y = lives_y + 18
        pwr_x = SCREEN_WIDTH - 100
        if player.glide_time_remaining > 0:
            gt = int(player.glide_time_remaining)
            col = (140, 220, 255) if gt > 3 else (255, 100, 100)
            # Cyan feather icon
            pygame.draw.polygon(screen, col, [
                (pwr_x, pwr_y), (pwr_x + 4, pwr_y - 10),
                (pwr_x + 8, pwr_y)])
            draw_text(screen, f"GLIDE {gt}s", 11, col, pwr_x + 14, pwr_y - 2)
            pwr_x += 75
        if player.dash_time_remaining > 0:
            dt_ = int(player.dash_time_remaining)
            col = (255, 180, 100) if dt_ > 5 else (255, 100, 100)
            draw_text(screen, f"DASH {dt_}s", 11, col, pwr_x, pwr_y - 2)
            pwr_x += 60
        if player.has_bamboo_weapon:
            wt = int(player.weapon_time_remaining)
            col = (255, 230, 120) if wt > 10 else (255, 100, 80)
            draw_text(screen, f"SWORD {wt}s", 11, col, pwr_x, pwr_y - 2)

        # Combo counter
        if player.combo_count > 1:
            sz = int(28 * self.combo_scale)
            draw_text_shadow(screen, f"x{player.combo_count}!", sz, COL_GOLD,
                             SCREEN_WIDTH // 2, 30, bold=True)

        # Persistent controls hint at bottom-right (always visible during play)
        hint_font = get_font(11)
        hint = hint_font.render(
            "ESC pause  |  F11 fullscreen", True, (150, 170, 150))
        screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 8,
                           SCREEN_HEIGHT - 16))

        # Floating texts
        for ft in self.floating_texts:
            ft.draw(screen, camera)

    def add_floating_text(self, text: str, x: float, y: float,
                          color: tuple = COL_GOLD) -> None:
        self.floating_texts.append(FloatingText(text, x, y, color))
        self.combo_display_timer = 1.0
        self.combo_scale = 1.5


# ---------------------------------------------------------------------------
# Character showcase - generate actual sprite previews at import time
# ---------------------------------------------------------------------------

_sprite_cache: dict[str, pygame.Surface] | None = None


def _get_sprite_cache() -> dict[str, pygame.Surface]:
    """Lazy-init sprite previews (needs pygame.display to be set)."""
    global _sprite_cache
    if _sprite_cache is not None:
        return _sprite_cache

    from sprites import (
        generate_panda_frames, _generate_mushroom_frames,
        _generate_chaser_frames, _generate_slime_frames,
        _generate_flying_frames, generate_mutant_boss,
    )

    _sprite_cache = {}

    panda_frames = generate_panda_frames()
    _sprite_cache["panda"] = pygame.transform.scale(panda_frames["idle"][0], (54, 66))

    mush = _generate_mushroom_frames()[0]
    _sprite_cache["mushroom"] = pygame.transform.scale(mush, (54, 54))

    chase = _generate_chaser_frames()[0]
    _sprite_cache["panther"] = pygame.transform.scale(chase, (66, 54))

    slime = _generate_slime_frames()[0]
    _sprite_cache["slime"] = pygame.transform.scale(slime, (54, 50))

    bat = _generate_flying_frames()[0]
    _sprite_cache["bat"] = pygame.transform.scale(bat, (54, 44))

    _sprite_cache["boss"] = pygame.transform.scale(generate_mutant_boss(90, 90), (66, 66))

    # Biome enemies (level 4-8)
    from biomes import (SulfurSlime, AshBat, KelpCrab, BasaltGolem,
                        DustDevil, CactusScorpion, StalactiteSpider,
                        FalseGlowworm, BrineShard, ReflectionPhantom,
                        SporePuffer, MagmaLeaper, TidalCrab, PhaseWraith,
                        GravityDrone, HomingSpecter, ForgeHammer, VoidEater)
    from config import FLOOR_Y
    _sprite_cache["sulfur"] = pygame.transform.scale(SulfurSlime(0, FLOOR_Y).image, (54, 50))
    _sprite_cache["ashbat"] = pygame.transform.scale(AshBat(0, FLOOR_Y).image, (54, 44))
    _sprite_cache["crab"] = pygame.transform.scale(KelpCrab(0, FLOOR_Y).image, (54, 36))
    _sprite_cache["golem"] = pygame.transform.scale(BasaltGolem(0, FLOOR_Y).image, (45, 66))
    _sprite_cache["dust"] = pygame.transform.scale(DustDevil(0, FLOOR_Y).image, (45, 66))
    _sprite_cache["scorp"] = pygame.transform.scale(CactusScorpion(0, FLOOR_Y).image, (54, 42))
    _sprite_cache["spider"] = pygame.transform.scale(StalactiteSpider(0, 0).image, (42, 30))
    _sprite_cache["glow"] = pygame.transform.scale(FalseGlowworm(0, 0).image, (32, 32))
    _sprite_cache["brine"] = pygame.transform.scale(BrineShard(0, FLOOR_Y).image, (32, 54))
    _sprite_cache["phantom"] = pygame.transform.scale(ReflectionPhantom(0, FLOOR_Y).image, (54, 54))
    # Levels 14-18 new enemies
    _sprite_cache["puffer"] = pygame.transform.scale(SporePuffer(0, FLOOR_Y).image, (42, 50))
    _sprite_cache["leaper"] = pygame.transform.scale(MagmaLeaper(0, FLOOR_Y).image, (45, 45))
    _sprite_cache["tidalcrab"] = pygame.transform.scale(TidalCrab(0, FLOOR_Y).image, (45, 33))
    _sprite_cache["wraith"] = pygame.transform.scale(PhaseWraith(0, FLOOR_Y).image, (45, 60))
    _sprite_cache["drone"] = pygame.transform.scale(GravityDrone(0, FLOOR_Y).image, (45, 45))
    _sprite_cache["specter"] = pygame.transform.scale(HomingSpecter(0, FLOOR_Y).image, (51, 42))
    _sprite_cache["hammer"] = pygame.transform.scale(ForgeHammer(0, 400).image, (72, 48))
    _sprite_cache["voideater"] = pygame.transform.scale(VoidEater(0, FLOOR_Y).image, (54, 54))

    return _sprite_cache


_CHARACTERS = [
    {"name": "Pain-da", "role": "HERO", "desc": "Exiled warrior of the grove",
     "key": "panda", "color": (220, 240, 220),
     "story": "Once the protector of the sacred Bamboo Grove, Pain-da was cast out when corruption tainted the forest. Armed only with bamboo, fury, and a questionable haircut, he returns to reclaim every biome from the mutant invaders. He jumps twice, dashes through danger, glides over pits, slams from above, and throws bamboo shurikens. He also dances when he wins.\n\nTIP: Stomp enemies from above. Pick up the bamboo staff to swing melee."},
    {"name": "Shroomba", "role": "PATROL", "desc": "Twisted fungus guardian",
     "key": "mushroom", "color": (220, 100, 100),
     "story": "A once-peaceful mushroom, corrupted by the spores of the Mutant King. Walks back and forth along a short patrol route, scowling. Slow but hits hard if you bump into its cap.\n\nHOW TO BEAT: Jump on its head. One stomp kills it. Avoid running into its side."},
    {"name": "Shadow", "role": "CHASER", "desc": "Shadowblade of the forest",
     "key": "panther", "color": (180, 255, 100),
     "story": "A sleek panther that slipped into the grove from the shadow realm. Its glowing eyes lock onto Pain-da whenever he's nearby -- it chases fast and doesn't stop until it catches you or you lose it.\n\nHOW TO BEAT: Jump over its head when it closes in, then stomp. Dash to escape if cornered."},
    {"name": "Blobby", "role": "BOUNCER", "desc": "Cute acid jelly",
     "key": "slime", "color": (100, 230, 140),
     "story": "Don't let the smile fool you. Blobby bounces in random arcs and leaves no trail -- but contact is lethal acid. The Mutant's bioweapon, too cute to hate, too dangerous to ignore.\n\nHOW TO BEAT: Time your jump for when Blobby is mid-hop. Stomp on the top of the bounce."},
    {"name": "Nightwing", "role": "FLYER", "desc": "Spiked bat -- can't be stomped",
     "key": "bat", "color": (170, 120, 230),
     "story": "Razor-winged bat with poisonous spikes on its back. Cannot be stomped -- try and you'll impale yourself. Flies in loose sine patterns through the sky.\n\nHOW TO BEAT: Do NOT jump on it. Use the bamboo staff (E) or shuriken (Q) from a safe distance, or just avoid it."},
    {"name": "The Mutant", "role": "BOSS", "desc": "Stomp only when stunned",
     "key": "boss", "color": (255, 120, 120),
     "story": "The fallen king of the forest, twisted by dark spores into a hulking mutant. Patrols, then charges at Pain-da. After each charge it stuns itself -- that's your only window to hit it.\n\nHOW TO BEAT: Dodge the charge, then stomp the BLUE (stunned) boss. 5 hits to defeat. Landing on its head at any other time is safe but deals no damage."},
    {"name": "Sulfurite", "role": "TOXIC", "desc": "Leaves poison trail",
     "key": "sulfur", "color": (200, 200, 40),
     "story": "A volcanic slime of liquid sulfur. Crawls slowly but drools an acid pool behind it that burns for 3 seconds. The Caldera's living trap.\n\nHOW TO BEAT: Stomp it directly. Jump OVER the yellow puddles it leaves -- don't step in them."},
    {"name": "Ash-Swoop", "role": "SWOOPER", "desc": "Dives at airborne prey",
     "key": "ashbat", "color": (120, 80, 70),
     "story": "Born of volcanic ash. Hovers in place until it senses you in the air -- then swoops down in a straight dive at your jump apex. A punishment for clumsy platforming.\n\nHOW TO BEAT: Jump at it to stomp on the way down. If it's swooping, dash under it horizontally."},
    {"name": "Kelp-Shell", "role": "ARMORED", "desc": "Stomp only -- sides bounce you off!",
     "key": "crab", "color": (180, 80, 60),
     "story": "Armored basalt crab with an impenetrable hard shell on all sides but the top. Side collisions do damage AND bounce you off.\n\nHOW TO BEAT: Come from above. Side hits = YOU take damage. The bamboo staff hits from the side work fine though."},
    {"name": "Column-Doom", "role": "AMBUSH", "desc": "Pillar that strikes when close",
     "key": "golem", "color": (90, 90, 110),
     "story": "Disguised as a harmless basalt column. When Pain-da comes within 80 pixels, it reveals glowing eyes and lunges horizontally toward him at high speed. Then cools for 2 seconds before retracting.\n\nHOW TO BEAT: Approach cautiously. When it telegraphs (reveals eyes), JUMP -- either over it or onto its head to stomp."},
    {"name": "Duster", "role": "DODGE", "desc": "Invincible vortex -- dodge!",
     "key": "dust", "color": (200, 180, 140),
     "story": "A desert dust-devil animated by old magic. Completely invincible. Moves in erratic sine-wave patterns across the rift. Does damage on contact.\n\nHOW TO BEAT: You can't kill it. You MUST evade. Watch its movement pattern, wait for a gap, dash through."},
    {"name": "Needler", "role": "RANGED", "desc": "Fires 45-degree thorns",
     "key": "scorp", "color": (160, 120, 60),
     "story": "Cactus-scorpion hybrid with a thorn-loaded tail. Fires a projectile every 2 seconds at a 45-degree upward arc.\n\nHOW TO BEAT: Stomp it from above. Watch for incoming thorns -- you can dash past them or duck by sliding on ice."},
    {"name": "Driptop", "role": "CEILING", "desc": "Drops from above when you pass",
     "key": "spider", "color": (80, 60, 60),
     "story": "Clings silently to cave ceilings. When Pain-da passes below, it drops straight down on a silk thread. Lands, then patrols the floor.\n\nHOW TO BEAT: Best handled mid-air -- hit its descent with a jump-stomp. Or dash past before it drops."},
    {"name": "Lure-Bug", "role": "TRAP", "desc": "Pretty light that snaps shut",
     "key": "glow", "color": (150, 255, 100),
     "story": "Glows a soft inviting green in the dark caves -- you'll be tempted to touch it. When you're within 60 pixels, it SNAPS to red and bites for 0.5s.\n\nHOW TO BEAT: It's invincible. Keep your distance. Green = safe, red = damage."},
    {"name": "Brine-Star", "role": "STATIC", "desc": "Grows if you stand still",
     "key": "brine", "color": (200, 220, 255),
     "story": "A salt crystal that responds to stillness. It grows larger the longer Pain-da stands near it motionless. At full size, it damages on contact.\n\nHOW TO BEAT: Keep moving! On the ice physics level, this is a test of control. The crystal is invincible -- never stand still near it."},
    {"name": "Phantom", "role": "MIRROR", "desc": "Only visible in reflection",
     "key": "phantom", "color": (220, 220, 240),
     "story": "A translucent spectre that roams the salt flats. Hard to see in the real world -- watch the mirror surface to spot them. Still does damage even when invisible.\n\nHOW TO BEAT: Use the reflection on the salt surface to track it. Stomp from above when you know where it is."},
    # --- Level 14-18 enemies ---
    {"name": "Puff-cap", "role": "SPORE", "desc": "Stationary, releases clouds",
     "key": "puffer", "color": (120, 200, 120),
     "story": "Sentient mushroom that periodically puffs drifting poison spores in two directions. Doesn't move, but its spores slowly float upward and damage on contact.\n\nHOW TO BEAT: Stomp it directly to kill -- this also clears its active spores. Or stay below its altitude."},
    {"name": "Magma-Leap", "role": "ERUPTER", "desc": "Jumps from rising lava",
     "key": "leaper", "color": (255, 150, 80),
     "story": "Molten creature that lurks beneath the rising lava. Periodically erupts in an arc, landing briefly before sinking back. Tracks toward the player during the rise.\n\nHOW TO BEAT: Stomp it while it's airborne -- it's vulnerable then. If it lands near you, dash away."},
    {"name": "Tide-Claw", "role": "CYCLING", "desc": "Patrols the timed gates",
     "key": "tidalcrab", "color": (80, 160, 180),
     "story": "Coastal crab that walks the alternating stone gates. When its gate vanishes, it plummets to the next solid surface and resumes patrolling. Their positions change every 3 seconds.\n\nHOW TO BEAT: Stomp from above. Just be aware its gate can disappear under you too."},
    {"name": "Phase-Wraith", "role": "TELEPORT", "desc": "Uses portals too",
     "key": "wraith", "color": (200, 140, 255),
     "story": "Ghostly figure that also uses the teleport portals. Patrols normally, then occasionally jumps through an active portal and reappears at its partner. Stompable but hard to predict.\n\nHOW TO BEAT: Track portal pairs. If you see it near a portal, expect it on the partner side next."},
    {"name": "Grav-Drone", "role": "PULLER", "desc": "Pulls you toward itself",
     "key": "drone", "color": (180, 120, 255),
     "story": "Floating mechanical sphere with a gravitational field. When you enter its 200px range, it drags your velocity toward its center -- disrupting jumps and platforming.\n\nHOW TO BEAT: Stomp it to kill. Or use the ice spell from outside its range."},
    {"name": "Specter", "role": "TRACKER", "desc": "ALWAYS homes on the player",
     "key": "specter", "color": (230, 160, 255),
     "story": "Ghostly flier designed to punish air-cheese. Slow on the ground but ACCELERATES when Pain-da is airborne -- especially when gliding. Red eyes lock on from across the level.\n\nHOW TO BEAT: Land often. Stomp it when it closes. Or freeze it with the ice spell."},
    {"name": "Forge-Hammer", "role": "CRUSHER", "desc": "Slams from the ceiling",
     "key": "hammer", "color": (100, 100, 120),
     "story": "Ceiling-mounted iron hammer on an invisible chain. Telegraphs for 0.5 seconds, then slams down with crushing force. Damages double on contact while slamming.\n\nHOW TO BEAT: Cannot be killed. Watch the telegraph flash and sprint out of its column."},
    {"name": "Void-Eater", "role": "MOUTH", "desc": "Hungry maw -- not stompable",
     "key": "voideater", "color": (140, 60, 200),
     "story": "A hungry void-spawn with a mouth that opens and closes on a timer. While open, it damages on contact. Floating bob pattern makes it tricky to predict.\n\nHOW TO BEAT: Not stompable. Freeze it with the ice spell, or dash past while its mouth is closed."},
]


def _draw_card(screen: pygame.Surface, char: dict,
               x: int, y: int, w: int, h: int,
               timer: float, idx: int, hovered: bool = False) -> None:
    """Draw one character card. Hovered cards are highlighted."""
    sprites = _get_sprite_cache()

    # Card bg -- brighter when hovered
    card = pygame.Surface((w, h), pygame.SRCALPHA)
    if hovered:
        card.fill((30, 55, 30, 240))
        pygame.draw.rect(card, (*char["color"], 255),
                         (0, 0, w, h), 2, border_radius=6)
    else:
        card.fill((12, 25, 12, 210))
        pygame.draw.rect(card, (40, 70, 40, 180), (0, 0, w, h), 1, border_radius=6)
    # Colored accent bar at top
    pygame.draw.rect(card, (*char["color"], 200 if hovered else 140),
                     (0, 0, w, 3), border_radius=6)
    screen.blit(card, (x, y))

    # Sprite preview -- scale to fit if card is small
    sprite = sprites.get(char["key"])
    if sprite:
        bob = math.sin(timer * 2.5 + idx * 1.1) * 2
        # Scale sprite to max 44px on small cards
        max_sprite = 44 if h < 110 else 54
        sw, sh = sprite.get_size()
        if sw > max_sprite or sh > max_sprite:
            scale = min(max_sprite / sw, max_sprite / sh)
            sw2 = int(sw * scale)
            sh2 = int(sh * scale)
            sprite = pygame.transform.scale(sprite, (sw2, sh2))
            sw, sh = sw2, sh2
        sx = x + (w - sw) // 2
        sy = y + 8 + int(bob)
        screen.blit(sprite, (sx, sy))

    # Name (smaller on compact cards)
    name_y = y + (h - 30)
    name_size = 13 if h < 110 else 16
    draw_text(screen, char["name"], name_size, char["color"],
              x + w // 2, name_y, bold=True)

    # Role tag
    role_y = name_y + 14
    tag_font = get_font(9 if h < 110 else 10)
    tag_surf = tag_font.render(char["role"], True, (30, 50, 30))
    tw, th = tag_surf.get_size()
    tag_bg = pygame.Surface((tw + 6, th + 3), pygame.SRCALPHA)
    tag_bg.fill((*char["color"], 100))
    tag_x = x + (w - tw - 6) // 2
    screen.blit(tag_bg, (tag_x, role_y - 2))
    screen.blit(tag_surf, (tag_x + 3, role_y))


# ---------------------------------------------------------------------------
# Title Screen
# ---------------------------------------------------------------------------

class TitleScreen:
    def __init__(self) -> None:
        self.title_y: float = -60.0
        self.title_target_y: float = SCREEN_HEIGHT * 0.09
        self.prompt_timer: float = 0.0
        self._bg: pygame.Surface | None = None
        # Interactive character selection
        self._card_rects: list[tuple[pygame.Rect, dict]] = []
        self.selected_char: dict | None = None
        # Dropdown state: gallery is HIDDEN by default to keep menu clean
        self.gallery_open: bool = False
        self._gallery_button_rect: pygame.Rect | None = None

    def update(self, dt: float) -> None:
        self.title_y += (self.title_target_y - self.title_y) * min(1.0, 4 * dt)
        self.prompt_timer += dt

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Handle mouse click. Returns True if consumed (don't start game)."""
        # If detail panel open, click anywhere closes it
        if self.selected_char is not None:
            self.selected_char = None
            return True
        # Gallery toggle button
        if (self._gallery_button_rect is not None
                and self._gallery_button_rect.collidepoint(pos)):
            self.gallery_open = not self.gallery_open
            return True
        # Click a character card -> detail popup (only if gallery is open)
        if self.gallery_open:
            for rect, char in self._card_rects:
                if rect.collidepoint(pos):
                    self.selected_char = char
                    return True
        return False

    def handle_key(self, key: int) -> bool:
        """Returns True if the key was consumed (don't start game)."""
        if self.selected_char is not None:
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN):
                self.selected_char = None
                return True
            return True  # any key closes
        # ESC closes the gallery (lets you see the clean title again)
        if self.gallery_open and key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.gallery_open = False
            return True
        return False

    def _ensure_bg(self) -> pygame.Surface:
        """Pre-render the static background."""
        if self._bg is not None:
            return self._bg
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        # Gradient
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(15 + 8 * t)
            g = int(35 + 15 * t)
            b = int(15 + 8 * t)
            pygame.draw.line(bg, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        # Bamboo stalks in background
        for bx in range(30, SCREEN_WIDTH, 80):
            bh = 80 + (bx * 37) % 60
            c = (20 + (bx % 12), 50 + (bx % 18), 18)
            pygame.draw.rect(bg, c, (bx, SCREEN_HEIGHT - bh, 5, bh))
            for jy in range(SCREEN_HEIGHT - bh + 12, SCREEN_HEIGHT, 18):
                pygame.draw.rect(bg, (16, 42, 14), (bx - 1, jy, 7, 2))
            # Tiny leaf
            pygame.draw.polygon(bg, (30, 65, 25),
                                [(bx + 5, SCREEN_HEIGHT - bh + 2),
                                 (bx + 14, SCREEN_HEIGHT - bh - 4),
                                 (bx + 5, SCREEN_HEIGHT - bh - 3)])
        self._bg = bg
        return bg

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self._ensure_bg(), (0, 0))

        # Title
        draw_text_shadow(screen, "BAMBOO FOREST", 54, (200, 255, 200),
                         SCREEN_WIDTH // 2, int(self.title_y), bold=True)
        draw_text(screen, "~ The Legend of Pain-da ~", 18, (120, 180, 120),
                  SCREEN_WIDTH // 2, int(self.title_y) + 32)

        self._card_rects.clear()
        mouse_pos = pygame.mouse.get_pos()

        # === DROPDOWN BUTTON (always visible) ===
        btn_w, btn_h = 280, 44
        btn_x = (SCREEN_WIDTH - btn_w) // 2
        btn_y = int(SCREEN_HEIGHT * 0.32)
        self._gallery_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        btn_hovered = self._gallery_button_rect.collidepoint(mouse_pos)
        bg_color = (40, 70, 40, 250) if not btn_hovered else (60, 110, 60, 255)
        btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
        btn_surf.fill(bg_color)
        pygame.draw.rect(btn_surf, (200, 255, 200), (0, 0, btn_w, btn_h),
                         2, border_radius=6)
        # Arrow indicator
        arrow = "V" if not self.gallery_open else "^"
        screen.blit(btn_surf, (btn_x, btn_y))
        label = ("View Characters  " + arrow) if not self.gallery_open else \
                ("Hide Characters  " + arrow)
        draw_text_shadow(screen, label, 20, (230, 255, 230),
                         btn_x + btn_w // 2, btn_y + btn_h // 2, bold=True)

        # === GALLERY (only when dropdown open) ===
        if self.gallery_open:
            # Dim background panel behind the grid
            cols = 4
            rows = (len(_CHARACTERS) + cols - 1) // cols
            card_w = 220
            card_h = 95
            gap_x = 10
            gap_y = 8
            total_w = cols * card_w + (cols - 1) * gap_x
            total_h = rows * card_h + (rows - 1) * gap_y
            start_x = (SCREEN_WIDTH - total_w) // 2
            start_y = btn_y + btn_h + 14
            # Semi-opaque panel behind
            panel = pygame.Surface((total_w + 20, total_h + 40),
                                    pygame.SRCALPHA)
            panel.fill((10, 20, 10, 230))
            pygame.draw.rect(panel, (100, 150, 100),
                             (0, 0, total_w + 20, total_h + 40),
                             2, border_radius=8)
            screen.blit(panel, (start_x - 10, start_y - 10))
            for i, char in enumerate(_CHARACTERS):
                col = i % cols
                row = i // cols
                cx = start_x + col * (card_w + gap_x)
                cy = start_y + row * (card_h + gap_y)
                rect = pygame.Rect(cx, cy, card_w, card_h)
                self._card_rects.append((rect, char))
                hovered = rect.collidepoint(mouse_pos)
                _draw_card(screen, char, cx, cy, card_w, card_h,
                           self.prompt_timer, i, hovered=hovered)
            draw_text(screen, "Click a character to read their story  |  ESC to close",
                      13, (180, 210, 180), SCREEN_WIDTH // 2,
                      start_y + total_h + 18)

        # Pulsing "Press ENTER" prompt (position based on whether gallery is open)
        prompt_y = (SCREEN_HEIGHT - 90 if not self.gallery_open
                    else SCREEN_HEIGHT - 62)
        alpha = int(128 + 127 * math.sin(self.prompt_timer * 3))
        font = get_font(26 if not self.gallery_open else 20)
        prompt = font.render("Press ENTER to Start", True, (200, 255, 200))
        prompt.set_alpha(alpha)
        screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, prompt_y)))

        # Controls (only when gallery is closed -- else it overlaps)
        if not self.gallery_open:
            draw_text(screen,
                      "Arrows/WASD  |  SPACE jump  |  SHIFT dash  |  E attack  |  F11 fullscreen",
                      13, (90, 140, 90), SCREEN_WIDTH // 2, SCREEN_HEIGHT - 48)
            best = get_best_score()
            if best > 0:
                draw_text_shadow(screen, f"Best: {best}", 18, COL_GOLD,
                                 SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)

        # Detail popup on top of everything
        if self.selected_char is not None:
            self._draw_detail(screen)

    def _draw_detail(self, screen: pygame.Surface) -> None:
        """Draw detail popup for the selected character."""
        char = self.selected_char
        # Dim the background
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        screen.blit(dim, (0, 0))

        # Panel
        pw, ph = 720, 440
        px = (SCREEN_WIDTH - pw) // 2
        py = (SCREEN_HEIGHT - ph) // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 28, 18, 250))
        pygame.draw.rect(panel, char["color"], (0, 0, pw, ph), 3, border_radius=10)
        # Accent bar
        pygame.draw.rect(panel, (*char["color"], 220), (0, 0, pw, 8),
                        border_radius=10)
        screen.blit(panel, (px, py))

        # Big sprite (centered left side)
        sprites = _get_sprite_cache()
        sprite = sprites.get(char["key"])
        if sprite:
            sw, sh = sprite.get_size()
            scale = min(200 / sw, 200 / sh)
            big = pygame.transform.scale(sprite,
                                        (int(sw * scale), int(sh * scale)))
            bw, bh = big.get_size()
            screen.blit(big, (px + 40 + (200 - bw) // 2,
                             py + 80 + (200 - bh) // 2))

        # Name (big)
        draw_text_shadow(screen, char["name"], 42, char["color"],
                        px + pw // 2, py + 40, bold=True)

        # Role tag
        role_font = get_font(14, bold=True)
        role_surf = role_font.render(char["role"], True, (30, 50, 30))
        rw, rh = role_surf.get_size()
        tag_bg = pygame.Surface((rw + 16, rh + 6), pygame.SRCALPHA)
        tag_bg.fill((*char["color"], 220))
        screen.blit(tag_bg, (px + pw // 2 - (rw + 16) // 2, py + 66))
        screen.blit(role_surf, (px + pw // 2 - rw // 2, py + 68))

        # Story (word-wrapped)
        story = char.get("story", char.get("desc", ""))
        body_font = get_font(16)
        story_x = px + 280
        story_y = py + 100
        max_w = pw - 280 - 40
        self._draw_wrapped(screen, story, body_font, (220, 235, 220),
                          story_x, story_y, max_w)

        # Close hint
        hint = get_font(14).render(
            "Click anywhere or press ESC to close", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(
            center=(px + pw // 2, py + ph - 20)))

    def _draw_wrapped(self, screen: pygame.Surface, text: str,
                     font: pygame.font.Font, color: tuple,
                     x: int, y: int, max_width: int) -> None:
        """Draw text with word wrapping + paragraph support."""
        for paragraph in text.split("\n\n"):
            words = paragraph.split(" ")
            line: list[str] = []
            for w in words:
                test = " ".join(line + [w])
                if font.size(test)[0] > max_width and line:
                    line_surf = font.render(" ".join(line), True, color)
                    screen.blit(line_surf, (x, y))
                    y += font.get_height() + 2
                    line = [w]
                else:
                    line.append(w)
            if line:
                line_surf = font.render(" ".join(line), True, color)
                screen.blit(line_surf, (x, y))
                y += font.get_height() + 2
            y += 8  # paragraph spacing


# ---------------------------------------------------------------------------
# Pause Overlay
# ---------------------------------------------------------------------------

class PauseOverlay:
    """Pause screen with compact enemy encyclopedia (read while waiting)."""

    def draw(self, screen: pygame.Surface) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        draw_text_shadow(screen, "PAUSED", 42, COL_WHITE,
                         SCREEN_WIDTH // 2, 36, bold=True)
        draw_text(screen, "ESC to Resume  |  Q to Quit", 16, (180, 180, 180),
                  SCREEN_WIDTH // 2, 62)

        # Mini enemy encyclopedia -- compact grid of all characters
        sprites = _get_sprite_cache()
        col_w = 180
        row_h = 90
        cols = 5
        start_x = (SCREEN_WIDTH - cols * col_w) // 2
        start_y = 90
        font_name = get_font(12, bold=True)
        font_desc = get_font(10)
        for i, char in enumerate(_CHARACTERS):
            col = i % cols
            row = i // cols
            x = start_x + col * col_w
            y = start_y + row * row_h
            # Compact card
            card = pygame.Surface((col_w - 8, row_h - 8), pygame.SRCALPHA)
            card.fill((15, 25, 15, 230))
            pygame.draw.rect(card, (*char["color"], 160),
                             (0, 0, col_w - 8, row_h - 8), 1, border_radius=4)
            screen.blit(card, (x, y))
            # Small sprite
            sprite = sprites.get(char["key"])
            if sprite:
                sm = pygame.transform.scale(sprite, (40, 40))
                screen.blit(sm, (x + 8, y + 10))
            # Name + desc
            name = font_name.render(char["name"], True, char["color"])
            screen.blit(name, (x + 56, y + 8))
            role = font_desc.render(char["role"], True, (160, 200, 160))
            screen.blit(role, (x + 56, y + 22))
            # Word-wrap description
            desc = char["desc"]
            max_chars = 22
            if len(desc) > max_chars:
                # Split on word
                words = desc.split()
                line1, line2 = "", ""
                for w in words:
                    if len(line1) + len(w) + 1 <= max_chars:
                        line1 = line1 + " " + w if line1 else w
                    else:
                        line2 = line2 + " " + w if line2 else w
                d1 = font_desc.render(line1, True, (200, 200, 200))
                d2 = font_desc.render(line2, True, (200, 200, 200))
                screen.blit(d1, (x + 56, y + 40))
                screen.blit(d2, (x + 56, y + 54))
            else:
                d = font_desc.render(desc, True, (200, 200, 200))
                screen.blit(d, (x + 56, y + 46))


# ---------------------------------------------------------------------------
# Game Over Screen
# ---------------------------------------------------------------------------

class GameOverScreen:
    def __init__(self) -> None:
        self.fade_alpha: float = 0.0

    def update(self, dt: float) -> None:
        self.fade_alpha = min(200, self.fade_alpha + 300 * dt)

    def draw(self, screen: pygame.Surface, final_score: int) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(self.fade_alpha)))
        screen.blit(overlay, (0, 0))
        if self.fade_alpha > 100:
            draw_text_shadow(screen, "GAME OVER", 64, COL_RED,
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, bold=True)
            draw_text(screen, f"Score: {final_score}", 32, COL_WHITE,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
            draw_text(screen, "Press ENTER to Try Again", 24, (180, 180, 180),
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)


# ---------------------------------------------------------------------------
# Victory Screen
# ---------------------------------------------------------------------------

class VictoryScreen:
    def __init__(self) -> None:
        self.timer: float = 0.0

    def update(self, dt: float) -> None:
        self.timer += dt

    def draw(self, screen: pygame.Surface, final_score: int,
             is_high_score: bool) -> None:
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(20 * (1 - t) + 5 * t)
            g = int(50 * (1 - t) + 20 * t)
            b = int(20 * (1 - t) + 5 * t)
            pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        bounce = math.sin(self.timer * 3) * 8
        draw_text_shadow(screen, "VICTORY!", 72, COL_GOLD,
                         SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.3 + bounce), bold=True)
        draw_text(screen, f"Final Score: {final_score}", 36, COL_WHITE,
                  SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.5))
        if is_high_score:
            alpha = int(128 + 127 * math.sin(self.timer * 5))
            font = get_font(28, bold=True)
            surf = font.render("NEW HIGH SCORE!", True, COL_GOLD)
            surf.set_alpha(alpha)
            screen.blit(surf, surf.get_rect(center=(
                SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.58))))
        draw_text(screen, "Press ENTER to Play Again", 24, (180, 180, 180),
                  SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.75))


# ---------------------------------------------------------------------------
# Level Transition
# ---------------------------------------------------------------------------

class LevelTransition:
    def __init__(self, level_number: int) -> None:
        self.level_number = level_number
        self.timer: float = 0.0
        self.duration: float = 2.0

    def update(self, dt: float) -> bool:
        self.timer += dt
        return self.timer >= self.duration

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(COL_BLACK)
        t = self.timer / self.duration
        alpha = int(255 * (1 - abs(t - 0.5) * 2))
        alpha = max(0, min(255, alpha))

        font = get_font(56, bold=True)
        text = font.render(f"LEVEL {self.level_number}", True, COL_WHITE)
        text.set_alpha(alpha)
        screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

        idx = self.level_number - 1
        if 0 <= idx < len(LEVEL_NAMES):
            name_font = get_font(28)
            name = name_font.render(LEVEL_NAMES[idx], True, (180, 220, 180))
            name.set_alpha(alpha)
            screen.blit(name, name.get_rect(center=(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))


# ---------------------------------------------------------------------------
# Death Animation
# ---------------------------------------------------------------------------

class DeathAnimation:
    def __init__(self) -> None:
        self.timer: float = 1.0
        self.time_scale: float = 0.3

    def update(self, dt: float) -> bool:
        self.timer -= dt
        return self.timer <= 0

    def get_time_scale(self) -> float:
        return self.time_scale
