# pgdao.py
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

load_dotenv()


SQL_DIR = os.getenv("SQL_DIR", "sql")


# --- connection ---


def _dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url.split("postgresql+psycopg://", 1)[1]
    return url


def _connect():
    return psycopg.connect(_dsn(), autocommit=True, row_factory=dict_row)


# --- file runner ---


def execute_sql_file(
    relpath: str, params: Tuple[Any, ...] = ()
) -> List[Dict[str, Any]]:
    """
    Execute an SQL file relative to SQL_DIR. Returns rows for SELECT/RETURNING; [] otherwise.
    """
    path = os.path.join(SQL_DIR, relpath)
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        try:
            rows = cur.fetchall()
            return list(rows)
        except psycopg.ProgrammingError:
            # no results to fetch (e.g., UPDATE without RETURNING)
            return []


# --- schema helpers (optional convenience) ---


def apply_schema() -> None:
    execute_sql_file("schema/001_create_table_runs.sql")
    execute_sql_file("schema/002_create_table_feed_register.sql")
    execute_sql_file("schema/003_create_table_feed_data.sql")
    execute_sql_file("schema/010_create_indexes.sql")


# --- RUNS ---


def runs_start() -> int:
    rows = execute_sql_file("queries/runs_start.sql")
    return int(rows[0]["run_id"])


def runs_finish(
    run_id: int,
    *,
    status: str,
    feeds_attempted: int,
    feeds_ok: int,
    feeds_not_modified: int,
    feeds_failed: int,
    entries_seen: int,
    entries_inserted: int,
) -> None:
    execute_sql_file(
        "queries/runs_finish.sql",
        (
            status,
            feeds_attempted,
            feeds_ok,
            feeds_not_modified,
            feeds_failed,
            entries_seen,
            entries_inserted,
            run_id,
        ),
    )


# --- FEED_REGISTER ---


def feeds_get_enabled() -> List[Dict[str, Any]]:
    return execute_sql_file("queries/feeds_get_enabled.sql")


def feed_register_upsert(
    feed_id: str,
    feed_url: str,
    category: str = "",
    enabled: bool = True,
    etag: str | None = None,
    last_modified: str | None = None,
    last_seen_published_dt: datetime | None = None,
    feed_xml_updated_dt: datetime | None = None,  # NEW
    last_run_id: int | None = None,
) -> None:
    execute_sql_file(
        "queries/feed_register_upsert.sql",
        (
            feed_id, feed_url, category, enabled,
            etag, last_modified, last_seen_published_dt, feed_xml_updated_dt, last_run_id,
        ),
    )


def feed_register_update_state(
    feed_id: str,
    *,
    etag: str | None,
    last_modified: str | None,
    last_seen_published_dt: datetime | None,
    feed_xml_updated_dt: datetime | None,  # NEW
    last_run_id: int | None,
) -> None:
    execute_sql_file(
        "queries/feed_register_update_state.sql",
        (etag, last_modified, last_seen_published_dt, feed_xml_updated_dt, last_run_id, feed_id),
    )

def feed_data_count_by_run(feed_id: str, run_id: int) -> int:
    rows = execute_sql_file("queries/feed_data_count_by_run.sql", (feed_id, run_id))
    return int(rows[0]["c"]) if rows else 0

def feed_data_all_by_run(run_id: int):
    return execute_sql_file("queries/feed_data_all_by_run.sql", (run_id,))


# --- FEED_DATA ---


def feed_data_upsert(
    *,
    feed_id: str,
    run_id: int,
    sha1_hash: str,
    uid: Optional[str],
    link: str,
    title: Optional[str],
    summary: Optional[str],
    published_dt: datetime,
    has_real_published: bool,
) -> None:
    execute_sql_file(
        "queries/feed_data_upsert.sql",
        (
            feed_id,
            run_id,
            sha1_hash,
            uid,
            link,
            title,
            summary,
            published_dt,
            has_real_published,
        ),
    )

# --- RSS keys (token security) ---

def rss_key_get(token: str):
    rows = execute_sql_file("queries/rss_key_get.sql", (token,))
    return rows[0] if rows else None

def rss_key_touch(token: str) -> None:
    execute_sql_file("queries/rss_key_touch.sql", (token,))


# --- RSS feed queries (aggregate + items) ---

def rss_head_aggregate(category: str | None, feed_id: str | None):
    # Pass each nullable param twice to match the SQL (%s is null or field = %s)
    rows = execute_sql_file(
        "queries/rss_head_aggregate.sql",
        (category, category, feed_id, feed_id),
    )
    return rows[0] if rows else {"max_published_dt": None, "max_run_id": None, "total_items": 0, "max_hash": None}

def rss_select_items(category: str | None, feed_id: str | None, limit: int):
    return execute_sql_file(
        "queries/rss_select_items.sql",
        (category, category, feed_id, feed_id, limit),
    )