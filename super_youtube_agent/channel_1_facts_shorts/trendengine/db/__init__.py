"""Database package for trendengine."""
from .models import get_db, init_db, save_discovered_topics, get_top_topics, mark_topic_status

__all__ = ["get_db", "init_db", "save_discovered_topics", "get_top_topics", "mark_topic_status"]
