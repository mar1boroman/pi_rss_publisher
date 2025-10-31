
# Change ENV

# Docker

```
docker compose up -d
```

```
docker compose exec rss_postgres psql -U appuser -d appdb -t -A -c "SELECT token FROM rss_keys WHERE is_admin = true;"
```