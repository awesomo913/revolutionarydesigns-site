"""Camera, particle system, parallax background, and screen shake."""

from __future__ import annotations

import math
import random
from typing import Any

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
        self.speedrun_lead: float = 1.0
        self.victory_zoom: float = 1.0
        self.squash: float = 1.0
        self.squash_timer: float = 0.0
        self.y_nudge: float = 0.0
        self.y_nudge_timer: float = 0.0
        self.y_nudge_duration: float = 0.1

    def update(self, target: pygame.sprite.Sprite, dt: float, level: Any = None) -> None:
        # Direct lock for no jitter + stronger velocity lead for juicy anticipation.
        # Lead peeks ahead on speed + glide/dash; feels alive and guides eye without wresting control.
        goal_x = -target.rect.centerx + SCREEN_WIDTH // 2
        goal_y = -target.rect.centery + SCREEN_HEIGHT // 2
        vx = getattr(target, "velocity_x", 0.0)
        vy = getattr(target, "velocity_y", 0.0)
        # Stronger lookahead on high speed + glide/dash
        lead = vx * 0.18
        if abs(vx) > 220:
            lead = vx * 0.28
        if abs(vx) > 350:
            lead = vx * 0.35
        lead *= getattr(self, 'speedrun_lead', 1.0)
        dashing = getattr(target, 'is_dashing', False)
        gliding = getattr(target, 'is_gliding', False)
        if dashing or gliding:
            lead *= 1.55
            if abs(vx) > 280:
                lead *= 1.15
        # tighter follow for GhostPanda replays (better follow, less predictive swing)
        tname = type(target).__name__
        if 'Ghost' in tname or not hasattr(target, 'velocity_x'):
            lead *= 0.38
        # Clamp total lead so stacked dash + speedrun multipliers (which could reach
        # ~980px) can't shove the player off the screen edge -- keep them visible. (N5)
        lead = max(-300.0, min(300.0, lead))
        goal_x -= lead
        # y-nudge / vertical anticipation (peek where player is headed in air)
        vlead_y = vy * 0.085
        if gliding:
            vlead_y *= 0.55
        goal_y -= vlead_y
        # Subtle inward pull (victory zoom juice)
        z = getattr(self, 'victory_zoom', 1.0)
        if z > 1.001:
            pull = (z - 1.0) * 0.45
            goal_x += (0.0 - goal_x) * pull
            goal_y += (0.0 - goal_y) * pull
        # Level anticipation: subtle bias toward upcoming portals/enemies/vines/gravity -- guides without taking control
        anticipate = 0.0
        ay_bias = 0.0
        if level is not None:
            px = target.rect.centerx if hasattr(target, "rect") else 0
            py = target.rect.centery if hasattr(target, "rect") else 0
            if px:
                look = 380 + min(420, abs(vx) * 0.9)
                bsum = 0.0
                wsum = 0.0
                ysum = 0.0
                ywsum = 0.0
                # portals first (big upcoming event)
                if hasattr(level, "portals"):
                    for p in level.portals:
                        if hasattr(p, "rect") and getattr(p, "active", True):
                            ox = p.rect.centerx
                            if vx > 40 and ox > px and ox < px + look:
                                d = ox - px
                                w = 1.0 / max(1, d / 95)
                                bsum += (ox - px) * w * 0.55
                                wsum += w
                            elif vx < -40 and ox < px and ox > px - look:
                                d = px - ox
                                w = 1.0 / max(1, d / 95)
                                bsum += (ox - px) * w * 0.55
                                wsum += w
                # enemies (threats pull eye)
                if hasattr(level, "enemies"):
                    for e in level.enemies:
                        if hasattr(e, "rect") and getattr(e, "alive_flag", True):
                            ox = e.rect.centerx
                            if abs(vx) > 40 and ((vx > 0 and ox > px and ox < px + look + 70) or (vx < 0 and ox < px and ox > px - look)):
                                d = abs(ox - px)
                                w = 1.1 / max(1, d / 80)
                                bsum += (ox - px) * w * 0.32
                                wsum += w
                # vines + gravity zones (vertical feel too)
                for gname in ("gravity_zones", "vines"):
                    if hasattr(level, gname):
                        for obj in getattr(level, gname):
                            if hasattr(obj, "rect"):
                                ox = obj.rect.centerx
                                oy = obj.rect.centery
                                if vx > 20 and ox > px and ox < px + look:
                                    d = ox - px
                                    w = 0.85 / max(1, d / 100)
                                    bsum += (ox - px) * w * 0.3
                                    wsum += w
                                    dy = (oy - py) * 0.9
                                    ysum += dy * w * 0.25
                                    ywsum += w
                if wsum > 0.01:
                    anticipate = (bsum / wsum) * 0.085  # tiny: guides eye, player stays in charge
                if ywsum > 0.01:
                    ay_bias = (ysum / ywsum) * 0.045
        goal_x -= anticipate
        goal_y += ay_bias
        # Squash juice (impact compress) -- improved smooth decay + y-nudge on hard moves (land, big cuts, vine snag, dash brake)
        if getattr(self, 'squash_timer', 0) > 0:
            self.squash_timer -= dt
            self.squash = min(1.0, self.squash + dt * 4.8)  # smooth exponential-ish return to normal (premium decay)
        else:
            self.squash = 1.0
        if getattr(self, 'y_nudge_timer', 0) > 0:
            self.y_nudge_timer -= dt
            fade = max(0.0, self.y_nudge_timer / max(0.01, getattr(self, 'y_nudge_duration', 0.1)))
            goal_y += self.y_nudge * fade
            if self.y_nudge_timer <= 0:
                self.y_nudge = 0.0
        s = getattr(self, 'squash', 1.0)
        if s < 0.999:
            goal_y += (SCREEN_HEIGHT * 0.5) * (1 - s) * 0.17  # softer overall
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

    def set_speedrun_lead(self, boost: float) -> None:
        """Speedrun: stronger forward camera lead for better upcoming terrain visibility."""
        self.speedrun_lead = max(1.0, min(2.5, float(boost)))

    def set_victory_zoom(self, z: float) -> None:
        """Subtle focus zoom on victory screen (pulls view inward slightly)."""
        self.victory_zoom = max(0.95, min(1.12, float(z)))

    def trigger_squash(self, amount: float = 0.08, duration: float = 0.12, y_nudge: float = 0.0) -> None:
        """Brief vertical compress on impacts (land, cut, buffer, snag) for juicy camera feedback.
        Small amounts (skilled cuts/lands) get softer effect automatically.
        y_nudge: extra vertical camera kick on hard moves (dash brake, high-vy land, heavy vine).
        """
        eff = amount * (0.62 if amount <= 0.07 else 1.0)  # softer squash on skilled
        self.squash = max(0.82, min(1.0, 1.0 - eff))
        self.squash_timer = duration
        if y_nudge:
            self.y_nudge = float(y_nudge)
            self.y_nudge_timer = duration * 0.75
            self.y_nudge_duration = duration * 0.75


# ---------------------------------------------------------------------------
# Screen Shake
# ---------------------------------------------------------------------------

class ScreenShake:
    def __init__(self) -> None:
        self.timer: float = 0.0
        self.intensity: int = 0
        self.scale: float = 1.0

    def set_scale(self, v: float) -> None:
        self.scale = max(0.0, min(2.0, float(v)))

    def trigger(self, intensity: int = SHAKE_INTENSITY,
                duration: float = SHAKE_DURATION) -> None:
        self.timer = duration
        self.intensity = intensity

    def update(self, dt: float) -> tuple[int, int]:
        if self.timer > 0:
            self.timer -= dt
            i = int(self.intensity * self.scale)
            return (random.randint(-i, i), random.randint(-i, i))
        return (0, 0)

    def tick(self, dt: float) -> None:
        """Advance timer only -- no RNG, no return. Use in update loop."""
        if self.timer > 0:
            self.timer -= dt

    def get_offset(self) -> tuple[int, int]:
        """Sample current shake offset. Use in draw loop."""
        if self.timer > 0:
            i = int(self.intensity * self.scale)
            return (random.randint(-i, i), random.randint(-i, i))
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
        self.intensity: float = 1.0
        self.reduced_motion: bool = False
        # Perf: reusable SRCALPHA scratch surfaces keyed by size, so translucent
        # particles don't allocate a fresh Surface every particle every frame
        # (major WASM/pygbag FPS win -- alloc churn crosses the heap boundary).
        self._surf_pool: dict[tuple[int, int], pygame.Surface] = {}

    def set_intensity(self, v: float) -> None:
        """Accessibility: scale emitted counts (0.0 = none, 1.0 = normal, 2.0 = lots)."""
        self.intensity = max(0.0, min(2.0, float(v)))

    def set_reduced_motion(self, v: bool) -> None:
        """Accessibility: when true, skip some sparkles (e.g. decorative/ambient)."""
        self.reduced_motion = bool(v)

    def _count(self, n: int) -> int:
        if self.intensity <= 0.01:
            return 0
        return max(0, int(n * self.intensity))

    def _pooled_surf(self, w: int, h: int) -> pygame.Surface:
        """Reuse a transparent SRCALPHA scratch surface by size.

        Cleared to fully transparent on reuse so the caller can draw fresh.
        blit() copies pixels synchronously, so a single surface per size is
        safe to reuse across particles within one frame.
        """
        key = (w, h)
        s = self._surf_pool.get(key)
        if s is None:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            self._surf_pool[key] = s
        else:
            s.fill((0, 0, 0, 0))
        return s

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
                if alpha > 180 or sz <= 3:
                    # direct for opaque + tiny: big win on per-frame allocs for trails/dust/ambient
                    if alpha < 255:
                        dc = tuple(int(c * (alpha/255.0)) for c in color)
                        pygame.draw.circle(screen, dc, (int(sx), int(sy)), sz)
                    else:
                        pygame.draw.circle(screen, color, (int(sx), int(sy)), sz)
                else:
                    s = self._pooled_surf(sz * 2, sz * 2)
                    pygame.draw.circle(s, (*color, alpha), (sz, sz), sz)
                    screen.blit(s, (int(sx) - sz, int(sy) - sz))
            elif p.shape == "leaf":
                if sz <= 3:
                    # tiny leaf: direct ellipse dim, no surface
                    dc = tuple(int(c * (alpha/255.0)) for c in color) if alpha < 255 else color
                    pygame.draw.ellipse(screen, dc, (int(sx), int(sy), sz+1, max(1, (sz+1)//2)))
                else:
                    s = self._pooled_surf(sz + 2, sz + 2)
                    pygame.draw.ellipse(s, (*color, alpha), (0, 0, sz + 2, max(1, sz // 2)))
                    screen.blit(s, (int(sx), int(sy)))
            elif p.shape == "rect":
                if alpha > 180 or sz <= 3:
                    if alpha < 255:
                        dc = tuple(int(c * (alpha/255.0)) for c in color)
                        pygame.draw.rect(screen, dc, (int(sx), int(sy), sz, sz))
                    else:
                        pygame.draw.rect(screen, color, (int(sx), int(sy), sz, sz))
                else:
                    s = self._pooled_surf(sz, sz)
                    s.fill((*color, alpha))
                    screen.blit(s, (int(sx), int(sy)))

    def emit_sparkle(self, x: float, y: float, count: int = 8) -> None:
        n = self._count(count)
        if self.reduced_motion:
            n = max(0, n // 2)  # simple reduced motion: skip some sparkles
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 180)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                SPARKLE_LIFE + random.uniform(-0.1, 0.1),
                (255, 215 + random.randint(-20, 20), random.randint(0, 80)),
                random.uniform(2, 5), "circle",
            ))

    def emit_dust(self, x: float, y: float, count: int = 5) -> None:
        for _ in range(self._count(count)):
            self.particles.append(Particle(
                x + random.uniform(-10, 10), y,
                random.uniform(-40, 40), random.uniform(-80, -20),
                DUST_LIFE + random.uniform(0, 0.1),
                (COL_PLAT_DIRT[0] + random.randint(-15, 15),
                 COL_PLAT_DIRT[1] + random.randint(-10, 10),
                 COL_PLAT_DIRT[2] + random.randint(-5, 5)),
                random.uniform(2, 4), "circle", gravity=True,
            ))

    def emit_dash_trail(self, x: float, y: float, direction: float = -1.0) -> None:
        """Speed lines / afterimage particles for dash. Small, fast, short life. Richer for juice."""
        for _ in range(3):  # +1 for stronger dash afterimage feedback
            # Horizontal speed lines, slight vertical scatter
            speed = random.uniform(180, 320)
            vx = direction * speed + random.uniform(-30, 30)
            vy = random.uniform(-40, 40)
            life = random.uniform(0.08, 0.16)
            # Cool blue-white streak color
            color = (180 + random.randint(0, 40),
                     200 + random.randint(0, 55),
                     255)
            self.particles.append(Particle(
                x, y, vx, vy, life, color,
                random.uniform(1.5, 3.0), "rect", gravity=False,
            ))
            # Mix in tiny forward bamboo leaf flecks for theme
            if random.random() < 0.6:
                self.particles.append(Particle(
                    x + random.uniform(-2, 2), y + random.uniform(-4, 4),
                    direction * random.uniform(140, 220), random.uniform(-30, 30),
                    random.uniform(0.09, 0.18),
                    (70, 160, 55),
                    random.uniform(2, 3.5), "leaf", gravity=False,
                ))

    def emit_glide_wisp(self, x: float, y: float) -> None:
        """Soft rising wisp while gliding. Very gentle, almost decorative."""
        # Slow upward drift, tiny horizontal wander + occasional leaf for forest feel
        vx = random.uniform(-8, 8)
        vy = random.uniform(-35, -15)
        life = random.uniform(0.25, 0.45)
        # Pale cyan/white soft
        color = (200 + random.randint(0, 55),
                 230 + random.randint(0, 25),
                 255)
        self.particles.append(Particle(
            x, y, vx, vy, life, color,
            random.uniform(1.0, 2.2), "circle", gravity=False,
        ))
        if random.random() < 0.55:  # more frequent leaf wisps for glide juice
            # light leaf accent
            self.particles.append(Particle(
                x + random.uniform(-3, 3), y,
                random.uniform(-12, 12), random.uniform(-28, -12),
                random.uniform(0.35, 0.65),
                random.choice([(60, 150, 50), (80, 170, 60)]),
                random.uniform(2.5, 4.5), "leaf", gravity=False,
            ))

    def emit_graft_leaves(self, x: float, y: float, count: int = 10) -> None:
        """Leaf burst + sparkle when grafts are applied (Grove meta juice)."""
        # VISUALS PARITY: emit params (vx,vy,life,color,leaf,gravity) forced identical root<->web 2026-06-24
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(-1.0, 1.0)
            speed = random.uniform(35, 95)
            vx = math.sin(angle) * speed
            vy = -abs(math.cos(angle) * speed) * 0.9 - random.uniform(20, 50)
            greens = [(55, 145, 45), (75, 165, 55), (45, 125, 35), (90, 175, 70)]
            self.particles.append(Particle(
                x + random.uniform(-4, 4), y + random.uniform(-2, 2),
                vx, vy,
                random.uniform(0.55, 1.05),
                random.choice(greens),
                random.uniform(3, 6), "leaf", gravity=True,
            ))
        # Bonus sparkles for "applied" pop -- more for ghost/graft/ice save feedback
        for _ in range(max(3, n // 2)):
            self.emit_sparkle(x + random.uniform(-6, 6), y - 4, 1)
        # Mastery 5-graft golden shower (lush endgame juice, only on high count calls)
        if count >= 15:
            for _ in range(self._count(max(6, count // 3))):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(40, 110)
                self.particles.append(Particle(
                    x + random.uniform(-5, 5), y - 2,
                    math.cos(angle) * speed * 0.7, -abs(math.sin(angle) * speed) * 0.6 - random.uniform(10, 40),
                    random.uniform(0.65, 1.15),
                    (235, 210, 70),  # gold
                    random.uniform(2.5, 4.5), "circle", gravity=True,
                ))

    def emit_ice_trail(self, x: float, y: float, direction: float = -1.0) -> None:
        """Frosty motes / speed lines for ice sliding and ice magic. Cold blue-white."""
        for _ in range(3):  # richer ice feedback for slides + casts
            vx = direction * random.uniform(90, 180) + random.uniform(-20, 20)
            vy = random.uniform(-25, 35)
            life = random.uniform(0.18, 0.32)
            c = (170 + random.randint(0, 50), 210 + random.randint(0, 40), 255)
            self.particles.append(Particle(
                x + random.uniform(-3, 3), y + random.uniform(-2, 2),
                vx, vy, life, c,
                random.uniform(1.2, 2.8), "circle", gravity=False,
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
        for _ in range(self._count(count)):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 300)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.3, 0.7),
                (255, random.randint(50, 150), random.randint(0, 50)),
                random.uniform(3, 7), "circle", gravity=True,
            ))

    def emit_ambient_leaves(self, visible_rect: pygame.Rect) -> None:
        target = self._count(LEAF_COUNT)
        leaf_count = sum(1 for p in self.particles if p.shape == "leaf")
        while leaf_count < target:
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

    def emit_dense_foliage(self, visible_rect: pygame.Rect, count: int = 6) -> None:
        """Dense foliage for overgrown post-game (more leaves, faster drift, lusher greens)."""
        for _ in range(self._count(count)):
            x = visible_rect.x + random.uniform(0, visible_rect.width)
            y = visible_rect.y + random.uniform(-10, visible_rect.height * 0.55)
            greens = [(40, 120, 30), (30, 105, 25), (55, 145, 40), (65, 155, 45),
                      (25, 95, 20), (75, 165, 50)]
            self.particles.append(Particle(
                x, y,
                random.uniform(-35, 35), random.uniform(20, 55),
                random.uniform(3.5, 7.5),
                random.choice(greens),
                random.uniform(2.5, 5.5), "leaf",
            ))

    def emit_geyser_burst(self, x: float, y: float, count: int = 12) -> None:
        """Strong upward volcanic launch juice for geyser rides."""
        for _ in range(self._count(count)):
            angle = random.uniform(-0.6, 0.6)
            speed = random.uniform(120, 320)
            vx = math.sin(angle) * speed * 0.3
            vy = -abs(math.cos(angle) * speed)
            self.particles.append(Particle(
                x + random.uniform(-8, 8), y,
                vx, vy,
                random.uniform(0.35, 0.65),
                (255, 160 + random.randint(0, 60), 40),
                random.uniform(2, 5), "circle", gravity=False,
            ))
        # enhance: 1-2 extra sparks for geyser pop (already good, now juicier)
        if random.random() < 0.7:
            self.emit_sparkle(x, y - 4, 2)

    def emit_updraft_lift(self, x: float, y: float, count: int = 3) -> None:
        """Gentle rising bubbles/leaves for thermal columns."""
        for _ in range(count):
            vx = random.uniform(-25, 25)
            vy = random.uniform(-140, -60)
            self.particles.append(Particle(
                x + random.uniform(-18, 18), y + random.uniform(0, 30),
                vx, vy,
                random.uniform(0.5, 1.0),
                (255, 230, 160),
                random.uniform(2, 4), "circle", gravity=False,
            ))

    def emit_wind_drift(self, x: float, y: float, direction: float, count: int = 4) -> None:
        """Horizontal sand/dust for wind zones."""
        for _ in range(count):
            vx = direction * random.uniform(80, 160)
            vy = random.uniform(-30, 30)
            self.particles.append(Particle(
                x + random.uniform(-10, 10), y + random.uniform(-40, 40),
                vx, vy,
                random.uniform(0.25, 0.55),
                (210, 180, 130),
                random.uniform(1.5, 3.5), "circle", gravity=True,
            ))

    def emit_gravity_motes(self, x: float, y: float, count: int = 5) -> None:
        """Subtle floating particles inside altered gravity zones."""
        for _ in range(count):
            vx = random.uniform(-35, 35)
            vy = random.uniform(-60, 60)
            self.particles.append(Particle(
                x + random.uniform(-20, 20), y + random.uniform(-15, 15),
                vx, vy,
                random.uniform(0.6, 1.2),
                (200, 160, 255),
                random.uniform(1, 3), "circle", gravity=False,
            ))

    def emit_mushroom_puff(self, x: float, y: float, count: int = 8) -> None:
        """Bouncy puff when mushroom launches player."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 110)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed - 60,
                random.uniform(0.3, 0.55),
                (220, 140, 200),
                random.uniform(2, 4), "circle", gravity=True,
            ))

    def emit_speedrun_trail(self, x: float, y: float, direction: float = -1.0) -> None:
        """Fast thin cyan speed lines / afterimages. Used only in speedrun for extra motion juice + visibility."""
        for _ in range(self._count(4)):
            vx = direction * random.uniform(220, 380)
            vy = random.uniform(-22, 22)
            life = random.uniform(0.055, 0.11)
            c = (135 + random.randint(0, 30), 225 + random.randint(0, 25), 255)
            self.particles.append(Particle(
                x + random.uniform(-1.5, 1.5), y + random.uniform(-3, 3),
                vx, vy, life, c,
                random.uniform(1.0, 2.0), "rect", gravity=False,
            ))

    def emit_hitstop_flash(self, x: float, y: float, count: int = 5) -> None:
        """Bright short white/yellow burst on heavy impacts (pairs with hitstop for punch)."""
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(35, 150)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.12, 0.19),
                (255, 252 + random.randint(0, 3), 210 + random.randint(0, 40)),
                random.uniform(1.8, 3.8), "circle", gravity=False,
            ))

    # --- New amplified juice emitters (Lane 3) ---
    def emit_leaf_burst(self, x: float, y: float, count: int = 12) -> None:
        """Denser/more varied leaf burst for land, cut, dash, snag, etc. Lush without perf cost."""
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(-1.4, 1.4)
            speed = random.uniform(45, 120)
            vx = math.sin(angle) * speed
            vy = -abs(math.cos(angle) * speed) - random.uniform(10, 45)
            greens = [(50, 140, 35), (70, 165, 50), (40, 120, 30), (85, 170, 65), (60, 145, 45)]
            life = random.uniform(0.5, 1.15)
            self.particles.append(Particle(
                x + random.uniform(-6, 6), y + random.uniform(-3, 3),
                vx, vy, life, random.choice(greens),
                random.uniform(2.5, 5.5), "leaf", gravity=True,
            ))

    def emit_impact_dust(self, x: float, y: float, count: int = 7) -> None:
        """Punchier impact dust (land, buffer, brake). Slightly longer life for lush feel."""
        for _ in range(self._count(count)):
            self.particles.append(Particle(
                x + random.uniform(-8, 8), y,
                random.uniform(-55, 55), random.uniform(-95, -15),
                DUST_LIFE + random.uniform(0.05, 0.18),
                (COL_PLAT_DIRT[0] + random.randint(-20, 20),
                 COL_PLAT_DIRT[1] + random.randint(-12, 12),
                 COL_PLAT_DIRT[2] + random.randint(-8, 8)),
                random.uniform(2, 4.5), "circle", gravity=True,
            ))

    def emit_golden_shower(self, x: float, y: float, count: int = 10) -> None:
        """Golden mastery shower (5-graft reward)."""
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 130)
            self.particles.append(Particle(
                x + random.uniform(-4, 4), y - 1,
                math.cos(angle) * speed * 0.65, -abs(math.sin(angle) * speed * 0.55) - 15,
                random.uniform(0.7, 1.25),
                (240, 215, 85),
                random.uniform(2.2, 4), "circle", gravity=True,
            ))

    def emit_portal_warp(self, x: float, y: float, count: int = 10) -> None:
        """Swirly warp burst on portal use."""
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(70, 180)
            c = random.choice([(70, 210, 255), (255, 100, 220), (140, 255, 230)])
            self.particles.append(Particle(
                x + random.uniform(-3, 3), y + random.uniform(-8, 8),
                math.cos(angle) * speed, math.sin(angle) * speed * 0.6,
                random.uniform(0.35, 0.65), c,
                random.uniform(2, 4), "circle", gravity=False,
            ))
        # a few leaf flecks for forest portal theme
        for _ in range(max(2, n // 4)):
            self.particles.append(Particle(
                x, y - 4, random.uniform(-30, 30), random.uniform(-70, -20),
                random.uniform(0.45, 0.8), (55, 145, 40), 3.5, "leaf", gravity=True,
            ))

    def emit_vine_snag_pop(self, x: float, y: float, count: int = 6) -> None:
        """Pop on vine snag (entangle juice)."""
        n = self._count(count)
        for _ in range(n):
            vx = random.uniform(-60, 60)
            vy = random.uniform(-40, 30)
            self.particles.append(Particle(
                x + random.uniform(-5, 5), y + random.uniform(-2, 6),
                vx, vy,
                random.uniform(0.35, 0.7),
                random.choice([(30, 95, 40), (45, 115, 50)]),
                random.uniform(2, 4), "leaf", gravity=True,
            ))
        if random.random() < 0.6:
            self.emit_sparkle(x, y + 2, 2)

    def emit_spore_puff(self, x: float, y: float, count: int = 6) -> None:
        """Spore puff counter for spore_shield + thorn_spore synergy (graft meta juice)."""
        n = self._count(count)
        for _ in range(n):
            vx = random.uniform(-55, 55)
            vy = random.uniform(-55, -10)
            self.particles.append(Particle(
                x + random.uniform(-6, 6), y + random.uniform(-4, 4),
                vx, vy,
                random.uniform(0.45, 0.95),
                random.choice([(90, 130, 70), (110, 90, 140), (70, 150, 85)]),
                random.uniform(2.5, 4.5), "circle", gravity=True,
            ))
        if random.random() < 0.7:
            self.emit_sparkle(x, y, 1)

    def emit_overgrowth_aura(self, x: float, y: float, count: int = 5) -> None:
        """Unique mastery aura for overgrown clear reward: lush chaotic green-purple swirl (5th graft + aura)."""
        n = self._count(count)
        for _ in range(n):
            vx = random.uniform(-45, 45)
            vy = random.uniform(-95, -25)
            col = random.choice([(55, 155, 70), (120, 80, 160), (40, 180, 90), (180, 100, 190), (80, 210, 120)])
            self.particles.append(Particle(
                x + random.uniform(-12, 12), y + random.uniform(-18, 8),
                vx, vy,
                random.uniform(0.75, 1.9),
                col,
                random.uniform(3, 6), "leaf", gravity=False,
            ))
        # extra chaotic motes for depth
        if random.random() < 0.5:
            for _ in range(max(1, n // 3)):
                self.particles.append(Particle(
                    x, y - 4,
                    random.uniform(-25, 25), random.uniform(-50, -10),
                    random.uniform(0.6, 1.1),
                    (200, 160, 255),
                    random.uniform(1, 3), "circle", gravity=False,
                ))

    def emit_ghost_beat_pop(self, x: float, y: float) -> None:
        """Special pop when beating a ghost record or ghost milestone."""
        for _ in range(4):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 140)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.4, 0.75),
                (170, 220, 255), random.uniform(2, 4), "circle", gravity=False,
            ))
        for _ in range(3):
            self.particles.append(Particle(
                x + random.uniform(-3, 3), y - 2,
                random.uniform(-25, 25), random.uniform(-55, -15),
                random.uniform(0.5, 0.9), (70, 155, 60), 3, "leaf", gravity=True,
            ))

    def emit_bamboo_glitter(self, x: float, y: float, count: int = 9) -> None:
        """Glitter on bamboo collect/break (gold + leaf mix)."""
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(55, 150)
            col = (255, 220, 90) if random.random() < 0.55 else random.choice([(75, 165, 55), (55, 140, 45)])
            shp = "circle" if col[0] > 200 else "leaf"
            self.particles.append(Particle(
                x + random.uniform(-4, 4), y + random.uniform(-6, 2),
                math.cos(angle) * speed, math.sin(angle) * speed * 0.8 - 20,
                random.uniform(0.45, 0.85), col,
                random.uniform(2, 4.5), shp, gravity=True,
            ))

    def emit_mastery_storm(self, x: float, y: float, count: int = 18) -> None:
        """High-impact 5-graft mastery storm: swirling gold + lush green burst. Premium payoff for full grafts."""
        n = self._count(count)
        for _ in range(n):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(55, 165)
            # gold core + green ring
            if random.random() < 0.55:
                col = (235, 205, 70)
                shp = "circle"
            else:
                col = random.choice([(55, 150, 45), (70, 170, 55), (40, 130, 35)])
                shp = "leaf"
            self.particles.append(Particle(
                x + random.uniform(-8, 8), y + random.uniform(-10, 2),
                math.cos(angle) * speed * 0.75, -abs(math.sin(angle) * speed * 0.7) - random.uniform(20, 70),
                random.uniform(0.65, 1.35),
                col, random.uniform(2.2, 5.0), shp, gravity=True,
            ))
        # extra spark ring for storm pop
        for _ in range(max(4, n // 3)):
            self.emit_sparkle(x + random.uniform(-5, 5), y - 6, 1)

    def emit_vine_bloom_pop(self, x: float, y: float, count: int = 12) -> None:
        """High-impact vine bloom pop (wild_weave / vine snag on mastery): lush green upward petals + motes."""
        n = self._count(count)
        for _ in range(n):
            vx = random.uniform(-70, 70)
            vy = random.uniform(-130, -35)
            col = random.choice([(35, 125, 40), (60, 155, 55), (80, 175, 65), (45, 110, 50)])
            self.particles.append(Particle(
                x + random.uniform(-4, 4), y + random.uniform(-2, 4),
                vx, vy,
                random.uniform(0.55, 1.1),
                col,
                random.uniform(2.5, 5.5), "leaf", gravity=True,
            ))
        if random.random() < 0.8:
            self.emit_sparkle(x, y - 2, max(2, n // 4))
