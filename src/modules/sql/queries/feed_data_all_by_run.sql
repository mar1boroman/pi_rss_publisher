select feed_id, sha1_hash, uid, link, title, summary, published_dt, has_real_published
from feed_data
where run_id = %s
order by feed_id asc, published_dt desc, id desc;