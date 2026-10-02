"""
Automated Storage & Cache Retention Manager for Vox Studio.
Keeps repository ultra-lightweight:
- Zero heavy video/image bloat committed to Git/GitHub.
- Auto-prunes temp files, intermediate chromium render frames, and raw audio.
- Retains final master videos with configurable expiration policy (e.g., 10 days).
"""
import time
import shutil
from pathlib import Path
from vox_studio.config import ASSETS_DIR, OUTPUT_DIR, TEMPLATES_DIR, WORKSPACE_ROOT


class StorageManager:
    """Manages workspace storage health and automated pruning."""

    def __init__(self, retention_days: int = 10):
        self.retention_seconds = retention_days * 86400

    def enforce_gitignore(self):
        """Ensures all heavy binary output, render caches, and media assets are ignored by Git."""
        gitignore_path = WORKSPACE_ROOT / ".gitignore"
        required_ignores = [
            "# Vox Studio Artifacts & Media",
            "vox_studio/assets/real_images/*",
            "vox_studio/assets/video_clips/*",
            "vox_studio/output/*.mp4",
            "vox_studio/output/*.wav",
            "vox_studio/output/*.mp3",
            "vox_studio/templates/*",
            "*.mp4",
            "*.wav",
            "*.mp3",
            "*.png",
            "*.jpg",
            "*.webp",
            "node_modules/",
            "__pycache__/",
        ]
        
        existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        lines = existing.splitlines()
        added = False
        
        for rule in required_ignores:
            if rule not in lines:
                lines.append(rule)
                added = True
                
        if added:
            gitignore_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(">> [StorageManager] Updated .gitignore: Git repository will stay 100% lightweight.")

    def auto_cleanup(self, purge_temp_now: bool = True):
        """Removes temporary build artifacts and deletes files older than retention policy."""
        now = time.time()
        pruned_count = 0
        freed_bytes = 0

        # 1. Clean intermediate template render HTML/JS caches
        if purge_temp_now and TEMPLATES_DIR.exists():
            for folder in TEMPLATES_DIR.iterdir():
                if folder.is_dir():
                    try:
                        shutil.rmtree(folder)
                        pruned_count += 1
                    except Exception:
                        pass

        # 2. Clean old crawled images and raw audio older than retention period
        for directory in [ASSETS_DIR / "real_images", ASSETS_DIR / "video_clips", ASSETS_DIR / "sfx", OUTPUT_DIR]:
            if not directory.exists():
                continue
            for f in directory.glob("*"):
                if f.is_file():
                    # Check age
                    mtime = f.stat().st_mtime
                    # Delete temp audio immediately if raw, or check age for masters
                    is_temp = "_raw." in f.name or "_visuals." in f.name or ".wav" in f.name
                    if is_temp or (now - mtime > self.retention_seconds):
                        size = f.stat().st_size
                        f.unlink(missing_ok=True)
                        pruned_count += 1
                        freed_bytes += size

        mb_freed = freed_bytes / (1024 * 1024)
        print(f">> [StorageManager] Cleanup completed: Pruned {pruned_count} files, freed {mb_freed:.1f} MB.")


def run_maintenance():
    manager = StorageManager(retention_days=10)
    manager.enforce_gitignore()
    manager.auto_cleanup()


if __name__ == "__main__":
    run_maintenance()
