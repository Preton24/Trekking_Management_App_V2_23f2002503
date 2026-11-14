"""Redis caching helpers (Flask-Caching with the RedisCache backend).

Why cache at all: the trek list, the trek detail and the admin stats are read
far more often than they change, so we keep the ready-made answer in Redis and
skip the database queries until the data changes or the timeout runs out.

The cache object lives in this file (not in app.py) so that the route files can
import it without importing app.py, which would be a circular import.
"""
import redis
from flask import current_app
from flask_caching import Cache

# Created once here and attached to the app inside create_app() with cache.init_app(app)
cache = Cache()

# How long a cached answer is kept before Redis removes it by itself (in seconds)
TREK_LIST_TIMEOUT = 300    # 5 minutes
TREK_DETAIL_TIMEOUT = 300  # 5 minutes
ADMIN_STATS_TIMEOUT = 120  # 2 minutes

# Key names. Every trek list key starts with the same text, so all of them
# can be found and deleted together when a trek changes.
TREK_LIST_PREFIX = "trek_list:"
TREK_DETAIL_PREFIX = "trek_detail:"
ADMIN_STATS_KEY = "admin_stats"


def trek_list_key(filters):
    """Build the cache key for one combination of trek list filters.

    `filters` is a dict such as {"difficulty": "Easy", "q": "", ...}.
    The names are sorted so the same filters always give the same key,
    e.g. "trek_list:difficulty=Easy&location=&max_duration=&min_duration=&q=".
    """
    parts = []
    for name in sorted(filters):
        value = filters[name]
        if value is None:
            value = ""
        parts.append(f"{name}={value}")
    return TREK_LIST_PREFIX + "&".join(parts)


def trek_detail_key(trek_id):
    """Cache key for one trek's details, e.g. "trek_detail:7"."""
    return TREK_DETAIL_PREFIX + str(trek_id)


def cache_get(key):
    """Read a key from Redis and log whether it was a HIT or a MISS.

    Returns None on a MISS, which tells the route to query the database.
    """
    value = cache.get(key)
    if value is None:
        current_app.logger.info("CACHE MISS  %s (reading from the database)", key)
    else:
        current_app.logger.info("CACHE HIT   %s (served from Redis)", key)
    return value


def cache_set(key, value, timeout):
    """Store a value in Redis for `timeout` seconds."""
    cache.set(key, value, timeout=timeout)


def delete_keys_starting_with(prefix):
    """Delete every cache key that starts with `prefix`.

    Flask-Caching can only delete a key when it knows the exact name. For the
    trek list we cannot know which filter combinations are cached right now,
    so we ask Redis itself for all keys with this prefix and delete each one.
    """
    redis_client = redis.Redis.from_url(current_app.config["CACHE_REDIS_URL"])
    # Flask-Caching puts CACHE_KEY_PREFIX in front of every key it stores
    full_prefix = current_app.config["CACHE_KEY_PREFIX"] + prefix

    deleted = 0
    # scan_iter walks through the keys in small batches, so Redis is never blocked
    for key in redis_client.scan_iter(match=full_prefix + "*"):
        redis_client.delete(key)
        deleted += 1
    return deleted


def clear_trek_caches(trek_id):
    """Throw away every cached answer that could now be wrong for this trek.

    Called AFTER db.session.commit() whenever a trek is created, edited or
    deleted, or a seat on it is booked or cancelled:
      1. all trek list keys  - the trek may appear in any filtered list
      2. this trek's detail  - its slots, status or other fields changed
      3. the admin stats     - trek and booking counts changed
    The next request for each of these is a MISS and reads fresh data.
    """
    lists_deleted = delete_keys_starting_with(TREK_LIST_PREFIX)
    cache.delete(trek_detail_key(trek_id))
    cache.delete(ADMIN_STATS_KEY)
    current_app.logger.info(
        "CACHE CLEAR trek %s changed: removed %s trek list key(s), %s and %s",
        trek_id, lists_deleted, trek_detail_key(trek_id), ADMIN_STATS_KEY,
    )
