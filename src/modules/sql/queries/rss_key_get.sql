select token, label, category, feed_id, limit_default, enabled, created_at, last_used_at
from rss_keys
where token = %s and enabled = true;