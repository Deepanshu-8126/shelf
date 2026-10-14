"""Channel 1: Reddit Drama & Gameplay Shorts - Production Engine"""
from .run_channel_1 import render_channel_1_short

def run_reddit_pipeline(*args, **kwargs):
    from .run_reddit_pipeline import run
    return run(*args, **kwargs)

__all__ = [
    "render_channel_1_short",
    "run_reddit_pipeline",
]