#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

URL = os.getenv("TARGET_URL", "https://www.marukyu-koyamaen.co.jp/english/shop/products/catalog/matcha")
STATE_PATH = Path(os.getenv("STATE_PATH", "state/last_hash.txt"))
SNAPSHOT_PATH = Path(os.getenv("SNAPSHOT_PATH", "state/last_snapshot.txt"))
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def normalize_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts/styles and invisible bits that add noise.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Capture visible text plus link targets to make change detection more stable.
    parts: list[str] = []
    for node in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "a", "button", "span", "div"]):
        text = " ".join(node.get_text(" ", strip=True).split())
        if not text:
            continue
        href = node.get("href")
        if href:
            parts.append(f"{text} -> {href}")
        else:
            parts.append(text)

    normalized = "\n".join(dict.fromkeys(parts))
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_previous_hash(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    content = path.read_text(encoding="utf-8").strip()
    return content or None


def write_state(hash_value: str, snapshot: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(hash_value + "\n", encoding="utf-8")
    SNAPSHOT_PATH.write_text(snapshot + "\n", encoding="utf-8")


def notify_discord(message: str) -> None:
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {"content": message}
    requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30).raise_for_status()


def main() -> int:
    html = fetch_page(URL)
    snapshot = normalize_html(html)
    current_hash = sha256(snapshot)
    previous_hash = read_previous_hash(STATE_PATH)

    now = datetime.now(timezone.utc).isoformat()

    print(json.dumps({
        "url": URL,
        "utc_time": now,
        "current_hash": current_hash,
        "previous_hash": previous_hash,
        "changed": previous_hash is not None and previous_hash != current_hash,
        "snapshot_chars": len(snapshot),
    }, ensure_ascii=False, indent=2))

    if previous_hash is None:
        print("Initial run: saving baseline snapshot.")
        write_state(current_hash, snapshot)
        return 0

    if previous_hash != current_hash:
        print("Change detected on the matcha page.")
        write_state(current_hash, snapshot)
        notify_discord(
            f"Marukyu Koyamaen matcha page changed: {URL}\n"
            f"Checked at {now} UTC"
        )
    else:
        print("No change detected.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
