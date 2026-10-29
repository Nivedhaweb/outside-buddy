from datetime import date, datetime, timedelta

from buddy import storage
from buddy.models import Mission
from buddy.share import invite_text, receipt_svg, whatsapp_link

M = Mission(title="<script>alert(1)</script> Walk", goal="Notice the little things around you.",
            steps=["Walk to the park", "Sit for a bit"], observe=["A bird", "A red door"],
            duration_min=20, where="Eyre Square", safety="Stay on paths.")


def _row(days_ago, **kw):
    r = dict(created=(datetime.now() - timedelta(days=days_ago)).isoformat(), title="x", mood="Bored",
             vibe="Fun", company="Alone", minutes=20, completed=1, feeling=4, again=1, spotted=0, wet=0)
    r.update(kw)
    return r


def test_xp_and_levels():
    assert storage.mission_xp(20, True, 2) == 50
    assert storage.mission_xp(20, False, 2) == 0
    assert storage.level_for(0)["name"] == "Seed"
    assert storage.level_for(200)["name"] == "Sapling"
    assert storage.level_for(5000)["next_name"] is None


def test_streak():
    rows = [_row(0), _row(1), _row(2), _row(5)]
    assert storage.streak(rows) == 3
    assert storage.streak([_row(1)]) == 1          # yesterday still counts
    assert storage.streak([_row(3)]) == 0


def test_badges():
    rows = [_row(0, wet=1, company="With family", spotted=3), _row(1), _row(2)]
    got = storage.earned_badges(rows, date.today())
    assert {"first", "rain", "squad", "streak3", "spotter"} <= got
    assert "five" not in got


def test_old_database_is_upgraded(tmp_path):
    import sqlite3
    db = str(tmp_path / "old.db")
    c = sqlite3.connect(db)
    c.execute("CREATE TABLE missions (id INTEGER PRIMARY KEY, created TEXT, title TEXT, mood TEXT, vibe TEXT,"
              " company TEXT, minutes INTEGER, completed INTEGER, feeling INTEGER, again INTEGER)")
    c.commit(); c.close()
    storage.save_result("t", "Bored", "Fun", "Alone", 10, 1, 4, 1, spotted=2, path=db)
    assert storage.history(path=db)[0]["spotted"] == 2


def test_receipt_escapes_ai_text():
    svg = receipt_svg(M, 1, 2, 5, 45, "Sprout", 2)
    assert "<script>" not in svg and "&lt;script&gt;" in svg


def test_invite_and_link_contain_no_location_coords():
    msg = invite_text(M)
    assert "Eyre Square" in msg and "Phone stays" in msg
    assert whatsapp_link(msg).startswith("https://wa.me/?text=")
