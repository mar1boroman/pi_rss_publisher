create table if not exists feed_data (
  id                bigserial primary key,
  feed_id           text not null references feed_register(feed_id),
  run_id            bigint not null references runs(run_id),
  sha1_hash         text not null,
  uid               text,
  link              text not null,
  title             text,
  summary           text,
  published_dt      timestamptz not null,
  has_real_published boolean not null,
  fetched_at        timestamptz not null default now()
);

-- Prevent duplicates per feed+link-hash
alter table feed_data
  add constraint uq_feed_data_unique_link unique (feed_id, sha1_hash);