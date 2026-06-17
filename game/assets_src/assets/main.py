"""Pygbag entry point -- delegates to game.main().

CRITICAL: Pygbag/Pyodide does not auto-register pygame's lazy submodules
(sprite, mixer, font, transform, draw, image) onto the pygame package.
Standard CPython does this via pygame's __init__.py __getattr__ mechanism,
but WASM doesn't always honour it. Explicitly importing them here forces
registration so every `pygame.<submodule>.X` reference from the rest of
the game resolves correctly.
"""

import asyncio

import pygame
import pygame.sprite   # noqa: F401 -- needed for pygame.sprite.Sprite to resolve
import pygame.mixer    # noqa: F401 -- needed for pygame.mixer.Sound
import pygame.font     # noqa: F401
import pygame.transform  # noqa: F401
import pygame.draw     # noqa: F401
import pygame.image    # noqa: F401
import pygame.event    # noqa: F401
import pygame.time     # noqa: F401

from game import main

asyncio.run(main())
