create table if not exists runs (
  run_id            bigserial primary key,
  started_at        timestamptz not null,
  finished_at       timestamptz,
  status            text not null default 'Success',
  feeds_attempted   integer not null default 0,
  feeds_ok          integer not null default 0,
  feeds_not_modified integer not null default 0,
  feeds_failed      integer not null default 0,
  entries_seen      integer not null default 0,
  entries_inserted  integer not null default 0
);