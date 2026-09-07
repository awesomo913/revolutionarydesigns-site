# Bamboo Forest art update

The deployed game runs from `web.tar.gz`, using the existing pygbag 0.9.3 loader.
The editable `assets_src` folder is a different revision; do not rebuild the
deployed archive from it just to update artwork.

`visual_skin.py` installs the forest background, panda frames, mossy terrain,
title screen and HUD before the shipped game modules are imported. It retains
the original 36 × 44 player collision box, level layouts, physics and save code.
Other biomes and enemy artwork remain owned by the original game.

The three PNG files in `art/` were generated for the approved September 2026
design. The panda atlas contains a pale matte; the loader removes connected
neutral background pixels while retaining the warm cream fur.

After changing this module or its artwork:

1. Run `python scripts/package-forest-art.py` from the repository root.
2. Run `python scripts/test-forest-art.py` (requires pygame).
3. Open `/game/` in a browser and test loading, starting and pausing.
4. Change the archive version query in `game/index.html` when publishing.

To regenerate the project cover and title/gameplay previews from the same
renderer, pass `--preview-dir PATH` to the test script. Copy the resulting
`bamboo-forest-cover.png` to `assets/` when updating the homepage cover.

The homepage cactus cover (`assets/cactus-cover.png`) is generated decorative
artwork. Botanical field-guide photographs and their existing credits are
separate and unchanged.
