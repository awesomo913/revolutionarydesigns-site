"""Smoke-test the shipped game with pygame; optionally render its new art preview.

Run: python scripts/test-forest-art.py [--preview-dir PATH]
Requires pygame. Uses an isolated temporary save directory.
"""
from pathlib import Path
import argparse
import os
import sys
import tarfile
import tempfile

os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--preview-dir", type=Path)
args = parser.parse_args()
out = args.preview_dir.resolve() if args.preview_dir else None
if out:
    out.mkdir(parents=True, exist_ok=True)

with tempfile.TemporaryDirectory(prefix="forest-art-test-") as temp:
    target = Path(temp)
    with tarfile.open(root / "game/web.tar.gz") as archive:
        for member in archive.getmembers():
            destination = (target / member.name).resolve()
            if not destination.is_relative_to(target) or member.issym() or member.islnk():
                raise ValueError("Unsafe archive member: " + member.name)
            if member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.extractfile(member).read())
    assets = target / "assets"
    previous = Path.cwd()
    os.chdir(assets)
    sys.path.insert(0, str(assets))
    try:
        import pygame
        pygame.init()
        pygame.display.set_mode((960, 540))
        import visual_skin
        visual_skin.install()
        visual_skin.install()  # installation is idempotent
        from game import Game
        from config import PLAYER_SIZE, ST_PAUSED
        game = Game()
        game._draw()
        if out:
            pygame.image.save(game.screen, str(out / "bamboo-title-updated.png"))
            # Project artwork composed from the same game renderer and assets.
            cover = pygame.Surface((640, 540))
            cover.blit(pygame.transform.smoothscale(visual_skin._image("forest-background.png"), (960,540)), (-120,0))
            cover.blit(visual_skin.platform_tile(640, 108), (0, 432))
            pose = visual_skin._panda_cells()[0]
            panda = pygame.transform.smoothscale(pose, (96,153))
            cover.blit(panda, panda.get_rect(midbottom=(360,432)))
            pygame.image.save(cover, str(out / "bamboo-forest-cover.png"))
        assert game.title_screen.handle_click(game.title_screen._gallery_button_rect.center)
        game._draw()
        game.title_screen.handle_key(pygame.K_ESCAPE)
        game._start_game()
        for _ in range(90):
            game._update(1/60)
            game._draw()
        assert game.player.rect.size == PLAYER_SIZE == (36, 44)
        if out:
            pygame.image.save(game.screen, str(out / "bamboo-gameplay-updated.png"))
        for level in range(18):
            game._load_level(level)
            game._update(1/60)
            game._draw()
        game._on_key_down(pygame.K_ESCAPE)
        assert game.state == ST_PAUSED
        game._draw()
        game._on_key_down(pygame.K_ESCAPE)
        game._draw()
        for frames in visual_skin.panda_frames().values():
            assert all(f.get_size() == PLAYER_SIZE and f.get_bounding_rect().height for f in frames)
        pygame.quit()
        print("PASS: title/gallery, 90 gameplay frames, all 18 levels, pause/resume, sprite collision sizes")
    finally:
        os.chdir(previous)

