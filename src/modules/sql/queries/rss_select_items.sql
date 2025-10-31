select
  fd.feed_id, fd.sha1_hash, fd.uid, fd.link, fd.title, fd.summary,
  fd.published_dt, fd.has_real_published,
  fr.category
from feed_data fd
join feed_register fr on fr.feed_id = fd.feed_id
where fr.enabled = true
  and (%s::text is null or fr.category = %s)
  and (%s::text is null or fd.feed_id  = %s)
order by fd.published_dt desc, fd.id desc
limit %s;