# Bamboo Forest: Woodland Edition

The running game is built from `game/src/`. This directory was recovered from
production's actual archive before the redesign. `assets_src/` is an older,
different development branch and is not a packaging input.

## Build and verify

From the repository root, with Python and pygame 2.6.1 installed:

```sh
python scripts/package-bamboo-journey.py
python scripts/test-bamboo-journey.py --preview-dir /path/to/previews
```

The build compiles all Python files, creates `game/web.tar.gz`, then verifies
every packaged byte against its source. The two older forest-art script names
forward to these scripts. Change the archive query in `game/index.html` when
publishing. CI runs the archive regression suite before deploying the site.

## Art system

The approved `assets/bamboo-sharp.webp` image supplied the art direction.
Built-in Imagegen produced five production atlases in `game/art/`:

- `panda-journey.png`: 12 poses covering movement, abilities, hurt and victory.
- `creatures-journey.png`: 24 creatures, including the guide and boss.
- `relics-journey.png`: 16 pickups, scenery objects and terrain materials.
- `worlds-grove.png`: six environment paintings.
- `worlds-beyond.png`: eight environment paintings.

Exact generation and matte-correction prompts are in `art/journey-prompts.json`.
The sprite atlases use a magenta color key decoded once with pygame. The decoder
also removes edge spill and stray adjacent sprite fragments. Environment panels
are cropped to cover the viewport without distorting their proportions.

`journey_art.py` owns all visible characters, pickups, terrain, area hazards and
backgrounds. Original collision rectangles remain authoritative. The old panda
rotation and flicker effect is removed. `journey_ui.py` supplies title, paged
field guide, abilities, chapter practice, pause, transition, defeat, victory,
HUD and dialogue styling. Native text and controls remain interactive.

Journey keeps the existing 18 chapter layouts and scored progression. Practice
allows any chapter, unlimited retries, timed starting equipment, and ice magic;
it does not submit high scores. Keyboard, mouse and touch can navigate menus.
All combat abilities have touch controls. Portrait phones receive a landscape
view hint. The browser keeps the 16:9 canvas clear of navigation and controls.

## Gameplay repairs

- Starting by clicking the title button now works; Escape never closes the game.
- New journeys reset permanent magic, tutorial flags, score and transient state.
- Dash boots and geysers preserve their supplied world height rather than using
  a temporary drawing-loop coordinate.
- Jumping away from an ascending platform is no longer canceled by its carry.
- Boss damage has a short immunity window, preventing repeated damage from one
  overlapping staff swing. The guide explains its real stun vulnerability.
- Ice removes otherwise invulnerable hazards before awarding their points.
- Gate clocks restart on chapter loads and checkpoint resets.
- Old overlapping tutorial banners become one compact rotating hint.
- Touch emits one bubbling key event per press; cancel/blur releases held keys.
- High scores survive browser reloads using localStorage when available, and
  malformed/unavailable storage cannot stop gameplay.
- BrowserFS 1.4.3 is vendored with its license to replace the broken CDN URL.

## Verification scope

Automated archive checks cover all 18 chapters, all 25 field-guide entries,
all chapter transition screens, mouse and keyboard menu routes, nested pause
navigation, practice resets, jumps, ability cooldowns, item timers, boss damage,
geysers, timed gates, crystal walls, crumbling platforms, portal reactivation,
ascending-platform jumps, storage validation, and sprite alpha decoding.

Chromium browser checks exercise real WASM loading, starting, movement, jumping,
pause/resume and touch input in desktop, portrait and landscape viewports.
Screenshots were reviewed for clipping, sprite identity and proportions. This
is broad regression coverage, not a claim that all 18 chapters received a full
manual speedrun or that every physical mobile device was tested.
