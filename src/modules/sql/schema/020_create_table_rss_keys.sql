create table if not exists rss_keys (
  token         text primary key,
  label         text not null,
  category      text,
  feed_id       text,
  limit_default integer not null default 100,
  enabled       boolean not null default true,
  is_admin      boolean not null default false,  -- << this line
  created_at    timestamptz not null default now(),
  last_used_at  timestamptz
);

create index if not exists idx_rss_keys_enabled on rss_keys(enabled);