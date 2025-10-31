update rss_keys
set last_used_at = now()
where token = %s;