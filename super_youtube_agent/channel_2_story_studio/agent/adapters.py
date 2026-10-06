from __future__ import annotations

from typing import Any


# The registry is intentionally honest: only YouTube upload is implemented today.
# The other entries are capability targets, not active publishers or unofficial browser bots.
PLATFORM_SPECS = [
    {
        "id": "youtube", "name": "YouTube", "state": "implemented",
        "delivery": "Official YouTube Data API uploader",
        "requirements": "Google OAuth for each owned channel; API quota and all review gates apply.",
    },
    {
        "id": "tiktok", "name": "TikTok", "state": "export_only",
        "delivery": "Copy-ready caption/video brief only; publisher adapter not implemented.",
        "requirements": "Official Content Posting API access, app review, account authorization and platform-specific formatting.",
    },
    {
        "id": "telegram", "name": "Telegram", "state": "export_only",
        "delivery": "Copy-ready message only; Bot API delivery not configured.",
        "requirements": "A bot token and destination authorization; never paste tokens into the dashboard.",
    },
    {
        "id": "bluesky", "name": "Bluesky", "state": "export_only",
        "delivery": "Copy-ready text only; publisher adapter not implemented.",
        "requirements": "Account/app-password setup and post-length/media constraints.",
    },
    {
        "id": "mastodon", "name": "Mastodon", "state": "export_only",
        "delivery": "Copy-ready text only; publisher adapter not implemented.",
        "requirements": "Instance-specific API registration, authorization and character/media limits.",
    },
    {
        "id": "discord", "name": "Discord", "state": "export_only",
        "delivery": "Copy-ready announcement only; Bot/Webhook delivery not configured.",
        "requirements": "Server/channel permission and a protected bot or webhook credential.",
    },
    {
        "id": "meta", "name": "Instagram / Facebook", "state": "export_only",
        "delivery": "Copy-ready caption only; publisher adapter not implemented.",
        "requirements": "Eligible professional account, Meta app review, Graph API permissions and OAuth.",
    },
]


def platform_matrix(authorized_channels: list[str] | None = None) -> list[dict[str, Any]]:
    authorized = set(authorized_channels or [])
    result = []
    for item in PLATFORM_SPECS:
        row = dict(item)
        if item["id"] == "youtube":
            row["connection"] = "OAuth connected" if authorized else "OAuth not connected"
        else:
            row["connection"] = "Not connected"
        result.append(row)
    return result


def distribution_variants(content: dict[str, Any], format_name: str) -> dict[str, Any]:
    """Create editable copy-only variants; this does not publish or upload anything."""
    title = str(content.get("title", "Original video"))[:100]
    hook = str(content.get("hook", "")).strip()
    description = str(content.get("description", "")).strip()
    tags = [str(tag).strip().lstrip("#") for tag in content.get("tags", []) if str(tag).strip()][:12]
    teaser = hook or description or title
    variants = {
        "youtube": {
            "status": "official uploader available when configured",
            "title": title,
            "description": description,
            "tags": tags,
            "format": format_name,
        },
        "tiktok": {
            "status": "draft only · no adapter",
            "caption": f"{teaser}\n\nWatch the full explanation on YouTube. #LearnOnTikTok"[:1800],
            "format_note": "Create and review a separate vertical cut; do not blindly reuse a landscape render.",
        },
        "telegram": {
            "status": "draft only · no adapter",
            "message": f"{title}\n\n{teaser}\n\nFull video: [add reviewed YouTube link]"[:3500],
        },
        "bluesky": {
            "status": "draft only · no adapter",
            "post": f"{title}: {teaser}"[:280],
        },
        "mastodon": {
            "status": "draft only · no adapter",
            "post": f"{title}\n\n{teaser}\n\n[add reviewed YouTube link]"[:480],
            "note": "Review the destination instance's character and media limits.",
        },
        "discord": {
            "status": "draft only · no adapter",
            "announcement": f"**{title}**\n{teaser}\n[add reviewed YouTube link]"[:1800],
        },
        "meta": {
            "status": "draft only · no adapter",
            "caption": f"{title}\n\n{teaser}\n\n{description}"[:2000],
            "format_note": "Prepare a platform-specific Reel/post and verify music, audio and commercial-use rights.",
        },
    }
    return {
        "delivery_mode": "copy-ready drafts only; no cross-platform posting was attempted",
        "generated_at_stage": "content package creation",
        "platforms": variants,
    }
