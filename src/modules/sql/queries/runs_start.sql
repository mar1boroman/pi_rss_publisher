insert into runs (
  started_at, status, feeds_attempted, feeds_ok, feeds_not_modified, feeds_failed, entries_seen, entries_inserted
) values (
  now(), 'Success', 0, 0, 0, 0, 0, 0
)
returning run_id;