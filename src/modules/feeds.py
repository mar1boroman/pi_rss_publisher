from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class FeedDef:
    """
    An individual RSS feed definition used to query an RSS feed.
    """

    feed_id: str
    feed_url: str
    category: str = ""
    enabled: str = "true"

    etag: Optional[str] = None
    last_modified: Optional[str] = None
    last_seen_published_dt: Optional[datetime] = None

    def __str__(self) -> str:
        tag = f" [{self.category}]" if self.category else ""
        return f"FeedDef [{self.feed_id}{tag}] {self.feed_url} (enabled={self.enabled})"


@dataclass
class RssEntry:
    """
    An individual RSS feed entry/item fetched by querying the RSS feed.
    """

    sha1_hash: str = ""
    title: str = ""
    link: str = ""
    uid: str = ""
    published: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str = ""
    has_real_published: bool = False  # marks whether published came from struct_time

    def __str__(self) -> str:
        ts = self.published.isoformat()
        title = self.title.strip()
        link = self.link.strip()
        return f"[{ts}] {title} — {link}"

    def to_record(self):
        return [
            self.title,
            self.link,
            self.uid,
            self.published.isoformat(),
            self.summary,
        ]
