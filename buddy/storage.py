"""Local-only history (SQLite file on your own machine) + streaks, XP and badges.

Privacy by design: we store the mission and your reflection,
never your location or any free text you typed.
"""

from __future__ import annotations

import os
import sqlite3
from collections import Counter
from contextlib import closing
from datetime import date, datetime, timedelta

DB_PATH = os.environ.get("OUTSIDE_BUDDY_DB", os.path.join("data", "history.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TEXT NOT NULL,
    title TEXT NOT NULL,
    mood TEXT, vibe TEXT, company TEXT,
    minutes INTEGER,
    completed INTEGER,
    feeling INTEGER,          -- 1..5
    again INTEGER             -- 1 yes, 0 no
);
"""
# Columns added in v0.2 — added to older databases automatically.
_NEW_COLUMNS = {"spotted": "INTEGER DEFAULT 0", "wet": "INTEGER DEFAULT 0"}

LEVELS = [(0, "Seed", "🌰"), (60, "Sprout", "🌱"), (180, "Sapling", "🌿"),
          (400, "Tree", "🌳"), (800, "Forest", "🏞️")]


def _conn(path: str | None = None) -> sqlite3.Connection:
    path = path or DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    c = sqlite3.connect(path)
    c.execute(_SCHEMA)
    have = {r[1] for r in c.execute("PRAGMA table_info(missions)")}
    for col, typ in _NEW_COLUMNS.items():
        if col not in have:
            c.execute(f"ALTER TABLE missions ADD COLUMN {col} {typ}")  # fixed names, not user input
    return c


def save_result(title, mood, vibe, company, minutes, completed, feeling, again,
                spotted: int = 0, wet: bool = False, path: str | None = None) -> None:
    # Parameterised query -> no SQL injection.
    with closing(_conn(path)) as c, c:
        c.execute(
            "INSERT INTO missions (created,title,mood,vibe,company,minutes,completed,feeling,again,"
            "spotted,wet) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), str(title)[:60], mood, vibe, company,
             int(minutes), int(bool(completed)), int(feeling), int(bool(again)),
             max(0, min(int(spotted), 10)), int(bool(wet))),
        )


def history(limit: int = 50, path: str | None = None) -> list[dict]:
    with closing(_conn(path)) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT * FROM missions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def delete_all(path: str | None = None) -> None:
    with closing(_conn(path)) as c, c:
        c.execute("DELETE FROM missions")


def weekly_stats(path: str | None = None) -> dict:
    since = (datetime.now() - timedelta(days=7)).isoformat()
    rows = [r for r in history(500, path) if r["created"] >= since]
    done = [r for r in rows if r["completed"]]
    return {
        "missions": len(rows),
        "completed": len(done),
        "minutes_outside": sum(r["minutes"] for r in done),
        "avg_feeling": round(sum(r["feeling"] for r in done) / len(done), 1) if done else None,
    }


# ---------- gamification ----------
def mission_xp(minutes: int, completed: bool, spotted: int) -> int:
    """XP for one mission: time outside + finishing bonus + things spotted."""
    if not completed:
        return 0
    return int(minutes) + 20 + 5 * int(spotted)


def total_xp(rows: list[dict]) -> int:
    return sum(mission_xp(r["minutes"], r["completed"], r.get("spotted") or 0) for r in rows)


def level_for(xp: int) -> dict:
    current = LEVELS[0]
    nxt = None
    for i, lvl in enumerate(LEVELS):
        if xp >= lvl[0]:
            current = lvl
            nxt = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
    if nxt:
        progress = (xp - current[0]) / (nxt[0] - current[0])
    else:
        progress = 1.0
    return {"name": current[1], "icon": current[2], "xp": xp,
            "next_name": nxt[1] if nxt else None, "next_xp": nxt[0] if nxt else None,
            "progress": round(progress, 3)}


def streak(rows: list[dict], today: date | None = None) -> int:
    """Consecutive days (ending today or yesterday) with a completed mission."""
    today = today or date.today()
    days = {datetime.fromisoformat(r["created"]).date() for r in rows if r["completed"]}
    d = today if today in days else today - timedelta(days=1)
    count = 0
    while d in days:
        count += 1
        d -= timedelta(days=1)
    return count


BADGES = [
    ("first", "🌱", "First steps", "Finish your first mission"),
    ("rain", "☔", "Rain check", "Finish a mission in wet weather"),
    ("squad", "👯", "Squad goals", "Go with friends or family"),
    ("streak3", "🔥", "On a roll", "3-day streak"),
    ("five", "🖐️", "High five", "Finish 5 missions"),
    ("spotter", "👀", "Eagle eye", "Spot everything on a mission"),
    ("hour", "⏳", "Two hours of grass", "120 minutes outside in total"),
    ("all_vibes", "🎨", "Vibe explorer", "Try every kind of mission"),
]


def earned_badges(rows: list[dict], today: date | None = None) -> set[str]:
    done = [r for r in rows if r["completed"]]
    got = set()
    if done:
        got.add("first")
    if any(r.get("wet") for r in done):
        got.add("rain")
    if any(r["company"] in ("With friends", "With family") for r in done):
        got.add("squad")
    if streak(rows, today) >= 3:
        got.add("streak3")
    if len(done) >= 5:
        got.add("five")
    if any((r.get("spotted") or 0) >= 3 for r in done):
        got.add("spotter")
    if sum(r["minutes"] for r in done) >= 120:
        got.add("hour")
    if {r["vibe"] for r in done} >= {"Relaxing", "Fun", "Creative", "Social", "Active"}:
        got.add("all_vibes")
    return got


def preference_hint(path: str | None = None) -> str:
    """Simple rule-based personalisation from past reflections."""
    rows = history(30, path)
    liked = Counter(r["vibe"] for r in rows if r["completed"] and r["again"] and r["feeling"] >= 4)
    disliked = Counter(r["vibe"] for r in rows if not r["again"] or r["feeling"] <= 2)
    parts = []
    if liked:
        parts.append("enjoyed " + ", ".join(v for v, _ in liked.most_common(2)) + " missions")
    if disliked:
        parts.append("was less keen on " + ", ".join(v for v, _ in disliked.most_common(2)))
    recent = [r["title"] for r in rows[:5]]
    if recent:
        parts.append("avoid repeating: " + "; ".join(recent))
    return ". ".join(parts)
