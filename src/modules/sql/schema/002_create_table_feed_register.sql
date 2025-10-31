create table if not exists feed_register (
  feed_id                  text primary key,
  feed_url                 text not null,
  category                 text not null default '',
  enabled                  boolean not null default true,
  etag                     text,
  last_modified            text,
  last_seen_published_dt   timestamptz,
  feed_xml_updated_dt      timestamptz,      
  last_run_id              bigint references runs(run_id),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);