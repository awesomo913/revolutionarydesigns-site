"""Compatibility entry point for the complete Journey regression suite."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('test-bamboo-journey.py')),run_name='__main__')
