insert into feed_register (
  feed_id, feed_url, category, enabled,
  etag, last_modified, last_seen_published_dt, feed_xml_updated_dt, last_run_id,
  created_at, updated_at
) values (
  %s, %s, %s, %s,
  %s, %s, %s, %s, %s,
  now(), now()
)
on conflict (feed_id) do update set
  feed_url = excluded.feed_url,
  category = excluded.category,
  enabled = excluded.enabled,
  etag = excluded.etag,
  last_modified = excluded.last_modified,
  last_seen_published_dt = excluded.last_seen_published_dt,
  feed_xml_updated_dt = excluded.feed_xml_updated_dt,
  last_run_id = excluded.last_run_id,
  updated_at = now();