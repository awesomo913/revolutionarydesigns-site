"""All sprite classes and procedural pixel-art generators."""

from __future__ import annotations

import math
import random
from math import floor as _fl

import pygame
from engine import Camera

from config import (
    BOSS_CHARGE_SPEED, BOSS_HP, BOSS_IDLE_SEC, BOSS_SIZE,
    BOSS_STUN_SEC, COL_BAMBOO, COL_BAMBOO_JOINT, COL_BLACK,
    COL_HEAL_PINK, COL_HEAL_RED, COL_PANDA_BLACK, COL_PANDA_WHITE,
    COL_WHITE, COMBO_MULTIPLIERS,
    COMBO_WINDOW, BAMBOO_SCORE, ENEMY_CHASE_RANGE, ENEMY_CHASE_SPEED,
    ENEMY_CHASE_Y_RANGE, ENEMY_PATROL_SPEED, FLYING_ENEMY_AMP, FLYING_ENEMY_FREQ, GRAVITY, MOVING_PLAT_SPEED,
    PLAYER_DAMAGE, PLAYER_INVINCIBLE_SEC, PLAYER_JUMP,
    PLAYER_MAX_HP, PLAYER_SIZE, PLAYER_SPEED, TERMINAL_VELOCITY,
    HEAL_AMOUNT, SAFE_ZONE_WIDTH, SLIME_BOUNCE_SPEED, SLIME_HOP_POWER,
    FLOOR_Y, SCREEN_HEIGHT,
    JUMP_BUFFER_TIME, GHOST_ALPHA, PROJECTILE_WORLD_WIDTH,
    ICE_ACCEL, ICE_FRICTION,
    JUMP_CUT_MULTIPLIER, GLIDE_DURATION_SEC,
    AIR_REVERSAL_KICK, LAND_DAMP,
    COYOTE_TIME, AIR_ACCEL, HITSTOP_LAND_SEC,
    SHURIKEN_SPEED, ICE_PROJECTILE_SPEED,
    CHRONO_SLOW_DASH_SEC, CHRONO_SLOW_STAFF_SEC,
    DASH_VELOCITY, SLAM_VELOCITY, KNOCKBACK_X, KNOCKBACK_Y,
    GRAFT_SYNERGIES, MASTERY_TIERS,
)

# ---------------------------------------------------------------------------
# Perf helpers
# ---------------------------------------------------------------------------

def _scratch_surface(cache: dict, size: tuple[int, int]) -> pygame.Surface:
    """Return a reusable SRCALPHA overlay surface of the given size.

    Callers fill() the whole surface before blitting, and blit() copies pixels
    synchronously, so one shared scratch per size is safe -- no two overlays are
    ever live at once. Avoids allocating a fresh Surface every frame in the hot
    draw path (big WASM/pygbag FPS win for player tints + ghost tints).
    """
    s = cache.get(size)
    if s is None:
        s = pygame.Surface(size, pygame.SRCALPHA)
        cache[size] = s
    return s


# ---------------------------------------------------------------------------
# Procedural art generators
# ---------------------------------------------------------------------------

def generate_panda_frames() -> dict[str, list[pygame.Surface]]:
    """Cleaner panda with rounder proportions and visible detail."""
    w, h = PLAYER_SIZE  # 36x44

    def _draw_panda(surf: pygame.Surface, body_dy: int = 0,
                    arm_l: tuple[int, int, int, int] = (2, 20, 7, 12),
                    arm_r: tuple[int, int, int, int] = (27, 20, 7, 12),
                    leg_l: tuple[int, int, int, int] = (8, 35, 9, 9),
                    leg_r: tuple[int, int, int, int] = (19, 35, 9, 9),
                    head_dy: int = 0) -> None:
        dy = body_dy
        hdy = head_dy if head_dy != 0 else dy  # head_dy explicit; defaults to body for compatibility
        # Shadow under body
        pygame.draw.ellipse(surf, (200, 200, 190), (7, 15 + dy, 22, 22))
        # Body (round white torso)
        pygame.draw.ellipse(surf, COL_PANDA_WHITE, (6, 14 + dy, 24, 24))
        # Belly patch
        pygame.draw.ellipse(surf, (220, 220, 215), (11, 18 + dy, 14, 14))
        # Arms (rounded rects)
        for ax, ay, aw, ah in (arm_l, arm_r):
            pygame.draw.rect(surf, COL_PANDA_BLACK, (ax, ay + dy, aw, ah),
                             border_radius=3)
        # Legs (rounded rects)
        for lx, ly, lw, lh in (leg_l, leg_r):
            pygame.draw.rect(surf, COL_PANDA_BLACK, (lx, ly + dy, lw, lh),
                             border_radius=4)
        # Head (uses head_dy for bob fidelity on all states)
        pygame.draw.circle(surf, COL_PANDA_WHITE, (w // 2, 12 + hdy), 11)
        # Ears (outer black + inner pink)
        for ex in (7, 29):
            pygame.draw.circle(surf, COL_PANDA_BLACK, (ex, 3 + hdy), 5)
            pygame.draw.circle(surf, (180, 130, 130), (ex, 3 + hdy), 2)
        # Eye patches (smooth ellipses)
        pygame.draw.ellipse(surf, COL_PANDA_BLACK, (10, 7 + hdy, 8, 7))
        pygame.draw.ellipse(surf, COL_PANDA_BLACK, (18, 7 + hdy, 8, 7))
        # Eyes (white with black pupil and highlight)
        for ex, px in ((14, 15), (22, 21)):
            pygame.draw.circle(surf, COL_WHITE, (ex, 10 + hdy), 3)
            pygame.draw.circle(surf, COL_BLACK, (px, 10 + hdy), 2)
            pygame.draw.circle(surf, COL_WHITE, (px - 1, 9 + hdy), 1)
        # Nose
        pygame.draw.ellipse(surf, (60, 40, 40), (16, 14 + hdy, 5, 3))
        # Mouth
        pygame.draw.arc(surf, COL_BLACK, (15, 15 + hdy, 7, 4), 3.14, 6.28, 1)

    frames: dict[str, list[pygame.Surface]] = {}

    # Idle: gentle breathing bob
    for dy in (0, 1):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        _draw_panda(s, body_dy=dy, head_dy=dy)
        frames.setdefault("idle", []).append(s)

    # Run: alternating limb positions + subtle body/head bob (head_dy explicit on ALL states)
    run_data = [
        (0, (1, 18, 7, 12), (28, 22, 7, 12), (6, 33, 9, 9), (21, 37, 9, 9)),
        (1, (2, 20, 7, 12), (27, 20, 7, 12), (8, 35, 9, 9), (19, 35, 9, 9)),
        (0, (28, 18, 7, 12), (1, 22, 7, 12), (21, 33, 9, 9), (6, 37, 9, 9)),
        (1, (2, 20, 7, 12), (27, 20, 7, 12), (8, 35, 9, 9), (19, 35, 9, 9)),
    ]
    for dy, al, ar, ll, lr in run_data:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        _draw_panda(s, body_dy=dy, head_dy=dy, arm_l=al, arm_r=ar, leg_l=ll, leg_r=lr)
        frames.setdefault("run", []).append(s)

    # Jump: arms up, legs tucked
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_panda(s, body_dy=-2, head_dy=-2,
                arm_l=(0, 10, 7, 12), arm_r=(28, 10, 7, 12),  # limb offset inward: no edge clip at 36
                leg_l=(10, 32, 8, 8), leg_r=(18, 32, 8, 8))
    frames["jump"] = [s]

    # Fall: arms spread, legs down
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_panda(s, body_dy=1, head_dy=1,
                arm_l=(1, 16, 8, 12), arm_r=(27, 16, 8, 12),
                leg_l=(9, 38, 8, 6), leg_r=(19, 38, 8, 6))
    frames["fall"] = [s]

    # Glide: arms fully spread, legs tucked, body slightly arched upward
    # limb offsets tightened to guarantee no surface clip on 36px width
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_panda(s, body_dy=-1, head_dy=-1,
                arm_l=(0, 14, 10, 8), arm_r=(25, 14, 10, 8),
                leg_l=(10, 34, 8, 7), leg_r=(18, 34, 8, 7))
    frames["glide"] = [s]

    # Dash: body leaned forward, arms behind like a sprinter
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    _draw_panda(s, body_dy=-1, head_dy=-1,
                arm_l=(4, 24, 6, 14), arm_r=(26, 24, 6, 14),
                leg_l=(8, 33, 9, 11), leg_r=(20, 33, 9, 11))
    frames["dash"] = [s]

    return frames


def generate_bamboo_surface() -> pygame.Surface:
    """20x55 bamboo stalk with joints and leaves."""
    surf = pygame.Surface((20, 55), pygame.SRCALPHA)
    pygame.draw.rect(surf, COL_BAMBOO, (7, 0, 6, 55))
    # Gradient stripe on stalk
    pygame.draw.rect(surf, (90, 170, 20), (9, 0, 2, 55))
    for jy in (12, 27, 42):
        pygame.draw.rect(surf, COL_BAMBOO_JOINT, (6, jy, 8, 3))
    # Leaves
    pygame.draw.polygon(surf, (50, 160, 30), [(10, 0), (19, 6), (10, 8)])
    pygame.draw.polygon(surf, (40, 140, 20), [(10, 0), (1, 6), (10, 8)])
    return surf


def generate_heal_surface() -> pygame.Surface:
    """25x25 heart shape."""
    surf = pygame.Surface((25, 25), pygame.SRCALPHA)
    pygame.draw.circle(surf, COL_HEAL_RED, (8, 8), 6)
    pygame.draw.circle(surf, COL_HEAL_RED, (17, 8), 6)
    pygame.draw.polygon(surf, COL_HEAL_RED, [(2, 10), (12, 23), (23, 10)])
    pygame.draw.circle(surf, COL_HEAL_PINK, (7, 6), 2)
    return surf


def generate_platform_tile(width: int, height: int) -> pygame.Surface:
    """Asian-themed platform: polished wood grain + bamboo cross-sections.

    Evokes a temple walkway / wooden tea-house plank.
    """
    surf = pygame.Surface((width, height))
    # Seed for deterministic visuals per platform instance
    seed_val = hash((width, height, width * 31 + height))
    random.seed(seed_val)
    # Deep earthy teak base with gradient
    for y in range(height):
        t = y / max(1, height)
        c = (int(110 - 30 * t), int(70 - 18 * t), int(35 - 10 * t))
        pygame.draw.line(surf, (max(0, c[0]), max(0, c[1]), max(0, c[2])),
                         (0, y), (width, y))
    # Wood grain lines
    for gy in range(6, height, 4):
        shade = random.randint(-20, 10)
        c = (max(0, min(255, 85 + shade)),
             max(0, min(255, 52 + shade)),
             max(0, min(255, 25 + shade)))
        pygame.draw.line(surf, c, (0, gy),
                         (width, gy + random.choice([-1, 0, 1])), 1)
    # Mossy green top (zen garden moss)
    moss_h = min(5, height)
    pygame.draw.rect(surf, (55, 130, 55), (0, 0, width, moss_h))
    pygame.draw.rect(surf, (40, 105, 40), (0, moss_h - 1, width, 1))
    # Short moss tufts
    for x in range(0, width - 1, 3):
        bh = random.randint(1, 3)
        shade = random.randint(-10, 25)
        gc = (min(255, 55 + shade), min(255, 130 + shade), min(255, 55 + shade))
        pygame.draw.line(surf, gc, (x, moss_h),
                         (x + random.randint(-1, 1), moss_h - bh), 1)
    # Bamboo cross-section decorations (every ~60px)
    spacing = 60
    for bx in range(spacing // 2, width - 10, spacing):
        by = height // 2 + random.randint(-2, 2)
        # Dark rim
        pygame.draw.circle(surf, (40, 80, 20), (bx, by), 4)
        # Pale bamboo interior
        pygame.draw.circle(surf, (180, 200, 130), (bx, by), 3)
        # Center node dot
        pygame.draw.circle(surf, (90, 130, 60), (bx, by), 1)
    # Dark edge trim (lacquered corners)
    pygame.draw.rect(surf, (40, 25, 15), (0, 0, 2, height))
    pygame.draw.rect(surf, (40, 25, 15), (width - 2, 0, 2, height))
    # Restore global RNG
    random.seed()
    return surf


def generate_safe_zone(height: int) -> pygame.Surface:
    """Asian temple grove: torii gate, pagoda silhouette, cherry blossoms."""
    w = SAFE_ZONE_WIDTH
    surf = pygame.Surface((w, height), pygame.SRCALPHA)
    ground_y = height - 18

    # Ground: soft mossy green with cherry petals
    for gy in range(ground_y, height):
        t = (gy - ground_y) / max(1, height - ground_y)
        r = int(70 - 30 * t)
        g = int(130 + 40 * t)
        b = int(55 - 25 * t)
        pygame.draw.line(surf, (r, g, b), (0, gy), (w, gy))

    # Stone path (sand/gravel zen-garden)
    path_w = 80
    path_x = w // 2 - path_w // 2
    pygame.draw.rect(surf, (200, 185, 150), (path_x, ground_y, path_w, 18))
    # Raked sand lines
    for gy in range(ground_y + 3, height, 4):
        pygame.draw.line(surf, (170, 155, 120),
                         (path_x + 4, gy), (path_x + path_w - 4, gy), 1)

    # === TORII GATE (red gate) in center ===
    tx = w // 2
    torii_top = ground_y - int(height * 0.55)
    torii_h = ground_y - torii_top
    gate_w = 120
    pillar_w = 10
    # Pillars
    pygame.draw.rect(surf, (200, 40, 40),
                     (tx - gate_w // 2, torii_top + 18, pillar_w, torii_h - 18))
    pygame.draw.rect(surf, (200, 40, 40),
                     (tx + gate_w // 2 - pillar_w, torii_top + 18,
                      pillar_w, torii_h - 18))
    pygame.draw.rect(surf, (150, 30, 30),
                     (tx - gate_w // 2, ground_y - 3, pillar_w, 3))
    pygame.draw.rect(surf, (150, 30, 30),
                     (tx + gate_w // 2 - pillar_w, ground_y - 3, pillar_w, 3))
    # Top crossbeam (kasagi) -- wider than pillars, upcurved ends
    beam_w = gate_w + 26
    pygame.draw.rect(surf, (40, 25, 20),
                     (tx - beam_w // 2, torii_top, beam_w, 8))
    pygame.draw.polygon(surf, (40, 25, 20), [
        (tx - beam_w // 2, torii_top + 8),
        (tx - beam_w // 2 - 6, torii_top + 2),
        (tx - beam_w // 2 - 6, torii_top),
        (tx - beam_w // 2, torii_top)])
    pygame.draw.polygon(surf, (40, 25, 20), [
        (tx + beam_w // 2, torii_top + 8),
        (tx + beam_w // 2 + 6, torii_top + 2),
        (tx + beam_w // 2 + 6, torii_top),
        (tx + beam_w // 2, torii_top)])
    # Second beam (nuki) below
    pygame.draw.rect(surf, (160, 30, 30),
                     (tx - gate_w // 2 - 6, torii_top + 18, gate_w + 12, 6))

    # === PAGODA silhouette (left of gate, small, distant) ===
    pag_x = 45
    pag_bot = ground_y - 10
    pag_levels = 3
    for li in range(pag_levels):
        lw = 40 - li * 6
        lh = 14
        ly = pag_bot - (li + 1) * (lh + 4)
        # Tier body
        pygame.draw.rect(surf, (90, 55, 35),
                         (pag_x - lw // 2, ly, lw, lh))
        # Curved red roof
        pygame.draw.polygon(surf, (180, 50, 40), [
            (pag_x - lw // 2 - 4, ly),
            (pag_x, ly - 8),
            (pag_x + lw // 2 + 4, ly),
        ])
    # Spire
    pygame.draw.rect(surf, (80, 50, 30),
                     (pag_x - 1, pag_bot - pag_levels * 18 - 14, 2, 10))
    pygame.draw.circle(surf, (220, 180, 60),
                       (pag_x, pag_bot - pag_levels * 18 - 14), 3)

    # === STONE LANTERN (right of gate) ===
    lx = w - 50
    lb = ground_y - 5
    pygame.draw.rect(surf, (150, 145, 135), (lx - 8, lb - 8, 16, 8))  # base
    pygame.draw.rect(surf, (160, 155, 145), (lx - 3, lb - 20, 6, 12))  # pillar
    pygame.draw.rect(surf, (140, 135, 125), (lx - 10, lb - 30, 20, 10))  # lantern
    # Glow from lantern
    pygame.draw.circle(surf, (255, 220, 120), (lx, lb - 25), 4)
    pygame.draw.polygon(surf, (90, 85, 80), [
        (lx - 12, lb - 30), (lx, lb - 38), (lx + 12, lb - 30)])  # roof

    # === CHERRY BLOSSOM TREES (pink canopies) ===
    cherry_defs = [(100, 0.8), (w - 100, 0.75)]
    for cx, scale in cherry_defs:
        th = int(height * scale * 0.6)
        trunk_w = int(6 + 5 * scale)
        trunk_top = ground_y - th
        # Dark trunk with curve
        trunk_c = (70, 40, 25)
        pygame.draw.rect(surf, trunk_c,
                         (cx - trunk_w // 2, trunk_top + th // 3,
                          trunk_w, th * 2 // 3))
        # Branches
        for bx_off in (-8, 8, -4):
            pygame.draw.line(surf, trunk_c,
                             (cx, trunk_top + th // 2),
                             (cx + bx_off * 3, trunk_top + th // 4), 2)
        # Pink/white blossom cloud
        cw = int(28 + 16 * scale)
        for _ in range(9):
            ox = random.randint(-cw, cw)
            oy = random.randint(-cw // 2, cw // 2)
            cr = random.randint(int(cw * 0.45), int(cw * 0.75))
            pc = random.choice([(255, 200, 220), (255, 180, 210),
                                (255, 230, 240), (240, 170, 200)])
            pygame.draw.circle(surf, pc,
                               (cx + ox, trunk_top + th // 4 + oy), cr)

    # === FALLING CHERRY PETALS on ground ===
    for _ in range(20):
        pet_x = random.randint(0, w)
        pet_y = random.randint(ground_y - 40, height)
        pygame.draw.circle(surf, (255, 190, 215), (pet_x, pet_y), 2)
        pygame.draw.circle(surf, (255, 160, 190), (pet_x, pet_y - 1), 1)

    # === BAMBOO STALKS (accent plants near gate) ===
    for bx in (tx - 80, tx + 80, tx - 60, tx + 60):
        bh = random.randint(45, 75)
        by = ground_y
        pygame.draw.rect(surf, (60, 145, 50), (bx - 2, by - bh, 4, bh))
        # Joints
        for jy in range(by - bh + 10, by, 14):
            pygame.draw.rect(surf, (30, 100, 25), (bx - 3, jy, 6, 2))
        # Leaves at top
        pygame.draw.polygon(surf, (55, 140, 45),
                            [(bx, by - bh), (bx + 8, by - bh + 4),
                             (bx + 2, by - bh + 8)])
        pygame.draw.polygon(surf, (45, 125, 35),
                            [(bx, by - bh), (bx - 8, by - bh + 4),
                             (bx - 2, by - bh + 8)])

    # Sunbeam rays (gold shafts)
    for _ in range(3):
        rx = random.randint(40, w - 40)
        beam = pygame.Surface((20, height), pygame.SRCALPHA)
        for by in range(height):
            alpha = max(0, int(35 * (1 - by / height)))
            pygame.draw.line(beam, (255, 240, 170, alpha), (0, by), (20, by))
        surf.blit(beam, (rx + random.randint(-10, 10), 0))

    # Butterflies
    bf_colors = [(255, 140, 200), (140, 200, 255), (255, 255, 140),
                 (200, 255, 180), (255, 180, 120)]
    for _ in range(6):
        bx = random.randint(30, w - 30)
        by = random.randint(30, ground_y - 20)
        bc = random.choice(bf_colors)
        pygame.draw.ellipse(surf, bc, (bx - 5, by - 3, 6, 7))
        pygame.draw.ellipse(surf, bc, (bx + 1, by - 3, 6, 7))
        pygame.draw.line(surf, (60, 40, 30), (bx, by - 3), (bx, by + 4), 1)

    # Small ferns along ground edges
    for fx in range(10, w - 10, 20):
        fh = random.randint(6, 12)
        fc = (30 + random.randint(-5, 10), 110 + random.randint(-10, 15),
              30 + random.randint(-5, 5))
        # Two frond curves
        for side in (-1, 1):
            pts = [(fx, ground_y), (fx + side * fh // 2, ground_y - fh),
                   (fx + side * fh, ground_y - fh // 2)]
            pygame.draw.lines(surf, fc, False, pts, 1)

    return surf


def generate_grass_tuft() -> pygame.Surface:
    """Small decorative grass blades."""
    surf = pygame.Surface((12, 10), pygame.SRCALPHA)
    greens = [(30, 130, 30), (45, 155, 45), (25, 115, 25)]
    for i, gx in enumerate((2, 5, 8)):
        c = greens[i % len(greens)]
        bh = random.randint(5, 9)
        pygame.draw.line(surf, c, (gx, 9), (gx + random.randint(-2, 2), 9 - bh), 2)
    return surf


# -- Enemy art generators --

def _generate_mushroom_frames() -> list[pygame.Surface]:
    """Two-frame mushroom patrol enemy -- cleaner design."""
    frames = []
    for dy in (0, 1):
        surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        # Cap (red dome with white spots)
        pygame.draw.ellipse(surf, (180, 40, 40), (2, 2 + dy, 32, 20))
        pygame.draw.ellipse(surf, (200, 55, 55), (4, 4 + dy, 28, 16))
        for sx, sy in ((10, 6), (20, 4), (26, 10), (8, 12)):
            pygame.draw.circle(surf, COL_WHITE, (sx, sy + dy), 2)
        # Stem
        pygame.draw.rect(surf, (230, 210, 180), (12, 18 + dy, 12, 12), border_radius=3)
        # Eyes (angry)
        pygame.draw.circle(surf, COL_WHITE, (15, 22 + dy), 3)
        pygame.draw.circle(surf, COL_WHITE, (21, 22 + dy), 3)
        pygame.draw.circle(surf, COL_BLACK, (16, 22 + dy), 2)
        pygame.draw.circle(surf, COL_BLACK, (20, 22 + dy), 2)
        # Angry brows
        pygame.draw.line(surf, COL_BLACK, (12, 18 + dy), (17, 20 + dy), 2)
        pygame.draw.line(surf, COL_BLACK, (24, 18 + dy), (19, 20 + dy), 2)
        # Feet
        pygame.draw.ellipse(surf, (200, 180, 150), (10, 30 + dy, 8, 6))
        pygame.draw.ellipse(surf, (200, 180, 150), (18, 30 + dy, 8, 6))
        frames.append(surf)
    return frames


def _generate_chaser_frames() -> list[pygame.Surface]:
    """Two-frame shadow panther chaser -- sleek dark cat with glowing eyes."""
    frames = []
    for dy in (0, 1):
        surf = pygame.Surface((44, 36), pygame.SRCALPHA)
        body_c = (50, 35, 60)
        belly_c = (70, 55, 80)
        # Body (sleek ellipse)
        pygame.draw.ellipse(surf, body_c, (8, 10 + dy, 28, 18))
        pygame.draw.ellipse(surf, belly_c, (12, 15 + dy, 20, 10))
        # Head (round)
        pygame.draw.circle(surf, body_c, (12, 12 + dy), 10)
        pygame.draw.circle(surf, belly_c, (12, 14 + dy), 6)
        # Ears (triangular, clean)
        pygame.draw.polygon(surf, body_c, [(5, 8 + dy), (3, 0), (10, 5 + dy)])
        pygame.draw.polygon(surf, body_c, [(15, 6 + dy), (18, 0), (11, 3 + dy)])
        # Inner ear
        pygame.draw.polygon(surf, (100, 70, 90), [(6, 6 + dy), (4, 2), (9, 5 + dy)])
        pygame.draw.polygon(surf, (100, 70, 90), [(15, 5 + dy), (17, 2), (12, 4 + dy)])
        # Eyes (bright yellow-green, menacing)
        pygame.draw.circle(surf, (180, 255, 50), (9, 11 + dy), 3)
        pygame.draw.circle(surf, (180, 255, 50), (16, 11 + dy), 3)
        # Slit pupils
        pygame.draw.rect(surf, COL_BLACK, (9, 9 + dy, 1, 4))
        pygame.draw.rect(surf, COL_BLACK, (16, 9 + dy, 1, 4))
        # Nose
        pygame.draw.circle(surf, (30, 20, 30), (12, 16 + dy), 2)
        # Legs (slim)
        for lx in (12, 18, 26, 30):
            pygame.draw.rect(surf, body_c, (lx, 26 + dy, 4, 10), border_radius=2)
            pygame.draw.ellipse(surf, (40, 25, 50), (lx - 1, 33 + dy, 6, 3))  # paw
        # Tail (smooth curve)
        pts = [(36, 14 + dy), (40, 10 + dy), (43, 8 + dy), (41, 6 + dy)]
        pygame.draw.lines(surf, body_c, False, pts, 3)
        pygame.draw.circle(surf, body_c, (41, 6 + dy), 2)
        frames.append(surf)
    return frames


def _generate_flying_frames() -> list[pygame.Surface]:
    """Two-frame bat with spikes -- cleaner wing shape."""
    frames = []
    for wing_up in (True, False):
        surf = pygame.Surface((34, 28), pygame.SRCALPHA)
        body_c = (80, 30, 120)
        pygame.draw.ellipse(surf, body_c, (11, 9, 12, 14))
        if wing_up:
            pygame.draw.polygon(surf, (110, 50, 150), [(11, 14), (0, 3), (15, 11)])
            pygame.draw.polygon(surf, (110, 50, 150), [(23, 14), (34, 3), (19, 11)])
        else:
            pygame.draw.polygon(surf, (110, 50, 150), [(11, 14), (0, 21), (15, 17)])
            pygame.draw.polygon(surf, (110, 50, 150), [(23, 14), (34, 21), (19, 17)])
        # Eyes
        pygame.draw.circle(surf, (255, 50, 50), (14, 13), 2)
        pygame.draw.circle(surf, (255, 50, 50), (20, 13), 2)
        pygame.draw.circle(surf, (255, 200, 200), (14, 12), 1)
        pygame.draw.circle(surf, (255, 200, 200), (20, 12), 1)
        # Spikes
        for sx in (13, 17, 21):
            pygame.draw.polygon(surf, (200, 60, 60),
                                [(sx, 9), (sx - 2, 3), (sx + 2, 3)])
        frames.append(surf)
    return frames


def generate_mutant_boss(w: int, h: int) -> pygame.Surface:
    """Procedural mutant panda boss -- corrupted, larger, menacing."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2

    # Body (bulky dark torso)
    body_c = (60, 45, 70)
    pygame.draw.ellipse(surf, body_c, (cx - 28, cy - 8, 56, 42))
    # Belly scar / corruption glow
    pygame.draw.ellipse(surf, (90, 40, 50), (cx - 16, cy + 2, 32, 22))
    # Corruption veins on belly
    for vx in (-8, 0, 8):
        pygame.draw.line(surf, (120, 50, 60),
                         (cx + vx, cy + 4), (cx + vx + 3, cy + 20), 1)

    # Arms (thick, clawed)
    arm_c = (50, 35, 60)
    # Left arm
    pygame.draw.rect(surf, arm_c, (cx - 38, cy - 2, 12, 28), border_radius=4)
    # Right arm
    pygame.draw.rect(surf, arm_c, (cx + 26, cy - 2, 12, 28), border_radius=4)
    # Claws
    claw_c = (200, 180, 160)
    for side, sx in [(-1, cx - 38), (1, cx + 30)]:
        for ci in range(3):
            px = sx + 2 + ci * 3
            pygame.draw.line(surf, claw_c, (px, cy + 24), (px + side, cy + 30), 2)

    # Legs (stocky)
    leg_c = (45, 30, 55)
    pygame.draw.rect(surf, leg_c, (cx - 20, cy + 28, 14, 16), border_radius=4)
    pygame.draw.rect(surf, leg_c, (cx + 6, cy + 28, 14, 16), border_radius=4)
    # Feet
    pygame.draw.ellipse(surf, (40, 25, 50), (cx - 22, cy + 40, 18, 6))
    pygame.draw.ellipse(surf, (40, 25, 50), (cx + 4, cy + 40, 18, 6))

    # Head (large, round, corrupted panda)
    head_c = (75, 60, 80)
    pygame.draw.circle(surf, head_c, (cx, cy - 16), 22)
    # Face lighter area
    pygame.draw.circle(surf, (100, 85, 105), (cx, cy - 12), 14)

    # Ears (tattered, one larger)
    ear_c = (65, 50, 70)
    pygame.draw.circle(surf, ear_c, (cx - 18, cy - 32), 9)
    pygame.draw.circle(surf, (120, 50, 50), (cx - 18, cy - 32), 4)  # red inner
    pygame.draw.circle(surf, ear_c, (cx + 18, cy - 34), 10)
    pygame.draw.circle(surf, (120, 50, 50), (cx + 18, cy - 34), 5)
    # Torn ear notch (triangle cut)
    pygame.draw.polygon(surf, (0, 0, 0, 0), [
        (cx + 14, cy - 42), (cx + 20, cy - 40), (cx + 16, cy - 36)])

    # Eye patches (corrupted red-tinted)
    pygame.draw.ellipse(surf, (80, 30, 40), (cx - 14, cy - 22, 12, 10))
    pygame.draw.ellipse(surf, (80, 30, 40), (cx + 2, cy - 22, 12, 10))

    # Eyes (glowing red with bright center)
    pygame.draw.circle(surf, (220, 40, 40), (cx - 8, cy - 17), 5)
    pygame.draw.circle(surf, (220, 40, 40), (cx + 8, cy - 17), 5)
    # Pupils (yellow slit)
    pygame.draw.rect(surf, (255, 200, 50), (cx - 9, cy - 20, 2, 6))
    pygame.draw.rect(surf, (255, 200, 50), (cx + 7, cy - 20, 2, 6))
    # Eye glow
    pygame.draw.circle(surf, (255, 80, 60), (cx - 8, cy - 17), 6, 1)
    pygame.draw.circle(surf, (255, 80, 60), (cx + 8, cy - 17), 6, 1)

    # Nose
    pygame.draw.ellipse(surf, (50, 30, 40), (cx - 3, cy - 10, 7, 5))

    # Mouth (snarling with fangs)
    pygame.draw.arc(surf, (40, 20, 30), (cx - 10, cy - 8, 20, 10), 3.14, 6.28, 2)
    # Fangs
    fang_c = (230, 220, 200)
    pygame.draw.polygon(surf, fang_c, [(cx - 7, cy - 4), (cx - 5, cy + 3), (cx - 3, cy - 4)])
    pygame.draw.polygon(surf, fang_c, [(cx + 3, cy - 4), (cx + 5, cy + 3), (cx + 7, cy - 4)])

    # Corruption marks (purple cracks across body)
    crack_c = (150, 50, 180)
    pygame.draw.line(surf, crack_c, (cx - 12, cy - 28), (cx - 20, cy - 10), 2)
    pygame.draw.line(surf, crack_c, (cx + 10, cy - 25), (cx + 22, cy - 8), 2)
    pygame.draw.line(surf, crack_c, (cx - 5, cy + 5), (cx - 15, cy + 20), 1)
    pygame.draw.line(surf, crack_c, (cx + 5, cy + 8), (cx + 12, cy + 22), 1)

    # Spiky corrupted mane/fur on top of head
    spike_c = (100, 40, 110)
    for sx_off in (-12, -6, 0, 6, 12):
        sh = 8 + abs(sx_off) // 3
        pygame.draw.polygon(surf, spike_c, [
            (cx + sx_off - 3, cy - 34),
            (cx + sx_off, cy - 34 - sh),
            (cx + sx_off + 3, cy - 34)])

    return surf


def _generate_slime_frames() -> list[pygame.Surface]:
    """Two-frame bouncing slime enemy -- green jelly blob."""
    frames = []
    # Frame 0: normal shape
    s0 = pygame.Surface((30, 28), pygame.SRCALPHA)
    pygame.draw.ellipse(s0, (50, 180, 80), (2, 6, 26, 22))
    pygame.draw.ellipse(s0, (70, 210, 100), (6, 10, 18, 14))  # highlight
    pygame.draw.circle(s0, COL_WHITE, (10, 14), 3)
    pygame.draw.circle(s0, COL_WHITE, (20, 14), 3)
    pygame.draw.circle(s0, COL_BLACK, (11, 14), 2)
    pygame.draw.circle(s0, COL_BLACK, (19, 14), 2)
    pygame.draw.arc(s0, COL_BLACK, (11, 18, 8, 5), 3.14, 6.28, 1)
    frames.append(s0)
    # Frame 1: squished (wider, shorter)
    s1 = pygame.Surface((30, 28), pygame.SRCALPHA)
    pygame.draw.ellipse(s1, (50, 180, 80), (0, 10, 30, 18))
    pygame.draw.ellipse(s1, (70, 210, 100), (4, 13, 22, 12))
    pygame.draw.circle(s1, COL_WHITE, (10, 17), 3)
    pygame.draw.circle(s1, COL_WHITE, (20, 17), 3)
    pygame.draw.circle(s1, COL_BLACK, (11, 17), 2)
    pygame.draw.circle(s1, COL_BLACK, (19, 17), 2)
    pygame.draw.arc(s1, COL_BLACK, (11, 20, 8, 4), 3.14, 6.28, 1)
    frames.append(s1)
    return frames


# ---------------------------------------------------------------------------
# Sprite classes
# ---------------------------------------------------------------------------

class Player(pygame.sprite.Sprite):
    """The panda protagonist with full physics and animation."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.frames = generate_panda_frames()
        self.anim_state = "idle"
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.facing_right = True

        self.image = self.frames["idle"][0]
        self.rect = self.image.get_rect(bottomleft=(x, y))

        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0
        self.is_on_ground = False

        self.health: int = PLAYER_MAX_HP
        self.score: int = 0
        self.invincible_timer: float = 0.0

        self.combo_count: int = 0
        self.combo_timer: float = 0.0

        self.has_double_jump: bool = False
        self.jumps_remaining: int = 1
        # Coyote time: brief window after leaving ground where jumps still fire.
        # Fixes "phantom fall" on moving platforms where the player technically
        # separates from the surface for 1-2 frames before jump input arrives.
        self.coyote_timer: float = 0.0

        self.friction_mode: str = "normal"  # "normal" or "ice"
        self.dead = False

        # Bamboo staff weapon system
        self.has_bamboo_weapon: bool = False
        self.weapon_time_remaining: float = 0.0  # counts down; 0 = no weapon
        self.is_attacking: bool = False
        self.attack_timer: float = 0.0
        self.attack_cooldown: float = 0.0
        # Special animation states
        self.is_victory_dancing: bool = False
        self.dance_timer: float = 0.0
        self.is_falling_trench: bool = False
        self.fall_anim_timer: float = 0.0
        # Knockback (applied on damage) -- short burst of velocity away from source
        self.knockback_timer: float = 0.0
        # Sub-pixel motion accumulator (fixes ice softlock)
        self._sub_x: float = 0.0
        # Input lock (dash, cutscene) -- ALWAYS cleared by reset_state()
        self.input_locked: bool = False
        self.input_lock_timer: float = 0.0  # safety timeout so locks cannot stick forever
        # Dash ability
        self.is_dashing: bool = False
        self.dash_timer: float = 0.0
        self.dash_cooldown: float = 0.0
        self.dash_direction: float = 1.0
        # Wall-slide
        self.is_wall_sliding: bool = False
        # Ground slam (down+jump while airborne) -- available from start
        self.is_slamming: bool = False
        # Glide (hold jump while falling) -- TIMED pickup (10s duration)
        self.is_gliding: bool = False
        self.glide_time_remaining: float = 0.0
        # Dash (pickup-based item, 30s duration)
        self.dash_time_remaining: float = 0.0
        # Bamboo throw projectile cooldown
        self.throw_cooldown: float = 0.0
        self.pending_throws: list = []
        # Gravity multiplier (1.0 normal, 0.3 low, 2.0 high, -1.0 reverse)
        self.gravity_multiplier: float = 1.0
        # Ice magic (unlocked after Level 3 boss defeat)
        self.has_ice_magic: bool = False
        self.mana: float = 0.0
        self.mana_max: float = 100.0
        self.ice_cast_cooldown: float = 0.0
        self.pending_ice_casts: list = []  # (x, y, direction) tuples
        # Jump buffer state for super responsive controls
        self._jump_buffered: bool = False
        self._jump_buffer_time: float = 0.0
        self._consumed_buffered_jump: bool = False  # set True for one frame when buffer auto-fires on land
        self._just_cut: bool = False  # one-frame for jump cut visual juice
        # Grafts from Grove meta (profile persisted modifiers, applied on spawn)
        self.grafts: list[str] = []
        self._graft_set: set[str] = set()  # micro-opt for hotpath 'in' checks (long-play/perf)
        # Hit flash juice (brief white pop on damage for feedback)
        self.hit_flash_timer: float = 0.0
        # Tiny hitstop juice for landing snap / vine snag feel (brief x damp so feet plant crisp)
        self.hitstop_timer: float = 0.0
        # Perf: reusable tint/overlay scratch surfaces keyed by size (see _scratch_surface).
        # Kills per-frame Surface allocation in _update_animation (dash/attack/hit/graft tints).
        self._tint_cache: dict[tuple[int, int], pygame.Surface] = {}

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper,
               platforms: pygame.sprite.Group) -> None:
        # HOTPATH: player physics, timers, movement, collisions. Called every frame.
        # Avoid allocations here; use precomputed grafts, dt scaling from caller.
        if self.dead:
            return

        # Long-play / perf stability micro-guard: safe timer decrements prevent neg creep in 1000+ frame runs
        # (early-out style + max0, no behavior change for normal dt>0)
        def _dec(t: float) -> float:
            return max(0.0, t - dt) if t > 0 else 0.0

        # Clear one-frame buffered-jump-consumed flag each frame
        self._consumed_buffered_jump = False
        self._just_cut = False

        # Hitstop juice countdown (tiny land/vine snap)
        self.hitstop_timer = _dec(self.hitstop_timer)

        # Coyote-time countdown (refreshed on every ground contact below)
        self.coyote_timer = _dec(self.coyote_timer)

        self.invincible_timer = _dec(self.invincible_timer)

        if self.combo_timer > 0:
            self.combo_timer = _dec(self.combo_timer)
            if self.combo_timer <= 0:
                self.combo_count = 0

        self.spore_puff_timer = _dec(getattr(self, 'spore_puff_timer', 0))
        self.chrono_slow_timer = _dec(getattr(self, 'chrono_slow_timer', 0))
        if hasattr(self, '_echo_timer') and self._echo_timer > 0:
            self._echo_timer -= dt

        # Attack timers
        self.attack_timer = _dec(self.attack_timer)
        if self.attack_timer <= 0:
            self.is_attacking = False
        self.attack_cooldown = _dec(self.attack_cooldown)
        # Dash timer
        if self.is_dashing:
            self.dash_timer = _dec(self.dash_timer)
            # Velocity during dash is fixed; no gravity decay yet
            self.velocity_x = DASH_VELOCITY * self.dash_direction
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.input_locked = False
                # Variable dash brake: stronger stop if no horiz input held (better control), gentler if steering through
                no_horiz = not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d])
                brake = 0.28 if no_horiz else 0.58
                spd = abs(self.velocity_x)
                if spd < 160:
                    # post-dash steering brake more forgiving at low speeds: retain momentum for responsive low-speed steering adjust (was abrupt)
                    brake = 0.82 if no_horiz else 0.90
                elif spd < 420:
                    brake = 0.42 if no_horiz else 0.68
                self.velocity_x *= brake  # variable post-dash slowdown for improved dash feel
        self.dash_cooldown = _dec(self.dash_cooldown)

        # Input lock safety: if locked (e.g. mid-dash), skip input.
        # ALWAYS clears after dash completes so player isn't stuck.
        # Extra ground-clear lives in game.py; reset_state always forces False.
        if self.input_locked:
            pass  # velocity controlled externally (dash)
        elif self.friction_mode == "ice":
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.velocity_x -= ICE_ACCEL * dt
                self.facing_right = False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.velocity_x += ICE_ACCEL * dt
                self.facing_right = True
            self.velocity_x *= ICE_FRICTION
            max_v = PLAYER_SPEED * 1.5
            self.velocity_x = max(-max_v, min(max_v, self.velocity_x))
            # Only snap to zero when truly stopped AND no input -- tighter snap for perfect no-creep predictable ice
            no_input = not (keys[pygame.K_LEFT] or keys[pygame.K_a]
                           or keys[pygame.K_RIGHT] or keys[pygame.K_d])
            if no_input and abs(self.velocity_x) < 0.6:
                self.velocity_x = 0.0  # ice snap: stop cleanly only with zero input (prevents creep/softlock)
        else:
            # Non-ice ground/air movement
            # On ground: instant full speed (snappy)
            # In air: partial control for floaty but responsive feel
            desired = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                desired = -PLAYER_SPEED
                self.facing_right = False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                desired = PLAYER_SPEED
                self.facing_right = True
            if self.is_on_ground:
                self.velocity_x = desired
            else:
                # Air control: proper acceleration (dt-based) for floaty but responsive feel
                # Ground is instant snap; air has momentum but you can steer
                # (use config AIR_ACCEL for easy lane tuning)
                air_mult = 1.0
                if "wind_ward" in self._graft_set:
                    air_mult = 1.25  # delightful slight air boost for wind_ward
                if desired != 0:
                    # Accelerate toward input; allow turning around with a bit more "bite"
                    # Tricky physics: when reversing direction mid-air, apply scaled AIR_REVERSAL_KICK so
                    # momentum doesn't trap the player facing old way (<1.0 for smooth not twitchy feel).
                    if (desired > 0) != (self.velocity_x > 0) and abs(self.velocity_x) > 60:
                        self.velocity_x += (desired - self.velocity_x) * AIR_REVERSAL_KICK * air_mult
                    else:
                        # Normal accel toward desired direction, capped at desired speed
                        # micro polish lane5/16: slightly snappier air control curve on horizontal -- use eased (boosted) accel when near target vel
                        step = AIR_ACCEL * dt
                        dist = abs(desired - self.velocity_x)
                        if dist < 85:
                            step *= 1.45  # eased accel when near target: crisp arrival without overshoot or mush
                        if desired > 0:
                            self.velocity_x = min(desired, self.velocity_x + step)
                        else:
                            self.velocity_x = max(desired, self.velocity_x - step)
                else:
                    # No input: gentle air friction so you eventually slow if you let go
                    self.velocity_x *= 0.980

        # Ultra visionary: wild_weave passive vine on movement (signal for game layer)
        _gs = getattr(self, '_graft_set', None) or set(getattr(self, 'grafts', []))
        if "wild_weave" in _gs:
            self._wild_vine_timer = getattr(self, '_wild_vine_timer', 0.0) - dt
            if self._wild_vine_timer <= 0 and (abs(self.velocity_x) > 10 or not self.is_on_ground):
                self._wild_vine_timer = 0.7
                # game.py will check and apply visual/entangle during update for parity

        # Glide: hold SPACE while airborne + falling
        # Low threshold (10) makes glide forgiving -- catches you soon after apex (glide forgiving threshold)
        jump_held = (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w])
        self.set_gliding(jump_held and not self.is_on_ground and self.velocity_y > 10)

        # Variable jump cut: releasing jump while rising reduces height for premium responsive feel
        # (JUMP_CUT) -- polled here for consistency; removed duplicate from game KEYUP to prevent double mul
        if not jump_held and self.velocity_y < 0 and not self.is_gliding and not self.is_dashing:
            self.velocity_y *= JUMP_CUT_MULTIPLIER
            self._just_cut = True  # for juice feedback in game loop

        # Jump buffer: allow pressing jump slightly before landing (JUMP_BUFFER_TIME window)
        # Makes controls feel much more responsive and forgiving
        if jump_held and not self._jump_buffered:
            self._jump_buffered = True
            self._jump_buffer_time = JUMP_BUFFER_TIME
        if self._jump_buffer_time > 0:
            self._jump_buffer_time -= dt
            if self._jump_buffer_time <= 0:
                self._jump_buffered = False

        # Weapon timer (limited duration) -- decrement if armed
        if self.has_bamboo_weapon and self.weapon_time_remaining > 0:
            self.weapon_time_remaining -= dt
            if self.weapon_time_remaining <= 0:
                self.has_bamboo_weapon = False
                self.weapon_time_remaining = 0.0

        # Throw cooldown
        if self.throw_cooldown > 0:
            self.throw_cooldown -= dt

        # Dash item timer (counts down while equipped)
        if self.dash_time_remaining > 0:
            self.dash_time_remaining -= dt
            if self.dash_time_remaining < 0:
                self.dash_time_remaining = 0.0

        # Glide timer decrements only while actively gliding
        if self.is_gliding and self.glide_time_remaining > 0:
            self.glide_time_remaining -= dt
            if self.glide_time_remaining <= 0:
                self.glide_time_remaining = 0.0
                self.is_gliding = False

        # Ice magic cooldown + mana regen
        # Mana regenerates to full over 10 seconds (10/sec)
        if self.has_ice_magic:
            if self.ice_cast_cooldown > 0:
                self.ice_cast_cooldown -= dt
            if self.mana < self.mana_max:
                self.mana = min(self.mana_max, self.mana + 10.0 * dt)

        # ==============================================================
        # X-AXIS MOVEMENT + COLLISION (strictly separated from Y)
        # Use the actual attempted delta (dx) to decide which side to snap
        # instead of trusting velocity_x (which can be 0 mid-bump).
        # ==============================================================
        self._sub_x += self.velocity_x * dt
        dx = _fl(self._sub_x)
        self._sub_x -= dx
        if dx != 0:
            self.rect.x += dx
            for hit in pygame.sprite.spritecollide(self, platforms, False):
                if dx > 0:
                    self.rect.right = hit.rect.left
                elif dx < 0:
                    self.rect.left = hit.rect.right
                self.velocity_x = 0
                self._sub_x = 0.0

        # Apply tiny hitstop juice snap (landing or snag): damp horiz briefly for crisp plant feel
        if self.hitstop_timer > 0:
            self.velocity_x *= 0.35  # quick settle, no slide after plant; feels planted not skiddy
            # (still allows tiny steer on air revgrav etc)

        # Power-modulated gravity (multiplied by gravity zone multiplier)
        g_mult = self.gravity_multiplier
        effective_gravity = GRAVITY * g_mult
        if self.is_slamming:
            self.velocity_y += effective_gravity * 1.3 * dt
        elif self.is_gliding and self.velocity_y >= 0 and g_mult > 0:
            # Slow fall while holding jump (only in normal/low gravity)
            # Light meta: weak_glide is milder permanent; efficiency is stronger legacy
            if "glide_efficiency" in _gs:
                glide_mult = 0.08
            elif "weak_glide" in _gs:
                glide_mult = 0.12
            else:
                glide_mult = 0.15
            self.velocity_y = min(self.velocity_y + effective_gravity * glide_mult * dt, 120.0)
        elif self.is_wall_sliding and self.velocity_y >= 0:
            self.velocity_y = min(self.velocity_y + effective_gravity * 0.3 * dt, 150.0)
        elif (not self.is_on_ground and abs(self.velocity_y) < 80
              and g_mult > 0 and not self.is_slamming):
            # Apex hang: at the top of a jump arc (|vy| < 80 px/s) apply
            # 40% gravity so the player lingers briefly at peak height.
            # 80 px/s ≈ 5 frames of reduced gravity before full gravity resumes;
            # 0.40 was tuned to feel floaty without making the jump feel slow.
            self.velocity_y += effective_gravity * 0.40 * dt
        else:
            self.velocity_y += effective_gravity * dt
        # Clamp to terminal velocity (both directions for reverse gravity)
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        elif self.velocity_y < -TERMINAL_VELOCITY:
            self.velocity_y = -TERMINAL_VELOCITY
        # ==============================================================
        # Y-AXIS MOVEMENT + COLLISION (strictly separated from X)
        # ==============================================================
        dy = _fl(self.velocity_y * dt)
        if dy != 0:
            self.rect.y += dy
        self.is_on_ground = False
        self.is_wall_sliding = False
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            # Determine landing direction based on gravity
            if self.gravity_multiplier < 0:
                # Reverse gravity: "ground" is above (ceiling contact)
                # Landing when moving up (velocity_y <= 0) or resting (dy==0, vy<=0)
                if dy < 0 or (dy == 0 and self.velocity_y <= 0):
                    self.rect.top = hit.rect.bottom
                    hard_land = (self.velocity_y < -280) or self.is_slamming  # revgrav: incoming up vel large
                    self.velocity_y = 0
                    self.is_on_ground = True
                    self.is_slamming = False
                    self.jumps_remaining = 2 if self.has_double_jump else 1
                    self.coyote_timer = COYOTE_TIME
                    if getattr(self, 'friction_mode', 'normal') != "ice":
                        self.velocity_x *= LAND_DAMP  # land forgiveness: slight planted damp for crisp stop (non-ice)
                        if hard_land:
                            self.velocity_x *= 0.76  # 1-frame micro brake extra for planted feel on hard land
                    # ice deliberately distinct (no extra planted brake) to preserve coast/slide vs normal ground
                    # Tiny juice: landing snap hitstop (plant feet crisp on ceiling revgrav)
                    self.hitstop_timer = HITSTOP_LAND_SEC
                    # Consume jump buffer on revgrav ceiling land (symmetric to normal gravity)
                    if self._jump_buffered and self.jumps_remaining > 0:
                        kick = -PLAYER_JUMP
                        self.velocity_y = kick
                        self.jumps_remaining -= 1
                        self.is_on_ground = False
                        self._jump_buffered = False
                        self._jump_buffer_time = 0.0
                        self._consumed_buffered_jump = True
                elif dy > 0:
                    # Bonked feet on top of platform while falling down in reverse grav
                    self.rect.bottom = hit.rect.top
                    self.velocity_y = 0
            else:
                # Normal gravity: ground is below
                if dy > 0 or (dy == 0 and self.velocity_y >= 0):
                    # Landing / resting on platform top
                    self.rect.bottom = hit.rect.top
                    hard_land = (self.velocity_y > 280) or self.is_slamming
                    self.velocity_y = 0
                    self.is_on_ground = True
                    self.is_slamming = False  # slam ends on impact
                    self.jumps_remaining = 2 if self.has_double_jump else 1
                    # Refresh coyote time on every ground contact
                    self.coyote_timer = COYOTE_TIME
                    if getattr(self, 'friction_mode', 'normal') != "ice":
                        self.velocity_x *= LAND_DAMP  # land forgiveness: slight planted damp for crisp stop (non-ice)
                        if hard_land:
                            self.velocity_x *= 0.76  # 1-frame micro brake extra for planted feel on hard land
                    # ice deliberately distinct (no extra planted brake) to preserve coast/slide vs normal ground
                    # Tiny juice: landing snap hitstop (brief x damp for satisfying plant without slide)
                    self.hitstop_timer = HITSTOP_LAND_SEC
                    # Consume jump buffer: if player pressed slightly before landing, auto-jump now
                    if self._jump_buffered and self.jumps_remaining > 0:
                        kick = PLAYER_JUMP
                        if getattr(self, 'gravity_multiplier', 1.0) < 0:
                            kick = -PLAYER_JUMP
                        self.velocity_y = kick
                        self.jumps_remaining -= 1
                        self.is_on_ground = False
                        self._jump_buffered = False
                        self._jump_buffer_time = 0.0
                        self._consumed_buffered_jump = True
                elif dy < 0:
                    # Bonked head on underside
                    self.rect.top = hit.rect.bottom
                    self.velocity_y = 0

        # Knockback timer decrement (lets knockback velocity ride out)
        if self.knockback_timer > 0:
            self.knockback_timer -= dt
            if self.knockback_timer <= 0 and not self.is_dashing:
                self.input_locked = False
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt

        # input lock safety timeout
        if self.input_locked:
            if self.input_lock_timer > 0:
                self.input_lock_timer -= dt
            if self.input_lock_timer <= 0:
                self.input_locked = False
                self.input_lock_timer = 0.0

        # Long-play edge guard (micro opt/safety): hard clamp vels so no explosion in 1000+ frame headless stress
        # (prevents any revgrav/ice/flood accumulation corner cases while preserving all current behavior)
        self.velocity_x = max(-12000.0, min(12000.0, float(self.velocity_x)))
        self.velocity_y = max(-TERMINAL_VELOCITY, min(TERMINAL_VELOCITY, float(self.velocity_y)))

        self._update_animation(dt)

    def jump(self, audio: object = None) -> bool:
        """Jump the player. Honors coyote time + jump buffer (press slightly early) for ultra snappy controls.

        If jump cannot fire now (mid-air, no coyote), the jump is buffered so the
        NEXT landing within JUMP_BUFFER_TIME will auto-jump. This makes timing
        forgiving: press slightly before you land and it still fires.
        """
        # Coyote or recent buffer press allows restoring a ground jump
        can_ground = (self.coyote_timer > 0 or self._jump_buffered) and self.jumps_remaining < (2 if self.has_double_jump else 1)
        if can_ground:
            self.jumps_remaining = 2 if self.has_double_jump else 1
            self.coyote_timer = 0.0
            self._jump_buffered = False
            self._jump_buffer_time = 0.0

        if self.jumps_remaining > 0:
            kick = PLAYER_JUMP
            if getattr(self, 'gravity_multiplier', 1.0) < 0:
                kick = -PLAYER_JUMP
            self.velocity_y = kick
            # Revgrav ceiling launch feel tweak: give a touch more "pop" off stick for crisp release -- 1.05 for closer symmetry to normal grav jump
            if getattr(self, 'gravity_multiplier', 1.0) < 0:
                self.velocity_y *= 1.05  # tiny extra launch snap without making floaty or easy; symmetric tuned
            self.jumps_remaining -= 1
            # Leaving the ground via a jump ends the coyote window. Without this,
            # a first ground jump (can_ground False, so the zero-out above is
            # skipped) leaves coyote_timer alive, letting a tap-release-tap within
            # COYOTE_TIME restore jumps_remaining for an extra ground-strength jump
            # (effective triple jump that defeats level reachability barriers).
            self.coyote_timer = 0.0
            if self.is_on_ground:
                self.is_on_ground = False
            self._jump_buffered = False
            self._jump_buffer_time = 0.0
            return True
        # Could not jump now -- queue it so landing will trigger
        self._jump_buffered = True
        self._jump_buffer_time = JUMP_BUFFER_TIME
        return False

    def take_damage(self, amount: int = PLAYER_DAMAGE,
                    source_x: float | None = None) -> bool:
        """Apply damage + i-frames + positional knockback.

        source_x: world-space x of the damage source. Player is knocked
        AWAY from this point. Defaults to current x (knocks up only).
        """
        if self.invincible_timer > 0 or self.dead:
            return False
        if "spore_shield" in self.grafts:
            amount = max(1, amount - 1)
            self.spore_puff_timer = 0.5  # visual + resist counter
        self.health -= amount
        self.invincible_timer = PLAYER_INVINCIBLE_SEC  # i-frames
        self.hit_flash_timer = 0.12  # hit juice flash
        self.hitstop_timer = max(self.hitstop_timer, 0.025)  # brief snag-like stop on hit for feedback punch
        # Knockback: away from source, slight up-bounce
        if source_x is None:
            kb_dir = 1.0 if self.facing_right else -1.0
            # Reverse direction so player bounces off attacker
            kb_dir = -kb_dir
        else:
            kb_dir = 1.0 if self.rect.centerx >= source_x else -1.0
        self.velocity_x = KNOCKBACK_X * kb_dir
        self._sub_x = 0.0
        self.velocity_y = KNOCKBACK_Y
        self.knockback_timer = 0.25
        self.is_dashing = False
        self.is_slamming = False
        self.is_gliding = False
        self.input_locked = True
        self.input_lock_timer = 0.3  # brief loss of control with timeout guard
        if self.health <= 0:
            self.health = 0
            self.dead = True
        return True

    def collect_bamboo(self) -> int:
        idx = min(self.combo_count, len(COMBO_MULTIPLIERS) - 1)
        if "combo_bonus" in self.grafts:
            idx = min(self.combo_count + 1, len(COMBO_MULTIPLIERS) - 1)
        mult = COMBO_MULTIPLIERS[idx]
        self.combo_count = min(self.combo_count + 1, len(COMBO_MULTIPLIERS) - 1)
        self.combo_timer = COMBO_WINDOW
        points = BAMBOO_SCORE * mult
        if "bamboo_yield" in self.grafts:
            points += 10
        # Mastery payoff (Ultra 5+ grafts): small delightful score elevation on every bamboo
        if len(getattr(self, "grafts", [])) >= 5:
            points += 5
        self.score += points
        return points

    def heal(self, amount: int = HEAL_AMOUNT) -> None:
        cap = PLAYER_MAX_HP + (1 if "hp_boost" in self.grafts else 0)
        self.health = min(cap, self.health + amount)

    def get_stomp_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.x + 4, self.rect.bottom - 8,
                           self.rect.width - 8, 8)

    def attack(self, audio: object = None) -> bool:
        """Swing the bamboo staff. Returns True if attack started."""
        if (self.has_bamboo_weapon and not self.is_attacking
                and self.attack_cooldown <= 0 and not self.is_dashing):
            self.is_attacking = True
            self.attack_timer = 0.25
            self.attack_cooldown = 0.4
            # Chrono graft delight: staff swing can trigger brief world slow (on-hit feel in game.py collision)
            if "chrono_step" in self.grafts:
                self.chrono_slow_timer = max(getattr(self, "chrono_slow_timer", 0.0), CHRONO_SLOW_STAFF_SEC * 0.6)
            # Ultra visionary: chrono_weave on any action
            if "chrono_weave" in self.grafts:
                self.chrono_slow_timer = max(getattr(self, "chrono_slow_timer", 0.0), CHRONO_SLOW_STAFF_SEC * 1.1)
            return True
        return False

    def dash(self, audio: object = None) -> bool:
        """SHIFT-key dash. Requires DashBoots pickup (timed item).

        Pickup grants dash_time_remaining > 0 for a limited duration.
        Player can still dash freely during that window, subject to the
        normal 700ms cooldown between dashes.
        """
        if self.dash_time_remaining <= 0:
            return False  # no dash boots equipped
        if self.is_dashing or self.dash_cooldown > 0:
            return False
        self.is_dashing = True
        self.dash_timer = 0.18
        if "chrono_step" in self.grafts:
            cd = 0.22
            chrono_dur = CHRONO_SLOW_DASH_SEC
            if "chrono_dash" in getattr(self, "active_synergies", set()):
                chrono_dur *= 1.6  # synergy prototype: chrono_dash
            self.chrono_slow_timer = chrono_dur  # brief chrono slow time feel (visual + feel)
        elif "dash_mastery" in self.grafts:
            cd = 0.35
        else:
            cd = 0.7
        self.dash_cooldown = cd
        self.input_locked = True
        self.input_lock_timer = 0.25
        self.invincible_timer = max(self.invincible_timer, 0.2)
        self.dash_direction = 1.0 if self.facing_right else -1.0
        self.velocity_x = DASH_VELOCITY * self.dash_direction
        # Richer synergy elevation: chrono_dash now gives tiny upward "chrono hop" (delightful air control pop)
        if "chrono_dash" in getattr(self, "active_synergies", set()):
            self.velocity_y = min(self.velocity_y - 95, -140)
        # Echo step: set timer for echo visual/feel (deeper mastery)
        if "echo_step" in self.grafts:
            self._echo_timer = 1.5
        return True

    def slam(self) -> bool:
        """Ground-slam: high downward velocity while airborne."""
        if self.is_on_ground or self.is_slamming:
            return False
        self.is_slamming = True
        self.velocity_y = SLAM_VELOCITY  # fast drop
        self.is_gliding = False
        return True

    def set_gliding(self, glide: bool) -> None:
        """Toggle glide -- consumes glide_time_remaining.

        Glide only activates while timer > 0. Timer counts down only while
        actually gliding, so one 10s pickup = 10 seconds of cumulative glide.
        """
        if (glide and self.glide_time_remaining > 0
                and not self.is_on_ground and self.velocity_y > 0
                and not self.is_slamming and not self.is_dashing):
            self.is_gliding = True
        else:
            self.is_gliding = False

    @property
    def has_glide(self) -> bool:
        """Legacy accessor -- returns True if player currently has glide time."""
        return self.glide_time_remaining > 0

    @has_glide.setter
    def has_glide(self, value: bool) -> None:
        """Legacy setter -- grants 10s of glide or clears timer."""
        if value:
            self.glide_time_remaining = GLIDE_DURATION_SEC
        else:
            self.glide_time_remaining = 0.0

    def throw_bamboo(self) -> bool:
        """Throw a bamboo shuriken. Returns True if thrown."""
        if self.throw_cooldown > 0 or not self.has_bamboo_weapon:
            return False
        self.throw_cooldown = 0.5
        # Signal to game loop to spawn a projectile
        self.pending_throws.append((self.rect.centerx,
                                   self.rect.centery,
                                   1.0 if self.facing_right else -1.0))
        return True

    def cast_ice_spell(self) -> bool:
        """Cast an ice projectile. Requires full mana and unlock.

        Returns True if cast, False if blocked (no unlock / no mana / cd).
        """
        if not self.has_ice_magic:
            return False
        if self.ice_cast_cooldown > 0:
            return False
        if self.mana < self.mana_max:
            return False
        # Consume all mana and set 10s cooldown
        self.mana = 0.0
        self.ice_cast_cooldown = 10.0
        self.pending_ice_casts.append((
            self.rect.centerx, self.rect.centery,
            1.0 if self.facing_right else -1.0))
        return True

    def reset_state(self) -> None:
        """Called on level load / respawn to clear any transient locks."""
        self.input_locked = False
        self.is_attacking = False
        self.is_dashing = False
        self.is_wall_sliding = False
        self.is_slamming = False
        self.is_gliding = False
        self.attack_timer = 0.0
        self.attack_cooldown = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.throw_cooldown = 0.0
        self.pending_throws = []
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self._sub_x = 0.0
        self.gravity_multiplier = 1.0
        # Ice magic: reset cooldown + pending cast list, keep has_ice_magic
        self.ice_cast_cooldown = 0.0
        self.pending_ice_casts = []
        # Clear jump buffering state so respawn doesn't carry phantom queued jumps
        self._jump_buffered = False
        self._jump_buffer_time = 0.0
        self._consumed_buffered_jump = False
        self._just_cut = False
        self._graft_set = set(self.grafts)  # keep cache in sync on reset (long play stability)

    def apply_grafts(self, grafts: list[str], audio: object = None) -> None:
        """Apply profile grafts. Called by Game after player creation.
        Grafts are permanent across levels/runs (small non-breaking tweaks).
        Supports combine recipes: ... + new Lane5: vine_whip, chrono_step, spore_shield, essence_magnet.
        """
        self.grafts = list(grafts) if grafts else []
        self._graft_set = set(self.grafts)  # micro-opt cache for hot 'in' checks during update loops
        # hp_boost: grant starting +1 HP (light meta)
        if "hp_boost" in self.grafts:
            if self.health <= PLAYER_MAX_HP:
                self.health = PLAYER_MAX_HP + 1
        if "ice_armor" in self.grafts:
            # Ice armor grants a small starting buffer on apply
            if self.health <= PLAYER_MAX_HP + 1:
                self.health = max(self.health, PLAYER_MAX_HP + 2)
        # New graft state init for visuals/effects
        self.spore_puff_timer = 0.0
        self.chrono_slow_timer = 0.0
        if "essence_magnet" in self.grafts:
            self._magnet_hint = True  # for draw feedback if needed
        # Chrono graft: ensure timer starts clean (actual slow logic in Game using CHRONO_*)

        # Prototype ambitious next-level: Graft Synergies
        self.active_synergies: set[str] = set()
        gset = set(self.grafts)
        for combo, name in GRAFT_SYNERGIES.items():
            if all(g in gset for g in combo):
                self.active_synergies.add(name)

        # Mastery depth + ultra visionary
        gcount = len(self.grafts)
        self.mastery_tier = MASTERY_TIERS.get(gcount, "")
        if "wild_weave" in self.grafts:
            self._wild_vine_timer = 0.0
        if "chrono_weave" in self.grafts:
            self._chrono_weave_timer = 0.0
        if "root_ward" in self.grafts:
            self._root_timer = 0.0  # for future
        if "echo_step" in self.grafts:
            self._echo_timer = 0.0

        # Audio layer for mastery (called from game with audio; new chimes for 3+/5)
        if audio is not None:
            try:
                gcount = len(self.grafts)
                if gcount >= 5:
                    audio.play("mastery_chime", pitch=1.25)
                elif gcount >= 3:
                    audio.play("mastery_chime", pitch=1.1)
            except Exception:
                pass

    def get_attack_rect(self) -> pygame.Rect:
        """Stab hitbox: fast out, hold, quick retract."""
        if not self.is_attacking:
            return pygame.Rect(0, 0, 0, 0)

    def trigger_hitstop(self, dur: float = 0.03) -> None:
        """Tiny juice hook (e.g. vine snag entangle or other hazards call this for brief plant feel)."""
        self.hitstop_timer = max(getattr(self, 'hitstop_timer', 0.0), float(dur))
        max_reach = 60
        if "vine_whip" in getattr(self, "grafts", []):
            max_reach = 95  # powerful vine whip extension
        total = 0.25
        atk_t = 1.0 - (self.attack_timer / total)
        atk_t = max(0.0, min(1.0, atk_t))
        # Reach curve: 0-0.2 grow fast, 0.2-0.7 hold max, 0.7-1.0 retract
        if atk_t < 0.2:
            reach = int(max_reach * (atk_t / 0.2))
        elif atk_t < 0.7:
            reach = max_reach
        else:
            reach = int(max_reach * (1.0 - (atk_t - 0.7) / 0.3))
        reach = max(reach, 20)  # minimum reach while attacking
        hit_h = 30
        hit_y = self.rect.y + 2
        if self.facing_right:
            return pygame.Rect(self.rect.right, hit_y, reach, hit_h)
        return pygame.Rect(self.rect.left - reach, hit_y, reach, hit_h)

    def _update_animation(self, dt: float) -> None:
        prev = self.anim_state
        # Special states override normal animation
        if self.is_falling_trench:
            self.fall_anim_timer += dt
            lst = self.frames["fall"]
            frame = lst[0]
            # Spinning frantic animation
            angle = (self.fall_anim_timer * 540) % 360
            new_image = pygame.transform.rotate(frame, angle)
            self.image = new_image
            self.rect = new_image.get_rect(center=self.rect.center)
            return
        if self.is_victory_dancing:
            self.dance_timer += dt
            # Hop + bounce animation -- juicier victory dance (bigger bounce, scale pulse, more tilt)
            idx = int(self.dance_timer * 7) % 4
            bounce_frames = ["idle", "jump", "idle", "fall"]
            lst = self.frames[bounce_frames[idx]]
            frame = lst[0]
            # Flip between facing dirs for a "dance"
            if idx % 2 == 0:
                frame = pygame.transform.flip(frame, True, False)
            # Bigger playful tilt + scale pulse
            angle = math.sin(self.dance_timer * 9) * 18
            bob_scale = 1.0 + math.sin(self.dance_timer * 11) * 0.07
            new_image = pygame.transform.rotate(frame, angle)
            if abs(bob_scale - 1.0) > 0.01:
                sw, sh = new_image.get_size()
                new_image = pygame.transform.scale(new_image, (int(sw * bob_scale), int(sh * bob_scale)))
            self.image = new_image
            self.rect = new_image.get_rect(center=self.rect.center)
            return

        if self.is_dashing:
            self.anim_state = "dash"
        elif self.is_slamming:
            self.anim_state = "fall"
        elif self.is_gliding:
            self.anim_state = "glide"
        elif not self.is_on_ground:
            self.anim_state = "jump" if self.velocity_y < 0 else "fall"
        elif abs(self.velocity_x) > 10:
            self.anim_state = "run"
        else:
            self.anim_state = "idle"

        if self.anim_state != prev:
            self.anim_frame = 0
            self.anim_timer = 0.0

        speed = 0.06 if self.anim_state == "dash" else (
            0.1 if self.anim_state == "run" else 0.5)
        self.anim_timer += dt
        if self.anim_timer >= speed:
            self.anim_timer -= speed
            self.anim_frame += 1

        lst = self.frames[self.anim_state]
        frame = lst[self.anim_frame % len(lst)]
        # Dash visual feedback: subtle forward lean + speed tint (procedural)
        if self.anim_state == "dash":
            lean = -5 if self.facing_right else 5
            frame = pygame.transform.rotate(frame, lean)
            tint = _scratch_surface(self._tint_cache, frame.get_size())
            tint.fill((100, 200, 255, 35))
            frame.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.rect = frame.get_rect(center=self.rect.center)
        # Attack pose: subtle forward lean for stab (less than before)
        if self.is_attacking:
            atk_t = 1.0 - (self.attack_timer / 0.25)
            lean = -6 if atk_t < 0.5 else 3
            if not self.facing_right:
                lean = -lean
            frame = pygame.transform.rotate(frame, lean)
            # Keep physics rect centered after rotation
            self.rect = frame.get_rect(center=self.rect.center)
        # Hit flash: bright white overlay tint for juice feedback (short, punchy)
        if self.hit_flash_timer > 0:
            flash = _scratch_surface(self._tint_cache, frame.get_size())
            a = int(160 * (self.hit_flash_timer / 0.12))
            flash.fill((255, 255, 255, a))
            frame.blit(flash, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            # Extra hitstop juice: subtle yellow edge rim
            if self.hit_flash_timer > 0.05:
                rim = _scratch_surface(self._tint_cache, frame.get_size())
                rim.fill((255, 240, 120, int(a * 0.55)))
                frame.blit(rim, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.image = frame if self.facing_right else pygame.transform.flip(frame, True, False)

        # Graft visual indicators (subtle player tint/aura based on active Grove grafts)
        # Minimal + performant: tiny per-frame SRC alpha overlays. Leafy for glide, fire for lava etc.
        # VISUALS PARITY LOCK: this graft tint block + generate_panda_frames + Ghost alpha EXACT in root/web (forced sync 2026-06-24)
        if getattr(self, "grafts", None):
            t = pygame.time.get_ticks() / 280.0
            pulse = 0.75 + 0.25 * math.sin(t)
            gt = _scratch_surface(self._tint_cache, self.image.get_size())
            gs = self._graft_set or set(getattr(self, "grafts", []))  # use cache (micro opt)
            if "lava_resist" in gs:
                gt.fill((255, 130, 50, int(22 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if any(g in gs for g in ("glide_efficiency", "weak_glide")):
                gt.fill((55, 175, 75, int(17 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "ice_armor" in gs:
                gt.fill((95, 175, 235, int(15 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "dash_mastery" in gs:
                gt.fill((255, 175, 55, int(13 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "vine_whip" in gs:
                gt.fill((60, 200, 90, int(19 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "chrono_step" in gs:
                gt.fill((160, 90, 210, int(16 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "spore_shield" in gs:
                gt.fill((140, 80, 180, int(14 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "essence_magnet" in gs:
                gt.fill((255, 215, 80, int(12 * pulse)))
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "root_ward" in gs:
                gt.fill((139, 90, 43, int(18 * pulse)))  # earthy root tint
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "echo_step" in gs:
                gt.fill((160, 100, 200, int(16 * pulse)))  # echo/purple
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if "wind_ward" in gs:
                gt.fill((100, 200, 220, int(14 * pulse)))  # wind/cyan
                self.image.blit(gt, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                # small visual delight: extra airy wind gust tint (subtle brighter pulse) on wind_ward
                wd = _scratch_surface(self._tint_cache, self.image.get_size())
                wd_a = int(7 + 4 * math.sin(t * 2.9))
                wd.fill((170, 225, 255, wd_a))
                self.image.blit(wd, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            # Mastery indicator (final parity closer): subtle green leaf aura when 3+ grafts; stronger for 5+ (overgrown mastery)
            # Visible on both root and web. Simple, low-alpha, pulses with graft tints.
            gcount = len(gs)
            if gcount >= 3:
                ma = _scratch_surface(self._tint_cache, self.image.get_size())
                ma_a = int(9 + 5 * math.sin(t * 1.2))
                ma.fill((60, 170, 85, ma_a))
                self.image.blit(ma, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if gcount >= 5:
                # extra lush leaf ring for 5+ grafts (overgrown booster feel)
                mb = _scratch_surface(self._tint_cache, self.image.get_size())
                mb_a = int(11 + 6 * math.sin(t * 1.7))
                mb.fill((45, 155, 70, mb_a))
                self.image.blit(mb, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                # Full mastery visible reward: golden wild aura (special endgame flair) -- elevated pulse for payoff pop
                if gcount >= 5:
                    mg = _scratch_surface(self._tint_cache, self.image.get_size())
                    mg_a = int(18 + 12 * math.sin(t * 2.4))
                    mg.fill((255, 225, 90, mg_a))
                    self.image.blit(mg, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


class GhostPanda(pygame.sprite.Sprite):
    """Lightweight non-interacting replay ghost for speedrun best times.
    Records (t, x, y, facing) samples. Draws semi-transparent using existing panda frames.
    Never participates in collisions or level groups.
    """
    def __init__(self, replay: list[list], is_best: bool = True) -> None:
        super().__init__()
        self.replay = replay or []
        self.play_t: float = 0.0
        self.idx: int = 0
        self.is_best: bool = bool(is_best)  # for visual distinction: best (chase target) vs personal library ghosts
        self._tint_cache: dict[tuple[int, int], pygame.Surface] = {}  # perf: reuse tint overlay by size
        self._frames = generate_panda_frames()
        self.image: pygame.Surface = self._frames.get("idle", [pygame.Surface((36, 44), pygame.SRCALPHA)])[0].copy()
        self.rect: pygame.Rect = self.image.get_rect()

    def update(self, dt: float, current_t: float) -> None:
        if not self.replay:
            return
        self.play_t = current_t
        # advance idx to latest sample whose t <= play_t
        while self.idx + 1 < len(self.replay) and self.replay[self.idx + 1][0] <= self.play_t:
            self.idx += 1
        if self.idx >= len(self.replay):
            self.idx = len(self.replay) - 1
        if self.idx < 0:
            self.idx = 0
        # Polish for exact victory time match: if at or past final sample, land on last idx
        if self.replay and self.play_t >= self.replay[-1][0]:
            self.idx = len(self.replay) - 1

    def reset(self) -> None:
        """Reset playback head for a fresh speedrun attempt (time-synced ghost replay)."""
        self.play_t = 0.0
        self.idx = 0

    def draw(self, screen: pygame.Surface, camera: Camera | None = None, offset_x: float = 0.0, offset_y: float = 0.0) -> None:
        if not self.replay or self.idx >= len(self.replay):
            return
        # Pro-level fidelity: linear interpolation between samples for smooth movement
        t = self.play_t
        curr = self.replay[self.idx]
        curr_t, curr_x, curr_y, curr_f = curr
        next_t, next_x, next_y, next_f = curr
        if self.idx + 1 < len(self.replay):
            next_t, next_x, next_y, next_f = self.replay[self.idx + 1]
        if next_t > curr_t:
            alpha = max(0.0, min(1.0, (t - curr_t) / (next_t - curr_t)))
        else:
            alpha = 0.0
        gx = curr_x + (next_x - curr_x) * alpha
        gy = curr_y + (next_y - curr_y) * alpha
        facing = curr_f if alpha < 0.5 else next_f
        self.rect.center = (int(gx), int(gy))

        # compute screen pos early (fixes prior smear ref-before-assign, enables visible hints)
        if camera is not None:
            sx, sy = camera.apply_pos(self.rect.x, self.rect.y)
        else:
            sx = self.rect.x + offset_x
            sy = self.rect.y + offset_y

        # delight bob for replay (lane 4/16 ghost delight)
        bob = int(math.sin(self.play_t * 5.5) * 2)

        # approx inst speed for smear/trail quality (from recent samples)
        speed = 0.0
        if self.idx > 0:
            pt, px, py, _ = self.replay[self.idx - 1]
            ddt = max(0.001, t - pt)
            speed = ((gx - px) ** 2 + (gy - py) ** 2) ** 0.5 / ddt

        # pick a sensible frame (prefer run for speedrun feel) + animate using play_t
        frames = self._frames
        key = "run" if len(self.replay) > 3 else "idle"
        lst = frames.get(key) or frames.get("idle") or []
        if not lst:
            return
        # Animate: cycle frames based on play time for premium ghost replay feel
        speed_anim = 0.08 if key == "run" else 0.45
        fidx = int(self.play_t / speed_anim) % len(lst)
        frame = lst[fidx].copy()
        if not facing:
            frame = pygame.transform.flip(frame, True, False)

        # Enhanced alpha + tint for 'yours vs ghost' comparison:
        # best (the target to chase) = cooler blue tint + higher visibility pulse
        # personal ("yours" past attempts) = warmer orange tint + subtler alpha
        base_a = GHOST_ALPHA + int(14 * math.sin(self.play_t * 3.9))  # lively pulse for premium feel
        if self.is_best:
            a_mult = 1.12
            frame.set_alpha(max(70, min(210, int(base_a * a_mult))))
            tint = _scratch_surface(self._tint_cache, frame.get_size())
            tint.fill((130, 200, 255, 24 + int(10 * math.sin(self.play_t * 4.2))))
            frame.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            a_mult = 0.82
            frame.set_alpha(max(50, min(175, int(base_a * a_mult))))
            tint = _scratch_surface(self._tint_cache, frame.get_size())
            tint.fill((255, 185, 90, 32))  # warm "yours" contrast vs cool best ghost
            frame.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # next-level visuals: speed smear for fast ghosts (elongated motion feel) -- now safe
        dir_x = 1 if facing else -1
        if speed > 170:
            for s in range(1, 4):
                ox = sx - dir_x * s * min(7, int(speed / 55))
                oframe = frame.copy()
                oframe.set_alpha(max(12, int(32 / s)))
                screen.blit(oframe, (ox, sy + bob))

        # More visible path hints: small contrast dots along current+recent path (encourages chase without clutter)
        for k in range(3):
            pidx = self.idx - k * 2
            if pidx < 0 or pidx >= len(self.replay):
                continue
            px, py = self.replay[pidx][1], self.replay[pidx][2]
            if camera is not None:
                psx, psy = camera.apply_pos(px, py)
            else:
                psx, psy = px + offset_x, py + offset_y
            hint_r = 2 if k == 0 else 1
            hint_a = 95 if self.is_best else 70
            pygame.draw.circle(screen, (200, 220, 255) if self.is_best else (255, 200, 140),
                               (int(psx + 2), int(psy + 2 + bob)), hint_r)
            pygame.draw.circle(screen, (120, 170, 230) if self.is_best else (230, 160, 90),
                               (int(psx), int(psy + bob)), hint_r)

        screen.blit(frame, (sx, sy + bob))

        # Richer motion-blur trail: faint prior frames with fading alpha (premium ghost feel, encouraging chase)
        # IMPROVED trail interp: trail positions lerp between their samples using lagged time (no more discrete snaps)
        # next-level: 6 trail + extra interp substeps for silky smooth
        trail_fades = [0.72, 0.55, 0.40, 0.28, 0.18, 0.10]
        for k, fade in enumerate(trail_fades):
            pidx = self.idx - 1 - k
            if pidx < 0:
                break
            pc = self.replay[pidx]
            _, pgx, pgy, pf = pc
            if pidx + 1 < len(self.replay):
                pnc = self.replay[pidx + 1]
                p_t, px, py, _ = pc
                pn_t, pnx, pny, _ = pnc
                if pn_t > p_t:
                    lag_t = t - 0.18 * (k + 1)
                    pa = max(0.0, min(1.0, (lag_t - p_t) / (pn_t - p_t)))
                    pgx = px + (pnx - px) * pa
                    pgy = py + (pny - py) * pa
            lag = (k + 1) * 1
            pframe = lst[(fidx - lag) % len(lst)].copy() if len(lst) > 1 else frame.copy()
            if not pf:
                pframe = pygame.transform.flip(pframe, True, False)
            pframe.set_alpha(int(GHOST_ALPHA * fade * (1.0 if self.is_best else 0.82)))
            if not self.is_best:
                ptint = pygame.Surface(pframe.get_size(), pygame.SRCALPHA)
                ptint.fill((255, 180, 85, 18))
                pframe.blit(ptint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if camera is not None:
                psx, psy = camera.apply_pos(pgx, pgy)
            else:
                psx = pgx + offset_x
                psy = pgy + offset_y
            screen.blit(pframe, (psx, psy))

        # Polish: faint 'echo' ghost copy on beat for rhythmic visual pulse (synced to replay timing)
        beat_phase = int(self.play_t * 2.1) % 3
        if beat_phase == 0 and speed > 40:
            echo = frame.copy()
            echo.set_alpha(22 if self.is_best else 16)
            ex = sx + (2 if facing else -2)
            ey = sy - 1
            screen.blit(echo, (ex, ey))


class Platform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, w: int, h: int = 20) -> None:
        super().__init__()
        self.image = generate_platform_tile(w, h)
        self.rect = self.image.get_rect(topleft=(x, y))


class MovingPlatform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, w: int, h: int,
                 axis: str = "horizontal", distance: float = 150.0) -> None:
        super().__init__()
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


class Bamboo(pygame.sprite.Sprite):
    """Collectible bamboo with pulsing golden glow aura (affordance)."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.base_image = generate_bamboo_surface()
        # Pre-render a composite with a glow halo around the stalk
        w, h = self.base_image.get_size()
        self._composite = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
        self._stalk_offset = (6, 6)
        self.image = self._composite.copy()
        # Blit stalk on top
        self.image.blit(self.base_image, self._stalk_offset)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.base_y = float(self.rect.y)
        self.bob_timer: float = random.uniform(0, 6.28)
        self.glow_timer: float = random.uniform(0, 6.28)

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.bob_timer += dt * 2
        self.glow_timer += dt * 3
        self.rect.y = _fl(self.base_y + math.sin(self.bob_timer) * 1.5)
        # Pulsing golden glow
        alpha = int(60 + 60 * (math.sin(self.glow_timer) + 1) * 0.5)
        w, h = self._composite.get_size()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        # Soft glow circles (layered for halo effect)
        cx, cy = w // 2, h // 2
        for r, a_frac in ((16, 0.4), (12, 0.6), (8, 1.0)):
            glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 230, 120, int(alpha * a_frac)),
                              (r, r), r)
            self.image.blit(glow, (cx - r, cy - r),
                          special_flags=pygame.BLEND_RGBA_ADD)
        self.image.blit(self.base_image, self._stalk_offset)


class BambooShuriken(pygame.sprite.Sprite):
    """Thrown bamboo shuriken projectile. Travels horizontally, rotating."""

    def __init__(self, x: int, y: int, direction: float) -> None:
        super().__init__()
        self._base = pygame.Surface((20, 20), pygame.SRCALPHA)
        # 4-point bamboo star
        cx = 10
        for angle in (0, 90, 180, 270):
            dx = math.cos(math.radians(angle)) * 9
            dy = math.sin(math.radians(angle)) * 9
            pygame.draw.polygon(self._base, (130, 200, 90),
                                [(cx, cx), (cx + dx, cx + dy),
                                 (cx + math.cos(math.radians(angle + 30)) * 4,
                                  cx + math.sin(math.radians(angle + 30)) * 4)])
        pygame.draw.circle(self._base, (70, 140, 50), (cx, cx), 4)
        pygame.draw.circle(self._base, (180, 230, 120), (cx, cx), 2)
        self.image = self._base
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vx = SHURIKEN_SPEED * direction
        self.vy = 0.0
        self.rotation: float = 0.0
        self.lifetime: float = 2.5

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.pos_x += self.vx * dt
        self.pos_y += self.vy * dt
        self.vy += GRAVITY * 0.15 * dt  # slight drop
        self.rotation += 720 * dt * (1 if self.direction > 0 else -1)
        self.image = pygame.transform.rotate(self._base, self.rotation % 360)
        old_center = (_fl(self.pos_x), _fl(self.pos_y))
        self.rect = self.image.get_rect(center=old_center)
        self.lifetime -= dt
        if self.lifetime <= 0 or self.pos_y > SCREEN_HEIGHT:
            self.kill()


class IceProjectile(pygame.sprite.Sprite):
    """Ice spell projectile. Travels in a straight line, pierces enemies,
    explodes at max range or on wall contact. Leaves a freeze particle trail.
    """

    def __init__(self, x: int, y: int, direction: float) -> None:
        super().__init__()
        self._base = self._make_shard()
        self.image = self._base
        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vx = ICE_PROJECTILE_SPEED * direction  # faster than shuriken
        self.vy = 0.0  # travels straight (no gravity)
        self.rotation: float = 0.0
        self.lifetime: float = 1.5  # ~1200px travel range
        self.damage: int = 999  # instant-kill vs non-boss enemies
        # Trail buffer
        self._trail: list[tuple[float, float]] = []

    @staticmethod
    def _make_shard() -> pygame.Surface:
        """Glowing cyan-white diamond-shaped ice shard."""
        W, H = 36, 20
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        # Outer glow halo (concentric ellipses)
        for r_scale, alpha in [(1.0, 60), (0.8, 120), (0.6, 180)]:
            w2, h2 = int(W * r_scale), int(H * r_scale)
            ox, oy = (W - w2) // 2, (H - h2) // 2
            pygame.draw.ellipse(surf, (140, 220, 255, alpha),
                                (ox, oy, w2, h2))
        # Core ice shard (diamond shape)
        pts = [(2, H // 2), (W // 2, 3), (W - 3, H // 2),
               (W // 2, H - 3)]
        pygame.draw.polygon(surf, (200, 240, 255), pts)
        # Inner highlight
        pts2 = [(6, H // 2), (W // 2, 6), (W - 7, H // 2), (W // 2, H - 6)]
        pygame.draw.polygon(surf, (255, 255, 255), pts2)
        # Tip sparkles
        pygame.draw.circle(surf, (255, 255, 255), (W - 3, H // 2), 2)
        pygame.draw.circle(surf, (255, 255, 255), (2, H // 2), 2)
        return surf

    def update(self, dt: float) -> None:  # type: ignore[override]
        # Store trail point (for drawing)
        self._trail.append((self.pos_x, self.pos_y))
        if len(self._trail) > 8:
            self._trail.pop(0)
        self.pos_x += self.vx * dt
        self.pos_y += self.vy * dt
        # Flip image horizontally based on direction
        if self.direction < 0:
            self.image = pygame.transform.flip(self._base, True, False)
        else:
            self.image = self._base
        self.rect = self.image.get_rect(center=(_fl(self.pos_x),
                                                _fl(self.pos_y)))
        self.lifetime -= dt
        if self.lifetime <= 0 or self.pos_x < -50 or self.pos_x > PROJECTILE_WORLD_WIDTH:
            self.kill()


class DashBoots(pygame.sprite.Sprite):
    """Pickup that grants 30 seconds of dash ability.

    Rendered as stylized winged boots with orange speed trails.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        W, H = 42, 42
        base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Boot sole (dark brown)
        pygame.draw.rect(base, (90, 50, 30), (6, H - 10, W - 12, 6))
        pygame.draw.rect(base, (60, 30, 15), (6, H - 4, W - 12, 2))
        # Boot body (orange-red leather)
        pygame.draw.polygon(base, (200, 80, 50), [
            (8, H - 10), (W - 8, H - 10),
            (W - 6, 20), (W - 14, 10),
            (10, 14), (6, 22),
        ])
        # Highlight
        pygame.draw.line(base, (255, 140, 90),
                         (10, 22), (W - 14, 14), 2)
        # Laces (dark X pattern)
        for i in range(3):
            y = 22 + i * 5
            pygame.draw.line(base, (40, 20, 10),
                             (12, y), (W - 12, y + 2), 1)
        # Wing detail (small feathers on the side)
        wing_col = (255, 180, 100)
        wing_pts = [(W - 4, 18), (W + 2, 10), (W + 2, 16),
                    (W + 4, 14), (W, 22)]
        pygame.draw.polygon(base, wing_col, wing_pts)
        pygame.draw.polygon(base, (255, 220, 140), wing_pts, 1)
        # Speed streak behind
        for i, a in [(0, 180), (3, 130), (6, 80)]:
            streak = pygame.Surface((10, 3), pygame.SRCALPHA)
            streak.fill((255, 200, 120, a))
            base.blit(streak, (i, H // 2))

        self._base = base
        self.image = self._base.copy()
        self.rect = self.image.get_rect(center=(x, y - 22))
        self.base_y = float(self.rect.y)
        self.glow_timer: float = 0.0

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.glow_timer += dt * 3.0
        self.rect.y = _fl(self.base_y + math.sin(self.glow_timer) * 4)
        alpha = int(100 + 50 * (math.sin(self.glow_timer * 1.5) + 1) * 0.5)
        W, H = self._base.get_size()
        img = pygame.Surface((W + 16, H + 16), pygame.SRCALPHA)
        cx, cy = (W + 16) // 2, (H + 16) // 2
        for r, a_f in ((24, 0.3), (18, 0.55), (12, 0.9)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 160, 80, int(alpha * a_f)),
                              (r, r), r)
            img.blit(halo, (cx - r, cy - r),
                    special_flags=pygame.BLEND_RGBA_ADD)
        img.blit(self._base, (8, 8))
        self.image = img


class GlideFeather(pygame.sprite.Sprite):
    """Pickup that grants Pain-da the glide ability (hold JUMP while falling).

    Rendered as a glowing cyan-white feather with sparkle halo.
    Floats gently and pulses to attract attention.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        W, H = 40, 44
        base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Feather quill (central spine)
        spine_col = (180, 230, 255)
        pygame.draw.line(base, spine_col, (W // 2, H - 4), (W // 2 - 2, 6), 2)
        # Left barbs (cyan-white gradient)
        barb_cols = [(140, 210, 255), (100, 190, 240), (160, 225, 255)]
        for i, frac in enumerate([0.2, 0.35, 0.5, 0.65, 0.8]):
            sy = int(H * (1.0 - frac))
            col = barb_cols[i % len(barb_cols)]
            # Left barb
            pygame.draw.line(base, col,
                             (W // 2 - 1, sy), (W // 2 - 14 + i, sy - 4), 2)
            # Right barb
            pygame.draw.line(base, col,
                             (W // 2 + 1, sy), (W // 2 + 14 - i, sy - 4), 2)
        # Feather tip (bright white)
        pygame.draw.circle(base, (255, 255, 255), (W // 2 - 2, 6), 3)
        # Small wing silhouette overlay
        wing_pts = [
            (W // 2 - 12, H // 2 + 2),
            (W // 2, H // 2 - 10),
            (W // 2 + 12, H // 2 + 2),
            (W // 2, H // 2 + 6),
        ]
        pygame.draw.polygon(base, (200, 240, 255, 140), wing_pts)
        pygame.draw.polygon(base, (255, 255, 255, 80), wing_pts, 1)

        self._base = base
        self.image = self._base.copy()
        self.rect = self.image.get_rect(center=(x, y - 22))
        self.base_y = float(self.rect.y)
        self.glow_timer: float = 0.0

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.glow_timer += dt * 3.0
        # Gentle float
        self.rect.y = _fl(self.base_y + math.sin(self.glow_timer) * 4)
        # Pulsing cyan halo
        alpha = int(100 + 50 * (math.sin(self.glow_timer * 1.8) + 1) * 0.5)
        W, H = self._base.get_size()
        img = pygame.Surface((W + 16, H + 16), pygame.SRCALPHA)
        cx, cy = (W + 16) // 2, (H + 16) // 2
        for r, a_f in ((24, 0.3), (18, 0.55), (12, 0.9)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (140, 220, 255, int(alpha * a_f)),
                              (r, r), r)
            img.blit(halo, (cx - r, cy - r),
                    special_flags=pygame.BLEND_RGBA_ADD)
        img.blit(self._base, (8, 8))
        self.image = img


class BambooStaff(pygame.sprite.Sprite):
    """Pickup that grants Pain-da a bamboo weapon (swing with E/X/LMB).

    Rendered as a proper bo-staff: diagonal bamboo pole with leaves at the
    tip, rope grip in the middle, golden halo around it.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        # Build diagonal bo-staff on a 56x56 canvas
        W, H = 56, 56
        base = pygame.Surface((W, H), pygame.SRCALPHA)
        # Pole endpoints (lower-left to upper-right diagonal)
        p1 = (8, H - 10)
        p2 = (W - 8, 10)
        # Shadow trail behind pole (depth)
        pygame.draw.line(base, (50, 110, 40), (p1[0] + 2, p1[1] + 2),
                         (p2[0] + 2, p2[1] + 2), 6)
        # Main bamboo pole (thick, vibrant)
        pygame.draw.line(base, (130, 195, 80), p1, p2, 6)
        # Highlight stripe
        pygame.draw.line(base, (180, 230, 120),
                         (p1[0] - 1, p1[1] - 1), (p2[0] - 1, p2[1] - 1), 2)
        # Joint segments along the pole
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        nx, ny = dx / length, dy / length
        perp_x, perp_y = -ny, nx
        for frac in (0.18, 0.42, 0.66, 0.88):
            jx = int(p1[0] + dx * frac)
            jy = int(p1[1] + dy * frac)
            # Dark ring perpendicular to pole
            rx = int(perp_x * 5)
            ry = int(perp_y * 5)
            pygame.draw.line(base, (60, 130, 35),
                             (jx - rx, jy - ry), (jx + rx, jy + ry), 2)
        # Rope grip in middle (dark red wrapping)
        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2
        for i in range(-6, 7, 2):
            gx = mid_x + int(nx * i)
            gy = mid_y + int(ny * i)
            rx = int(perp_x * 4)
            ry = int(perp_y * 4)
            pygame.draw.line(base, (160, 40, 35),
                             (gx - rx, gy - ry), (gx + rx, gy + ry), 1)
        # Leaves at top tip
        leaf_c1 = (85, 170, 55)
        leaf_c2 = (130, 200, 80)
        tip = p2
        pygame.draw.polygon(base, leaf_c1, [
            (tip[0], tip[1] - 2),
            (tip[0] + 14, tip[1] - 8),
            (tip[0] + 4, tip[1] + 2),
        ])
        pygame.draw.polygon(base, leaf_c2, [
            (tip[0] + 1, tip[1] - 3),
            (tip[0] + 10, tip[1] - 6),
            (tip[0] + 4, tip[1])])
        pygame.draw.polygon(base, leaf_c1, [
            (tip[0], tip[1]),
            (tip[0] + 10, tip[1] + 8),
            (tip[0] - 2, tip[1] + 6),
        ])
        # Hollow tip (bamboo cross-section)
        pygame.draw.circle(base, (200, 230, 150), tip, 3)
        pygame.draw.circle(base, (80, 140, 50), tip, 3, 1)
        # Butt cap at bottom
        pygame.draw.circle(base, (60, 130, 35), p1, 4)
        pygame.draw.circle(base, (100, 170, 65), p1, 3)

        self._base = base
        self.image = self._base.copy()
        self.rect = self.image.get_rect(center=(x, y - 26))
        self.base_y = float(self.rect.y)
        self.glow_timer: float = 0.0

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.glow_timer += dt * 3.5
        # Gentle float + subtle rotation wobble
        self.rect.y = _fl(self.base_y + math.sin(self.glow_timer) * 3)
        # Pulsing golden halo behind
        alpha = int(110 + 60 * (math.sin(self.glow_timer * 1.5) + 1) * 0.5)
        W, H = self._base.get_size()
        img = pygame.Surface((W + 14, H + 14), pygame.SRCALPHA)
        # Soft halo (3 concentric rings for glow softness)
        cx, cy = (W + 14) // 2, (H + 14) // 2
        for r, a_f in ((28, 0.3), (22, 0.55), (16, 0.9)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 230, 120, int(alpha * a_f)),
                              (r, r), r)
            img.blit(halo, (cx - r, cy - r),
                    special_flags=pygame.BLEND_RGBA_ADD)
        img.blit(self._base, (7, 7))
        self.image = img


class HealingItem(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.base_image = generate_heal_surface()
        self.image = self.base_image
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.pulse_timer: float = random.uniform(0, 6.28)

    def update(self, dt: float) -> None:  # type: ignore[override]
        self.pulse_timer += dt * 4
        scale = 1.0 + 0.1 * math.sin(self.pulse_timer)
        w = int(25 * scale)
        h = int(25 * scale)
        cx, cy = self.rect.center
        self.image = pygame.transform.scale(self.base_image, (w, h))
        self.rect = self.image.get_rect(center=(cx, cy))


class PatrolEnemy(pygame.sprite.Sprite):
    """Mushroom that walks back and forth. Stompable."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 200.0) -> None:
        super().__init__()
        self._frames = _generate_mushroom_frames()
        self.image = self._frames[0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.patrol_width = patrol_width
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True
        self.anim_timer: float = 0.0

    def update(self, dt: float, platforms: pygame.sprite.Group,  # type: ignore[override]
               player: Player | None = None) -> None:
        if not self.alive_flag:
            return
        self.pos_x += ENEMY_PATROL_SPEED * self.direction * dt
        if abs(self.pos_x - self.origin_x) > self.patrol_width:
            self.direction *= -1
        self.rect.x = _fl(self.pos_x)
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0
        self.anim_timer += dt
        idx = int(self.anim_timer * 4) % 2
        frame = self._frames[idx]
        self.image = frame if self.direction > 0 else pygame.transform.flip(frame, True, False)

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class ChaserEnemy(pygame.sprite.Sprite):
    """Dark wolf that chases the player."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._frames = _generate_chaser_frames()
        self.image = self._frames[0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.velocity_y: float = 0.0
        self.alive_flag = True
        self.facing_right = True
        self.anim_timer: float = 0.0

    def update(self, dt: float, platforms: pygame.sprite.Group,  # type: ignore[override]
               player: Player | None = None) -> None:
        if not self.alive_flag or player is None:
            return
        dx = player.rect.centerx - self.rect.centerx
        dy_abs = abs(player.rect.centery - self.rect.centery)
        if abs(dx) < ENEMY_CHASE_RANGE and dy_abs < ENEMY_CHASE_Y_RANGE:
            if dx > 0:
                self.rect.x += _fl(ENEMY_CHASE_SPEED * dt)
                self.facing_right = True
            elif dx < 0:
                self.rect.x -= _fl(ENEMY_CHASE_SPEED * dt)
                self.facing_right = False
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0
        self.anim_timer += dt
        idx = int(self.anim_timer * 5) % 2
        frame = self._frames[idx]
        self.image = frame if self.facing_right else pygame.transform.flip(frame, True, False)

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class SlimeEnemy(pygame.sprite.Sprite):
    """Bouncing slime blob. Stompable."""
    is_stompable: bool = True

    def __init__(self, x: int, y: int, patrol_width: float = 180.0) -> None:
        super().__init__()
        self._frames = _generate_slime_frames()
        self.image = self._frames[0]
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.origin_x = float(x)
        self.patrol_width = patrol_width
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.velocity_y: float = 0.0
        self.alive_flag = True
        self.on_ground = False
        self.hop_timer: float = 0.0

    def update(self, dt: float, platforms: pygame.sprite.Group,  # type: ignore[override]
               player: Player | None = None) -> None:
        if not self.alive_flag:
            return
        # Horizontal drift
        self.pos_x += SLIME_BOUNCE_SPEED * self.direction * dt
        if abs(self.pos_x - self.origin_x) > self.patrol_width:
            self.direction *= -1
        self.rect.x = _fl(self.pos_x)
        # Hop periodically
        self.hop_timer += dt
        if self.on_ground and self.hop_timer > 0.8:
            self.velocity_y = SLIME_HOP_POWER
            self.on_ground = False
            self.hop_timer = 0.0
        # Gravity
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        self.on_ground = False
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0
                self.on_ground = True
        # Squished frame when on ground, normal when airborne
        self.image = self._frames[1] if self.on_ground else self._frames[0]
        if self.direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class FlyingEnemy(pygame.sprite.Sprite):
    """Flying bat. NOT stompable."""
    is_stompable: bool = False

    def __init__(self, x: int, y: int, flight_range: float = 200.0) -> None:
        super().__init__()
        self._frames = _generate_flying_frames()
        self.image = self._frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.origin_x = float(x)
        self.origin_y = float(y)
        self.flight_range = flight_range
        self.direction: float = 1.0
        self.pos_x = float(x)
        self.time: float = random.uniform(0, 6.28)
        self.alive_flag = True
        self.anim_timer: float = 0.0

    def update(self, dt: float, platforms: pygame.sprite.Group | None = None,  # type: ignore[override]
               player: Player | None = None) -> None:
        if not self.alive_flag:
            return
        # Slower, smoother horizontal drift
        self.pos_x += ENEMY_PATROL_SPEED * 0.6 * self.direction * dt
        if abs(self.pos_x - self.origin_x) > self.flight_range:
            self.direction *= -1
        # Slower frequency for organic feel + slight horizontal wobble
        self.time += dt * FLYING_ENEMY_FREQ * 0.6 * 2 * math.pi
        self.rect.x = _fl(self.pos_x + math.sin(self.time * 0.3) * 8)
        self.rect.y = _fl(self.origin_y + math.sin(self.time) * FLYING_ENEMY_AMP)
        self.anim_timer += dt
        idx = int(self.anim_timer * 5) % 2
        frame = self._frames[idx]
        self.image = frame if self.direction > 0 else pygame.transform.flip(frame, True, False)

    def die(self) -> None:
        self.alive_flag = False
        self.kill()


class Boss(pygame.sprite.Sprite):
    """Mutant panda boss with clear state-machine telegraph.

    States:
      idle (1.5s)       -- faces player, calm
      telegraph (0.8s)  -- FLASHES RED, warning charge incoming
      charging (varies) -- dashes toward player's last position
      stunned (1.5s)    -- BLUE TINT, vulnerable window, player can stomp
      defeated          -- dies after BOSS_HP stomps during stun

    Win condition: Stomp the boss BOSS_HP times during its stunned state.
    Each hit shows damage flash + HP bar decrement above the boss.
    """
    is_stompable: bool = True

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._base_image = generate_mutant_boss(*BOSS_SIZE)
        self.image = self._base_image
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.max_hp: int = BOSS_HP
        self.hp: int = BOSS_HP
        self.state: str = "idle"
        self.state_timer: float = BOSS_IDLE_SEC
        self.charge_target_x: float = 0.0
        self.stunned: bool = False
        self.facing_right: bool = False
        self.velocity_y: float = 0.0
        self.alive_flag: bool = True
        self.flash_timer: float = 0.0
        self.telegraph_timer: float = 0.0
        self._lunge_dir: int = 1

    def update(self, dt: float, player: Player,  # type: ignore[override]
               platforms: pygame.sprite.Group) -> None:
        if not self.alive_flag:
            return
        self.flash_timer = max(0.0, self.flash_timer - dt)

        # Always track the player
        dx_player = player.rect.centerx - self.rect.centerx
        abs_dist = abs(dx_player)
        self.facing_right = dx_player > 0

        AGGRO_RANGE = 600.0
        ATTACK_RANGE = 140.0
        CHASE_SPEED = BOSS_CHARGE_SPEED * 0.75  # faster chase -- feels threatening
        LUNGE_SPEED = BOSS_CHARGE_SPEED * 1.6   # FAST attack lunge

        if self.state == "idle":
            self.state_timer -= dt
            if self.state_timer <= 0:
                if abs_dist < AGGRO_RANGE:
                    self.state = "chasing"
                else:
                    self.state_timer = BOSS_IDLE_SEC
            self.stunned = False
        elif self.state == "chasing":
            if abs_dist > ATTACK_RANGE:
                self.rect.x += _fl(CHASE_SPEED * dt * (1 if dx_player > 0 else -1))
            else:
                # Telegraph (longer + VERY obvious)
                self.state = "telegraph"
                self.state_timer = 0.9
                self.telegraph_timer = 0.9
        elif self.state == "telegraph":
            self.state_timer -= dt
            self.telegraph_timer = self.state_timer
            if self.state_timer <= 0:
                self.state = "attacking"
                # Lock the attack direction at lunge start so the boss
                # commits -- player can dodge past him if timed right
                self._lunge_dir = 1 if dx_player > 0 else -1
                self.state_timer = 0.45
        elif self.state == "attacking":
            # Commit to the locked direction -- no mid-lunge tracking
            self.rect.x += _fl(LUNGE_SPEED * dt * self._lunge_dir)
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "stunned"
                self.stunned = True
                self.state_timer = BOSS_STUN_SEC
        elif self.state == "stunned":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "idle"
                self.state_timer = BOSS_IDLE_SEC * 0.5
                self.stunned = False

        # Gravity
        self.velocity_y += GRAVITY * dt
        if self.velocity_y > TERMINAL_VELOCITY:
            self.velocity_y = TERMINAL_VELOCITY
        self.rect.y += _fl(self.velocity_y * dt)
        for hit in pygame.sprite.spritecollide(self, platforms, False):
            if self.velocity_y > 0:
                self.rect.bottom = hit.rect.top
                self.velocity_y = 0

        # Visuals: base flip by facing
        img = self._base_image if self.facing_right else pygame.transform.flip(
            self._base_image, True, False)
        # Telegraph: strong red flash 4 times/sec
        if self.state == "telegraph":
            if int(self.telegraph_timer * 8) % 2 == 0:
                img = img.copy()
                img.fill((255, 0, 0, 120), special_flags=pygame.BLEND_RGBA_ADD)
        # Damage flash (white burst after being hit)
        elif self.flash_timer > 0:
            if int(self.flash_timer * 20) % 2:
                img = img.copy()
                img.fill((255, 255, 255, 180), special_flags=pygame.BLEND_RGBA_ADD)
        # Stun tint (strong pulsing BLUE overlay -- the vulnerable window)
        # Sword + stomp + ice all deal 1 HP while this is visible.
        if self.stunned:
            img = img.copy()
            # Pulsing intensity synced to game clock for visibility
            t = pygame.time.get_ticks() / 120.0
            pulse = int(140 + 60 * math.sin(t))
            img.fill((60, 140, 255, pulse), special_flags=pygame.BLEND_RGBA_ADD)
        self.image = img

    def take_hit(self) -> bool:
        self.hp -= 1
        self.flash_timer = 0.35
        if self.hp <= 0:
            self.alive_flag = False
            self.kill()
            return True
        return False

    def alive(self) -> bool:  # type: ignore[override]
        return self.alive_flag


class GrassTuft(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = generate_grass_tuft()
        self.rect = self.image.get_rect(bottomleft=(x, y))


class SafeZone(pygame.sprite.Sprite):
    """Forest clearing that acts as the level goal (replaces the old flag)."""
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        height = FLOOR_Y - y + (SCREEN_HEIGHT - FLOOR_Y)
        self.image = generate_safe_zone(max(80, height))
        self.rect = self.image.get_rect(bottomleft=(x, SCREEN_HEIGHT))


def _generate_checkpoint_surface(activated: bool = False) -> pygame.Surface:
    """A wooden signpost with a flag -- gray when inactive, green when hit."""
    surf = pygame.Surface((28, 60), pygame.SRCALPHA)
    # Pole
    pole_c = (100, 70, 40) if not activated else (110, 85, 50)
    pygame.draw.rect(surf, pole_c, (12, 10, 4, 50))
    # Base
    pygame.draw.rect(surf, (80, 55, 30), (6, 54, 16, 6), border_radius=2)
    # Flag
    if activated:
        flag_c = (50, 200, 80)
        flag_c2 = (40, 170, 60)
        # Checkmark on flag
        pygame.draw.polygon(surf, flag_c, [(16, 5), (28, 14), (16, 23)])
        pygame.draw.polygon(surf, flag_c2, [(16, 14), (28, 14), (16, 23)])
        pygame.draw.line(surf, COL_WHITE, (18, 15), (21, 19), 2)
        pygame.draw.line(surf, COL_WHITE, (21, 19), (26, 10), 2)
    else:
        flag_c = (160, 160, 160)
        flag_c2 = (130, 130, 130)
        pygame.draw.polygon(surf, flag_c, [(16, 5), (28, 14), (16, 23)])
        pygame.draw.polygon(surf, flag_c2, [(16, 14), (28, 14), (16, 23)])
    # Pole top knob
    pygame.draw.circle(surf, pole_c, (14, 8), 3)
    return surf


class Checkpoint(pygame.sprite.Sprite):
    """Checkpoint signpost. Saves player progress when touched."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self._img_off = _generate_checkpoint_surface(False)
        self._img_on = _generate_checkpoint_surface(True)
        self.image = self._img_off
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.activated = False
        self.spawn_x = x
        self.spawn_y = y

    def activate(self) -> bool:
        """Activate this checkpoint. Returns True if newly activated."""
        if self.activated:
            return False
        self.activated = True
        self.image = self._img_on
        return True
