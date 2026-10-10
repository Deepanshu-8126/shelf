"""
Channel 2: Vox Documentary Mystery & High-RPM Reality Engine.
Exposes the 4 Pillars, Script Generator, Motion Graphics HUDs, and Master Runner.
"""
from .vox_pillars_config import PILLARS_REGISTRY, get_pillar_by_id_or_key
from .vox_script_generator import generate_vox_documentary_package
from .vox_broll_fetcher import fetch_broll_clip
from .vox_motion_graphics import (
    create_radar_coordinates_hud,
    create_evidence_marker_hud,
    create_telemetry_hud,
    create_iris_target_hud,
    build_hud_clip
)
from .run_vox_pipeline import run as run_vox_pipeline

__all__ = [
    "PILLARS_REGISTRY",
    "get_pillar_by_id_or_key",
    "generate_vox_documentary_package",
    "fetch_broll_clip",
    "create_radar_coordinates_hud",
    "create_evidence_marker_hud",
    "create_telemetry_hud",
    "create_iris_target_hud",
    "build_hud_clip",
    "run_vox_pipeline",
]