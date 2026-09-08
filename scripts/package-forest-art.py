"""Compatibility entry point. The complete game is now built from game/src."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('package-bamboo-journey.py')),run_name='__main__')
