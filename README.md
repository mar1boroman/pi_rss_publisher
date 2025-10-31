
# Pi RSS Publisher (OPML in → Unified RSS out)

A tiny Dockerized app for your Raspberry Pi that:
- reads **OPML** of verified RSS sources,
- reads a **bridges.csv** for sources needing an RSS "bridge" (either **gnews** or **css** mode),
- polls everything on a schedule with caching & dedupe,
- **publishes a single RSS** at `http://<pi>:8088/feed.xml` you can plug into any reader/app.

## Quick start

```bash
cd pi_rss_publisher
docker compose up -d
# Then open http://<pi>:8088/feed.xml
```

Put your files in `./config/`:
- `feeds.opml` — import your curated feeds (the OPML you liked before).
- `bridges.csv` — define bridge sources.

The container stores a SQLite DB in `./data/`.

## bridges.csv format

CSV headers:
```
name,mode,url,list_selector,item_selector,link_selector,title_selector,date_selector,date_format,gnews_query
```

**mode**:
- `gnews` (default): builds a Google News RSS query (works out-of-the-box).
- `css`: scrape a listing page with CSS selectors (for first-class items).

Examples (gnews):
```
MongoDB case studies,gnews,https://www.mongodb.com/solutions/customer-case-studies,,,,,,,"site:mongodb.com \"customer case study\" OR \"customer story\""
```

Examples (css): (you can fill selectors later)
```
VendorX customers,css,https://vendorx.com/customers,.cards,.card,a,.card-title,time,%Y-%m-%d
```

> Start with `gnews` mode for reliability, then upgrade to `css` once you’ve verified selectors.

## Tuning

- Poll interval: `POLL_INTERVAL_SEC` (default 300s).
- Channel title/link: `APP_TITLE`, `CHANNEL_LINK`.
- Keeps last 7 days (endpoint renders last 200 items by default).

## Endpoints
- `/feed.xml` — aggregated RSS
- `/sources` — JSON list of sources
- `/healthz` — liveness

## Notes
- Uses HTTP caching (ETag / Last-Modified) for polite polling.
- Dedupe via GUID/URL hash — no duplicates in your feed.
- Safe on a Pi; CPU-light and I/O-light.
