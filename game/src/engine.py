"""Camera, particle system, parallax background, and screen shake."""

from __future__ import annotations

import math
import random

import pygame

from config import (
    COL_PLAT_DIRT, COL_SKY, COL_WHITE, DUST_LIFE, LEAF_COUNT,
    SCREEN_HEIGHT, SCREEN_WIDTH, SHAKE_DURATION, SHAKE_INTENSITY, SPARKLE_LIFE,
)


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

class Camera:
    """Smooth-follow camera. Logic state is float, render state is int.

    offset_x / offset_y: float -- smooth lerp tracking (logic camera).
    render_x / render_y: int   -- math.floor of offset (render camera).

    All sprites and tiles are drawn relative to render_x/render_y,
    which locks everything to the same integer pixel grid.
    """

    def __init__(self, world_width: int, world_height: int) -> None:
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.render_x: int = 0
        self.render_y: int = 0
        self.world_width = world_width
        self.world_height = world_height

    def update(self, target: pygame.sprite.Sprite, dt: float) -> None:
        # Lock camera directly to player -- no lerp, no float drift.
        # Player rect is always integer, so goal is always integer,
        # which means offset is always integer. Zero sub-pixel jitter.
        goal_x = -target.rect.centerx + SCREEN_WIDTH // 2
        goal_y = -target.rect.centery + SCREEN_HEIGHT // 2
        self.offset_x = float(max(-(self.world_width - SCREEN_WIDTH), min(0, goal_x)))
        self.offset_y = float(max(-(self.world_height - SCREEN_HEIGHT), min(0, goal_y)))
        self.render_x = math.floor(self.offset_x)
        self.render_y = math.floor(self.offset_y)

    def apply(self, entity: pygame.sprite.Sprite) -> pygame.Rect:
        return entity.rect.move(math.floor(self.offset_x), math.floor(self.offset_y))

    def apply_pos(self, x: float, y: float) -> tuple[float, float]:
        return (x + self.offset_x, y + self.offset_y)

    def get_visible_rect(self) -> pygame.Rect:
        return pygame.Rect(-self.render_x, -self.render_y, SCREEN_WIDTH, SCREEN_HEIGHT)


# ---------------------------------------------------------------------------
# Screen Shake
# ---------------------------------------------------------------------------

class ScreenShake:
    def __init__(self) -> None:
        self.timer: float = 0.0
        self.intensity: int = 0

    def trigger(self, intensity: int = SHAKE_INTENSITY,
                duration: float = SHAKE_DURATION) -> None:
        self.timer = duration
        self.intensity = intensity

    def update(self, dt: float) -> tuple[int, int]:
        if self.timer > 0:
            self.timer -= dt
            return (random.randint(-self.intensity, self.intensity),
                    random.randint(-self.intensity, self.intensity))
        return (0, 0)


# ---------------------------------------------------------------------------
# Particle System
# ---------------------------------------------------------------------------

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color",
                 "size", "shape", "gravity")

    def __init__(self, x: float, y: float, vx: float, vy: float,
                 life: float, color: tuple, size: float,
                 shape: str = "circle", gravity: bool = False) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.shape = shape
        self.gravity = gravity


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def update(self, dt: float) -> None:
        alive: list[Particle] = []
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.gravity:
                p.vy += 400 * dt
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, screen: pygame.Surface, camera: Camera) -> None:
        for p in self.particles:
            sx, sy = camera.apply_pos(p.x, p.y)
            if sx < -20 or sx > SCREEN_WIDTH + 20 or sy < -20 or sy > SCREEN_HEIGHT + 20:
                continue
            alpha = max(0, min(255, int(255 * (p.life / p.max_life))))
            r, g, b = p.color
            color = (min(255, r), min(255, g), min(255, b))
            sz = max(1, int(p.size * (p.life / p.max_life)))
            if p.shape == "circle":
                if alpha > 200:
                    pygame.draw.circle(screen, color, (int(sx), int(sy)), sz)
                else:
                    s = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*color, alpha), (sz, sz), sz)
                    screen.blit(s, (int(sx) - sz, int(sy) - sz))
            elif p.shape == "leaf":
                s = pygame.Surface((sz + 2, sz + 2), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (*color, alpha), (0, 0, sz + 2, max(1, sz // 2)))
                screen.blit(s, (int(sx), int(sy)))
            elif p.shape == "rect":
                if alpha > 200:
                    pygame.draw.rect(screen, color, (int(sx), int(sy), sz, sz))
                else:
                    s = pygame.Surface((sz, sz), pygame.SRCALPHA)
                    s.fill((*color, alpha))
                    screen.blit(s, (int(sx), int(sy)))

    def emit_sparkle(self, x: float, y: float, count: int = 8) -> None:
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 180)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                SPARKLE_LIFE + random.uniform(-0.1, 0.1),
                (255, 215 + random.randint(-20, 20), random.randint(0, 80)),
                random.uniform(2, 5), "circle",
            ))

    def emit_dust(self, x: float, y: float, count: int = 5) -> None:
        for _ in range(count):
            self.particles.append(Particle(
                x + random.uniform(-10, 10), y,
                random.uniform(-40, 40), random.uniform(-80, -20),
                DUST_LIFE + random.uniform(0, 0.1),
                (COL_PLAT_DIRT[0] + random.randint(-15, 15),
                 COL_PLAT_DIRT[1] + random.randint(-10, 10),
                 COL_PLAT_DIRT[2] + random.randint(-5, 5)),
                random.uniform(2, 4), "circle", gravity=True,
            ))

    def emit_damage(self, x: float, y: float, count: int = 6) -> None:
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                0.3, (255, random.randint(30, 80), random.randint(0, 30)),
                random.uniform(2, 5), "circle", gravity=True,
            ))

    def emit_death(self, x: float, y: float, count: int = 15) -> None:
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 300)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.3, 0.7),
                (255, random.randint(50, 150), random.randint(0, 50)),
                random.uniform(3, 7), "circle", gravity=True,
            ))

    def emit_ambient_leaves(self, visible_rect: pygame.Rect) -> None:
        leaf_count = sum(1 for p in self.particles if p.shape == "leaf")
        while leaf_count < LEAF_COUNT:
            x = visible_rect.x + random.uniform(0, visible_rect.width)
            y = visible_rect.y + random.uniform(-40, visible_rect.height * 0.4)
            greens = [(60, 140, 40), (40, 120, 30), (80, 160, 50), (50, 130, 20),
                      (70, 150, 35), (90, 170, 55)]
            self.particles.append(Particle(
                x, y,
                random.uniform(-20, 20), random.uniform(15, 45),
                random.uniform(4, 8),
                random.choice(greens),
                random.uniform(3, 6), "leaf",
            ))
            leaf_count += 1


# ---------------------------------------------------------------------------
# Parallax Background -- fully opaque layers, no SRCALPHA artifacts
# ---------------------------------------------------------------------------

class ParallaxBackground:
    """Clean parallax with seamlessly-tileable layers.

    Each layer is drawn on a surface exactly SCREEN_WIDTH wide.
    Features that cross the right edge wrap to the left edge,
    so two copies placed side-by-side have no visible seam.
    """

    def __init__(self) -> None:
        self.w = SCREEN_WIDTH
        self.combined = self._build_combined()
        self.layers: list[tuple[pygame.Surface, float]] = [
            (self.combined, 0.18),
        ]
        # Sky is drawn first (static, no scroll)
        self.sky = self._build_sky()

    def draw(self, screen: pygame.Surface, camera_x: float) -> None:
        bg_w = self.combined.get_width()
        for surface, factor in self.layers:
            parallax_x = camera_x * factor
            offset_x = -(parallax_x % bg_w)
            draw_x = math.floor(offset_x)
            screen.blit(surface, (draw_x, 0))
            screen.blit(surface, (draw_x + bg_w, 0))

    def _build_sky(self) -> pygame.Surface:
        """Static sky gradient + clouds -- never scrolls so no tiling needed."""
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(120 + 80 * t)
            g = int(185 + 45 * t)
            b = int(235 + 15 * t)
            pygame.draw.line(surf, (min(255, r), min(255, g), min(255, b)),
                             (0, y), (SCREEN_WIDTH, y))
        # Clouds
        random.seed(42)
        for _ in range(5):
            cx = random.randint(80, SCREEN_WIDTH - 80)
            cy = random.randint(40, 140)
            for _ in range(6):
                pygame.draw.circle(surf, (215, 228, 242),
                                   (cx + random.randint(-30, 30),
                                    cy + random.randint(-4, 8) + 3),
                                   random.randint(18, 30))
            for _ in range(8):
                pygame.draw.circle(surf, COL_WHITE,
                                   (cx + random.randint(-30, 30),
                                    cy + random.randint(-8, 5)),
                                   random.randint(18, 30))
        random.seed()
        return surf

    def _wrap_polygon(self, surf: pygame.Surface, color: tuple,
                      pts: list[tuple[int, int]]) -> None:
        """Draw a polygon that wraps seamlessly at x=0 and x=self.w."""
        pygame.draw.polygon(surf, color, pts)
        # Also draw shifted copies so edges wrap cleanly
        shifted_left = [(x - self.w, y) for x, y in pts]
        shifted_right = [(x + self.w, y) for x, y in pts]
        pygame.draw.polygon(surf, color, shifted_left)
        pygame.draw.polygon(surf, color, shifted_right)

    def _build_combined(self) -> pygame.Surface:
        """Opaque surface with sky + mountains + trees, tileable."""
        surf = self._build_sky().copy()  # start with sky -- fully opaque

        random.seed(101)
        # Back mountains (blue-gray)
        for i in range(8):
            x = int(i * self.w / 6) + random.randint(-40, 40)
            peak_h = random.randint(190, 290)
            base_w = random.randint(250, 400)
            top_y = SCREEN_HEIGHT - peak_h
            shade = random.randint(-8, 8)
            c = (105 + shade, 130 + shade, 160 + shade)
            self._wrap_polygon(surf, c, [
                (x - base_w // 2, SCREEN_HEIGHT),
                (x, top_y),
                (x + base_w // 2, SCREEN_HEIGHT)])
            # Dark left face
            c2 = (90 + shade, 115 + shade, 145 + shade)
            self._wrap_polygon(surf, c2, [
                (x - base_w // 2, SCREEN_HEIGHT),
                (x, top_y),
                (x - base_w // 8, SCREEN_HEIGHT)])
            # Snow cap (part of the peak, not floating)
            sw = base_w // 7
            self._wrap_polygon(surf, (230, 238, 248), [
                (x - sw, top_y + 18), (x, top_y), (x + sw, top_y + 18)])

        # Front hills (green-gray, shorter)
        for i in range(7):
            x = int(i * self.w / 5) + random.randint(-30, 30)
            peak_h = random.randint(100, 170)
            base_w = random.randint(200, 340)
            top_y = SCREEN_HEIGHT - peak_h
            shade = random.randint(-6, 6)
            c = (80 + shade, 110 + shade, 75 + shade)
            self._wrap_polygon(surf, c, [
                (x - base_w // 2, SCREEN_HEIGHT),
                (x, top_y),
                (x + base_w // 2, SCREEN_HEIGHT)])
            c2 = (90 + shade, 120 + shade, 85 + shade)
            self._wrap_polygon(surf, c2, [
                (x + base_w // 8, SCREEN_HEIGHT),
                (x, top_y),
                (x + base_w // 2, SCREEN_HEIGHT)])

        # Pine trees
        for i in range(18):
            tx = int(i * self.w / 14) + random.randint(-30, 30)
            tree_h = random.randint(60, 110)
            trunk_top = SCREEN_HEIGHT - tree_h
            trunk_w = random.randint(4, 8)
            trunk_c = (70 + random.randint(-8, 8),
                       48 + random.randint(-8, 8),
                       28 + random.randint(-5, 5))
            # Trunk (simple rect, wraps fine without helper)
            for dx in (-self.w, 0, self.w):
                pygame.draw.rect(surf, trunk_c,
                                 (tx - trunk_w // 2 + dx,
                                  trunk_top + tree_h // 3,
                                  trunk_w, tree_h * 2 // 3))
            # Canopy layers
            canopy_c = (32 + random.randint(-8, 12),
                        105 + random.randint(-15, 15),
                        32 + random.randint(-8, 12))
            cw = random.randint(20, 34)
            for li, (ly_f, lw_f) in enumerate(
                    [(0.55, 1.0), (0.35, 0.8), (0.15, 0.6)]):
                ly = trunk_top + int(tree_h * ly_f)
                lw = int(cw * lw_f)
                s = li * 8
                lc = (min(255, canopy_c[0] + s),
                      min(255, canopy_c[1] + s),
                      min(255, canopy_c[2] + s))
                self._wrap_polygon(surf, lc, [
                    (tx - lw, ly),
                    (tx, trunk_top + int(tree_h * 0.12 * (li + 1))),
                    (tx + lw, ly)])

        # Ground strip (dark green blending bar)
        for y in range(SCREEN_HEIGHT - 12, SCREEN_HEIGHT):
            t = (y - (SCREEN_HEIGHT - 12)) / 12
            gc = (int(30 + 20 * t), int(85 + 30 * t), int(28 + 15 * t))
            pygame.draw.line(surf, gc, (0, y), (self.w, y))

        random.seed()
        return surf
