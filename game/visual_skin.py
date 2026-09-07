"""Art-only skin for the shipped Bamboo Forest build.

Installed before game imports. Collision sizes, physics, levels, and saves stay
owned by the original shipped modules. Images are decoded and cached once.
"""
from pathlib import Path
from collections import deque
import math
import pygame
import pygame.image
import pygame.transform
import pygame.font
import pygame.draw

ART = Path(__file__).with_name("art")
_cache = {}
CREAM = (239, 234, 210)
GOLD = (222, 180, 97)
MUTED = (194, 205, 164)
DARK = (8, 24, 20)


def _image(name):
    if name not in _cache:
        _cache[name] = pygame.image.load(str(ART / name)).convert_alpha()
    return _cache[name]


def _panda_cells():
    if "panda_cells" in _cache:
        return _cache["panda_cells"]
    atlas = _image("panda-atlas.png")
    cells = []
    for row in range(2):
        for col in range(4):
            # Floor each edge independently: generated dimensions need not be
            # divisible by four. No poses share pixels.
            x0, x1 = col * atlas.get_width() // 4, (col + 1) * atlas.get_width() // 4
            y0, y1 = row * atlas.get_height() // 2, (row + 1) * atlas.get_height() // 2
            cell = pygame.transform.smoothscale(atlas.subsurface((x0, y0, x1-x0, y1-y0)), (256, 256)).convert_alpha()
            # The supplied atlas has a pale neutral matte. Decode only matte
            # connected to the outer edge; cream fur and enclosed eyes remain.
            queue = deque([(x, y) for x in range(256) for y in (0, 255)] +
                          [(x, y) for y in range(256) for x in (0, 255)])
            seen = set()
            while queue:
                x, y = queue.popleft()
                if (x, y) in seen or not (0 <= x < 256 and 0 <= y < 256):
                    continue
                seen.add((x, y))
                r, g, b, a = cell.get_at((x, y))
                if a == 0 or (min(r, g, b) > 195 and max(r, g, b) - min(r, g, b) < 18):
                    cell.set_at((x, y), (0, 0, 0, 0))
                    queue.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
            bounds = cell.get_bounding_rect()
            if not bounds.width or not bounds.height:
                raise ValueError("Empty panda pose")
            cells.append(cell.subsurface(bounds).copy())
    _cache["panda_cells"] = cells
    return cells


def panda_frames():
    from config import PLAYER_SIZE
    if "frames" not in _cache:
        poses = []
        # Fit each visual into the existing collision footprint.
        for cell in _panda_cells():
            scale = min(PLAYER_SIZE[0] / cell.get_width(), PLAYER_SIZE[1] / cell.get_height())
            rendered = pygame.transform.smoothscale(cell, (max(1, round(cell.get_width()*scale)), max(1, round(cell.get_height()*scale))))
            frame = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
            frame.blit(rendered, rendered.get_rect(midbottom=(PLAYER_SIZE[0]//2, PLAYER_SIZE[1])))
            poses.append(frame)
        _cache["frames"] = {"idle":poses[0:2], "run":[poses[2],poses[0],poses[3],poses[1]], "jump":[poses[4]], "fall":[poses[5]]}
    return _cache["frames"]


def forest_build(self):
    from config import SCREEN_HEIGHT
    return pygame.transform.smoothscale(_image("forest-background.png"), (self.w, SCREEN_HEIGHT)).convert()


def forest_draw(self, screen, camera_x):
    # Mirrored alternate panels share identical edge pixels, removing a hard
    # seam even though the generated source is not perfectly repeatable.
    if not hasattr(self, "_mirror"):
        self._mirror = pygame.transform.flip(self.surface, True, False)
    shift = camera_x * 0.12
    offset = math.floor(shift % (2 * self.w))
    for tile in range(-1, 4):
        x = tile * self.w - offset
        if x < screen.get_width() and x + self.w > 0:
            screen.blit(self.surface if tile % 2 == 0 else self._mirror, (x, 0))


def platform_tile(width, height):
    key = ("terrain", width, height)
    if key not in _cache:
        # Moss always sits exactly on the collider top. Keep stone proportions
        # for both thin jumping platforms and the deeper floor.
        tile_h = max(64, height)
        texture = pygame.transform.smoothscale(_image("moss-stone-tile.png"), (256, tile_h))
        surface = pygame.Surface((width, height))
        for x in range(0, width, 256):
            surface.blit(texture, (x, 0))
        _cache[key] = surface.convert()
    return _cache[key]


def _font(size, bold=False):
    key = ("font", size, bold)
    if key not in _cache:
        font = pygame.font.Font(None, size)
        font.set_bold(bold)
        _cache[key] = font
    return _cache[key]


def _text(screen, value, pos, size=22, color=CREAM, centered=False):
    s = _font(size).render(str(value), True, color)
    screen.blit(s, s.get_rect(center=pos) if centered else pos)


def _panel(screen, rect):
    panel = pygame.Surface(rect[2:], pygame.SRCALPHA)
    panel.fill((*DARK, 230))
    pygame.draw.rect(panel, (109, 128, 80, 225), panel.get_rect(), 1, border_radius=4)
    screen.blit(panel, rect[:2])


def hud_draw(self, screen, player, level_num, camera):
    from config import PLAYER_MAX_HP
    left_h = 100 if player.has_ice_magic else 80
    _panel(screen, (16, 16, 232, left_h))
    _text(screen, "HEALTH", (30, 28), 17, MUTED)
    pygame.draw.rect(screen, (68, 59, 45), (105, 29, 125, 10), border_radius=3)
    ratio = max(0, min(1, self.displayed_hp / PLAYER_MAX_HP))
    pygame.draw.rect(screen, (167, 186, 104), (105, 29, round(125 * ratio), 10), border_radius=3)
    _text(screen, f"SCORE  {player.score:05}", (30, 48), 23, GOLD)
    _text(screen, f"BAMBOO  {self.collected_bamboos} / {self.total_bamboos}", (30, 74), 17, MUTED)
    if player.has_ice_magic:
        _text(screen, f"MAGIC  {int(player.mana)} / {int(player.mana_max)}", (30, 96), 17, (166, 214, 216))
    right_x = screen.get_width() - 222
    powers = []
    for attr, timer, label in (("has_glide","glide_time_remaining","GLIDE"),("has_dash","dash_time_remaining","DASH"),("has_bamboo_weapon","weapon_time_remaining","STAFF")):
        seconds = getattr(player, timer, 0)
        if seconds > 0:
            powers.append(f"{label} {math.ceil(seconds)}s")
    _panel(screen, (right_x, 16, 206, 67 + 20 * len(powers)))
    _text(screen, f"LEVEL {level_num:02}", (right_x+16, 28), 21, CREAM)
    _text(screen, f"LIVES  {self.lives}", (right_x+16, 52), 18, GOLD)
    for i, power in enumerate(powers):
        _text(screen, power, (right_x+16, 78+i*20), 17, MUTED)
    if player.combo_count > 1:
        _text(screen, f"{player.combo_count}x COMBO", (screen.get_width()//2, 34), int(24*self.combo_scale), GOLD, True)
    _text(screen, "ESC pause   /   F11 fullscreen", (screen.get_width()-240, screen.get_height()-22), 16, CREAM)
    for floating in self.floating_texts:
        floating.draw(screen, camera)


def title_background(self):
    if self._bg is None:
        self._bg = pygame.transform.smoothscale(_image("forest-background.png"), (960, 540)).convert()
        shade = pygame.Surface((960, 540), pygame.SRCALPHA)
        shade.fill((4, 15, 12, 105))
        self._bg.blit(shade, (0, 0))
    return self._bg


def install():
    import backgrounds
    import sprites
    import ui
    if getattr(sprites, "_painted_art_installed", False):
        return
    sprites._painted_art_installed = True
    sprites.generate_panda_frames = panda_frames
    sprites.generate_platform_tile = platform_tile
    backgrounds.ForestBackground._build = forest_build
    backgrounds.ForestBackground.draw = forest_draw
    ui.TitleScreen._ensure_bg = title_background
    ui.HUD.draw = hud_draw
    ui.get_font = _font
    original_title_draw = ui.TitleScreen.draw

    def title_draw(self, screen):
        if self.gallery_open or self.selected_char is not None:
            original_title_draw(self, screen)
            return
        screen.blit(self._ensure_bg(), (0, 0))
        self._card_rects.clear()
        _text(screen, "BAMBOO FOREST", (480, 92), 64, CREAM, True)
        _text(screen, "The Legend of Pain-da", (480, 139), 26, MUTED, True)
        pose = _panda_cells()[0]
        panda = pygame.transform.smoothscale(pose, (105, 150))
        screen.blit(platform_tile(220, 44), (370, 330))
        screen.blit(panda, panda.get_rect(midbottom=(480, 330)))
        _panel(screen, (326, 386, 308, 44))
        _text(screen, "Press ENTER or tap to begin", (480, 408), 25, CREAM, True)
        self._gallery_button_rect = pygame.Rect(375, 441, 210, 30)
        _text(screen, "Meet the characters", (480, 456), 21, MUTED, True)
        _text(screen, "Arrows / WASD move    SPACE jump    SHIFT dash    E attack", (480, 498), 20, CREAM, True)
        _text(screen, "ESC pause    F11 fullscreen", (480, 523), 17, MUTED, True)
    ui.TitleScreen.draw = title_draw
