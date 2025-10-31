# init.py
import csv
import base64
import secrets
from dotenv import load_dotenv
from src.modules.pgdao import apply_schema, execute_sql_file, feed_register_upsert

FEEDS_CSV_PATH = "src/config/feeds.csv"


def _init_feeds():
    with open(FEEDS_CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            feed_register_upsert(
                feed_id=row.get("feed_id", "").strip(),
                feed_url=row.get("feed_url", "").strip(),
                category=row.get("category", "").strip(),
                enabled=(row.get("enabled", "true").strip().lower() == "true"),
                etag=None,
                last_modified=None,
                last_seen_published_dt=None,
                last_run_id=None,
            )
            count += 1
    print(f"📡 Loaded {count} feeds into feed_register.")


def _token(nbytes: int = 24) -> str:
    # 192-bit random, URL-safe, no padding
    return base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).decode().rstrip("=")


def _init_tokens():
    # Apply the rss_keys schema (in case apply_schema doesn't include it yet)
    execute_sql_file("schema/020_create_table_rss_keys.sql")

    # Admin token: global scope, higher limit
    admin_tok = _token()
    execute_sql_file(
        "queries/rss_key_insert.sql",
        (admin_tok, "admin", None, None, 500, True, True),
    )

    # Regular token: global scope, default limit
    regular_tok = _token()
    execute_sql_file(
        "queries/rss_key_insert.sql",
        (regular_tok, "user", None, None, 100, True, False),
    )

    print("🔐 Tokens created:")
    print(f"• Admin:    {admin_tok}")
    print(f"• User:     {regular_tok}")


def main():
    load_dotenv()
    execute_sql_file("schema/000_drop_tables.sql")
    apply_schema()
    # Ensure rss_keys exists (kept explicit so we don't touch your existing apply_schema)
    execute_sql_file("schema/020_create_table_rss_keys.sql")
    _init_feeds()
    _init_tokens()
    print("✅ Schema applied, feeds initialized, and tokens generated.")


if __name__ == "__main__":
    main()