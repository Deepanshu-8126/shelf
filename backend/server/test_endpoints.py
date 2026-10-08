#!/usr/bin/env python3
"""Automated API endpoint audit for Shelf Storefront & Catalog API."""
from __future__ import annotations

import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from catalog_api import app

client = TestClient(app)

def test_endpoints():
    print("Testing /api/products...")
    res = client.get("/api/products")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert "products" in data
    print(f"[OK] /api/products OK (Found {len(data['products'])} products)")

    print("Testing /api/blog/articles...")
    res = client.get("/api/blog/articles")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert "articles" in data
    print(f"[OK] /api/blog/articles OK (Found {len(data['articles'])} articles)")

    print("Testing /api/orders...")
    res = client.get("/api/orders")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("[OK] /api/orders OK")

    print("Testing /published static mount...")
    res = client.get("/published/index.html")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "shelf.trends" in res.text
    print("[OK] /published/index.html static mount OK")

    print("Testing /api/wishlink/config...")
    res = client.get("/api/wishlink/config")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("[OK] /api/wishlink/config OK")

    print("\n=== ALL API ENDPOINTS PASSED AUDIT (100% HEALTHY) ===")


if __name__ == "__main__":
    test_endpoints()
