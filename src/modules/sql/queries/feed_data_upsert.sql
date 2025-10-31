insert into feed_data (
  feed_id, run_id, sha1_hash, uid, link, title, summary, published_dt, has_real_published, fetched_at
) values (
  %s, %s, %s, %s, %s, %s, %s, %s, %s, now()
)
on conflict (feed_id, sha1_hash) do update set
  run_id             = excluded.run_id,
  uid                = excluded.uid,
  link               = excluded.link,
  title              = excluded.title,
  summary            = excluded.summary,
  published_dt       = excluded.published_dt,
  has_real_published = excluded.has_real_published,
  fetched_at         = now()
where
  feed_data.uid                is distinct from excluded.uid or
  feed_data.link               is distinct from excluded.link or
  feed_data.title              is distinct from excluded.title or
  feed_data.summary            is distinct from excluded.summary or
  feed_data.published_dt       is distinct from excluded.published_dt or
  feed_data.has_real_published is distinct from excluded.has_real_published;