"""
Progress Bar Overlay - Sleek bottom animated timer line (Anti-Swipe Timer).
Renders a thin 4px glowing progress bar at y=1910-1916 that fills linearly.
Keeps viewers psychologically engaged until the final CTA question.
"""
from moviepy import ColorClip, CompositeVideoClip, VideoFileClip
from typing import Tuple


# Progress bar configuration
PROGRESS_BAR_HEIGHT = 4
PROGRESS_BAR_Y = 1910  # Bottom of 1080x1920 frame (1920 - 10 = 1910, bar at 1910-1914)
PROGRESS_BAR_COLOR = (0, 229, 255)  # Vibrant Cyan #00E5FF
PROGRESS_BAR_BG_COLOR = (0, 229, 255, 128)  # 50% opacity cyan background
PROGRESS_BAR_BG_ALPHA = 0.5
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def create_progress_bar_clips(video_duration: float, fps: int = 30) -> list:
    """
    Create animated progress bar clips that fill from 0 to 1080 over video_duration.
    Returns a list of clips to composite onto the video.
    """
    clips = []

    # Background track (static, 50% opacity)
    # We'll create this as a semi-transparent overlay
    bg_track = ColorClip(
        size=(VIDEO_WIDTH, PROGRESS_BAR_HEIGHT),
        color=PROGRESS_BAR_COLOR,
        duration=video_duration
    ).with_opacity(PROGRESS_BAR_BG_ALPHA).with_position((0, PROGRESS_BAR_Y))

    clips.append(bg_track)

    # Animated foreground fill
    # We create a clip that grows width over time
    def make_progress_frame(t):
        """Generate frame at time t showing progress fill."""
        progress = min(t / video_duration, 1.0)
        fill_width = int(VIDEO_WIDTH * progress)

        # Create frame: transparent background with filled portion
        import numpy as np
        frame = np.zeros((PROGRESS_BAR_HEIGHT, VIDEO_WIDTH, 4), dtype=np.uint8)

        # Fill the progress portion with vibrant cyan
        frame[:, :fill_width] = [0, 229, 255, 255]  # RGBA

        return frame

    from moviepy import VideoClip
    progress_fill = VideoClip(make_progress_frame, duration=video_duration)
    progress_fill = progress_fill.with_position((0, PROGRESS_BAR_Y))
    progress_fill = progress_fill.with_fps(fps)

    clips.append(progress_fill)

    return clips


def create_progress_bar_video(video_duration: float, fps: int = 30) -> VideoFileClip:
    """
    Create a standalone progress bar video clip that can be composited.
    """
    clips = create_progress_bar_clips(video_duration, fps)
    return CompositeVideoClip(clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT)).with_duration(video_duration)


def add_progress_bar_to_video(base_video: VideoFileClip) -> CompositeVideoClip:
    """
    Add progress bar overlay to an existing video.
    """
    progress_clips = create_progress_bar_clips(base_video.duration, base_video.fps)
    all_clips = [base_video] + progress_clips
    return CompositeVideoClip(all_clips, size=base_video.size)