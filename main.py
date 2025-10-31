# main.py
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Iterable, Optional

import feedparser

from src.modules.feeds import FeedDef, RssEntry
from src.modules.pgdao import (
    runs_start,
    runs_finish,
    feeds_get_enabled,
    feed_register_update_state,
    feed_data_upsert,
    feed_data_count_by_run,
    feed_data_all_by_run,
)


# ---------- tiny helpers ----------

def _to_dt_from_struct(t) -> Optional[datetime]:
    if isinstance(t, time.struct_time):
        return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def _to_published_dt(t) -> datetime:
    dt = _to_dt_from_struct(t)
    return dt if dt is not None else datetime.now(timezone.utc)


def _sha1(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def _to_rss_entries(entries: Iterable[object]) -> List[RssEntry]:
    out: List[RssEntry] = []
    for e in entries:
        ts = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        has_real = isinstance(ts, time.struct_time)
        link = getattr(e, "link", "") or ""
        out.append(
            RssEntry(
                sha1_hash=_sha1(link),
                title=getattr(e, "title", ""),
                link=link,
                uid=getattr(e, "id", "") or getattr(e, "guid", "") or "",
                published=_to_published_dt(ts),
                summary=getattr(e, "summary", ""),
                has_real_published=has_real,
            )
        )
    return out


def _dict_to_feeddef(row) -> FeedDef:
    return FeedDef(
        feed_id=row["feed_id"],
        feed_url=row["feed_url"],
        category=row.get("category", "") or "",
        enabled="true" if row.get("enabled", True) else "false",
        etag=row.get("etag"),
        last_modified=row.get("last_modified"),
        last_seen_published_dt=row.get("last_seen_published_dt"),
    )


def _status_str(http_status: Optional[int]) -> str:
    if http_status == 304:
        return "🔄 304 Not Modified"
    if http_status == 307:
        return "➡️ 307 Redirect"
    if http_status is None:
        return "ℹ️ (no HTTP status)"
    if 200 <= http_status < 300:
        return f"✅ {http_status} OK"
    if 400 <= http_status < 500:
        return f"⚠️ {http_status} Client Error"
    return f"⛔ {http_status}"


def _print_feed_status(feed: FeedDef, http_status: Optional[int], new_count: int):
    print(f"📰 {feed}  |  {_status_str(http_status)}  |  🆕 {new_count} new this run")


def _update_feed_register_if_changed(
    *,
    feed: FeedDef,
    new_etag: Optional[str],
    new_last_modified: Optional[str],
    new_waterline: Optional[datetime],
    new_xml_dt: Optional[datetime],
    new_last_run_id: Optional[int],
    prev_xml_dt: Optional[datetime],
    prev_last_run_id: Optional[int],
):
    """Avoid redundant writes: only update when any value actually changes."""
    etag = new_etag if new_etag is not None else feed.etag
    last_mod = new_last_modified if new_last_modified is not None else feed.last_modified
    waterline = new_waterline if new_waterline is not None else feed.last_seen_published_dt
    xml_dt = new_xml_dt if new_xml_dt is not None else prev_xml_dt
    last_run_id = new_last_run_id if new_last_run_id is not None else prev_last_run_id

    changed = (
        etag != feed.etag
        or last_mod != feed.last_modified
        or waterline != feed.last_seen_published_dt
        or xml_dt != prev_xml_dt
        or last_run_id != prev_last_run_id
    )
    if changed:
        feed_register_update_state(
            feed.feed_id,
            etag=etag,
            last_modified=last_mod,
            last_seen_published_dt=waterline,
            feed_xml_updated_dt=xml_dt,
            last_run_id=last_run_id,
        )


# ---------- main orchestration ----------

def main():
    started = datetime.now(timezone.utc)
    run_id = runs_start()

    feeds_attempted = 0
    feeds_ok = 0
    feeds_not_modified = 0
    feeds_failed = 0
    entries_seen = 0
    entries_processed = 0  # inserted or updated

    for row in feeds_get_enabled():
        feeds_attempted += 1
        feed = _dict_to_feeddef(row)
        prev_xml_dt = row.get("feed_xml_updated_dt")
        prev_last_run_id = row.get("last_run_id")

        # 1) HTTP conditional GET
        parsed = feedparser.parse(feed.feed_url, etag=feed.etag, modified=feed.last_modified)
        status = getattr(parsed, "status", None)

        # Transport-layer no change
        if status == 304:
            feeds_not_modified += 1
            _print_feed_status(feed, status, 0)
            continue

        # treat 200–299 + 307 as OK
        if status is not None and (200 <= int(status) < 300 or status == 307):
            feeds_ok += 1
        elif status is not None:
            feeds_failed += 1

        # 2) XML-level timestamp (<updated> / <lastBuildDate>) check
        xml_updated_struct = (
            getattr(getattr(parsed, "feed", {}), "updated_parsed", None)
            or getattr(getattr(parsed, "feed", {}), "published_parsed", None)
        )
        xml_updated_dt = _to_dt_from_struct(xml_updated_struct)
        if xml_updated_dt is not None and prev_xml_dt is not None and xml_updated_dt <= prev_xml_dt:
            _update_feed_register_if_changed(
                feed=feed,
                new_etag=parsed.get("etag"),
                new_last_modified=parsed.get("modified"),
                new_waterline=None,
                new_xml_dt=prev_xml_dt,
                new_last_run_id=None,
                prev_xml_dt=prev_xml_dt,
                prev_last_run_id=prev_last_run_id,
            )
            _print_feed_status(feed, status, 0)
            continue

        # 3) Parse entries (only when needed)
        entries = _to_rss_entries(parsed.entries or [])
        entries_seen += len(entries)

        # 4) Upsert entries; compute safe waterline
        max_real_published = feed.last_seen_published_dt
        for e in entries:
            if e.has_real_published and (max_real_published is None or e.published > max_real_published):
                max_real_published = e.published

            feed_data_upsert(
                feed_id=feed.feed_id,
                run_id=run_id,
                sha1_hash=e.sha1_hash,
                uid=e.uid or None,
                link=e.link,
                title=e.title or None,
                summary=e.summary or None,
                published_dt=e.published,
                has_real_published=bool(e.has_real_published),
            )
            entries_processed += 1

        # 5) Count only new/updated entries for this feed
        new_count = feed_data_count_by_run(feed.feed_id, run_id)
        _print_feed_status(feed, status, new_count)

        # 6) Update feed_register if changed; bump last_run_id only when new_count > 0
        _update_feed_register_if_changed(
            feed=feed,
            new_etag=parsed.get("etag"),
            new_last_modified=parsed.get("modified"),
            new_waterline=max_real_published,
            new_xml_dt=xml_updated_dt,
            new_last_run_id=(run_id if new_count > 0 else None),
            prev_xml_dt=prev_xml_dt,
            prev_last_run_id=prev_last_run_id,
        )

    # 7) Print all new entries this run (ordered by feed_id)
    rows_all = feed_data_all_by_run(run_id)
    if rows_all:
        print("\n📥 New entries this run (all feeds):")
        for i, r in enumerate(rows_all, 1):
            e = RssEntry(
                sha1_hash=r["sha1_hash"],
                title=r.get("title") or "",
                link=r.get("link") or "",
                uid=r.get("uid") or "",
                published=r["published_dt"],
                summary=r.get("summary") or "",
                has_real_published=bool(r["has_real_published"]),
            )
            print(f"   {i:>2}. [{r['feed_id']}] {e}")
    else:
        print("\n📥 New entries this run (all feeds): none ✨")

    # Finish run in DB
    runs_finish(
        run_id,
        status="Success",
        feeds_attempted=feeds_attempted,
        feeds_ok=feeds_ok,
        feeds_not_modified=feeds_not_modified,
        feeds_failed=feeds_failed,
        entries_seen=entries_seen,
        entries_inserted=entries_processed,
    )

    # One-line emoji summary
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    print(
        f"\n📊 Run {run_id} summary | 🧭 attempted: {feeds_attempted}  "
        f"✅ ok: {feeds_ok}  🔄 not-modified: {feeds_not_modified}  "
        f"⛔ failed: {feeds_failed}  👀 seen: {entries_seen}  ✍️ processed: {entries_processed}  "
        f"⏱️ {elapsed:.2f}s"
    )


if __name__ == "__main__":
    main()