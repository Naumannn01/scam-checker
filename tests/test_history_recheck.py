from app.models import CheckedEntry, InputType, Verdict


def seed(db, value, verdict, score, input_type=InputType.url, details=None):
    entry = CheckedEntry(
        input_value=value,
        input_type=input_type,
        verdict=verdict,
        risk_score=score,
        details=details or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def test_history_returns_all_entries(client, db_session):
    seed(db_session, "a.com", Verdict.safe, 0.0)
    seed(db_session, "b.tk", Verdict.high_risk, 0.9)
    r = client.get("/check/history")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_history_filters_by_verdict(client, db_session):
    seed(db_session, "a.com", Verdict.safe, 0.0)
    seed(db_session, "b.tk", Verdict.high_risk, 0.9)
    r = client.get("/check/history", params={"verdict": "high_risk"})
    values = [e["input_value"] for e in r.json()]
    assert values == ["b.tk"]


def test_history_filters_by_input_type(client, db_session):
    seed(db_session, "a.com", Verdict.safe, 0.0)
    seed(db_session, "x@ybl", Verdict.unknown, 0.0, input_type=InputType.upi)
    r = client.get("/check/history", params={"input_type": "upi"})
    values = [e["input_value"] for e in r.json()]
    assert values == ["x@ybl"]


def test_history_filters_by_min_score(client, db_session):
    seed(db_session, "low.com", Verdict.safe, 0.1)
    seed(db_session, "high.tk", Verdict.high_risk, 0.8)
    r = client.get("/check/history", params={"min_score": 0.5})
    values = [e["input_value"] for e in r.json()]
    assert values == ["high.tk"]


def test_history_respects_limit(client, db_session):
    for i in range(5):
        seed(db_session, f"site{i}.com", Verdict.safe, 0.0)
    r = client.get("/check/history", params={"limit": 2})
    assert len(r.json()) == 2


def test_get_check_404(client):
    assert client.get("/check/9999").status_code == 404


def test_recheck_404(client):
    assert client.post("/check/9999/recheck").status_code == 404


def test_recheck_resets_entry_and_requeues_task(client, db_session, mock_task):
    entry = seed(
        db_session, "old.tk", Verdict.high_risk, 0.9,
        details={"blocklist_hit": True},
    )
    r = client.post(f"/check/{entry.id}/recheck")
    assert r.status_code == 200
    data = r.json()
    assert data["verdict"] == "unknown"
    assert data["risk_score"] == 0.0
    assert data["details"] == {}
    mock_task.delay.assert_called_once_with(entry.id, None)