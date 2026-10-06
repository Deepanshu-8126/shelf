"""
ComfyUI + Wan 2.2 Video Generation API Client.
Enables local GPU text-to-video generation with graceful fallback when server is offline.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from .dark_crime_prompts import NEGATIVE_PROMPT
except ImportError:
    from dark_crime_prompts import NEGATIVE_PROMPT

DEFAULT_COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")


class ComfyUIClient:
    """Client for interacting with local or remote ComfyUI server."""

    def __init__(self, base_url: str = DEFAULT_COMFYUI_URL, timeout: int = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def is_online(self) -> bool:
        """Checks if the ComfyUI server is reachable and active."""
        try:
            req = urllib.request.Request(f"{self.base_url}/system_stats")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    def build_wan_workflow(
        self,
        prompt: str,
        negative_prompt: str = NEGATIVE_PROMPT,
        width: int = 720,
        height: int = 1280,
        frames: int = 24,
        fps: int = 24,
        steps: int = 30,
        cfg: float = 7.5,
    ) -> dict[str, Any]:
        """Builds standard ComfyUI API workflow graph for Wan 2.2 Text-to-Video."""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int(time.time() * 1000) % 1_000_000_000,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler_ancestral",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["5", 0],
                    "positive": ["7", 0],
                    "negative": ["8", 0],
                    "latent_image": ["6", 0],
                },
            },
            "5": {
                "class_type": "WanVideoSampler",
                "inputs": {
                    "model": "Wan2.2-14B",
                    "resolution": f"{width}x{height}",
                    "num_frames": frames,
                    "fps": fps,
                },
            },
            "6": {
                "class_type": "EmptyLatentVideo",
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": frames,
                    "batch_size": 1,
                },
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["5", 1]},
            },
            "8": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative_prompt, "clip": ["5", 1]},
            },
            "9": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["5", 2]},
            },
            "11": {
                "class_type": "SaveVideo",
                "inputs": {
                    "filename_prefix": "wan_dark_sutra",
                    "images": ["9", 0],
                    "fps": fps,
                },
            },
        }

    def generate_video_clip(
        self,
        prompt: str,
        output_path: Path | str,
        negative_prompt: str = NEGATIVE_PROMPT,
        poll_interval: float = 2.0,
        max_wait_seconds: int = 300,
    ) -> Path | None:
        """
        Sends generation prompt to ComfyUI, waits for render, and downloads result.
        Returns output Path on success, or None on failure/offline.
        """
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        if not self.is_online():
            print(f"⚠️ ComfyUI is offline at {self.base_url}. Switching to CPU/Ken Burns fallback.")
            return None

        workflow = self.build_wan_workflow(prompt, negative_prompt)
        payload = json.dumps({"prompt": workflow}).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                prompt_id = data.get("prompt_id")
        except Exception as exc:
            print(f"❌ Failed to submit prompt to ComfyUI: {exc}")
            return None

        if not prompt_id:
            return None

        print(f"🚀 Queued Wan 2.2 generation (ID: {prompt_id}). Polling progress...")
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            time.sleep(poll_interval)
            try:
                hist_req = urllib.request.Request(f"{self.base_url}/history/{prompt_id}")
                with urllib.request.urlopen(hist_req, timeout=10) as hist_resp:
                    hist_data = json.loads(hist_resp.read().decode("utf-8"))
                    if prompt_id in hist_data:
                        outputs = hist_data[prompt_id].get("outputs", {})
                        # Find video/gif file in outputs
                        for _, node_output in outputs.items():
                            videos = node_output.get("videos") or node_output.get("gifs") or []
                            for v in videos:
                                filename = v.get("filename")
                                subfolder = v.get("subfolder", "")
                                vtype = v.get("type", "output")
                                if filename:
                                    # Download file
                                    params = urllib.parse.urlencode({
                                        "filename": filename,
                                        "subfolder": subfolder,
                                        "type": vtype,
                                    })
                                    download_url = f"{self.base_url}/view?{params}"
                                    urllib.request.urlretrieve(download_url, str(out_p))
                                    print(f"✅ Wan 2.2 video clip saved: {out_p.name}")
                                    return out_p
            except Exception:
                pass

        print(f"⚠️ Wan 2.2 generation timed out after {max_wait_seconds}s.")
        return None


def is_comfyui_online(url: str = DEFAULT_COMFYUI_URL) -> bool:
    """Convenience helper to check if ComfyUI is running."""
    return ComfyUIClient(base_url=url).is_online()


def generate_crime_scene(
    prompt: str,
    output_path: Path | str,
    negative_prompt: str = NEGATIVE_PROMPT,
) -> Path | None:
    """Convenience helper to generate a crime scene video clip via ComfyUI."""
    client = ComfyUIClient()
    return client.generate_video_clip(prompt, output_path, negative_prompt)
