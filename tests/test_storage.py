from buddy import storage


def test_save_stats_preferences_delete(tmp_path):
    db = str(tmp_path / "h.db")
    storage.save_result("Reset", "Bored", "Relaxing", "Alone", 20, True, 5, True, path=db)
    storage.save_result("Dash", "Restless", "Active", "Alone", 10, True, 2, False, path=db)
    stats = storage.weekly_stats(db)
    assert stats["completed"] == 2 and stats["minutes_outside"] == 30
    hint = storage.preference_hint(db)
    assert "enjoyed Relaxing" in hint and "less keen on Active" in hint
    storage.delete_all(db)
    assert storage.history(path=db) == []


def test_sql_injection_is_inert(tmp_path):
    db = str(tmp_path / "h.db")
    storage.save_result("x'); DROP TABLE missions;--", "Bored", "Fun", "Alone", 10, 1, 3, 1, path=db)
    assert len(storage.history(path=db)) == 1
