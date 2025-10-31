-- Active feeds quick scan
create index if not exists idx_feed_register_enabled
  on feed_register(enabled);

-- Fast latest queries
create index if not exists idx_feed_data_feed_published_desc
  on feed_data(feed_id, published_dt desc);