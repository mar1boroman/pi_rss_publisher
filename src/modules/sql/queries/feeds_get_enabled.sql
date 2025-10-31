select
  feed_id, feed_url, category, enabled,
  etag, last_modified, last_seen_published_dt, feed_xml_updated_dt, last_run_id
from feed_register
where enabled = true
order by feed_id;