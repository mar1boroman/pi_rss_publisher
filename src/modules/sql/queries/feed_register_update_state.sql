update feed_register set
  etag                   = %s,
  last_modified          = %s,
  last_seen_published_dt = %s,
  feed_xml_updated_dt    = %s,
  last_run_id            = %s,
  updated_at             = now()
where feed_id = %s;