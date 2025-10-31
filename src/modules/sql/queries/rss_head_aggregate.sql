select
  max(fd.published_dt) as max_published_dt,
  max(fd.run_id)       as max_run_id,
  count(*)             as total_items,
  max(fd.sha1_hash)    as max_hash
from feed_data fd
join feed_register fr on fr.feed_id = fd.feed_id
where fr.enabled = true
  and (%s::text is null or fr.category = %s)
  and (%s::text is null or fd.feed_id  = %s);