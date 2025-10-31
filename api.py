# api.py
import os, hashlib
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Response, Request, HTTPException
from fastapi.responses import PlainTextResponse
from feedgen.feed import FeedGenerator

from src.modules.pgdao import (
    rss_key_get,
    rss_key_touch,
    rss_head_aggregate,
    rss_select_items,
)

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Personalized RSS")
APP_LINK = os.getenv("APP_LINK", "https://example.com")
MAX_LIMIT = int(os.getenv("RSS_MAX_LIMIT", "500"))

app = FastAPI(title="RSS API", version="1.0.0")


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return (
        dt.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None
        else dt.astimezone(timezone.utc)
    )


def _etag(
    scope: str,
    max_run_id: Optional[int],
    max_published_dt: Optional[datetime],
    total_items: int,
    max_hash: Optional[str],
) -> str:
    parts = [
        scope,
        str(max_run_id or 0),
        (max_published_dt.isoformat() if max_published_dt else "0"),
        str(total_items),
        (max_hash or "0"),
    ]
    return f"\"{hashlib.sha1('|'.join(parts).encode('utf-8')).hexdigest()}\""


def _http_last_modified(dt: Optional[datetime]) -> str:
    return format_datetime(_to_utc(dt) or datetime.now(timezone.utc), usegmt=True)


def _feed_title(base: str, category: Optional[str], feed_id: Optional[str]) -> str:
    if feed_id:
        return f"{base} · feed:{feed_id}"
    if category:
        return f"{base} · category:{category}"
    return base


@app.get("/rss/{token}", response_class=PlainTextResponse)
def rss_by_token(token: str, request: Request, limit: Optional[int] = None):
    row = rss_key_get(token)
    if not row:
        raise HTTPException(status_code=403, detail="Invalid token")

    category = row.get("category")
    feed_id = row.get("feed_id")
    lim = min(max(1, limit or row.get("limit_default", 100)), MAX_LIMIT)

    agg = rss_head_aggregate(category, feed_id)
    max_pub = _to_utc(agg.get("max_published_dt"))
    etag = _etag(
        f"cat={category or '*'}|feed={feed_id or '*'}|limit={lim}",
        agg.get("max_run_id"),
        max_pub,
        int(agg.get("total_items") or 0),
        agg.get("max_hash"),
    )
    last_mod = _http_last_modified(max_pub)

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304)
    if request.headers.get("if-modified-since") == last_mod:
        return Response(status_code=304)

    items = rss_select_items(category, feed_id, lim)

    fg = FeedGenerator()
    fg.title(_feed_title(APP_TITLE, category, feed_id))
    fg.link(href=APP_LINK, rel="alternate")
    fg.description("Merged items from FEED_DATA")
    if max_pub:
        fg.lastBuildDate(max_pub)

    for r in items:
        fe = fg.add_entry()
        fe.title(r.get("title") or r.get("link") or "(untitled)")
        link = r.get("link") or ""
        if link:
            fe.link(href=link, rel="alternate")
        fe.guid(r.get("sha1_hash") or link, permalink=False)
        pubdt = _to_utc(r.get("published_dt"))
        if pubdt:
            fe.pubDate(pubdt)
        summary = r.get("summary") or ""
        if summary:
            fe.description(summary)
        cat = r.get("category") or ""
        if cat:
            fe.category(term=cat)

    rss_key_touch(token)

    return Response(
        content=fg.rss_str(pretty=True),
        media_type="application/rss+xml; charset=utf-8",
        headers={
            "ETag": etag,
            "Last-Modified": last_mod,
            "Cache-Control": "public, max-age=60",
        },
        status_code=200,
    )
