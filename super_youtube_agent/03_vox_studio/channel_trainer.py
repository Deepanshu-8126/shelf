"""
Multi-Channel Persona & Visual Identity Matrix for Vox Studio.
Allows training and configuring custom visual styles, color palettes, typography,
and narrative voices for any new YouTube channel.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChannelPersona:
    channel_id: str
    name: str
    niche: str
    accent_color: str
    glow_color: str
    hud_label: str
    font_headline: str
    font_mono: str
    voice_id: str
    voice_stability: float
    voice_style: float
    system_instruction: str


# ==============================================================================
# PRE-TRAINED CHANNEL PROFILES
# ==============================================================================
CHANNEL_PROFILES: dict[str, ChannelPersona] = {
    "dark_mystery": ChannelPersona(
        channel_id="ch_dark_mystery",
        name="Dark Case Files",
        niche="dark_mystery",
        accent_color="#ff3b30",
        glow_color="rgba(255, 59, 48, 0.8)",
        hud_label="DECLASSIFIED FILE // TOP SECRET",
        font_headline="Space Grotesk",
        font_mono="JetBrains Mono",
        voice_id="nPczCjzI2devNBz1zQrb",  # Brian - Deep Cinematic
        voice_stability=0.30,
        voice_style=0.50,
        system_instruction="Focus on unsolved crimes, military disappearances, declassified documents, and forensic anomalies. Pacing is slow, chilling, and forensic.",
    ),
    "space_science": ChannelPersona(
        channel_id="ch_space_science",
        name="Cosmic Curiosities",
        niche="space_science",
        accent_color="#00f0ff",
        glow_color="rgba(0, 240, 255, 0.8)",
        hud_label="NASA DECLASSIFIED // DEEP SPACE OBSERVATORY",
        font_headline="Space Grotesk",
        font_mono="JetBrains Mono",
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # George - BBC Storyteller
        voice_stability=0.35,
        voice_style=0.45,
        system_instruction="Focus on black holes, relativity paradoxes, quantum anomalies, and James Webb discoveries. Pacing is awe-inspiring and mind-bending.",
    ),
    "dark_web": ChannelPersona(
        channel_id="ch_dark_web",
        name="Deep Web Archive",
        niche="dark_web",
        accent_color="#39ff14",  # Terminal Green
        glow_color="rgba(57, 255, 20, 0.8)",
        hud_label="ENCRYPTED ONION ROUTER // CYBER INVESTIGATION",
        font_headline="JetBrains Mono",
        font_mono="Courier Prime",
        voice_id="N2lVS1w4EtoT3dr4eOWO",  # Callum - Gritty Suspense
        voice_stability=0.28,
        voice_style=0.52,
        system_instruction="Focus on unbreakable cyphers, dark web mysteries, lost hardware, and internet legends. Pacing is tense and cyber-forensic.",
    ),
    "bizarre_history": ChannelPersona(
        channel_id="ch_bizarre_history",
        name="Forbidden History",
        niche="bizarre_history",
        accent_color="#ffd60a",  # Ancient Gold
        glow_color="rgba(255, 214, 10, 0.8)",
        hud_label="HISTORICAL ANOMALY // FORBIDDEN ARCHIVE",
        font_headline="Playfair Display",
        font_mono="JetBrains Mono",
        voice_id="nPczCjzI2devNBz1zQrb",  # Brian
        voice_stability=0.32,
        voice_style=0.46,
        system_instruction="Focus on ancient maps, buried cities, mysterious manuscripts, and historical coincidences. Pacing is majestic and investigative.",
    ),
}


class ChannelTrainer:
    """Manages channel visual identities and custom persona training."""

    @classmethod
    def get_persona(cls, niche: str) -> ChannelPersona:
        return CHANNEL_PROFILES.get(niche, CHANNEL_PROFILES["dark_mystery"])

    @classmethod
    def register_new_channel(
        cls,
        channel_id: str,
        name: str,
        niche: str,
        accent_color: str,
        system_instruction: str,
        voice_id: str = "nPczCjzI2devNBz1zQrb"
    ) -> ChannelPersona:
        """Dynamically trains and registers a brand new channel persona."""
        persona = ChannelPersona(
            channel_id=channel_id,
            name=name,
            niche=niche,
            accent_color=accent_color,
            glow_color=f"{accent_color}cc",
            hud_label=f"{name.upper()} // PRODUCTION LOG",
            font_headline="Space Grotesk",
            font_mono="JetBrains Mono",
            voice_id=voice_id,
            voice_stability=0.32,
            voice_style=0.48,
            system_instruction=system_instruction,
        )
        CHANNEL_PROFILES[niche] = persona
        print(f"✅ [ChannelTrainer] Registered and trained new channel persona: '{name}' ({niche})")
        return persona
