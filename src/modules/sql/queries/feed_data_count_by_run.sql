select count(*)::int as c
from feed_data
where feed_id = %s and run_id = %s;