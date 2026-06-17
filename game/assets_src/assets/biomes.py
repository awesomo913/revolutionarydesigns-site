"""Biome-specific sprites: mechanics, enemies, NPCs for levels 4-8."""

from __future__ import annotations

import math
import random
from math import floor as _fl

import pygame
# Pygbag/WASM: lazy submodule imports (see web/main.py)
import pygame.sprite  # noqa: F401
import pygame.transform  # noqa: F401
import pygame.draw  # noqa: F401

from config import (
    ASH_BAT_RANGE, ASH_BAT_SWOOP, BRINE_DMG_RADIUS, BRINE_GROW_RATE,
    COL_BASALT, COL_BLACK, COL_CRYSTAL, COL_ICE, COL_LAVA, COL_LIMESTONE,
    COL_SALT, COL_SANDSTONE, COL_TOXIC, COL_WHITE, CRUMBLE_DELAY,
    CRUMBLE_RESPAWN, CRYSTAL_LIGHT_TIME, CRYSTAL_RADIUS, DARK_RADIUS,
    DUST_DEVIL_SPEED, ENEMY_PATROL_SPEED, FLOOR_Y, GLOWWORM_SNAP_RANGE,
    GEYSER_DURATION, GEYSER_INTERVAL, GEYSER_LAUNCH, GOLEM_COOLDOWN,
    GOLEM_STRIKE_RANGE, GOLEM_STRIKE_SPEED, GRAVITY, ICE_ACCEL,
    ICE_FRICTION, KELP_CRAB_SPEED, NPC_RANGE, PHANTOM_SPEED,
    PLAYER_SPEED, SCORPION_FIRE_RATE, SCORPION_PROJ_SPEED,
    SPIDER_DROP_RANGE, SPIDER_DROP_SPEED, SULFUR_SPEED,
    SULFUR_TRAIL_DMG, SULFUR_TRAIL_LIFE, TERMINAL_VELOCITY,
    WIND_PUSH,
    # Level 14-18 new constants
    MUSHROOM_BOUNCE, MUSHROOM_COMPRESS_SEC, SPORE_INTERVAL,
    SPORE_LIFETIME, SPORE_DRIFT, SPORE_DAMAGE,
    LAVA_RISE_SPEED, LAVA_PAUSE_SEC, LAVA_START_Y,
    LEAPER_JUMP, LEAPER_INTERVAL,
    GATE_CYCLE_SEC, GATE_TELEGRAPH_SEC, TIDAL_CRAB_SPEED,
    PORTAL_COOLDOWN_SEC, WRAITH_SPEED,
    GRAVITY_LOW_MULT, GRAVITY_HIGH_MULT, GRAVITY_REVERSE_MULT,
    DRONE_RANGE, DRONE_PULL,
)

# ===================================================================
# BIOME-THEMED PLATFORM TILES
# ===================================================================

def generate_volcanic_tile(width: int, height: int) -> pygame.Surface:
    """Dark volcanic basalt with orange lava crack highlights."""
    surf = pygame.Surface((width, height))
    # Dark rock base
    for y in range(height):
        t = y / max(1, height)
        c = (int(45 - 15 * t), int(30 - 10 * t), int(25 - 5 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Top crust (cooled lava)
    pygame.draw.rect(surf, (80, 50, 40), (0, 0, width, 4))
    pygame.draw.rect(surf, (120, 70, 40), (0, 0, width, 2))
    # Lava cracks (random horizontal squiggles)
    for _ in range(width // 20):
        cx = random.randint(0, width - 10)
        cy = random.randint(6, height - 4)
        cw = random.randint(6, 14)
        pygame.draw.line(surf, (220, 80, 30), (cx, cy), (cx + cw, cy + 2), 1)
        pygame.draw.line(surf, (255, 150, 60), (cx, cy), (cx + cw, cy + 2), 1)
    # Pumice specks
    for _ in range(width * height // 50):
        nx = random.randint(1, width - 2)
        ny = random.randint(5, height - 2)
        surf.set_at((nx, ny), (80, 60, 55))
    # Edge
    pygame.draw.rect(surf, (20, 15, 20), (0, 0, 2, height))
    pygame.draw.rect(surf, (20, 15, 20), (width - 2, 0, 2, height))
    return surf


def generate_basalt_tile(width: int, height: int) -> pygame.Surface:
    """Hexagonal basalt columns -- dark gray with top lip."""
    surf = pygame.Surface((width, height))
    # Deep gray body
    for y in range(height):
        t = y / max(1, height)
        c = (int(70 - 20 * t), int(75 - 20 * t), int(90 - 20 * t))
        pygame.draw.line(surf, c, (0, y), (width, y))
    # Hex top stripe (lighter)
    pygame.draw.rect(surf, (100, 105, 120), (0, 0, width, 3))
    # Vertical column lines (every 40px)
    for cx in range(0, width, 40):
        pygame.draw.line(surf, (40, 45, 55), (cx, 3), (cx, height), 1)
        pygame.draw.line(surf, (90, 95, 110), (cx + 1, 3), (cx + 1, height), 1)
    # Subtle horizontal banding
    for by in range(8, height, 12):
        pygame.draw.line(surf, (55, 60, 75), (0, by), (width, by), 1)
    # Edge
    pygame.draw.rect(surf, (30, 30, 40), (0, 0, 2, height))
    pygame.draw.rect(surf, (30, 30, 40), (width - 2, 0, 2, height))
    return surf


def generate_sandstone_tile(width: int, height: int) -> pygame.Surface:
    """Layered tan sandstone with erosion marks."""
    surf = pygame.Surface((width, height))
    # Layered bands of varying tan
    band_colors = [
        (210, 175, 120), (195, 160, 105), (180, 145, 90),
        (170, 135, 85), (160, 125, 80),
    ]
    band_h = max(2, height // len(band_colors))
    for i, c in enumerate(band_colors):
        pygame.draw.rect(surf, c, (0, i * band_h, width, band_h))
    # Top lighter stripe (wind-polished)
    pygame.draw.rect(surf, (225, 195, 140), (0, 0, width, 3))
    # Erosion divots
    for _ in range(width // 15):
        ex = random.randint(2, width - 4)
        ey = random.randint(4, height - 2)
        pygame.draw.ellipse(surf, (150, 115, 75), (ex, ey, 4, 2))
    # Specks
    for _ in range(width * height // 60):
        nx = random.randint(1, width - 2)
        ny = random.randint(3, height - 2)
        shade = random.randint(-15, 15)
        surf.set_at((nx, ny),
                    (max(0, min(255, 180 + shade)),
                     max(0, min(255, 145 + shade)),
                     max(0, min(255, 90 + shade))))
    pygame.draw.rect(surf, (120, 95, 60), (0, 0, 2, height))
    pygame.draw.rect(surf, (120, 95, 60), (width - 2, 0, 2, height))
    return surf


def generate_limestone_tile(width: int, height: int) -> pygame.Surface:
    """Pale gray-tan limestone cave floor with fossil marks."""
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height)
        c = (int(170 - 30 * t), int(165 - 30 * t), int(150 - 30 * t))
        pygame.draw.line(surf, c, (0, y), (width, y))
    pygame.draw.rect(surf, (190, 180, 165), (0, 0, width, 3))
    # Fossil impressions (small curved lines)
    for _ in range(width // 25):
        fx = random.randint(4, width - 8)
        fy = random.randint(6, height - 4)
        pygame.draw.arc(surf, (120, 115, 100), (fx, fy, 6, 4), 0, 3.14, 1)
    # Specks
    for _ in range(width * height // 70):
        nx = random.randint(1, width - 2)
        ny = random.randint(3, height - 2)
        shade = random.randint(-15, 10)
        surf.set_at((nx, ny),
                    (max(0, min(255, 155 + shade)),
                     max(0, min(255, 150 + shade)),
                     max(0, min(255, 135 + shade))))
    pygame.draw.rect(surf, (90, 85, 75), (0, 0, 2, height))
    pygame.draw.rect(surf, (90, 85, 75), (width - 2, 0, 2, height))
    return surf


def generate_salt_tile(width: int, height: int) -> pygame.Surface:
    """Pale blue-white salt crystal surface, reflective."""
    surf = pygame.Surface((width, height))
    # Near-white body with pale blue hint
    for y in range(height):
        t = y / max(1, height)
        c = (int(220 - 20 * t), int(235 - 15 * t), int(250 - 10 * t))
        pygame.draw.line(surf, c, (0, y), (width, y))
    # Bright top
    pygame.draw.rect(surf, (245, 250, 255), (0, 0, width, 4))
    # Crystal facet lines
    for cx in range(0, width, random.randint(20, 35)):
        pygame.draw.line(surf, (180, 210, 235), (cx, 4),
                         (cx + random.randint(-3, 3), height), 1)
    # Sparkle highlights
    for _ in range(width // 10):
        sx = random.randint(1, width - 2)
        sy = random.randint(3, height - 2)
        surf.set_at((sx, sy), (255, 255, 255))
    pygame.draw.rect(surf, (160, 190, 220), (0, 0, 2, height))
    pygame.draw.rect(surf, (160, 190, 220), (width - 2, 0, 2, height))
    return surf


def generate_mushroom_tile(width: int, height: int) -> pygame.Surface:
    """Bioluminescent fungal soil -- dark purple with glowing spores."""
    surf = pygame.Surface((width, height))
    # Base: deep moss purple
    for y in range(height):
        t = y / max(1, height)
        c = (int(55 - 20 * t), int(30 - 10 * t), int(65 - 20 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Top moss
    pygame.draw.rect(surf, (80, 160, 110), (0, 0, width, 3))
    pygame.draw.rect(surf, (120, 200, 140), (0, 0, width, 1))
    # Glowing spores (pink/cyan pixels)
    for _ in range(width // 6):
        sx = random.randint(1, width - 2)
        sy = random.randint(3, height - 2)
        col = random.choice([(220, 100, 200), (100, 220, 220), (200, 220, 100)])
        surf.set_at((sx, sy), col)
    # Tiny mushroom stems along top
    for _ in range(width // 30):
        mx = random.randint(2, width - 4)
        pygame.draw.line(surf, (200, 220, 200), (mx, 3), (mx, 6), 1)
        pygame.draw.circle(surf, (220, 100, 180), (mx, 2), 2)
    return surf


def generate_tidal_tile(width: int, height: int) -> pygame.Surface:
    """Barnacled coastal stone with teal water stains."""
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height)
        c = (int(90 - 30 * t), int(110 - 30 * t), int(130 - 30 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Wet top strip
    pygame.draw.rect(surf, (60, 130, 150), (0, 0, width, 3))
    pygame.draw.rect(surf, (90, 170, 190), (0, 0, width, 1))
    # Barnacle clusters
    for _ in range(width // 15):
        bx = random.randint(2, width - 4)
        by = random.randint(4, height - 4)
        pygame.draw.circle(surf, (240, 230, 210), (bx, by), 2)
        pygame.draw.circle(surf, (180, 160, 140), (bx, by), 2, 1)
    # Teal drips
    for _ in range(width // 25):
        dx = random.randint(0, width - 2)
        pygame.draw.line(surf, (80, 180, 180), (dx, 3),
                         (dx, random.randint(5, height - 2)), 1)
    return surf


def generate_gravity_tile(width: int, height: int) -> pygame.Surface:
    """Arcane metal with glowing circuit veins."""
    surf = pygame.Surface((width, height))
    # Dark metallic base
    for y in range(height):
        t = y / max(1, height)
        c = (int(40 - 10 * t), int(30 - 10 * t), int(55 - 15 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Top ridge
    pygame.draw.rect(surf, (120, 90, 160), (0, 0, width, 3))
    pygame.draw.rect(surf, (180, 150, 220), (0, 0, width, 1))
    # Circuit lines
    for _ in range(width // 12):
        cx = random.randint(2, width - 10)
        cy = random.randint(5, height - 3)
        cw = random.randint(6, 14)
        pygame.draw.line(surf, (150, 120, 220), (cx, cy), (cx + cw, cy), 1)
        pygame.draw.circle(surf, (220, 180, 255), (cx, cy), 1)
        pygame.draw.circle(surf, (220, 180, 255), (cx + cw, cy), 1)
    # Rivets
    for _ in range(width // 25):
        rx = random.randint(2, width - 4)
        pygame.draw.circle(surf, (80, 60, 100), (rx, height // 2), 1)
    return surf


def generate_corrupted_tile(width: int, height: int) -> pygame.Surface:
    """Sickly forest ground -- dark green with purple corruption veins."""
    surf = pygame.Surface((width, height))
    # Darker moss base
    for y in range(height):
        t = y / max(1, height)
        c = (int(55 - 20 * t), int(85 - 30 * t), int(50 - 20 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Sickly grass top (darkened)
    pygame.draw.rect(surf, (70, 110, 60), (0, 0, width, 3))
    pygame.draw.rect(surf, (100, 150, 80), (0, 0, width, 1))
    # Purple corruption veins creeping through
    for _ in range(width // 15):
        vx = random.randint(2, width - 10)
        vy = random.randint(4, height - 4)
        vlen = random.randint(4, 12)
        pygame.draw.line(surf, (140, 60, 150), (vx, vy),
                        (vx + vlen, vy + random.randint(-2, 2)), 1)
    # Dead grass specks
    for _ in range(width // 8):
        sx = random.randint(1, width - 2)
        sy = random.randint(3, height - 2)
        surf.set_at((sx, sy), (60, 70, 40))
    # Rot spots
    for _ in range(width // 30):
        rx = random.randint(3, width - 6)
        ry = random.randint(5, height - 4)
        pygame.draw.circle(surf, (80, 40, 90), (rx, ry), 2)
    return surf


def generate_lair_tile(width: int, height: int) -> pygame.Surface:
    """Corrupted boss-lair ground -- crimson shadow with dark veins."""
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height)
        c = (int(50 - 15 * t), int(20 - 5 * t), int(35 - 10 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Top crust (dark red-purple)
    pygame.draw.rect(surf, (80, 30, 50), (0, 0, width, 3))
    pygame.draw.rect(surf, (130, 40, 70), (0, 0, width, 1))
    # Crimson veins
    for _ in range(width // 14):
        vx = random.randint(2, width - 10)
        vy = random.randint(5, height - 4)
        vlen = random.randint(5, 14)
        pygame.draw.line(surf, (180, 50, 70), (vx, vy),
                        (vx + vlen, vy + random.randint(-2, 2)), 1)
    # Pulsing ember spots
    for _ in range(width // 25):
        ex = random.randint(2, width - 4)
        ey = random.randint(5, height - 3)
        pygame.draw.circle(surf, (220, 80, 50), (ex, ey), 1)
        pygame.draw.circle(surf, (255, 150, 100), (ex, ey), 1, 1)
    # Dark specks
    for _ in range(width // 8):
        sx = random.randint(1, width - 2)
        sy = random.randint(3, height - 2)
        surf.set_at((sx, sy), (30, 10, 20))
    return surf


def generate_forge_tile(width: int, height: int) -> pygame.Surface:
    """Industrial iron forge -- rivets, soot, ember glow."""
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height)
        c = (int(75 - 25 * t), int(65 - 20 * t), int(65 - 20 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Hot metal top edge
    pygame.draw.rect(surf, (200, 100, 60), (0, 0, width, 3))
    pygame.draw.rect(surf, (255, 180, 100), (0, 0, width, 1))
    # Rivets (darker circles) along the top edge
    for rx in range(8, width, 16):
        pygame.draw.circle(surf, (30, 30, 35), (rx, height // 2), 2)
        pygame.draw.circle(surf, (80, 80, 90), (rx - 1, height // 2 - 1), 1)
    # Ember cracks
    for _ in range(width // 15):
        cx = random.randint(2, width - 10)
        cy = random.randint(5, height - 4)
        pygame.draw.line(surf, (255, 120, 40),
                        (cx, cy), (cx + 6, cy + random.randint(-2, 2)), 1)
    # Soot specks
    for _ in range(width * height // 40):
        sx = random.randint(1, width - 2)
        sy = random.randint(2, height - 2)
        surf.set_at((sx, sy), (20, 18, 18))
    return surf


def generate_void_tile(width: int, height: int) -> pygame.Surface:
    """Ethereal void -- deep purple with swirling stars."""
    surf = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height)
        c = (int(35 - 10 * t), int(15 - 5 * t), int(65 - 20 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Top ether-glow edge
    pygame.draw.rect(surf, (160, 100, 220), (0, 0, width, 3))
    pygame.draw.rect(surf, (220, 180, 255), (0, 0, width, 1))
    # Purple sparkle stars
    for _ in range(width // 8):
        sx = random.randint(1, width - 2)
        sy = random.randint(3, height - 2)
        col = random.choice([(220, 180, 255), (180, 140, 230), (255, 220, 255)])
        surf.set_at((sx, sy), col)
    # Vertical ether wisps
    for _ in range(width // 25):
        wx = random.randint(2, width - 4)
        pygame.draw.line(surf, (120, 80, 180),
                        (wx, 3), (wx + random.randint(-2, 2), height - 2), 1)
    return surf


_TILE_GENERATORS = {
    "volcanic": generate_volcanic_tile,
    "basalt": generate_basalt_tile,
    "desert": generate_sandstone_tile,
    "cave": generate_limestone_tile,
    "salt": generate_salt_tile,
    "mushroom": generate_mushroom_tile,
    "tidal": generate_tidal_tile,
    "gravity": generate_gravity_tile,
    "corrupted": generate_corrupted_tile,
    "lair": generate_lair_tile,
    "forge": generate_forge_tile,
    "void": generate_void_tile,
}


class BiomePlatform(pygame.sprite.Sprite):
    """Platform with biome-specific tile art."""

    def __init__(self, x: int, y: int, w: int, h: int = 20,
                 biome: str = "forest") -> None:
        super().__init__()
        gen = _TILE_GENERATORS.get(biome)
        if gen:
            self.image = gen(w, h)
        else:
            from sprites import generate_platform_tile
            self.image = generate_platform_tile(w, h)
        self.rect = self.image.get_rect(topleft=(x, y))


class BiomeMovingPlatform(pygame.sprite.Sprite):
    """Moving platform with biome-specific tile art."""

    def __init__(self, x: int, y: int, w: int, h: int,
                 axis: str = "horizontal", distance: float = 150.0,
                 biome: str = "forest") -> None:
        super().__init__()
        gen = _TILE_GENERATORS.get(biome)
        if gen:
            self.image = gen(w, h)
        else:
            from sprites import generate_platform_tile
            self.image = generate_platform_tile(w, h)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.origin_x = float(x)
        self.origin_y = float(y)
        self.axis = axis
        self.distance = distance
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.pos_y = float(y)

    def update_moving(self, dt: float) -> tuple[float, float]:
        from config import MOVING_PLAT_SPEED
        old_x, old_y = self.pos_x, self.pos_y
        step = MOVING_PLAT_SPEED * self.direction * dt
        if self.axis == "horizontal":
            self.pos_x += step
            if self.pos_x > self.origin_x + self.distance:
                self.pos_x = self.origin_x + self.distance
                self.direction = -1.0
            elif self.pos_x < self.origin_x - self.distance:
                self.pos_x = self.origin_x - self.distance
                self.direction = 1.0
        else:
            self.pos_y += step
            if self.pos_y > self.origin_y + self.distance:
                self.pos_y = self.origin_y + self.distance
                self.direction = -1.0
            elif self.pos_y < self.origin_y - self.distance:
                self.pos_y = self.origin_y - self.distance
                self.direction = 1.0
        self.rect.x = _fl(self.pos_x)
        self.rect.y = _fl(self.pos_y)
        return (self.pos_x - old_x, self.pos_y - old_y)


# ===================================================================
# MECHANIC SPRITES
# ===================================================================


class Geyser(pygame.sprite.Sprite):
    """Level 4. Periodically erupts, launching player upward."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        # Dormant: dark rock opening with faint orange glow
        self._img_off = pygame.Surface((44, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(self._img_off, (40, 25, 30), (0, 8, 44, 16))
        pygame.draw.ellipse(self._img_off, (80, 45, 35), (4, 10, 36, 12))
        pygame.draw.ellipse(self._img_off, (180, 80, 40), (8, 12, 28, 8))
        pygame.draw.ellipse(self._img_off, (60, 35, 30), (2, 18, 40, 6))  # rock lip
        # Erupting: tall steam+lava column
        self._img_on = pygame.Surface((44, 200), pygame.SRCALPHA)
        # Base glow
        pygame.draw.ellipse(self._img_on, (40, 25, 30), (0, 184, 44, 16))
        pygame.draw.ellipse(self._img_on, (255, 100, 30), (4, 186, 36, 12))
        # Rising jet (narrowing toward top)
        for y in range(0, 185):
            t = y / 185.0
            w = int(8 + 24 * t)  # wider at bottom
            xc = 22
            alpha = int(200 - 150 * (1 - t))
            if y < 40:
                c = (255, 240, 180, min(255, alpha))
            elif y < 100:
                c = (255, 180, 80, min(255, alpha))
            else:
                c = (255, 120, 50, min(255, alpha))
            pygame.draw.rect(self._img_on, c, (xc - w // 2, y, w, 1))
        # Steam puffs at top
        for _ in range(8):
            px = random.randint(8, 36)
            py = random.randint(0, 40)
            pygame.draw.circle(self._img_on, (240, 230, 220, 180), (px, py),
                               random.randint(4, 8))
        self.image = self._img_off
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self._off_rect = self.image.get_rect(bottomleft=(x, y))
        self._on_rect = self._img_on.get_rect(bottomleft=(x, y))
        self.erupt_timer: float = random.uniform(0, GEYSER_INTERVAL)
        self.erupt_remaining: float = 0.0

    def update(self, dt: float) -> None:
        if self.erupt_remaining > 0:
            self.erupt_remaining -= dt
            if self.image is not self._img_on:
                self.image = self._img_on
                self.rect = self._on_rect.copy()
            if self.erupt_remaining <= 0:
                self.erupt_timer = GEYSER_INTERVAL
                self.image = self._img_off
                self.rect = self._off_rect.copy()
        else:
            self.erupt_timer -= dt
            if self.erupt_timer <= 0:
                self.erupt_remaining = GEYSER_DURATION

    def is_active(self) -> bool:
        return self.erupt_remaining > 0


class ToxicTrail(pygame.sprite.Sprite):
    """Level 4. Damage zone left by SulfurSlime."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((22, 8), pygame.SRCALPHA)
        # Goo puddle with bubbles
        pygame.draw.ellipse(self.image, (100, 160, 40), (0, 2, 22, 6))
        pygame.draw.ellipse(self.image, (160, 220, 60), (2, 3, 18, 3))
        # Bubbles
        pygame.draw.circle(self.image, (220, 255, 120), (6, 3), 1)
        pygame.draw.circle(self.image, (220, 255, 120), (14, 4), 1)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.lifetime: float = SULFUR_TRAIL_LIFE

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.lifetime -= dt
        # Fade as it ages
        if self.lifetime < 1.0:
            alpha = int(255 * self.lifetime)
            self.image.set_alpha(alpha)
        if self.lifetime <= 0:
            self.kill()


class CrumblingPlatform(pygame.sprite.Sprite):
    """Level 5. Crumbles after player stands on it, then respawns."""

    def __init__(self, x: int, y: int, w: int, h: int = 20,
                 platforms_group: pygame.sprite.Group | None = None) -> None:
        super().__init__()
        self.w, self.h = w, h
        self._img_solid = pygame.Surface((w, h))
        self._img_solid.fill(COL_BASALT)
        pygame.draw.rect(self._img_solid, (80, 80, 90), (0, 0, w, 4))
        self._img_crumbling = pygame.Surface((w, h), pygame.SRCALPHA)
        for bx in range(0, w, 6):
            by = random.randint(0, h - 4)
            pygame.draw.rect(self._img_crumbling, (70, 70, 80, 150), (bx, by, 5, 4))

        self.image = self._img_solid
        self.rect = self.image.get_rect(topleft=(x, y))
        self.solid = True
        self.touched = False
        self.crumble_timer: float = 0.0
        self.respawn_timer: float = 0.0
        self._platforms_group = platforms_group
        self._origin = (x, y)

    def touch(self) -> None:
        if not self.touched and self.solid:
            self.touched = True
            self.crumble_timer = CRUMBLE_DELAY

    def update(self, dt: float) -> None:  # type: ignore[override]
        if self.touched and self.solid:
            self.crumble_timer -= dt
            # Flicker before crumbling
            if self.crumble_timer < 0.3 and int(self.crumble_timer * 20) % 2:
                self.image = self._img_crumbling
            else:
                self.image = self._img_solid
            if self.crumble_timer <= 0:
                self.solid = False
                self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
                self.rect = self.image.get_rect(topleft=self._origin)
                if self._platforms_group and self in self._platforms_group:
                    self._platforms_group.remove(self)
                self.respawn_timer = CRUMBLE_RESPAWN
        elif not self.solid:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.solid = True
                self.touched = False
                self.image = self._img_solid
                self.rect = self.image.get_rect(topleft=self._origin)
                if self._platforms_group and self not in self._platforms_group:
                    self._platforms_group.add(self)


class WindZone(pygame.sprite.Sprite):
    """Level 6. Pushes player sideways."""

    def __init__(self, x: int, y: int, w: int, h: int,
                 direction: float = 1.0) -> None:
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (*COL_SANDSTONE, 40)
        self.image.fill(col)
        # Arrow indicators
        for ay in range(10, h - 10, 30):
            ax = w // 2 + (10 if direction > 0 else -10)
            pygame.draw.polygon(self.image, (*COL_SANDSTONE, 80), [
                (ax - 8, ay), (ax + 8, ay + 8), (ax - 8, ay + 16)])
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction = direction

    def get_push(self) -> float:
        return WIND_PUSH * self.direction


class ThermalUpdraft(pygame.sprite.Sprite):
    """Level 6. Vertical column giving upward boost."""

    def __init__(self, x: int, y: int, w: int = 60, h: int = 200) -> None:
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image.fill((220, 180, 100, 30))
        for uy in range(0, h, 15):
            pygame.draw.line(self.image, (240, 200, 120, 50),
                             (w // 2 - 5, uy), (w // 2 + 5, uy - 8), 1)
        self.rect = self.image.get_rect(bottomleft=(x, y))


class Crystal(pygame.sprite.Sprite):
    """Level 7. Strike to expand visibility in dark levels."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._img_dim = pygame.Surface((20, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self._img_dim, (60, 100, 140),
                            [(10, 0), (20, 15), (10, 30), (0, 15)])
        self._img_lit = pygame.Surface((20, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self._img_lit, COL_CRYSTAL,
                            [(10, 0), (20, 15), (10, 30), (0, 15)])
        pygame.draw.polygon(self._img_lit, (180, 240, 255),
                            [(10, 4), (16, 15), (10, 26), (4, 15)])
        self.image = self._img_dim
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.lit = False
        self.light_timer: float = 0.0

    def strike(self) -> None:
        self.lit = True
        self.light_timer = CRYSTAL_LIGHT_TIME
        self.image = self._img_lit

    def update(self, dt: float) -> None:  # type: ignore[override]
        if self.lit:
            self.light_timer -= dt
            if self.light_timer <= 0:
                self.lit = False
                self.image = self._img_dim

    def is_lit(self) -> bool:
        return self.lit


class IcePlatform(pygame.sprite.Sprite):
    """Level 8. Platform with ice physics flag."""

    is_ice: bool = True

    def __init__(self, x: int, y: int, w: int, h: int = 20) -> None:
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(COL_ICE)
        pygame.draw.rect(self.image, (200, 235, 255), (0, 0, w, 4))
        # Ice shine
        for sx in range(0, w, 8):
            pygame.draw.rect(self.image, (220, 240, 255), (sx, 1, 3, 2))
        self.rect = self.image.get_rect(topleft=(x, y))


class ScorpionProjectile(pygame.sprite.Sprite):
    """Level 6. 45-degree thorn from CactusScorpion."""

    def __init__(self, x: int, y: int, direction: float) -> None:
        super().__init__()
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200, 180, 60), (4, 4), 4)
        self.rect = self.image.get_rect(center=(x, y))
        angle = math.radians(45)
        self.vx = SCORPION_PROJ_SPEED * direction * math.cos(angle)
        self.vy = -SCORPION_PROJ_SPEED * math.sin(angle)
        self.pos_x = float(x)
        self.pos_y = float(y)

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.pos_x += self.vx * dt
        self.pos_y += self.vy * dt
        self.vy += GRAVITY * 0.3 * dt  # slight arc
        self.rect.x = _fl(self.pos_x)
        self.rect.y = _fl(self.pos_y)
        if self.rect.y > FLOOR_Y + 100 or self.rect.x < -50 or self.rect.x > 8000:
            self.kill()


# ===================================================================
# ENEMIES (all: update(dt, platforms, player), is_stompable, die())
# ===================================================================

class SulfurSlime(pygame.sprite.Sprite):
    """Level 4. Slow patrol, leaves toxic trail."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 150.0) -> None:
        super().__init__()
        self.image = pygame.Surface((30, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (180, 200, 40), (0, 4, 30, 24))
        pygame.draw.circle(self.image, COL_WHITE, (10, 12), 3)
        pygame.draw.circle(self.image, COL_WHITE, (20, 12), 3)
        pygame.draw.circle(self.image, COL_BLACK, (11, 12), 2)
        pygame.draw.circle(self.image, COL_BLACK, (19, 12), 2)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.patrol_width = patrol_width
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True
        self.trail_timer: float = 0.0
        self._pending_trails: list[ToxicTrail] = []

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag:
            return
        self._pending_trails.clear()
        self.pos_x += SULFUR_SPEED * self.direction * dt
        if self.pos_x > self.origin_x + self.patrol_width:
            self.pos_x = self.origin_x + self.patrol_width
            self.direction = -1.0
        elif self.pos_x < self.origin_x - self.patrol_width:
            self.pos_x = self.origin_x - self.patrol_width
            self.direction = 1.0
        self.rect.x = _fl(self.pos_x)
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0
        self.trail_timer += dt
        if self.trail_timer >= 0.5:
            self.trail_timer = 0.0
            self._pending_trails.append(ToxicTrail(self.rect.centerx - 10, self.rect.bottom))

    def get_new_trails(self) -> list[ToxicTrail]:
        return self._pending_trails

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class AshBat(pygame.sprite.Sprite):
    """Level 4. Swoops when player is mid-air."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((34, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (80, 60, 60), (10, 8, 14, 16))
        pygame.draw.polygon(self.image, (100, 70, 70), [(10, 14), (0, 4), (14, 10)])
        pygame.draw.polygon(self.image, (100, 70, 70), [(24, 14), (34, 4), (20, 10)])
        pygame.draw.circle(self.image, (255, 120, 40), (14, 13), 2)
        pygame.draw.circle(self.image, (255, 120, 40), (20, 13), 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.origin_x = float(x)
        self.origin_y = float(y)
        self.state = "hover"
        self.swoop_tx: float = 0.0
        self.swoop_ty: float = 0.0
        self.alive_flag = True
        self.hover_timer: float = 0.0

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag or player is None:
            return
        if self.state == "hover":
            self.hover_timer += dt
            self.rect.y = _fl(self.origin_y + math.sin(self.hover_timer * 3) * 8)
            dist = math.hypot(player.rect.centerx - self.rect.centerx,
                              player.rect.centery - self.rect.centery)
            if not player.is_on_ground and dist < ASH_BAT_RANGE:
                self.state = "swoop"
                self.swoop_tx = float(player.rect.centerx)
                self.swoop_ty = float(player.rect.centery)
        elif self.state == "swoop":
            dx = self.swoop_tx - self.rect.centerx
            dy = self.swoop_ty - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.rect.x += _fl(dx / dist * ASH_BAT_SWOOP * dt)
                self.rect.y += _fl(dy / dist * ASH_BAT_SWOOP * dt)
            else:
                self.state = "return"
        elif self.state == "return":
            dx = self.origin_x - self.rect.centerx
            dy = self.origin_y - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.rect.x += _fl(dx / dist * ASH_BAT_SWOOP * 0.5 * dt)
                self.rect.y += _fl(dy / dist * ASH_BAT_SWOOP * 0.5 * dt)
            else:
                self.state = "hover"

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class KelpCrab(pygame.sprite.Sprite):
    """Level 5. Armored patrol, stomp-only kill."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 120.0) -> None:
        super().__init__()
        self.image = pygame.Surface((36, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (180, 80, 60), (2, 2, 32, 18))
        pygame.draw.rect(self.image, (160, 60, 40), (0, 6, 6, 4))
        pygame.draw.rect(self.image, (160, 60, 40), (30, 6, 6, 4))
        pygame.draw.circle(self.image, COL_WHITE, (12, 8), 3)
        pygame.draw.circle(self.image, COL_WHITE, (24, 8), 3)
        pygame.draw.circle(self.image, COL_BLACK, (13, 8), 2)
        pygame.draw.circle(self.image, COL_BLACK, (23, 8), 2)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.patrol_width = patrol_width
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag:
            return
        self.pos_x += KELP_CRAB_SPEED * self.direction * dt
        if self.pos_x > self.origin_x + self.patrol_width:
            self.pos_x = self.origin_x + self.patrol_width
            self.direction = -1.0
        elif self.pos_x < self.origin_x - self.patrol_width:
            self.pos_x = self.origin_x - self.patrol_width
            self.direction = 1.0
        self.rect.x = _fl(self.pos_x)
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class BasaltGolem(pygame.sprite.Sprite):
    """Level 5. Disguised pillar that lunges when close."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._img_dormant = pygame.Surface((30, 50), pygame.SRCALPHA)
        pygame.draw.rect(self._img_dormant, COL_BASALT, (0, 0, 30, 50), border_radius=3)
        self._img_active = pygame.Surface((30, 50), pygame.SRCALPHA)
        pygame.draw.rect(self._img_active, (90, 80, 80), (0, 0, 30, 50), border_radius=3)
        pygame.draw.circle(self._img_active, (255, 80, 40), (10, 15), 4)
        pygame.draw.circle(self._img_active, (255, 80, 40), (20, 15), 4)
        self.image = self._img_dormant
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.state = "dormant"
        self.state_timer: float = 0.0
        self.strike_dir: float = 0.0
        self.origin_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag or player is None:
            return
        # Gravity
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0

        dist = abs(player.rect.centerx - self.rect.centerx)
        if self.state == "dormant":
            self.image = self._img_dormant
            if dist < GOLEM_STRIKE_RANGE:
                self.state = "telegraph"
                self.state_timer = 0.3
                self.strike_dir = 1.0 if player.rect.centerx > self.rect.centerx else -1.0
        elif self.state == "telegraph":
            self.image = self._img_active
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "striking"
                self.state_timer = 0.4
        elif self.state == "striking":
            self.image = self._img_active
            self.rect.x += _fl(GOLEM_STRIKE_SPEED * self.strike_dir * dt)
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "cooldown"
                self.state_timer = GOLEM_COOLDOWN
        elif self.state == "cooldown":
            self.image = self._img_dormant
            # Return to origin
            dx = self.origin_x - self.rect.x
            if abs(dx) > 2:
                self.rect.x += _fl(dx * 2 * dt)
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "dormant"

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class DustDevil(pygame.sprite.Sprite):
    """Level 6. Invincible erratic sandstorm, must dodge. Minimum 150px patrol
    to ensure the movement pattern reads clearly even in tight spaces.
    """
    is_stompable: bool = False

    def __init__(self, x: int, y: int, patrol_width: float = 300.0) -> None:
        super().__init__()
        # Minimum patrol width so movement reads clearly even in tight spaces
        self.patrol_width = max(150.0, patrol_width)
        # Build a BIG tornado -- wide at top, narrow at ground (real dust-devil shape)
        W, H = 64, 110
        self._frames = []
        for frame_offset in range(6):
            surf = pygame.Surface((W, H), pygame.SRCALPHA)
            # Column slabs: width starts wide at top and tapers to narrow point
            for dy in range(0, H, 3):
                frac = dy / H  # 0 at top, 1 at bottom
                # Wide top (50% of W), narrow bottom (15%)
                base_w = int(W * (0.5 - 0.35 * frac))
                # Swirl wobble -- shifts with frame for rotation illusion
                wobble = int(9 * math.sin(dy * 0.18 + frame_offset * 0.9))
                w = max(4, base_w + abs(wobble))
                off_x = wobble // 2
                # Alpha gradient: more opaque in middle of the column
                alpha = 180 - int(abs(wobble) * 6)
                alpha = max(70, min(200, alpha))
                # Darker sand core, lighter at edges
                col_core = (150, 110, 65, alpha)
                col_edge = (200, 170, 120, max(40, alpha - 60))
                rect_x = (W - w) // 2 + off_x
                pygame.draw.rect(surf, col_core, (rect_x, dy, w, 3))
                # Bright edge highlights to catch the eye
                pygame.draw.rect(surf, col_edge, (rect_x, dy, 2, 3))
                pygame.draw.rect(surf, col_edge, (rect_x + w - 2, dy, 2, 3))
            # Rotating debris streaks (darker, diagonal)
            for i in range(6):
                sx_top = (frame_offset * 4 + i * 11) % W
                sx_bot = (sx_top + W // 2) % W  # crossover diagonal
                pygame.draw.line(surf, (90, 60, 30, 180),
                                 (sx_top, 4), (sx_bot, H - 6), 2)
            # Flying sand particles scattered around
            for _ in range(15):
                px = random.randint(0, W - 1)
                py_ = random.randint(0, H - 1)
                pygame.draw.circle(surf, (220, 190, 130, 200), (px, py_), 1)
            # Cap at top: wide dark "cloud" cap so it reads as a SANDSTORM
            cap_w = int(W * 0.55)
            cap_x = (W - cap_w) // 2
            pygame.draw.ellipse(surf, (120, 90, 55, 200),
                                (cap_x, 0, cap_w, 14))
            pygame.draw.ellipse(surf, (160, 130, 90, 150),
                                (cap_x + 4, 2, cap_w - 8, 10))
            self._frames.append(surf)
        self.image = self._frames[0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.pos_x = float(x)
        self.time: float = random.uniform(0, 6.28)
        self.alive_flag = True
        self._W, self._H = W, H

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        self.time += dt * 3
        self.pos_x = self.origin_x + math.sin(self.time) * self.patrol_width * 0.5
        self.pos_x += math.sin(self.time * 2.7) * self.patrol_width * 0.3
        self.rect.x = _fl(self.pos_x)
        self.rect.y = _fl(FLOOR_Y - self._H + math.sin(self.time * 1.5) * 8)
        # Fast swirl frame cycle (~16fps) for strong rotation feel
        frame_idx = int(self.time * 10) % len(self._frames)
        self.image = self._frames[frame_idx]

    def die(self) -> None:
        pass

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


class CactusScorpion(pygame.sprite.Sprite):
    """Level 6. Fires 45-degree projectiles."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 100.0) -> None:
        super().__init__()
        self.image = pygame.Surface((36, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (160, 120, 60), (4, 8, 28, 18))
        pygame.draw.rect(self.image, (140, 100, 40), (28, 2, 6, 10))
        pygame.draw.circle(self.image, (200, 180, 60), (32, 2), 3)
        pygame.draw.circle(self.image, COL_WHITE, (12, 14), 3)
        pygame.draw.circle(self.image, COL_WHITE, (22, 14), 3)
        pygame.draw.circle(self.image, COL_BLACK, (13, 14), 2)
        pygame.draw.circle(self.image, COL_BLACK, (21, 14), 2)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.patrol_width = patrol_width
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True
        self.fire_timer: float = SCORPION_FIRE_RATE
        self._pending_proj: list[ScorpionProjectile] = []

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag:
            return
        self._pending_proj.clear()
        self.pos_x += ENEMY_PATROL_SPEED * 0.5 * self.direction * dt
        if self.pos_x > self.origin_x + self.patrol_width:
            self.pos_x = self.origin_x + self.patrol_width
            self.direction = -1.0
        elif self.pos_x < self.origin_x - self.patrol_width:
            self.pos_x = self.origin_x - self.patrol_width
            self.direction = 1.0
        self.rect.x = _fl(self.pos_x)
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = SCORPION_FIRE_RATE
            self._pending_proj.append(
                ScorpionProjectile(self.rect.centerx, self.rect.top, self.direction))

    def get_new_projectiles(self) -> list[ScorpionProjectile]:
        return self._pending_proj

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class StalactiteSpider(pygame.sprite.Sprite):
    """Level 7. Drops from ceiling when player passes below."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((28, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (60, 50, 50), (4, 2, 20, 16))
        for lx in (2, 8, 16, 22):
            pygame.draw.line(self.image, (50, 40, 40), (lx, 10), (lx - 2, 18), 1)
        pygame.draw.circle(self.image, (200, 40, 40), (11, 7), 2)
        pygame.draw.circle(self.image, (200, 40, 40), (17, 7), 2)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.state = "hanging"
        self.origin_y = y
        self.velocity_y: float = 0.0
        self.alive_flag = True
        self.pos_x = float(x)
        self.direction: float = 1.0

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag or player is None:
            return
        if self.state == "hanging":
            if (abs(player.rect.centerx - self.rect.centerx) < SPIDER_DROP_RANGE
                    and player.rect.centery > self.rect.centery):
                self.state = "dropping"
                self.velocity_y = 0
        elif self.state == "dropping":
            self.velocity_y += GRAVITY * dt
            if self.velocity_y > SPIDER_DROP_SPEED:
                self.velocity_y = SPIDER_DROP_SPEED
            self.rect.y += _fl(self.velocity_y * dt)
            for hit in pygame.sprite.spritecollide(self, platforms, False):
                if self.velocity_y > 0:
                    self.rect.bottom = hit.rect.top
                    self.velocity_y = 0
                    self.state = "grounded"
                    self.pos_x = float(self.rect.x)
        elif self.state == "grounded":
            self.pos_x += ENEMY_PATROL_SPEED * 0.6 * self.direction * dt
            if abs(self.pos_x - self.rect.x) > 80:
                self.direction *= -1
            self.rect.x = _fl(self.pos_x)

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class FalseGlowworm(pygame.sprite.Sprite):
    """Level 7. Looks like light source, snaps shut as trap."""
    is_stompable: bool = False

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._img_lure = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self._img_lure, (150, 255, 100), (8, 8), 8)
        pygame.draw.circle(self._img_lure, (200, 255, 180), (8, 8), 4)
        self._img_snap = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self._img_snap, (255, 60, 40), (8, 8), 8)
        pygame.draw.circle(self._img_snap, (255, 120, 100), (8, 8), 4)
        self.image = self._img_lure
        self.rect = self.image.get_rect(center=(x, y))
        self.state = "luring"
        self.state_timer: float = 0.0
        self.alive_flag = True

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if player is None:
            return
        dist = math.hypot(player.rect.centerx - self.rect.centerx,
                          player.rect.centery - self.rect.centery)
        if self.state == "luring":
            self.image = self._img_lure
            if dist < GLOWWORM_SNAP_RANGE:
                self.state = "snapping"
                self.state_timer = 0.5
        elif self.state == "snapping":
            self.image = self._img_snap
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "cooldown"
                self.state_timer = 3.0
        elif self.state == "cooldown":
            self.image = self._img_lure
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "luring"

    def die(self) -> None:
        pass  # invincible


class BrineShard(pygame.sprite.Sprite):
    """Level 8. Static crystal that grows when player stands still nearby."""
    is_stompable: bool = False

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.base_size = 16
        self.size_scale: float = 1.0
        self._regen_image()
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.base_y = y
        self.alive_flag = True

    def _regen_image(self) -> None:
        sz = max(8, int(self.base_size * self.size_scale))
        self.image = pygame.Surface((sz, sz * 2), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, COL_SALT,
                            [(sz // 2, 0), (sz, sz * 2), (0, sz * 2)])
        pygame.draw.polygon(self.image, COL_ICE,
                            [(sz // 2, sz // 2), (sz - 2, sz * 2), (2, sz * 2)])

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if player is None:
            return
        dist = math.hypot(player.rect.centerx - self.rect.centerx,
                          player.rect.centery - self.rect.centery)
        player_still = abs(player.velocity_x) < 10
        if dist < BRINE_DMG_RADIUS * 2 and player_still:
            self.size_scale = min(3.0, self.size_scale + BRINE_GROW_RATE * dt)
        else:
            self.size_scale = max(1.0, self.size_scale - BRINE_GROW_RATE * 0.5 * dt)
        old_center = self.rect.center
        self._regen_image()
        self.rect = self.image.get_rect(center=old_center)

    def die(self) -> None:
        pass


class ReflectionPhantom(pygame.sprite.Sprite):
    """Level 8. Patrol enemy only visible in reflection."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 200.0) -> None:
        super().__init__()
        self.image = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (*COL_WHITE, 60), (2, 2, 32, 32))
        pygame.draw.circle(self.image, (*COL_ICE, 80), (12, 14), 3)
        pygame.draw.circle(self.image, (*COL_ICE, 80), (24, 14), 3)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.patrol_width = patrol_width
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True

    def update(self, dt: float, platforms: pygame.sprite.Group,
               player=None) -> None:
        if not self.alive_flag:
            return
        self.pos_x += PHANTOM_SPEED * self.direction * dt
        if self.pos_x > self.origin_x + self.patrol_width:
            self.pos_x = self.origin_x + self.patrol_width
            self.direction = -1.0
        elif self.pos_x < self.origin_x - self.patrol_width:
            self.pos_x = self.origin_x - self.patrol_width
            self.direction = 1.0
        self.rect.x = _fl(self.pos_x)
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


# ===================================================================
# NPC
# ===================================================================

class NPC(pygame.sprite.Sprite):
    """Non-combat character that shows dialog when player approaches."""

    def __init__(self, x: int, y: int, name: str,
                 dialog: list[str], color: tuple) -> None:
        super().__init__()
        self.image = pygame.Surface((32, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, color, (2, 4, 28, 32))
        pygame.draw.circle(self.image, color, (16, 8), 10)
        pygame.draw.circle(self.image, COL_WHITE, (12, 7), 3)
        pygame.draw.circle(self.image, COL_WHITE, (20, 7), 3)
        pygame.draw.circle(self.image, COL_BLACK, (13, 7), 2)
        pygame.draw.circle(self.image, COL_BLACK, (19, 7), 2)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.name = name
        self.dialog_lines = dialog
        self.current_line = 0
        self.show_dialog = False

    def update(self, dt: float, player) -> None:
        dist = math.hypot(player.rect.centerx - self.rect.centerx,
                          player.rect.centery - self.rect.centery)
        self.show_dialog = dist < NPC_RANGE


# ===================================================================
# LEVEL 14: FUNGAL HOLLOWS -- MushroomSpring + SporePuffer
# ===================================================================

class MushroomSpring(pygame.sprite.Sprite):
    """Always-active bounce pad. Player landing on it gets launched upward."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._base = self._make_surf(False)
        self._compressed = self._make_surf(True)
        self.image = self._base
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.compress_timer: float = 0.0

    @staticmethod
    def _make_surf(compressed: bool) -> pygame.Surface:
        W, H = 56, 32 if not compressed else 20
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        # Short stalk (white) at the bottom
        stalk_h = 6 if not compressed else 3
        pygame.draw.rect(surf, (230, 220, 210),
                         (W // 2 - 4, H - stalk_h, 8, stalk_h))
        # Cap (magenta with yellow spots)
        cap_h = H - stalk_h
        pygame.draw.ellipse(surf, (180, 60, 160), (0, 0, W, cap_h))
        # Highlight on top
        pygame.draw.ellipse(surf, (230, 130, 200),
                            (6, 2, W - 12, cap_h // 2))
        # Yellow spots
        for dx, dy in [(W // 4, cap_h // 2), (W * 3 // 4, cap_h // 2),
                       (W // 2, cap_h // 4)]:
            pygame.draw.circle(surf, (255, 240, 130), (dx, dy), 3)
            pygame.draw.circle(surf, (255, 255, 200), (dx - 1, dy - 1), 1)
        return surf

    def compress(self) -> None:
        self.compress_timer = MUSHROOM_COMPRESS_SEC
        self.image = self._compressed
        # Adjust rect so bottom stays in place when image shrinks
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

    def update(self, dt: float) -> None:  # type: ignore[override]
        if self.compress_timer > 0:
            self.compress_timer -= dt
            if self.compress_timer <= 0:
                old_midbottom = self.rect.midbottom
                self.image = self._base
                self.rect = self.image.get_rect(midbottom=old_midbottom)


class PoisonSpore(pygame.sprite.Sprite):
    """Slow-drifting spore cloud that damages on contact."""

    def __init__(self, x: int, y: int, drift_x: float) -> None:
        super().__init__()
        W, H = 22, 22
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Fuzzy sickly-green orb
        for r, a in [(10, 80), (7, 140), (4, 200)]:
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (160, 220, 120, a), (r, r), r)
            self._base.blit(surf, (W // 2 - r, H // 2 - r))
        self.image = self._base
        self.rect = self.image.get_rect(center=(x, y))
        self._px, self._py = float(x), float(y)
        self._vx = drift_x
        self._vy = -SPORE_DRIFT
        self.lifetime: float = SPORE_LIFETIME
        self.damage: int = SPORE_DAMAGE

    def update(self, dt: float) -> None:  # type: ignore[override]
        self._px += self._vx * dt
        self._py += self._vy * dt
        self.rect.center = (int(self._px), int(self._py))
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()


class SporePuffer(pygame.sprite.Sprite):
    """Stationary fungus that releases drifting poison spores."""

    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 0.0) -> None:
        super().__init__()
        W, H = 32, 38
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Stalk
        pygame.draw.rect(self._base, (240, 230, 210), (W // 2 - 4, 12, 8, H - 12))
        # Cap (rounded fungus head)
        pygame.draw.ellipse(self._base, (100, 160, 100), (2, 0, W - 4, 22))
        pygame.draw.ellipse(self._base, (150, 200, 140), (6, 2, W - 12, 10))
        # Dark spots
        for dx, dy in [(W // 3, 10), (W * 2 // 3, 12), (W // 2, 6)]:
            pygame.draw.circle(self._base, (60, 90, 60), (dx, dy), 2)
        # Eyes
        pygame.draw.circle(self._base, COL_WHITE, (W // 2 - 4, 14), 2)
        pygame.draw.circle(self._base, COL_WHITE, (W // 2 + 4, 14), 2)
        pygame.draw.circle(self._base, COL_BLACK, (W // 2 - 4, 14), 1)
        pygame.draw.circle(self._base, COL_BLACK, (W // 2 + 4, 14), 1)
        self.image = self._base.copy()
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.puff_timer: float = random.uniform(0.5, SPORE_INTERVAL)
        self.pending_spores: list[PoisonSpore] = []
        self.alive_flag: bool = True
        self.flash: float = 0.0

    def update(self, dt: float, platforms=None, player=None) -> None:  # type: ignore[override]
        if not self.alive_flag:
            return
        self.puff_timer -= dt
        if self.flash > 0:
            self.flash -= dt
            img = self._base.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        else:
            self.image = self._base
        if self.puff_timer <= 0:
            self.puff_timer = SPORE_INTERVAL
            # Emit 2 spores drifting in opposite horizontal directions
            sx = self.rect.centerx
            sy = self.rect.top + 4
            self.pending_spores.append(PoisonSpore(sx, sy, -SPORE_DRIFT * 0.6))
            self.pending_spores.append(PoisonSpore(sx, sy, SPORE_DRIFT * 0.6))

    def get_new_spores(self) -> list[PoisonSpore]:
        spores = self.pending_spores
        self.pending_spores = []
        return spores

    def die(self) -> None:
        self.alive_flag = False
        self.kill()

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


# ===================================================================
# LEVEL 15: THE CRUCIBLE -- RisingLava + MagmaLeaper
# ===================================================================

class RisingLava(pygame.sprite.Sprite):
    """Lethal lava floor that rises steadily from below.

    Pauses at configured Y values for a breathing period, then resumes.
    """

    def __init__(self, world_width: int, pause_ys: list[int] | None = None) -> None:
        super().__init__()
        self.world_width = world_width
        self.pause_ys = sorted(pause_ys or [], reverse=False)  # ascending (top-most first after sort)
        # Actually we want highest-y first (deepest), then pause higher as we rise
        # pause_ys are Y values where lava pauses. Lower Y = higher on screen.
        # So after rising past y=450 (pause #1), next is y=400, then y=350.
        self.pause_ys = sorted(pause_ys or [], reverse=True)  # e.g. [450, 400, 350]
        self._next_pause_idx: int = 0
        self.current_y: float = float(LAVA_START_Y)  # starts below screen
        self.paused: bool = False
        self.pause_timer: float = 0.0
        self._base = self._make_surf()
        self.image = self._base
        self.rect = self.image.get_rect(topleft=(0, int(self.current_y)))
        self._wave_timer: float = 0.0

    def _make_surf(self) -> pygame.Surface:
        W, H = self.world_width, 260
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        # Molten body gradient
        for y in range(H):
            t = y / H
            r = int(240 - 40 * t)
            g = int(90 - 70 * t)
            b = int(20 - 15 * t)
            pygame.draw.line(surf, (max(0, r), max(0, g), max(0, b)),
                             (0, y), (W, y))
        # Bright crust at top
        pygame.draw.rect(surf, (255, 220, 100), (0, 0, W, 4))
        pygame.draw.rect(surf, (255, 255, 180), (0, 0, W, 1))
        # Bubble specks
        for _ in range(W // 40):
            bx = random.randint(10, W - 10)
            by = random.randint(6, H - 4)
            pygame.draw.circle(surf, (255, 200, 80), (bx, by), 2)
        return surf

    def update(self, dt: float) -> None:  # type: ignore[override]
        self._wave_timer += dt
        if self.paused:
            self.pause_timer -= dt
            if self.pause_timer <= 0:
                self.paused = False
        else:
            self.current_y -= LAVA_RISE_SPEED * dt  # y decreases as lava rises
            # Check pause points
            if self._next_pause_idx < len(self.pause_ys):
                target = self.pause_ys[self._next_pause_idx]
                if self.current_y <= target:
                    self.current_y = float(target)
                    self.paused = True
                    self.pause_timer = LAVA_PAUSE_SEC
                    self._next_pause_idx += 1
        # Subtle wave offset on y
        wave_y = int(self.current_y) + int(math.sin(self._wave_timer * 3) * 2)
        self.rect.y = wave_y


class MagmaLeaper(pygame.sprite.Sprite):
    """Fiery creature that leaps out of the lava in arcs."""

    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 0.0) -> None:
        super().__init__()
        W, H = 30, 30
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.ellipse(self._base, (220, 80, 30), (0, 0, W, H))
        pygame.draw.ellipse(self._base, (255, 150, 50), (4, 2, W - 8, H - 8))
        pygame.draw.circle(self._base, (255, 240, 120), (W // 2, H // 2), 6)
        # Fiery eyes
        pygame.draw.circle(self._base, COL_WHITE, (W // 2 - 5, H // 2 - 2), 2)
        pygame.draw.circle(self._base, COL_WHITE, (W // 2 + 5, H // 2 - 2), 2)
        pygame.draw.circle(self._base, COL_BLACK, (W // 2 - 5, H // 2 - 2), 1)
        pygame.draw.circle(self._base, COL_BLACK, (W // 2 + 5, H // 2 - 2), 1)
        self.image = self._base
        # Spawn far below, then leap periodically
        self.start_x = float(x)
        self.start_y = float(y)
        self.rect = self.image.get_rect(center=(x, y + 200))  # submerged
        self._px, self._py = self.start_x, self.start_y + 200
        self._vy = 0.0
        self.state = "submerged"  # submerged / leaping / falling
        self.leap_timer: float = random.uniform(1.0, LEAPER_INTERVAL)
        self.alive_flag = True
        self.flash: float = 0.0

    def update(self, dt: float, platforms=None, player=None) -> None:  # type: ignore[override]
        if not self.alive_flag:
            return
        if self.flash > 0:
            self.flash -= dt
        if self.state == "submerged":
            self.leap_timer -= dt
            if self.leap_timer <= 0:
                self.state = "leaping"
                self._vy = LEAPER_JUMP
                # Leap from current x position; slightly track toward player
                if player is not None:
                    dx = player.rect.centerx - self._px
                    self._px += max(-100, min(100, dx * 0.3))
                self._py = self.start_y
        elif self.state in ("leaping", "falling"):
            self._vy += GRAVITY * dt
            self._py += self._vy * dt
            if self._vy > 0:
                self.state = "falling"
            if self._py > self.start_y + 200:
                # Back under
                self.state = "submerged"
                self.leap_timer = LEAPER_INTERVAL
                self._py = self.start_y + 200
        self.rect.center = (int(self._px), int(self._py))
        # Flash on hit
        if self.flash > 0:
            img = self._base.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        else:
            self.image = self._base

    def die(self) -> None:
        self.alive_flag = False
        self.kill()

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


# ===================================================================
# LEVEL 16: TIDAL LOCKS -- TimedGate + TidalCrab
# ===================================================================

class TimedGate(pygame.sprite.Sprite):
    """Platform that cycles between solid and intangible.

    Gates in group A are solid while group B is intangible, then swap.
    Added/removed from platforms_group automatically.
    """

    # Shared class-level clock so all gates stay in sync
    _global_timer: float = 0.0

    def __init__(self, x: int, y: int, w: int, h: int,
                 group_id: str, platforms_group: pygame.sprite.Group) -> None:
        super().__init__()
        self.group_id = group_id  # "A" or "B"
        self._platforms_group = platforms_group
        self.rect = pygame.Rect(x, y, w, h)
        self._solid_img = self._make_surf(w, h, lit=True)
        self._intangible_img = self._make_surf(w, h, lit=False)
        self.solid: bool = (group_id == "A")  # A starts solid, B starts intangible
        self.image = self._solid_img if self.solid else self._intangible_img
        if self.solid:
            platforms_group.add(self)
        self._flicker: float = 0.0

    @staticmethod
    def _make_surf(w: int, h: int, lit: bool) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if lit:
            # Solid stone with glowing cyan runes
            pygame.draw.rect(surf, (80, 100, 130), (0, 0, w, h))
            pygame.draw.rect(surf, (140, 180, 220), (0, 0, w, 3))
            pygame.draw.rect(surf, (60, 80, 110), (0, h - 3, w, 3))
            # Cyan rune dots
            for i in range(w // 24):
                rx = 12 + i * 24
                if rx < w - 6:
                    pygame.draw.circle(surf, (80, 220, 255),
                                      (rx, h // 2), 3)
        else:
            # Ghostly outline
            pygame.draw.rect(surf, (80, 100, 130, 60), (0, 0, w, h))
            pygame.draw.rect(surf, (140, 180, 220, 120), (0, 0, w, h), 2)
            for i in range(w // 24):
                rx = 12 + i * 24
                if rx < w - 6:
                    pygame.draw.circle(surf, (80, 180, 220, 80),
                                      (rx, h // 2), 3, 1)
        return surf

    @classmethod
    def tick_global(cls, dt: float) -> None:
        cls._global_timer += dt
        if cls._global_timer >= GATE_CYCLE_SEC:
            cls._global_timer = 0.0

    def update(self, dt: float) -> None:  # type: ignore[override]
        # Flicker during telegraph phase
        in_phase_a = TimedGate._global_timer < (GATE_CYCLE_SEC * 0.5)
        time_until_swap = (GATE_CYCLE_SEC * 0.5) - (
            TimedGate._global_timer % (GATE_CYCLE_SEC * 0.5))
        flickering = time_until_swap < GATE_TELEGRAPH_SEC

        should_be_solid = (self.group_id == "A") == in_phase_a
        if should_be_solid and not self.solid:
            self.solid = True
            self._platforms_group.add(self)
        elif not should_be_solid and self.solid:
            self.solid = False
            self._platforms_group.remove(self)
        # Choose image with flicker
        if flickering and self.solid:
            # Alternate between solid and intangible at 10Hz
            t = pygame.time.get_ticks()
            self.image = self._solid_img if (t // 100) % 2 == 0 else self._intangible_img
        else:
            self.image = self._solid_img if self.solid else self._intangible_img


class TidalCrab(pygame.sprite.Sprite):
    """Patrols on gates. Falls when its gate vanishes, relocates on landing."""

    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 150.0) -> None:
        super().__init__()
        W, H = 30, 22
        self._left = pygame.Surface((W, H), pygame.SRCALPHA)
        # Teal body
        pygame.draw.ellipse(self._left, (80, 140, 160), (3, 4, W - 6, H - 6))
        # Orange claws
        pygame.draw.circle(self._left, (220, 130, 60), (3, H // 2), 4)
        pygame.draw.circle(self._left, (220, 130, 60), (W - 3, H // 2), 4)
        # Eye stalks
        pygame.draw.line(self._left, (80, 140, 160),
                         (W // 2 - 3, 5), (W // 2 - 3, 1), 1)
        pygame.draw.line(self._left, (80, 140, 160),
                         (W // 2 + 3, 5), (W // 2 + 3, 1), 1)
        pygame.draw.circle(self._left, COL_BLACK, (W // 2 - 3, 1), 1)
        pygame.draw.circle(self._left, COL_BLACK, (W // 2 + 3, 1), 1)
        self._right = pygame.transform.flip(self._left, True, False)
        self.image = self._left
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self._px = float(x)
        self._py = float(y - H)
        self.vx = -TIDAL_CRAB_SPEED
        self.vy = 0.0
        self.start_x = x
        self.patrol_width = patrol_width
        self.alive_flag = True
        self.flash: float = 0.0

    def update(self, dt: float, platforms, player) -> None:  # type: ignore[override]
        if not self.alive_flag:
            return
        if self.flash > 0:
            self.flash -= dt
        # Gravity
        self.vy += GRAVITY * dt
        if self.vy > TERMINAL_VELOCITY:
            self.vy = TERMINAL_VELOCITY
        # X movement + patrol bounds
        self._px += self.vx * dt
        if self._px < self.start_x - self.patrol_width:
            self._px = self.start_x - self.patrol_width
            self.vx = abs(self.vx)
        elif self._px > self.start_x + self.patrol_width:
            self._px = self.start_x + self.patrol_width
            self.vx = -abs(self.vx)
        self.image = self._left if self.vx < 0 else self._right
        # Y movement
        self._py += self.vy * dt
        self.rect.x = int(self._px)
        self.rect.y = int(self._py)
        # Floor collision (via platforms group)
        hit = pygame.sprite.spritecollideany(self, platforms)
        if hit and self.vy > 0:
            self.rect.bottom = hit.rect.top
            self._py = float(self.rect.y)
            self.vy = 0.0
        # Fall off screen if gate vanishes
        if self.rect.top > 600:
            self._py = -40.0  # respawn up top, re-fall
            self.rect.y = int(self._py)
        if self.flash > 0:
            img = self.image.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img

    def die(self) -> None:
        self.alive_flag = False
        self.kill()

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


# ===================================================================
# LEVEL 17: PHANTOM CORRIDOR -- TeleportPortal + PhaseWraith
# ===================================================================

_PORTAL_PAIR_COLORS = [
    (0, 220, 255), (255, 80, 220), (255, 200, 50), (120, 255, 120),
]


class TeleportPortal(pygame.sprite.Sprite):
    """Linked portal. Entering transports player to partner's position."""

    def __init__(self, x: int, y: int, pair_id: int) -> None:
        super().__init__()
        self.pair_id = pair_id
        self.color = _PORTAL_PAIR_COLORS[pair_id % len(_PORTAL_PAIR_COLORS)]
        self.partner: TeleportPortal | None = None
        self.active: bool = True
        self.cooldown: float = 0.0
        self._rot: float = 0.0
        self._w, self._h = 44, 64
        self.rect = pygame.Rect(0, 0, self._w, self._h)
        self.rect.midbottom = (x, y)
        self.image = self._make_surf()

    def _make_surf(self) -> pygame.Surface:
        W, H = self._w, self._h
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        alpha_scale = 1.0 if self.active else 0.4
        cr, cg, cb = self.color
        # Outer glowing ring
        for r, a_f in ((1.0, 80), (0.8, 140), (0.6, 200)):
            w2 = int(W * r)
            h2 = int(H * r)
            ox = (W - w2) // 2
            oy = (H - h2) // 2
            alpha = int(a_f * alpha_scale)
            pygame.draw.ellipse(surf, (cr, cg, cb, alpha),
                                (ox, oy, w2, h2), 2)
        # Swirl lines
        cx, cy = W // 2, H // 2
        for i in range(4):
            angle = self._rot + i * math.pi / 2
            x1 = cx + int(math.cos(angle) * W * 0.25)
            y1 = cy + int(math.sin(angle) * H * 0.25)
            x2 = cx + int(math.cos(angle) * W * 0.4)
            y2 = cy + int(math.sin(angle) * H * 0.4)
            pygame.draw.line(surf, (cr, cg, cb, int(220 * alpha_scale)),
                             (x1, y1), (x2, y2), 2)
        # Core
        pygame.draw.circle(surf, (255, 255, 255, int(200 * alpha_scale)),
                          (cx, cy), 5)
        return surf

    def teleport(self) -> None:
        self.active = False
        self.cooldown = PORTAL_COOLDOWN_SEC

    def update(self, dt: float) -> None:  # type: ignore[override]
        self._rot += dt * 3.0
        if self.cooldown > 0:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self.active = True
        self.image = self._make_surf()


class PhaseWraith(pygame.sprite.Sprite):
    """Patrols and teleports through nearby active portals."""

    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 150.0) -> None:
        super().__init__()
        W, H = 30, 40
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Ghostly translucent body
        body_pts = [(W // 2, 2), (W - 4, H // 2), (W - 6, H - 4),
                    (W // 2, H - 6), (6, H - 4), (4, H // 2)]
        pygame.draw.polygon(self._base, (180, 140, 220, 160), body_pts)
        pygame.draw.polygon(self._base, (220, 180, 255, 200), body_pts, 2)
        # Glowing eyes
        pygame.draw.circle(self._base, (255, 200, 255),
                          (W // 2 - 5, H // 2 - 2), 3)
        pygame.draw.circle(self._base, (255, 200, 255),
                          (W // 2 + 5, H // 2 - 2), 3)
        pygame.draw.circle(self._base, COL_BLACK,
                          (W // 2 - 5, H // 2 - 2), 1)
        pygame.draw.circle(self._base, COL_BLACK,
                          (W // 2 + 5, H // 2 - 2), 1)
        self.image = self._base
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self._px = float(x)
        self._py = float(y - H)
        self.vx = -WRAITH_SPEED
        self.start_x = x
        self.patrol_width = patrol_width
        self.alive_flag = True
        self.flash: float = 0.0
        self.teleport_cooldown: float = 0.0

    def update(self, dt: float, platforms, player) -> None:  # type: ignore[override]
        if not self.alive_flag:
            return
        if self.flash > 0:
            self.flash -= dt
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt
        self._px += self.vx * dt
        if self._px < self.start_x - self.patrol_width:
            self._px = self.start_x - self.patrol_width
            self.vx = abs(self.vx)
        elif self._px > self.start_x + self.patrol_width:
            self._px = self.start_x + self.patrol_width
            self.vx = -abs(self.vx)
        self.rect.x = int(self._px)
        self.rect.y = int(self._py)
        # Subtle float
        self._py += math.sin(pygame.time.get_ticks() / 200.0) * 0.3
        if self.flash > 0:
            img = self._base.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        else:
            self.image = self._base

    def teleport_to(self, x: int, y: int) -> None:
        self._px = float(x)
        self._py = float(y - self.rect.height)
        self.teleport_cooldown = 2.0

    def die(self) -> None:
        self.alive_flag = False
        self.kill()

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


# ===================================================================
# LEVEL 18: THE GRAVITY ENGINE -- GravityZone + GravityDrone
# ===================================================================

class GravityZone(pygame.sprite.Sprite):
    """Rectangular zone that alters player gravity while inside.

    Types: 'low' (0.3x), 'high' (2.0x), 'reverse' (-1.0x).
    """

    def __init__(self, x: int, y: int, w: int, h: int, gravity_type: str) -> None:
        super().__init__()
        self.gravity_type = gravity_type
        self.rect = pygame.Rect(x, y, w, h)
        self.image = self._make_surf(w, h, gravity_type)
        self._wave_timer: float = 0.0

    @staticmethod
    def _make_surf(w: int, h: int, gtype: str) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if gtype == "low":
            # Pale blue with upward lines
            surf.fill((100, 180, 255, 30))
            pygame.draw.rect(surf, (140, 220, 255, 120), (0, 0, w, h), 2)
            for i in range(0, w, 20):
                pygame.draw.line(surf, (160, 230, 255, 80),
                                 (i + 10, h), (i + 10, h - 20), 2)
                # Arrow up
                pygame.draw.line(surf, (160, 230, 255, 120),
                                 (i + 10, h - 20), (i + 6, h - 16), 2)
                pygame.draw.line(surf, (160, 230, 255, 120),
                                 (i + 10, h - 20), (i + 14, h - 16), 2)
        elif gtype == "reverse":
            # Purple with inverted arrows
            surf.fill((180, 100, 220, 40))
            pygame.draw.rect(surf, (220, 140, 255, 140), (0, 0, w, h), 2)
            for i in range(0, w, 30):
                # Arrow pointing UP (player falls up)
                pygame.draw.line(surf, (220, 140, 255, 120),
                                 (i + 15, h - 10), (i + 15, 10), 2)
                pygame.draw.line(surf, (220, 140, 255, 140),
                                 (i + 15, 10), (i + 10, 18), 2)
                pygame.draw.line(surf, (220, 140, 255, 140),
                                 (i + 15, 10), (i + 20, 18), 2)
        else:  # high
            # Dark red with downward lines
            surf.fill((180, 40, 40, 35))
            pygame.draw.rect(surf, (220, 70, 70, 130), (0, 0, w, h), 2)
            for i in range(0, w, 20):
                pygame.draw.line(surf, (255, 100, 80, 120),
                                 (i + 10, 0), (i + 10, 20), 3)
                pygame.draw.line(surf, (255, 100, 80, 140),
                                 (i + 10, 20), (i + 6, 16), 2)
                pygame.draw.line(surf, (255, 100, 80, 140),
                                 (i + 10, 20), (i + 14, 16), 2)
        return surf

    def get_multiplier(self) -> float:
        if self.gravity_type == "low":
            return GRAVITY_LOW_MULT
        if self.gravity_type == "high":
            return GRAVITY_HIGH_MULT
        return GRAVITY_REVERSE_MULT

    def update(self, dt: float) -> None:  # type: ignore[override]
        # Static zone; no state to update
        pass


class GravityDrone(pygame.sprite.Sprite):
    """Hovering mech sphere that pulls the player toward itself."""

    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 0.0) -> None:
        super().__init__()
        W, H = 32, 32
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Metal sphere body
        pygame.draw.circle(self._base, (100, 110, 130), (W // 2, H // 2), W // 2 - 2)
        pygame.draw.circle(self._base, (140, 150, 180),
                          (W // 2 - 3, H // 2 - 3), W // 3)
        # Glowing core
        pygame.draw.circle(self._base, (180, 120, 255), (W // 2, H // 2), 5)
        pygame.draw.circle(self._base, (230, 200, 255), (W // 2, H // 2), 3)
        # Ring
        pygame.draw.ellipse(self._base, (180, 150, 220),
                           (2, H // 2 - 2, W - 4, 4), 2)
        self.image = self._base
        self.rect = self.image.get_rect(center=(x, y))
        self.base_y = float(y)
        self.alive_flag = True
        self.flash: float = 0.0
        self._bob: float = random.uniform(0, 6.28)

    def update(self, dt: float, platforms=None, player=None) -> None:  # type: ignore[override]
        if not self.alive_flag:
            return
        if self.flash > 0:
            self.flash -= dt
        self._bob += dt * 2.0
        self.rect.y = int(self.base_y + math.sin(self._bob) * 6)
        if self.flash > 0:
            img = self._base.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        else:
            self.image = self._base

    def die(self) -> None:
        self.alive_flag = False
        self.kill()

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


# ===================================================================
# HomingSpecter -- tracking aerial enemy (anti-glide-cheese)
# ===================================================================

class HomingSpecter(pygame.sprite.Sprite):
    """Ghostly flier that always tracks the player. Stompable.

    Accelerates when player is airborne/gliding -- designed to punish
    air-cheese strategies.
    """

    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 0.0) -> None:
        super().__init__()
        W, H = 34, 28
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        body_pts = [(W // 2, 2), (W - 2, H // 2),
                    (W - 6, H - 2), (W // 2, H - 6),
                    (6, H - 2), (2, H // 2)]
        pygame.draw.polygon(self._base, (180, 100, 200, 180), body_pts)
        pygame.draw.polygon(self._base, (230, 160, 255, 220), body_pts, 2)
        pygame.draw.circle(self._base, (255, 80, 80),
                          (W // 2 - 5, H // 2), 3)
        pygame.draw.circle(self._base, (255, 80, 80),
                          (W // 2 + 5, H // 2), 3)
        pygame.draw.circle(self._base, COL_WHITE,
                          (W // 2 - 5, H // 2 - 1), 1)
        pygame.draw.circle(self._base, COL_WHITE,
                          (W // 2 + 5, H // 2 - 1), 1)
        self.image = self._base
        self.rect = self.image.get_rect(center=(x, y))
        self._px, self._py = float(x), float(y)
        self._vx, self._vy = 0.0, 0.0
        self.alive_flag = True
        self.flash: float = 0.0
        self._base_speed = 90.0
        self._chase_speed = 180.0

    def update(self, dt, platforms=None, player=None):
        if not self.alive_flag:
            return
        if self.flash > 0:
            self.flash -= dt
        if player is not None:
            target = self._base_speed
            if not player.is_on_ground:
                target = self._chase_speed
            if getattr(player, 'is_gliding', False):
                target = self._chase_speed * 1.3
            dx = player.rect.centerx - self._px
            dy = player.rect.centery - self._py
            dist = math.hypot(dx, dy)
            if dist > 5:
                self._vx = (dx / dist) * target
                self._vy = (dy / dist) * target
            else:
                self._vx = self._vy = 0
        self._px += self._vx * dt
        self._py += self._vy * dt
        # Compute bob offset and apply in ONE rect.center assignment so the
        # collision rect always matches the final drawn position.
        bob = int(math.sin(pygame.time.get_ticks() / 180.0) * 2)
        self.rect.center = (int(self._px), int(self._py) + bob)
        if self.flash > 0:
            img = self._base.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img
        else:
            self.image = self._base

    def die(self):
        self.alive_flag = False
        self.kill()

    def alive(self):
        return self.alive_flag


# ===================================================================
# ForgeHammer -- L15 ceiling hammer, lethal while slamming
# ===================================================================

class ForgeHammer(pygame.sprite.Sprite):
    """Ceiling-mounted iron hammer. Periodically slams to floor."""

    is_stompable: bool = False

    def __init__(self, x, y, patrol_width=0.0):
        super().__init__()
        W, H = 60, 40
        self._base = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.rect(self._base, (50, 50, 60), (4, 4, W - 8, H - 8))
        pygame.draw.rect(self._base, (90, 90, 110), (6, 6, W - 12, 4))
        pygame.draw.rect(self._base, (30, 30, 40), (4, H - 8, W - 8, 4))
        pygame.draw.circle(self._base, (160, 120, 60), (W // 2, 12), 4)
        pygame.draw.circle(self._base, (220, 180, 100), (W // 2, 12), 2)
        for i, j in [(8, 8), (W - 12, 8), (8, H - 12), (W - 12, H - 12)]:
            pygame.draw.circle(self._base, (20, 20, 25), (i, j), 2)
        self.image = self._base
        self.rect = self.image.get_rect(topleft=(x, 0))
        self.base_x = float(x)
        self._top_y = 0.0
        self._bottom_y = float(y)
        self._py = self._top_y
        self.state = "holding"
        self.timer = random.uniform(1.0, 3.0)
        self.alive_flag = True
        self.flash = 0.0

    def update(self, dt, platforms=None, player=None):
        self.timer -= dt
        if self.state == "holding":
            if self.timer <= 0:
                self.state = "telegraph"
                self.timer = 0.5
        elif self.state == "telegraph":
            if self.timer <= 0:
                self.state = "slamming"
        elif self.state == "slamming":
            self._py += 1400 * dt
            if self._py >= self._bottom_y:
                self._py = self._bottom_y
                self.state = "rising"
                self.timer = 0.3
        elif self.state == "rising":
            if self.timer <= 0:
                self._py -= 200 * dt
                if self._py <= self._top_y:
                    self._py = self._top_y
                    self.state = "holding"
                    self.timer = random.uniform(2.5, 4.0)
        self.rect.x = int(self.base_x)
        self.rect.y = int(self._py)

    def is_lethal(self):
        return self.state == "slamming"

    def die(self):
        pass

    def alive(self):
        return True


# ===================================================================
# VoidEater -- L17 Contact damage when open
# ===================================================================

class VoidEater(pygame.sprite.Sprite):
    is_stompable: bool = False

    def __init__(self, x, y, patrol_width=0.0):
        super().__init__()
        self._base = self._make_surf(False)
        self._open = self._make_surf(True)
        self.image = self._base
        self.rect = self.image.get_rect(center=(x, y))
        self.base_x, self.base_y = float(x), float(y)
        self.alive_flag = True
        self.flash = 0.0
        self._pulse = 0.0
        self.open_timer = random.uniform(1.5, 3.0)
        self.state = "closed"

    @staticmethod
    def _make_surf(open_mouth):
        W, H = 36, 36
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for r, a in [(16, 120), (14, 180), (12, 230)]:
            pygame.draw.circle(surf, (20, 5, 40, a), (W // 2, H // 2), r)
        pygame.draw.circle(surf, (140, 60, 180), (W // 2, H // 2), 16, 2)
        if open_mouth:
            pygame.draw.circle(surf, COL_BLACK, (W // 2, H // 2), 10)
            for ang in range(0, 360, 45):
                t = math.radians(ang)
                tx = int(W // 2 + math.cos(t) * 10)
                ty = int(H // 2 + math.sin(t) * 10)
                pygame.draw.circle(surf, (220, 220, 255), (tx, ty), 2)
        else:
            pygame.draw.line(surf, (80, 20, 100),
                           (W // 2 - 6, H // 2), (W // 2 + 6, H // 2), 2)
        pygame.draw.circle(surf, (220, 100, 255),
                         (W // 2 - 4, H // 2 - 4), 2)
        return surf

    def update(self, dt, platforms=None, player=None):
        if not self.alive_flag:
            return
        if self.flash > 0:
            self.flash -= dt
        self._pulse += dt * 2.0
        self.open_timer -= dt
        if self.open_timer <= 0:
            if self.state == "closed":
                self.state = "open"
                self.open_timer = 1.0
                self.image = self._open
            else:
                self.state = "closed"
                self.open_timer = random.uniform(2.0, 3.5)
                self.image = self._base
        self.rect.x = int(self.base_x)
        self.rect.y = int(self.base_y + math.sin(self._pulse) * 8)
        if self.flash > 0:
            img = self.image.copy()
            img.fill((255, 255, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
            self.image = img

    def is_dangerous(self):
        return self.state == "open"

    def die(self):
        self.alive_flag = False
        self.kill()

    def alive(self):
        return self.alive_flag


# ===================================================================
# DarkWall -- blocks movement unless crystal lit nearby (L7/L9/L13/L17)
# ===================================================================

class DarkWall(pygame.sprite.Sprite):
    """Wall that only disappears when a crystal within range is lit."""

    def __init__(self, x, y, w, h, crystals_group, platforms_group,
                 reveal_range=350.0):
        super().__init__()
        self.rect = pygame.Rect(x, y, w, h)
        self._crystals = crystals_group
        self._platforms = platforms_group
        self._reveal_range = reveal_range
        # --- Magical barrier: 4-frame animation with flowing runic energy ---
        self._frames = []
        for phase in range(4):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            # Deep void base with slight violet tint
            surf.fill((12, 4, 28, 235))
            # Layered hex-pattern for barrier "mesh" feel
            for hy in range(-4 + phase * 2, h + 4, 10):
                pygame.draw.line(surf, (60, 30, 100, 180),
                                 (0, hy), (w, hy + 4), 1)
                pygame.draw.line(surf, (60, 30, 100, 180),
                                 (0, hy + 6), (w, hy + 2), 1)
            # Runic bars (thick horizontal energy threads)
            for i, bar_y in enumerate(range(10, h - 10, max(20, h // 4))):
                # Outer purple glow
                pygame.draw.rect(surf, (110, 40, 180),
                                 (3, bar_y - 3, w - 6, 8))
                # Inner bright cyan-purple core
                pygame.draw.rect(surf, (200, 140, 255),
                                 (5, bar_y, w - 10, 2))
                # Animated flowing highlight packet
                packet_x = ((phase * 12) + i * 16) % max(12, w - 12)
                pygame.draw.rect(surf, (255, 230, 255),
                                 (packet_x, bar_y, 8, 2))
            # Central runic sigils (circle + cross)
            for rune_y in [h // 3, 2 * h // 3]:
                cx = w // 2
                # Outer ring (pulses with phase)
                ring_col = (130 + phase * 20, 60 + phase * 10,
                            200 + phase * 10)
                pygame.draw.circle(surf, ring_col, (cx, rune_y),
                                   min(8, w // 3), 2)
                # Inner filled dot
                pygame.draw.circle(surf, (200, 100, 230),
                                   (cx, rune_y), 3)
                pygame.draw.circle(surf, (255, 220, 255),
                                   (cx, rune_y), 1)
                # Cross strokes
                pygame.draw.line(surf, (255, 200, 255),
                                 (cx - 6, rune_y), (cx + 6, rune_y), 1)
                pygame.draw.line(surf, (255, 200, 255),
                                 (cx, rune_y - 6), (cx, rune_y + 6), 1)
            # Glowing edge particles climbing up both sides
            for py_ in range(0, h, 5):
                offset = (phase * 3 + py_ // 5) % 5
                pygame.draw.circle(surf, (200, 120, 255),
                                   (2 + offset, py_), 1)
                pygame.draw.circle(surf, (200, 120, 255),
                                   (w - 3 - offset, py_), 1)
            # Thick bright cap at top and bottom (so it reads as a WALL)
            pygame.draw.rect(surf, (180, 80, 220), (0, 0, w, 3))
            pygame.draw.rect(surf, (255, 180, 255), (0, 0, w, 1))
            pygame.draw.rect(surf, (180, 80, 220), (0, h - 3, w, 3))
            pygame.draw.rect(surf, (255, 180, 255), (0, h - 1, w, 1))
            self._frames.append(surf)
        # Faded frames (shown when nearby crystal is lit -- shows the wall
        # dissolving, still visible as a ghost so the player sees the passage)
        self._faded_frames = []
        for f in self._frames:
            ff = f.copy()
            ff.set_alpha(55)
            self._faded_frames.append(ff)
        self.solid = True
        self.image = self._frames[0]
        self._frame_timer: float = 0.0
        platforms_group.add(self)

    def update(self, dt):
        # Animate across 4 frames at ~6 fps
        self._frame_timer += dt
        frame_idx = int(self._frame_timer * 6) % 4

        nearby_lit = False
        for cr in self._crystals:
            if getattr(cr, 'is_lit', lambda: False)():
                dx = cr.rect.centerx - self.rect.centerx
                dy = cr.rect.centery - self.rect.centery
                if math.hypot(dx, dy) < self._reveal_range:
                    nearby_lit = True
                    break
        should_solid = not nearby_lit
        if should_solid and not self.solid:
            self.solid = True
            self._platforms.add(self)
        elif not should_solid and self.solid:
            self.solid = False
            self._platforms.remove(self)
        # Pick frame from active (solid) or faded bank every tick
        if self.solid:
            self.image = self._frames[frame_idx]
        else:
            self.image = self._faded_frames[frame_idx]
