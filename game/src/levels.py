"""Level definitions and construction."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import pygame
import pygame.sprite  # noqa: F401 -- Pygbag lazy submodule

from config import FLOOR_Y, LEVEL_WIDTHS, SCREEN_HEIGHT
from sprites import (
    Bamboo, BambooStaff, Boss, ChaserEnemy, Checkpoint, DashBoots,
    FlyingEnemy, GlideFeather, GrassTuft, HealingItem, MovingPlatform,
    PatrolEnemy, Platform, SafeZone, SlimeEnemy,
)
from biomes import (
    AshBat, BasaltGolem, BiomeMovingPlatform, BiomePlatform, BrineShard,
    CactusScorpion, Crystal, CrumblingPlatform, DustDevil, FalseGlowworm,
    Geyser, IcePlatform, KelpCrab, NPC, ReflectionPhantom,
    StalactiteSpider, SulfurSlime, ThermalUpdraft, WindZone,
    # Levels 14-18 original
    GravityDrone, GravityZone, MagmaLeaper, MushroomSpring, PhaseWraith,
    RisingLava, SporePuffer, TeleportPortal, TidalCrab, TimedGate,
    # L14-L18 rework: new enemies + anti-cheese + dark walls
    HomingSpecter, ForgeHammer, VoidEater, DarkWall,
)


@dataclass
class PlatformDef:
    x: int
    y: int
    w: int
    h: int = 20
    moving: bool = False
    axis: str = "horizontal"
    distance: float = 150.0


@dataclass
class EnemyDef:
    x: int
    y: int
    kind: str
    patrol_width: float = 200.0
    flight_range: float = 200.0


@dataclass
class LevelDef:
    world_width: int
    platforms: list[PlatformDef]
    enemies: list[EnemyDef]
    bamboo_positions: list[tuple[int, int]]
    heal_positions: list[tuple[int, int]]
    goal_x: int
    checkpoint_positions: list[int] = field(default_factory=list)
    has_boss: bool = False
    boss_pos: tuple[int, int] = (0, 0)
    player_start: tuple[int, int] = (100, FLOOR_Y)
    # Biome extensions
    biome: str = "forest"
    geyser_positions: list[tuple[int, int]] = field(default_factory=list)
    crumbling_defs: list[PlatformDef] = field(default_factory=list)
    wind_zones: list[tuple[int, int, int, int, float]] = field(default_factory=list)
    updraft_positions: list[tuple[int, int]] = field(default_factory=list)
    crystal_positions: list[tuple[int, int]] = field(default_factory=list)
    ice_defs: list[PlatformDef] = field(default_factory=list)
    npc_defs: list[tuple[int, int, str, list[str], tuple]] = field(default_factory=list)
    weapon_positions: list[tuple[int, int]] = field(default_factory=list)
    glide_positions: list[tuple[int, int]] = field(default_factory=list)
    dash_positions: list[tuple[int, int]] = field(default_factory=list)
    # List of (start_x, end_x) floor gaps that are lethal pits
    trenches: list[tuple[int, int]] = field(default_factory=list)
    is_dark: bool = False
    is_icy: bool = False
    # Levels 14-18
    mushroom_positions: list[tuple[int, int]] = field(default_factory=list)
    rising_lava: bool = False
    lava_pause_ys: list[int] = field(default_factory=list)
    # (x, y, w, h, group_id "A"|"B")
    timed_gate_defs: list[tuple[int, int, int, int, str]] = field(default_factory=list)
    # (x1, y1, x2, y2, pair_id)
    portal_defs: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    # (x, y, w, h, gravity_type "low"|"high"|"reverse")
    gravity_zone_defs: list[tuple[int, int, int, int, str]] = field(default_factory=list)
    # (x, y, w, h) -- walls that block unless nearby crystal is lit
    dark_wall_defs: list[tuple[int, int, int, int]] = field(default_factory=list)


def _scatter_bamboos(platforms: list[PlatformDef], world_width: int,
                     floor_y: int, target_count: int) -> list[tuple[int, int]]:
    """Generate bamboo positions attached to STATIC platforms only.
    Moving platforms are excluded -- bamboo would float when they move.
    """
    positions: list[tuple[int, int]] = []
    # Exclude moving platforms from placement
    static_plats = [p for p in platforms if not p.moving]
    sorted_plats = sorted(static_plats, key=lambda p: p.x)
    if not sorted_plats:
        # Fallback: scatter on floor
        for i in range(target_count):
            bx = 200 + (world_width - 400) * i // max(1, target_count - 1)
            positions.append((bx, floor_y))
        return positions
    for p in sorted_plats:
        margin = min(25, p.w // 4)
        bx = p.x + random.randint(margin, max(margin, p.w - margin))
        positions.append((bx, p.y))
    for p in sorted_plats:
        if p.w >= 220 and len(positions) < target_count:
            bx = p.x + random.randint(10, p.w // 3)
            positions.append((bx, p.y))
    plat_idx = 0
    while len(positions) < target_count:
        p = sorted_plats[plat_idx % len(sorted_plats)]
        bx = p.x + random.randint(0, p.w)
        positions.append((bx, floor_y))
        plat_idx += 1
    return positions


class LevelState:
    """Instantiated level with all sprite groups."""

    def __init__(self, level_def: LevelDef, level_number: int) -> None:
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.moving_platforms = pygame.sprite.Group()
        self.bamboos = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.heals = pygame.sprite.Group()
        self.checkpoints = pygame.sprite.Group()
        self.decorations = pygame.sprite.Group()
        # Biome groups
        self.geysers = pygame.sprite.Group()
        self.crumbling = pygame.sprite.Group()
        self.wind_zones = pygame.sprite.Group()
        self.updrafts = pygame.sprite.Group()
        self.crystals = pygame.sprite.Group()
        self.toxic_trails = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.weapons = pygame.sprite.Group()
        self.glide_pickups = pygame.sprite.Group()
        self.dash_pickups = pygame.sprite.Group()
        # Levels 14-18 groups
        self.mushrooms = pygame.sprite.Group()
        self.timed_gates = pygame.sprite.Group()
        self.portals = pygame.sprite.Group()
        self.gravity_zones = pygame.sprite.Group()
        self.poison_spores = pygame.sprite.Group()
        self.rising_lava: RisingLava | None = None
        self.dark_walls = pygame.sprite.Group()

        self.goal: SafeZone | None = None
        self.boss: Boss | None = None
        self.world_width = level_def.world_width
        self.level_number = level_number
        self.player_start = level_def.player_start
        self.biome = level_def.biome
        self.is_dark = level_def.is_dark
        self.is_icy = level_def.is_icy

        # Floor segments with gaps for trenches (pits)
        use_biome = self.biome != "forest"
        self.trenches: list[tuple[int, int]] = list(level_def.trenches)
        # Build floor as multiple segments around each trench
        segments: list[tuple[int, int]] = []
        cursor = 0
        for (t_start, t_end) in sorted(self.trenches):
            if t_start > cursor:
                segments.append((cursor, t_start))
            cursor = t_end
        if cursor < level_def.world_width:
            segments.append((cursor, level_def.world_width))
        for (sx, ex) in segments:
            w = ex - sx
            if w <= 0:
                continue
            if use_biome:
                floor = BiomePlatform(sx, FLOOR_Y, w,
                                      SCREEN_HEIGHT - FLOOR_Y, self.biome)
            else:
                floor = Platform(sx, FLOOR_Y, w, SCREEN_HEIGHT - FLOOR_Y)
            self.platforms.add(floor)
            self.all_sprites.add(floor)

        # Standard platforms (biome-themed)
        for pd in level_def.platforms:
            if pd.moving:
                if use_biome:
                    mp = BiomeMovingPlatform(pd.x, pd.y, pd.w, pd.h,
                                             pd.axis, pd.distance, self.biome)
                else:
                    mp = MovingPlatform(pd.x, pd.y, pd.w, pd.h,
                                        pd.axis, pd.distance)
                self.moving_platforms.add(mp)
                self.platforms.add(mp)
                self.all_sprites.add(mp)
            else:
                if use_biome:
                    p = BiomePlatform(pd.x, pd.y, pd.w, pd.h, self.biome)
                else:
                    p = Platform(pd.x, pd.y, pd.w, pd.h)
                self.platforms.add(p)
                self.all_sprites.add(p)

        # Ice platforms
        for ip in level_def.ice_defs:
            p = IcePlatform(ip.x, ip.y, ip.w, ip.h)
            self.platforms.add(p)
            self.all_sprites.add(p)

        # Crumbling platforms (need reference to platforms group)
        for cd in level_def.crumbling_defs:
            cp = CrumblingPlatform(cd.x, cd.y, cd.w, cd.h,
                                   platforms_group=self.platforms)
            self.crumbling.add(cp)
            self.platforms.add(cp)
            self.all_sprites.add(cp)

        # Geysers
        for gx, gy in level_def.geyser_positions:
            g = Geyser(gx, gy)
            self.geysers.add(g)
            self.all_sprites.add(g)

        # Wind zones
        for wx, wy, ww, wh, wdir in level_def.wind_zones:
            wz = WindZone(wx, wy, ww, wh, wdir)
            self.wind_zones.add(wz)
            self.all_sprites.add(wz)

        # Thermal updrafts
        for ux, uy in level_def.updraft_positions:
            tu = ThermalUpdraft(ux, uy)
            self.updrafts.add(tu)
            self.all_sprites.add(tu)

        # Crystals
        for cx, cy in level_def.crystal_positions:
            cr = Crystal(cx, cy)
            self.crystals.add(cr)
            self.all_sprites.add(cr)

        # Bamboo
        for bx, by in level_def.bamboo_positions:
            b = Bamboo(bx, by)
            self.bamboos.add(b)
            self.all_sprites.add(b)

        # Heals
        for hx, hy in level_def.heal_positions:
            h = HealingItem(hx, hy)
            self.heals.add(h)
            self.all_sprites.add(h)

        # Enemies
        _enemy_map = {
            "patrol": lambda ed: PatrolEnemy(ed.x, ed.y, ed.patrol_width),
            "chaser": lambda ed: ChaserEnemy(ed.x, ed.y),
            "flying": lambda ed: FlyingEnemy(ed.x, ed.y, ed.flight_range),
            "slime": lambda ed: SlimeEnemy(ed.x, ed.y, ed.patrol_width),
            "sulfur_slime": lambda ed: SulfurSlime(ed.x, ed.y, ed.patrol_width),
            "ash_bat": lambda ed: AshBat(ed.x, ed.y),
            "kelp_crab": lambda ed: KelpCrab(ed.x, ed.y, ed.patrol_width),
            "basalt_golem": lambda ed: BasaltGolem(ed.x, ed.y),
            "dust_devil": lambda ed: DustDevil(ed.x, ed.y, ed.patrol_width),
            "cactus_scorpion": lambda ed: CactusScorpion(ed.x, ed.y, ed.patrol_width),
            "stalactite_spider": lambda ed: StalactiteSpider(ed.x, ed.y),
            "false_glowworm": lambda ed: FalseGlowworm(ed.x, ed.y),
            "brine_shard": lambda ed: BrineShard(ed.x, ed.y),
            "reflection_phantom": lambda ed: ReflectionPhantom(ed.x, ed.y, ed.patrol_width),
            # Levels 14-18 enemies
            "spore_puffer": lambda ed: SporePuffer(ed.x, ed.y),
            "magma_leaper": lambda ed: MagmaLeaper(ed.x, ed.y),
            "tidal_crab": lambda ed: TidalCrab(ed.x, ed.y, ed.patrol_width),
            "phase_wraith": lambda ed: PhaseWraith(ed.x, ed.y, ed.patrol_width),
            "gravity_drone": lambda ed: GravityDrone(ed.x, ed.y),
            "homing_specter": lambda ed: HomingSpecter(ed.x, ed.y),
            "forge_hammer": lambda ed: ForgeHammer(ed.x, ed.y),
            "void_eater": lambda ed: VoidEater(ed.x, ed.y),
        }
        for ed in level_def.enemies:
            factory = _enemy_map.get(ed.kind)
            if factory:
                e = factory(ed)
                self.enemies.add(e)
                self.all_sprites.add(e)

        # NPCs
        for nx, ny, nname, ndialog, ncol in level_def.npc_defs:
            npc = NPC(nx, ny, nname, ndialog, ncol)
            self.npcs.add(npc)
            self.all_sprites.add(npc)

        # Checkpoints
        for cp_x in level_def.checkpoint_positions:
            cp = Checkpoint(cp_x, FLOOR_Y)
            self.checkpoints.add(cp)
            self.all_sprites.add(cp)

        # Bamboo weapon pickups
        for wx, wy in level_def.weapon_positions:
            ws = BambooStaff(wx, wy)
            self.weapons.add(ws)
            self.all_sprites.add(ws)

        # Glide feather pickups (10-second timed buff)
        for gx, gy in level_def.glide_positions:
            gf = GlideFeather(gx, gy)
            self.glide_pickups.add(gf)
            self.all_sprites.add(gf)

        # Dash boots pickups (30-second timed buff)
        for dx, dy in level_def.dash_positions:
            db = DashBoots(dx, dy)
            self.dash_pickups.add(db)
            self.all_sprites.add(db)

        # Mushroom springs (Level 14)
        for mx, my in level_def.mushroom_positions:
            ms = MushroomSpring(mx, my)
            self.mushrooms.add(ms)
            self.all_sprites.add(ms)

        # Rising lava (Level 15)
        if level_def.rising_lava:
            self.rising_lava = RisingLava(
                level_def.world_width, level_def.lava_pause_ys)
            self.all_sprites.add(self.rising_lava)

        # Timed gates (Level 16)
        for (tgx, tgy, tgw, tgh, group_id) in level_def.timed_gate_defs:
            tg = TimedGate(tgx, tgy, tgw, tgh, group_id, self.platforms)
            tg.image = tg._solid_img if tg.solid else tg._intangible_img
            self.timed_gates.add(tg)
            self.all_sprites.add(tg)

        # Teleport portals (Level 17)
        _portal_bucket: dict[int, list[TeleportPortal]] = {}
        for (x1, y1, x2, y2, pair_id) in level_def.portal_defs:
            p1 = TeleportPortal(x1, y1, pair_id)
            p2 = TeleportPortal(x2, y2, pair_id)
            p1.partner = p2
            p2.partner = p1
            self.portals.add(p1, p2)
            self.all_sprites.add(p1, p2)
            _portal_bucket.setdefault(pair_id, []).extend([p1, p2])

        # Gravity zones (Level 18)
        for (gzx, gzy, gzw, gzh, gtype) in level_def.gravity_zone_defs:
            gz = GravityZone(gzx, gzy, gzw, gzh, gtype)
            self.gravity_zones.add(gz)
            self.all_sprites.add(gz)

        # Dark walls (L7/L9/L13/L17) -- must be built AFTER crystals exist
        for (dwx, dwy, dww, dwh) in level_def.dark_wall_defs:
            dw = DarkWall(dwx, dwy, dww, dwh,
                          self.crystals, self.platforms)
            self.dark_walls.add(dw)
            self.all_sprites.add(dw)

        # Goal
        sz = SafeZone(level_def.goal_x, 200)
        self.goal = sz
        self.all_sprites.add(sz)

        # Boss
        if level_def.has_boss:
            self.boss = Boss(level_def.boss_pos[0], level_def.boss_pos[1])
            self.all_sprites.add(self.boss)

        # Decorative grass -- skip over trench gaps so we don't have
        # floating grass above empty air
        def _in_trench(px: int) -> bool:
            for (ts, te) in self.trenches:
                if ts <= px <= te:
                    return True
            return False
        step = random.randint(45, 65)
        for gx in range(0, level_def.world_width, step):
            if not _in_trench(gx):
                self.decorations.add(GrassTuft(gx, FLOOR_Y))


# ===================================================================
# Level builders -- original 3 + 5 new biomes
# ===================================================================

def _build_level_1() -> LevelDef:
    plats = [
        PlatformDef(400, 420, 240), PlatformDef(900, 380, 200),
        PlatformDef(1400, 410, 260),
        PlatformDef(1900, 370, 220, moving=True, axis="horizontal", distance=100),
        PlatformDef(2450, 400, 240),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[0], platforms=plats,
        enemies=[EnemyDef(440, 410, "patrol", 180), EnemyDef(1440, 400, "patrol", 200),
                 EnemyDef(2480, 390, "slime", 160)],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[0], FLOOR_Y, 11),
        heal_positions=[(950, 380), (2500, 400)],
        goal_x=2800, checkpoint_positions=[1500],
        weapon_positions=[(700, FLOOR_Y)],
        dash_positions=[(400, FLOOR_Y)],  # L1 intro dash item
    )


def _build_level_2() -> LevelDef:
    plats = [
        PlatformDef(400, 420, 220), PlatformDef(900, 370, 180),
        PlatformDef(1400, 410, 240),
        PlatformDef(1900, 360, 200, moving=True, axis="horizontal", distance=110),
        PlatformDef(2450, 400, 200),
        PlatformDef(2950, 350, 200, moving=True, axis="vertical", distance=50),
        PlatformDef(3450, 390, 240), PlatformDef(3950, 380, 220),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[1], platforms=plats, biome="corrupted",
        enemies=[EnemyDef(440, 410, "patrol", 180), EnemyDef(1440, 400, "patrol", 200),
                 EnemyDef(2480, 390, "patrol", 160), EnemyDef(3480, 380, "slime", 180),
                 EnemyDef(950, 360, "chaser"), EnemyDef(2990, 340, "chaser"),
                 EnemyDef(1700, 260, "flying", 200), EnemyDef(3200, 270, "slime", 150)],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[1], FLOOR_Y, 16),
        heal_positions=[(1450, 410), (3490, 390)],
        goal_x=4200, checkpoint_positions=[1700, 3200],
        weapon_positions=[(2000, FLOOR_Y)],
        dash_positions=[(600, FLOOR_Y)],
        trenches=[(1220, 1390), (2600, 2720)],
        npc_defs=[(3900, FLOOR_Y, "Sage",
                   ["The forest is sick... corruption spreads.",
                    "The lair lies ahead. Be ready, Pain-da."],
                   (120, 160, 100))],
    )


def _build_level_3() -> LevelDef:
    plats = [
        PlatformDef(400, 420, 220), PlatformDef(900, 370, 180),
        PlatformDef(1400, 410, 240),
        PlatformDef(1950, 360, 200, moving=True, axis="vertical", distance=50),
        PlatformDef(2500, 400, 220), PlatformDef(3050, 370, 200),
        PlatformDef(3550, 400, 240, moving=True, axis="horizontal", distance=100),
        PlatformDef(4100, 380, 220), PlatformDef(4600, 400, 260),
        PlatformDef(5100, 420, 700, 20),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[2], platforms=plats, biome="lair",
        enemies=[EnemyDef(440, 410, "patrol", 180), EnemyDef(1440, 400, "patrol", 200),
                 EnemyDef(2540, 390, "slime", 180), EnemyDef(3090, 360, "patrol", 160),
                 EnemyDef(4140, 370, "patrol", 160), EnemyDef(950, 360, "chaser"),
                 EnemyDef(2000, 350, "chaser"), EnemyDef(3580, 390, "chaser"),
                 EnemyDef(1200, 260, "flying", 200), EnemyDef(2800, 250, "flying", 200),
                 EnemyDef(4300, 260, "flying", 180), EnemyDef(3300, 390, "slime", 160)],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[2], FLOOR_Y, 20),
        heal_positions=[(1450, 410), (3080, 370), (4900, FLOOR_Y)],
        goal_x=5850, checkpoint_positions=[1800, 3500, 4900],
        weapon_positions=[(2500, FLOOR_Y)],
        dash_positions=[(700, FLOOR_Y), (3500, FLOOR_Y)],
        trenches=[(1330, 1470), (2920, 3050), (4380, 4520)],
        has_boss=True, boss_pos=(5500, FLOOR_Y),
        npc_defs=[(4950, FLOOR_Y, "Elder",
                   ["The mutant waits beyond this gate.",
                    "You alone can end this, Pain-da!"],
                   (180, 140, 90))],
    )


# ---- NEW BIOMES ----

def _build_level_4() -> LevelDef:
    """The Caldera -- volcanic geysers and toxic slimes."""
    plats = [
        PlatformDef(400, 410, 220), PlatformDef(1000, 360, 200),
        PlatformDef(1600, 400, 240), PlatformDef(2200, 340, 200),
        PlatformDef(2800, 390, 220), PlatformDef(3400, 360, 200),
        PlatformDef(4000, 400, 240), PlatformDef(4600, 380, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[3], platforms=plats, biome="volcanic",
        enemies=[
            EnemyDef(440, 400, "sulfur_slime", 180),
            EnemyDef(1640, 390, "sulfur_slime", 200),
            EnemyDef(2840, 380, "sulfur_slime", 160),
            EnemyDef(800, 280, "ash_bat"), EnemyDef(2500, 260, "ash_bat"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[3], FLOOR_Y, 14),
        heal_positions=[(1020, 360), (3420, 360), (4650, 380)],
        goal_x=5200, checkpoint_positions=[2000, 3800],
        weapon_positions=[(2200, FLOOR_Y)],
        geyser_positions=[
            (700, FLOOR_Y), (1350, FLOOR_Y), (1950, FLOOR_Y),
            (2600, FLOOR_Y), (3200, FLOOR_Y),
        ],
        npc_defs=[(4200, FLOOR_Y, "Cinder",
                   ["The geysers erupt every 3 seconds.",
                    "Ride them to reach high platforms!"],
                   (180, 100, 50))],
    )


def _build_level_5() -> LevelDef:
    """Basalt Columns -- crumbling platforms and armored crabs."""
    plats = [
        PlatformDef(400, 420, 200), PlatformDef(950, 380, 180),
        PlatformDef(1500, 410, 220), PlatformDef(2100, 370, 200),
        PlatformDef(2650, 400, 220), PlatformDef(3200, 380, 200),
        PlatformDef(3750, 410, 240),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[4], platforms=plats, biome="basalt",
        enemies=[
            EnemyDef(440, 410, "kelp_crab", 160),
            EnemyDef(1540, 400, "kelp_crab", 180),
            EnemyDef(2690, 390, "kelp_crab", 140),
            EnemyDef(1200, 380, "basalt_golem"),
            EnemyDef(2400, 370, "basalt_golem"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[4], FLOOR_Y, 14),
        heal_positions=[(980, 380), (2680, 400)],
        goal_x=4700, checkpoint_positions=[1800, 3300],
        weapon_positions=[(2000, FLOOR_Y)],
        dash_positions=[(500, FLOOR_Y)],
        crumbling_defs=[
            PlatformDef(700, 400, 120), PlatformDef(1250, 350, 100),
            PlatformDef(1850, 380, 120), PlatformDef(2400, 340, 100),
            PlatformDef(3000, 370, 120),
        ],
        npc_defs=[(3500, FLOOR_Y, "Finn",
                   ["These columns are ancient basalt.",
                    "Some crumble... be quick on your feet!"],
                   (40, 40, 40))],
    )


def _build_level_6() -> LevelDef:
    """The Arid Rift -- wind and scorpion projectiles."""
    plats = [
        PlatformDef(400, 420, 220), PlatformDef(950, 380, 180),
        PlatformDef(1500, 410, 240), PlatformDef(2050, 360, 200),
        PlatformDef(2600, 400, 220), PlatformDef(3150, 370, 200),
        PlatformDef(3700, 400, 240), PlatformDef(4250, 380, 200),
        PlatformDef(4800, 410, 240), PlatformDef(5350, 390, 220),
        PlatformDef(5900, 400, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[5], platforms=plats, biome="desert",
        enemies=[
            EnemyDef(1000, FLOOR_Y - 50, "dust_devil", 300),
            EnemyDef(3200, FLOOR_Y - 50, "dust_devil", 280),
            EnemyDef(550, 410, "cactus_scorpion", 120),
            EnemyDef(2100, 350, "cactus_scorpion", 100),
            EnemyDef(4300, 370, "cactus_scorpion", 120),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[5], FLOOR_Y, 18),
        heal_positions=[(1520, 410), (3730, 400), (5370, 390)],
        goal_x=6200, checkpoint_positions=[2200, 4200],
        wind_zones=[
            (800, 200, 200, 300, 1.0),
            (2300, 200, 200, 300, -1.0),
            (3900, 200, 200, 300, 1.0),
            (5100, 200, 200, 300, -1.0),
        ],
        updraft_positions=[(1300, FLOOR_Y), (2900, FLOOR_Y), (4600, FLOOR_Y)],
        npc_defs=[(5500, FLOOR_Y, "Silas",
                   ["Watch the wind patterns...",
                    "Use updrafts to reach high ground."],
                   (180, 160, 80))],
    )


def _build_level_7() -> LevelDef:
    """Karst Caves -- darkness with crystal lights."""
    plats = [
        PlatformDef(400, 420, 220), PlatformDef(900, 380, 180),
        PlatformDef(1400, 410, 240), PlatformDef(1900, 360, 200),
        PlatformDef(2450, 400, 220), PlatformDef(2950, 370, 200),
        PlatformDef(3500, 400, 240), PlatformDef(4050, 380, 200),
        PlatformDef(4600, 410, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[6], platforms=plats,
        biome="cave", is_dark=True,
        enemies=[
            EnemyDef(600, 50, "stalactite_spider"),
            EnemyDef(1200, 60, "stalactite_spider"),
            EnemyDef(2200, 50, "stalactite_spider"),
            EnemyDef(3300, 60, "stalactite_spider"),
            EnemyDef(800, 350, "false_glowworm"),
            EnemyDef(1700, 320, "false_glowworm"),
            EnemyDef(2800, 340, "false_glowworm"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[6], FLOOR_Y, 16),
        heal_positions=[(1420, 410), (2970, 370), (4080, 380)],
        goal_x=5200, checkpoint_positions=[1500, 2800, 4100],
        crystal_positions=[
            (300, FLOOR_Y), (750, FLOOR_Y), (1250, FLOOR_Y),
            (1800, FLOOR_Y), (2500, FLOOR_Y), (3200, FLOOR_Y), (3900, FLOOR_Y),
        ],
        dark_wall_defs=[(1100, 340, 40, 130), (2900, 340, 40, 130)],
        npc_defs=[(4300, FLOOR_Y, "Nyx",
                   ["I can hear the echoes of danger...",
                    "Strike the crystals to see!"],
                   (100, 60, 120))],
    )


def _build_level_8() -> LevelDef:
    """Salt Flats -- ice physics and phantom enemies."""
    ice = [
        PlatformDef(400, 420, 240), PlatformDef(950, 380, 200),
        PlatformDef(1500, 410, 260), PlatformDef(2100, 360, 220),
        PlatformDef(2700, 400, 240), PlatformDef(3300, 370, 200),
        PlatformDef(3900, 400, 260), PlatformDef(4500, 380, 220),
        PlatformDef(5100, 410, 260), PlatformDef(5700, 390, 240),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[7], platforms=[], biome="salt",
        is_icy=True, ice_defs=ice,
        enemies=[
            EnemyDef(600, FLOOR_Y, "brine_shard"),
            EnemyDef(1800, FLOOR_Y, "brine_shard"),
            EnemyDef(3500, FLOOR_Y, "brine_shard"),
            EnemyDef(1200, 410, "reflection_phantom", 200),
            EnemyDef(2900, 400, "reflection_phantom", 200),
        ],
        bamboo_positions=_scatter_bamboos(ice, LEVEL_WIDTHS[7], FLOOR_Y, 18),
        heal_positions=[(970, 380), (3320, 370), (5120, 410)],
        goal_x=6700, checkpoint_positions=[2400, 4500, 6000],
        npc_defs=[(6200, FLOOR_Y, "Mirage",
                   ["Nothing is what it seems here...",
                    "Watch for phantoms in the reflection."],
                   (200, 140, 80))],
    )


def _build_level_9() -> LevelDef:
    """Abyssal Trench -- underwater feel. Uses cave biome dark + crystals."""
    plats = [
        PlatformDef(400, 420, 200),
        PlatformDef(900, 380, 220),
        PlatformDef(1400, 350, 180),
        PlatformDef(1900, 400, 200, moving=True, axis="vertical", distance=70),
        PlatformDef(2450, 370, 220),
        PlatformDef(3000, 400, 200),
        PlatformDef(3550, 360, 220, moving=True, axis="horizontal", distance=120),
        PlatformDef(4100, 390, 240),
        PlatformDef(4700, 400, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[8], platforms=plats, biome="cave", is_dark=True,
        enemies=[
            EnemyDef(450, 410, "flying", 200),
            EnemyDef(1450, 340, "flying", 200),
            EnemyDef(2500, 360, "chaser"),
            EnemyDef(3050, 390, "chaser"),
            EnemyDef(3600, 350, "slime", 150),
            EnemyDef(4150, 380, "slime", 150),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[8], FLOOR_Y, 14),
        heal_positions=[(940, 380), (3020, 400), (4730, 400)],
        goal_x=5600, checkpoint_positions=[1700, 3400],
        weapon_positions=[(1200, FLOOR_Y)],
        crystal_positions=[(600, FLOOR_Y), (1700, FLOOR_Y), (2800, FLOOR_Y),
                          (3900, FLOOR_Y), (5000, FLOOR_Y)],
        trenches=[(1720, 1860), (3400, 3520)],
        npc_defs=[(5200, FLOOR_Y, "Luminesce",
                   ["The abyss remembers the light.",
                    "Strike crystals to see your path."],
                   (100, 200, 240))],
    )


def _build_level_10() -> LevelDef:
    """Orogeny Peak -- vertical scaling. Many stacked platforms."""
    plats = [
        PlatformDef(400, 430, 220),
        PlatformDef(750, 370, 180),
        PlatformDef(1100, 310, 160),
        PlatformDef(1450, 380, 200, moving=True, axis="horizontal", distance=120),
        PlatformDef(1850, 330, 160),
        PlatformDef(2200, 400, 200),
        PlatformDef(2600, 350, 180, moving=True, axis="vertical", distance=60),
        PlatformDef(3000, 300, 160),
        PlatformDef(3400, 380, 220),
        PlatformDef(3850, 340, 200),
        PlatformDef(4300, 400, 220),
        PlatformDef(4800, 360, 240),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[9], platforms=plats, biome="basalt",
        enemies=[
            EnemyDef(450, 420, "patrol", 180),
            EnemyDef(1500, 370, "patrol", 180),
            EnemyDef(2250, 390, "patrol", 160),
            EnemyDef(3450, 370, "slime", 200),
            EnemyDef(4350, 390, "slime", 180),
            EnemyDef(1150, 220, "flying", 180),
            EnemyDef(3050, 210, "flying", 200),
            EnemyDef(800, 360, "chaser"),
            EnemyDef(3050, 290, "chaser"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[9], FLOOR_Y, 18),
        heal_positions=[(1470, 380), (3420, 380), (4820, 360)],
        goal_x=5300, checkpoint_positions=[1500, 3200, 4500],
        weapon_positions=[(1000, FLOOR_Y)],
        trenches=[(680, 760), (1840, 1950), (3380, 3490)],
        npc_defs=[(5100, FLOOR_Y, "Kora",
                   ["The mountain tests your endurance.",
                    "Dash past the avalanche zones!"],
                   (255, 255, 255))],
    )


def _build_level_11() -> LevelDef:
    """Hypersaline Rift -- wide gaps needing dash/glide."""
    plats = [
        PlatformDef(400, 410, 200),
        PlatformDef(900, 380, 180),
        PlatformDef(1500, 360, 180),   # gap needs glide/dash
        PlatformDef(2100, 400, 220),
        PlatformDef(2700, 370, 200),
        PlatformDef(3300, 390, 220),
        PlatformDef(3900, 360, 200),
        PlatformDef(4500, 400, 240),
        PlatformDef(5100, 380, 220),
        PlatformDef(5700, 400, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[10], platforms=plats, biome="salt", is_icy=True,
        enemies=[
            EnemyDef(450, 400, "reflection_phantom", 180),
            EnemyDef(2150, 390, "reflection_phantom", 200),
            EnemyDef(3350, 380, "brine_shard"),
            EnemyDef(4550, 390, "brine_shard"),
            EnemyDef(1000, 360, "chaser"),
            EnemyDef(3900, 340, "chaser"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[10], FLOOR_Y, 16),
        heal_positions=[(950, 380), (3350, 390), (5130, 380)],
        goal_x=5900, checkpoint_positions=[2100, 3900],
        weapon_positions=[(600, FLOOR_Y)],
        trenches=[(1200, 1440), (2400, 2600), (4200, 4400)],
        npc_defs=[(5600, FLOOR_Y, "Saltbeard",
                   ["The salt ocean looks calm...",
                    "Phantoms strike from reflection!"],
                   (200, 200, 230))],
    )


def _build_level_12() -> LevelDef:
    """Tabletop Canopy -- dense small platforms (jungle vine feel)."""
    plats = [
        PlatformDef(350, 420, 140),
        PlatformDef(600, 370, 120),
        PlatformDef(830, 410, 140),
        PlatformDef(1050, 350, 120, moving=True, axis="horizontal", distance=80),
        PlatformDef(1300, 390, 140),
        PlatformDef(1550, 330, 120),
        PlatformDef(1800, 380, 140),
        PlatformDef(2100, 350, 140, moving=True, axis="vertical", distance=50),
        PlatformDef(2400, 400, 160),
        PlatformDef(2750, 350, 140),
        PlatformDef(3100, 390, 160),
        PlatformDef(3500, 360, 140, moving=True, axis="horizontal", distance=90),
        PlatformDef(3900, 400, 180),
        PlatformDef(4300, 370, 160),
        PlatformDef(4700, 400, 200),
        PlatformDef(5200, 380, 240),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[11], platforms=plats, biome="forest",
        enemies=[
            EnemyDef(400, 410, "patrol", 120),
            EnemyDef(1350, 380, "patrol", 120),
            EnemyDef(2450, 390, "patrol", 140),
            EnemyDef(3550, 350, "slime", 120),
            EnemyDef(4350, 360, "slime", 120),
            EnemyDef(880, 300, "flying", 160),
            EnemyDef(2500, 260, "flying", 180),
            EnemyDef(4000, 260, "flying", 180),
            EnemyDef(1900, 370, "chaser"),
            EnemyDef(3150, 380, "chaser"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[11], FLOOR_Y, 22),
        heal_positions=[(1080, 350), (3130, 390), (5230, 380)],
        goal_x=6100, checkpoint_positions=[1800, 3400, 4900],
        weapon_positions=[(500, FLOOR_Y)],
        glide_positions=[(200, FLOOR_Y), (2500, FLOOR_Y)],
        dash_positions=[(1200, FLOOR_Y), (4000, FLOOR_Y)],
        trenches=[(490, 580), (970, 1040), (1460, 1540), (2020, 2090),
                  (2920, 3090), (4180, 4290)],
        npc_defs=[(5900, FLOOR_Y, "Capy",
                   ["Rest your paws, traveler.",
                    "This is the longest leg."],
                   (180, 140, 100))],
    )


def _build_level_13() -> LevelDef:
    """Crystal Geode -- final level. Dark, crystals, boss + many flying."""
    plats = [
        PlatformDef(400, 420, 220),
        PlatformDef(900, 370, 180),
        PlatformDef(1400, 410, 220),
        PlatformDef(1950, 360, 200, moving=True, axis="vertical", distance=50),
        PlatformDef(2500, 400, 220),
        PlatformDef(3050, 370, 200),
        PlatformDef(3550, 400, 240, moving=True, axis="horizontal", distance=100),
        PlatformDef(4100, 380, 220),
        PlatformDef(4600, 400, 260),
        PlatformDef(5100, 420, 900, 20),  # boss arena
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[12], platforms=plats, biome="cave", is_dark=True,
        enemies=[
            EnemyDef(450, 410, "patrol", 180),
            EnemyDef(1450, 400, "slime", 180),
            EnemyDef(2550, 390, "patrol", 180),
            EnemyDef(1000, 360, "chaser"),
            EnemyDef(2000, 350, "chaser"),
            EnemyDef(3600, 390, "chaser"),
            EnemyDef(4150, 370, "chaser"),
            EnemyDef(700, 260, "flying", 200),
            EnemyDef(2200, 250, "flying", 200),
            EnemyDef(3700, 260, "flying", 200),
            EnemyDef(4500, 260, "flying", 200),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[12], FLOOR_Y, 22),
        heal_positions=[(940, 370), (3080, 370), (4130, 380), (4800, FLOOR_Y)],
        goal_x=6700, checkpoint_positions=[1800, 3500, 4900, 5800],
        weapon_positions=[(500, FLOOR_Y), (3200, FLOOR_Y)],
        dash_positions=[(2500, FLOOR_Y)],
        crystal_positions=[(300, FLOOR_Y), (1200, FLOOR_Y), (2200, FLOOR_Y),
                          (3200, FLOOR_Y), (4200, FLOOR_Y), (5400, FLOOR_Y)],
        dark_wall_defs=[(1500, 340, 40, 130), (3700, 340, 40, 130)],
        has_boss=True,
        boss_pos=(5500, FLOOR_Y),
        npc_defs=[(6500, FLOOR_Y, "Core Guardian",
                   ["The corruption ends here.",
                    "Pain-da -- make us proud."],
                   (255, 220, 120))],
    )


def _build_level_14() -> LevelDef:
    """Fungal Hollows -- bouncy mushroom springs + spore puffers."""
    plats = [
        PlatformDef(400, 420, 220),
        PlatformDef(900, 380, 180),
        PlatformDef(1450, 410, 220),
        PlatformDef(2000, 370, 200, moving=True, axis="horizontal", distance=90),
        PlatformDef(2550, 400, 200),
        # High platforms reachable ONLY via mushroom bounce:
        PlatformDef(3100, 280, 160),
        PlatformDef(3600, 290, 160),
        PlatformDef(4100, 400, 220),
        PlatformDef(4600, 360, 200, moving=True, axis="vertical", distance=50),
        PlatformDef(5200, 400, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[13], platforms=plats, biome="mushroom",
        enemies=[
            EnemyDef(440, 410, "patrol", 180),
            EnemyDef(1490, 400, "slime", 180),
            EnemyDef(800, 360, "spore_puffer"),
            EnemyDef(2600, 390, "spore_puffer"),
            EnemyDef(4150, 390, "spore_puffer"),
            EnemyDef(4700, 360, "chaser"),
            EnemyDef(1500, 260, "flying", 180),
            EnemyDef(3300, 260, "flying", 180),
            EnemyDef(2600, 150, "homing_specter"),
            EnemyDef(4500, 150, "homing_specter"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[13], FLOOR_Y, 16),
        heal_positions=[(950, 380), (3120, 280), (5230, 400)],
        goal_x=5800, checkpoint_positions=[2000, 4200],
        weapon_positions=[(1200, FLOOR_Y)],
        mushroom_positions=[
            (2800, FLOOR_Y), (3350, FLOOR_Y), (3850, FLOOR_Y),
            (4400, FLOOR_Y), (5000, FLOOR_Y),
        ],
        crumbling_defs=[
            PlatformDef(1750, 380, 120),
            PlatformDef(3350, 280, 100),  # crumbles after bounce
            PlatformDef(4900, 370, 120),
        ],
        crystal_positions=[(700, FLOOR_Y), (3900, FLOOR_Y)],
        trenches=[(1250, 1400), (3700, 3850)],
        glide_positions=[(5400, 300)],
        npc_defs=[(5400, FLOOR_Y, "Myco",
                   ["Land on the mushroom caps to bounce super high!",
                    "Watch out -- specters track you in the air!"],
                   (180, 120, 200))],
    )


def _build_level_15() -> LevelDef:
    """The Crucible -- rising lava, constant upward pressure."""
    plats = [
        # Ascending platforms, left-to-right climb
        PlatformDef(400, 430, 240),
        PlatformDef(950, 380, 200),
        PlatformDef(1500, 410, 200),
        PlatformDef(2050, 360, 180, moving=True, axis="vertical", distance=50),
        PlatformDef(2550, 330, 160),
        PlatformDef(3050, 370, 180),
        PlatformDef(3550, 300, 160),
        PlatformDef(4050, 340, 180, moving=True, axis="vertical", distance=60),
        PlatformDef(4550, 290, 160),
        PlatformDef(5050, 330, 180),
        PlatformDef(5550, 280, 160),
        PlatformDef(6050, 320, 200),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[14], platforms=plats, biome="forge",
        enemies=[
            # Industrial forge denizens -- NOT volcanic reuse
            EnemyDef(800, 430, "forge_hammer"),
            EnemyDef(1700, 410, "forge_hammer"),
            EnemyDef(2700, 330, "forge_hammer"),
            EnemyDef(3700, 300, "forge_hammer"),
            EnemyDef(4700, 290, "forge_hammer"),
            EnemyDef(5500, 280, "forge_hammer"),
            # Aerial trackers
            EnemyDef(2200, 200, "homing_specter"),
            EnemyDef(4200, 200, "homing_specter"),
            EnemyDef(5600, 200, "homing_specter"),
            # Ground patrol
            EnemyDef(500, 420, "patrol", 180),
            EnemyDef(3100, 360, "magma_leaper"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[14], FLOOR_Y, 16),
        heal_positions=[(1520, 410), (3570, 300), (5570, 280)],
        goal_x=6400, checkpoint_positions=[2200, 4300],
        rising_lava=True,
        lava_pause_ys=[460, 410, 360, 310],
        geyser_positions=[(800, FLOOR_Y), (2800, 400), (4300, 360)],
        dash_positions=[(400, 420)],
        npc_defs=[(6200, 310, "Vulcan",
                   ["The forge hammers crush what lava doesn't burn.",
                    "Dodge the slamming anvils and keep climbing!"],
                   (220, 100, 40))],
    )


def _build_level_16() -> LevelDef:
    """Tidal Locks -- timed gates cycle every 3 seconds."""
    plats = [
        PlatformDef(400, 420, 220),
        PlatformDef(950, 380, 180),
        PlatformDef(2000, 400, 200),  # after first gate section
        PlatformDef(2500, 370, 180),
        PlatformDef(3700, 400, 200),  # after second gate section
        PlatformDef(4200, 380, 180),
        PlatformDef(4700, 410, 220),
        PlatformDef(5200, 380, 240),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[15], platforms=plats, biome="tidal",
        enemies=[
            EnemyDef(440, 410, "tidal_crab", 150),
            EnemyDef(2040, 390, "tidal_crab", 140),
            EnemyDef(3740, 390, "tidal_crab", 150),
            EnemyDef(4740, 400, "patrol", 160),
            EnemyDef(1100, 260, "flying", 200),
            EnemyDef(3000, 260, "flying", 200),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[15], FLOOR_Y, 14),
        heal_positions=[(970, 380), (4220, 380), (5230, 380)],
        goal_x=5800, checkpoint_positions=[2000, 4000],
        weapon_positions=[(1000, FLOOR_Y)],
        # Alternating A/B gates bridging two big trenches
        # First section: 3 gates bridging a gap 1100-1920
        timed_gate_defs=[
            (1200, 400, 120, 20, "A"),
            (1400, 380, 120, 20, "B"),
            (1600, 400, 120, 20, "A"),
            (1800, 380, 120, 20, "B"),
            # Second section: bridge a gap 2800-3600
            (2900, 400, 120, 20, "B"),
            (3100, 380, 120, 20, "A"),
            (3300, 400, 120, 20, "B"),
            (3500, 380, 120, 20, "A"),
        ],
        crumbling_defs=[
            PlatformDef(1100, 420, 80),
            PlatformDef(2700, 400, 100),
        ],
        trenches=[(1130, 1920), (2800, 3600), (4100, 4190)],
        npc_defs=[(5600, FLOOR_Y, "Chronos",
                   ["The ancient locks run on a cycle.",
                    "Watch the glow -- step when it's bright!"],
                   (100, 160, 200))],
    )


def _build_level_17() -> LevelDef:
    """Phantom Corridor -- teleport portals + dark caves."""
    plats = [
        PlatformDef(400, 420, 220),
        PlatformDef(900, 380, 180),
        PlatformDef(1400, 410, 220),
        PlatformDef(1900, 360, 180, moving=True, axis="horizontal", distance=100),
        PlatformDef(2450, 400, 200),
        PlatformDef(2950, 370, 180),
        PlatformDef(3500, 410, 220),
        PlatformDef(4050, 380, 200),
        PlatformDef(4600, 400, 220),
        PlatformDef(5100, 410, 260),
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[16], platforms=plats, biome="void", is_dark=True,
        enemies=[
            EnemyDef(440, 410, "phase_wraith", 140),
            EnemyDef(1450, 400, "phase_wraith", 150),
            EnemyDef(3550, 400, "phase_wraith", 150),
            # Void-specific: hungry mouths you can't stomp
            EnemyDef(1200, 320, "void_eater"),
            EnemyDef(2700, 300, "void_eater"),
            EnemyDef(4500, 320, "void_eater"),
            # Tracking specters
            EnemyDef(2000, 200, "homing_specter"),
            EnemyDef(4000, 200, "homing_specter"),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[16], FLOOR_Y, 15),
        heal_positions=[(950, 380), (3550, 410), (5130, 410)],
        goal_x=5400, checkpoint_positions=[2000, 4000],
        weapon_positions=[(700, FLOOR_Y)],
        crystal_positions=[
            (300, FLOOR_Y), (1700, FLOOR_Y), (3200, FLOOR_Y),
            (4400, FLOOR_Y), (5000, FLOOR_Y),
        ],
        # Portal pairs: x1, y1, x2, y2, pair_id
        portal_defs=[
            (700, FLOOR_Y, 2200, FLOOR_Y, 0),
            (1500, FLOOR_Y, 3800, FLOOR_Y, 1),
            (2800, FLOOR_Y, 4200, FLOOR_Y, 2),
            (1100, 360, 4700, 380, 3),
        ],
        # Dark walls force crystal-strikes before passage
        dark_wall_defs=[
            (1300, 340, 40, 120),
            (3400, 340, 40, 120),
        ],
        npc_defs=[(5200, FLOOR_Y, "Rift",
                   ["The void hungers. Stay moving.",
                    "Strike crystals to melt the walls ahead!"],
                   (0, 180, 220))],
    )


def _build_level_18() -> LevelDef:
    """The Gravity Engine -- altered gravity zones + final boss."""
    plats = [
        PlatformDef(400, 420, 220),
        PlatformDef(900, 380, 180),
        PlatformDef(1400, 410, 220),
        PlatformDef(1900, 370, 180, moving=True, axis="horizontal", distance=100),
        # Inside low-gravity zone ahead (wide gap; floating crossing)
        PlatformDef(2700, 390, 180),
        PlatformDef(3200, 370, 180),
        PlatformDef(3700, 400, 200),
        # Reverse gravity tunnel ceilings (high up so player falls "up" onto them)
        PlatformDef(4200, 180, 200, 20),
        PlatformDef(4500, 180, 200, 20),
        PlatformDef(4800, 180, 200, 20),
        PlatformDef(5200, 400, 220),
        # High gravity approach
        PlatformDef(5700, 380, 200),
        PlatformDef(6200, 400, 200),
        PlatformDef(6700, 420, 700, 20),  # boss arena
    ]
    return LevelDef(
        world_width=LEVEL_WIDTHS[17], platforms=plats, biome="gravity",
        enemies=[
            EnemyDef(450, 410, "patrol", 180),
            EnemyDef(1450, 400, "slime", 160),
            EnemyDef(2700, 360, "gravity_drone"),
            EnemyDef(3500, 340, "gravity_drone"),
            EnemyDef(5700, 370, "gravity_drone"),
            # Tracking specters around gravity zones
            EnemyDef(2500, 250, "homing_specter"),
            EnemyDef(4500, 250, "homing_specter"),
            EnemyDef(6000, 250, "homing_specter"),
            EnemyDef(950, 360, "chaser"),
            EnemyDef(3200, 350, "chaser"),
            EnemyDef(5700, 380, "chaser"),
            EnemyDef(1000, 260, "flying", 200),
            EnemyDef(3500, 260, "flying", 200),
            EnemyDef(6100, 260, "flying", 200),
        ],
        bamboo_positions=_scatter_bamboos(plats, LEVEL_WIDTHS[17], FLOOR_Y, 22),
        heal_positions=[(940, 380), (3220, 370), (5220, 400), (6400, FLOOR_Y)],
        goal_x=7300, checkpoint_positions=[2000, 4000, 5500, 6700],
        weapon_positions=[(500, FLOOR_Y), (5300, FLOOR_Y)],
        crystal_positions=[(300, FLOOR_Y), (2400, 450), (5000, 450), (6600, FLOOR_Y)],
        # Gravity zones: (x, y, w, h, type)
        gravity_zone_defs=[
            (2300, 200, 500, 240, "low"),      # floating low-grav chasm
            (4100, 200, 900, 250, "reverse"),  # reverse ceiling tunnel
            (5600, 300, 700, 200, "high"),     # high gravity approach
        ],
        crumbling_defs=[
            PlatformDef(3900, 200, 150),  # in reverse gravity zone
            PlatformDef(4400, 200, 150),
        ],
        wind_zones=[(2600, 250, 150, 180, 1.0)],
        geyser_positions=[(6450, FLOOR_Y)],
        has_boss=True, boss_pos=(7000, FLOOR_Y),
        npc_defs=[(7250, FLOOR_Y, "The Architect",
                   ["You have mastered gravity itself.",
                    "The bamboo forest is safe again, Pain-da."],
                   (200, 180, 255))],
    )


_BUILDERS = [
    _build_level_1, _build_level_2, _build_level_3,
    _build_level_4, _build_level_5, _build_level_6,
    _build_level_7, _build_level_8,
    _build_level_9, _build_level_10, _build_level_11,
    _build_level_12, _build_level_13,
    _build_level_14, _build_level_15, _build_level_16,
    _build_level_17, _build_level_18,
]


def _verify_jump_arc(level_def: LevelDef) -> None:
    """Check that every platform is reachable within the player's jump arc.

    Player jump physics:
      PLAYER_JUMP = -660 px/s, GRAVITY = 1800 px/s^2
      Peak height = 660^2 / (2*1800) = 121 px per jump
      Double jump effective height = ~242 px
      Horizontal reach during jump = ~264 px
    """
    from config import PLAYER_JUMP, GRAVITY
    max_height_single = (PLAYER_JUMP ** 2) / (2.0 * GRAVITY)  # 121
    max_height_double = max_height_single * 2.0               # 242
    # Safety margin: platforms must be within 200px of next reachable surface
    # measured from the floor or another platform.
    all_y = [FLOOR_Y] + [p.y for p in level_def.platforms]
    # For each platform, find the closest lower surface (floor or lower platform)
    for p in level_def.platforms:
        # Lower surfaces with y greater than p.y (lower on screen)
        lower = [y for y in all_y if y > p.y]
        if not lower:
            continue
        closest = min(lower, key=lambda y: y - p.y)
        gap = closest - p.y
        # A platform can always be reached from the floor (floor is continuous)
        # with a double jump if the gap is <= 242 + 10 safety margin
        if gap > max_height_double + 10:
            raise ValueError(
                f"Platform at ({p.x}, {p.y}) unreachable: "
                f"vertical gap {gap}px > max double jump {max_height_double:.0f}px")


def build_level_state(level_number: int) -> LevelState:
    level_def = _BUILDERS[level_number]()
    _verify_jump_arc(level_def)  # raise ValueError if unreachable platforms
    return LevelState(level_def, level_number)
