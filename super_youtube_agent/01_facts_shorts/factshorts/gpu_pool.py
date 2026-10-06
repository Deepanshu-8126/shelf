"""Multi-Cloud Free GPU Pool & Auto-Failover Router.

Connects Google Colab, Kaggle, Modal, HuggingFace ZeroGPU, and local GPUs
into a unified resilient worker pool.

Features:
- Health check & latency sorting across all registered workers.
- Zero-downtime auto-failover: if Colab disconnects, switches to Kaggle/Modal mid-pipeline.
- Comma-separated or list-based URL parsing from GPU_WORKER_URL.
- Preserves 100% free (₹0) GPU compute hours across providers.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .utils import module_logger

log = module_logger("gpu_pool")


@dataclass
class GPUWorkerNode:
    url: str
    provider: str = "unknown"
    online: bool = False
    device: str = "unknown"
    vram_gb: float = 0.0
    latency_ms: float = 9999.0
    models: list[str] = None
    last_check: float = 0.0

    def __post_init__(self):
        if self.models is None:
            self.models = ["wan-2.2", "ltx-2.3", "z-image-turbo"]
        if "trycloudflare.com" in self.url:
            self.provider = "Colab/Kaggle Cloudflare Tunnel"
        elif "ngrok" in self.url:
            self.provider = "Ngrok Tunnel"
        elif "modal.run" in self.url:
            self.provider = "Modal Serverless"
        elif "127.0.0.1" in self.url or "localhost" in self.url:
            self.provider = "Local GPU"
        else:
            self.provider = "Cloud GPU"


class GPUPoolManager:
    """Manages multi-cloud GPU instances with automatic fallback."""

    def __init__(self, raw_urls: str | list[str] = ""):
        self.workers: dict[str, GPUWorkerNode] = {}
        self.update_urls(raw_urls)

    def update_urls(self, raw_urls: str | list[str]) -> None:
        if isinstance(raw_urls, str):
            # Split comma or newline separated URLs
            urls = [u.strip() for u in raw_urls.replace("\n", ",").split(",") if u.strip()]
        else:
            urls = [u.strip() for u in raw_urls if u.strip()]

        for u in urls:
            clean = u.rstrip("/")
            if clean and clean not in self.workers:
                self.workers[clean] = GPUWorkerNode(url=clean)

    def add_worker(self, url: str) -> None:
        clean = url.strip().rstrip("/")
        if clean and clean not in self.workers:
            self.workers[clean] = GPUWorkerNode(url=clean)

    async def check_node(self, node: GPUWorkerNode) -> GPUWorkerNode:
        """Pings /health on node and measures round-trip latency."""
        t0 = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.5)) as client:
                resp = await client.get(f"{node.url}/health")
                latency = (time.monotonic() - t0) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    node.online = bool(data.get("gpu", True))
                    node.device = str(data.get("device", "GPU Worker"))
                    node.vram_gb = float(data.get("vram_gb", 16.0))
                    node.models = data.get("supported_video_models", node.models)
                    node.latency_ms = round(latency, 1)
                    node.last_check = time.time()
                    return node
        except Exception:
            pass

        node.online = False
        node.latency_ms = 9999.0
        node.last_check = time.time()
        return node

    async def get_active_workers(self, force_refresh: bool = False) -> list[GPUWorkerNode]:
        """Returns online workers sorted by fastest response time."""
        now = time.time()
        tasks = []
        for node in self.workers.values():
            if force_refresh or (now - node.last_check > 45.0):
                tasks.append(self.check_node(node))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        online_nodes = [w for w in self.workers.values() if w.online]
        online_nodes.sort(key=lambda n: n.latency_ms)
        return online_nodes

    async def execute_with_failover(
        self,
        endpoint: str,
        payload: dict[str, Any],
        timeout: float = 300.0,
    ) -> tuple[httpx.Response | None, str]:
        """Tries the fastest online GPU first; if it drops or errors, fails over to next."""
        nodes = await self.get_active_workers(force_refresh=False)
        if not nodes:
            # Force refresh in case check was stale
            nodes = await self.get_active_workers(force_refresh=True)

        if not nodes:
            log.warning("No online GPU workers in pool (%d registered)", len(self.workers))
            return None, "No online GPU worker in pool"

        last_error = ""
        for node in nodes:
            url = f"{node.url}/{endpoint.lstrip('/')}"
            log.info("Dispatching to GPU Worker [%s - %s]: %s", node.provider, node.device, url)
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        log.info("GPU Worker succeeded: %s", node.url)
                        return resp, ""
                    log.warning("GPU Worker %s returned HTTP %d: %s", node.url, resp.status_code, resp.text[:120])
                    last_error = f"HTTP {resp.status_code}"
            except Exception as exc:
                log.warning("GPU Worker %s failed with exception: %s -> Failing over to next node", node.url, exc)
                node.online = False
                last_error = str(exc)

        return None, f"All GPU workers in pool failed ({last_error})"


# Global singleton pool
_GLOBAL_POOL: GPUPoolManager | None = None


def get_gpu_pool(raw_urls: str | list[str] = "") -> GPUPoolManager:
    global _GLOBAL_POOL
    if _GLOBAL_POOL is None:
        _GLOBAL_POOL = GPUPoolManager(raw_urls)
    elif raw_urls:
        _GLOBAL_POOL.update_urls(raw_urls)
    return _GLOBAL_POOL
