update runs set
  finished_at        = now(),
  status             = %s,
  feeds_attempted    = %s,
  feeds_ok           = %s,
  feeds_not_modified = %s,
  feeds_failed       = %s,
  entries_seen       = %s,
  entries_inserted   = %s
where run_id = %s;