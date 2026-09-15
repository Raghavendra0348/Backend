"""
cache.py — Shared in-memory TTL cache for the AI Skill Gap system.

Uses cachetools.TTLCache (Thread-safe via RLock wrapper):
  - gap_cache:   keyed by (student_id, job_role_id), TTL=5 min
  - rec_cache:   keyed by student_id,                TTL=10 min
  - match_cache: keyed by student_id,                TTL=5 min

Call invalidate_student(student_id) whenever a student's skills/assessments change
to keep results fresh.
"""
from cachetools import TTLCache
from threading import RLock


# ─── Cache stores ────────────────────────────────────────────────────────────
_gap_cache   = TTLCache(maxsize=1000, ttl=300)   # 5 min
_rec_cache   = TTLCache(maxsize=500,  ttl=600)   # 10 min
_match_cache = TTLCache(maxsize=500,  ttl=300)   # 5 min
_path_cache  = TTLCache(maxsize=500,  ttl=600)   # 10 min

_lock = RLock()


# ─── Gap analysis cache ───────────────────────────────────────────────────────
def get_gaps(student_id: int, job_role_id: int):
    with _lock:
        return _gap_cache.get((student_id, job_role_id))


def set_gaps(student_id: int, job_role_id: int, value):
    with _lock:
        _gap_cache[(student_id, job_role_id)] = value


# ─── Recommendation cache ─────────────────────────────────────────────────────
def get_recs(student_id: int):
    with _lock:
        return _rec_cache.get(student_id)


def set_recs(student_id: int, value):
    with _lock:
        _rec_cache[student_id] = value


# ─── Role-match cache ─────────────────────────────────────────────────────────
def get_match(student_id: int):
    with _lock:
        return _match_cache.get(student_id)


def set_match(student_id: int, value):
    with _lock:
        _match_cache[student_id] = value


# ─── Learning path cache ──────────────────────────────────────────────────────
def get_path(student_id: int, job_role_id: int):
    with _lock:
        return _path_cache.get((student_id, job_role_id))


def set_path(student_id: int, job_role_id: int, value):
    with _lock:
        _path_cache[(student_id, job_role_id)] = value


# ─── Invalidation ─────────────────────────────────────────────────────────────
def invalidate_student(student_id: int):
    """Call this when a student's skills or assessments are updated."""
    with _lock:
        # Remove all gap entries for this student
        to_delete_gap = [k for k in _gap_cache if k[0] == student_id]
        for k in to_delete_gap:
            _gap_cache.pop(k, None)

        # Remove recommendation + match + path caches
        _rec_cache.pop(student_id, None)
        _match_cache.pop(student_id, None)

        to_delete_path = [k for k in _path_cache if k[0] == student_id]
        for k in to_delete_path:
            _path_cache.pop(k, None)


def cache_stats() -> dict:
    """Return current cache sizes for the health/debug endpoint."""
    with _lock:
        return {
            "gap_cache":   {"size": len(_gap_cache),   "maxsize": _gap_cache.maxsize,   "ttl": 300},
            "rec_cache":   {"size": len(_rec_cache),   "maxsize": _rec_cache.maxsize,   "ttl": 600},
            "match_cache": {"size": len(_match_cache), "maxsize": _match_cache.maxsize, "ttl": 300},
            "path_cache":  {"size": len(_path_cache),  "maxsize": _path_cache.maxsize,  "ttl": 600},
        }
