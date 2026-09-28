from app.config import settings
from app.models import BlocklistEntry

ADMIN = {"X-Admin-Key": settings.admin_api_key}


def submit(client, value="fake-scam-site.com", note="got this by SMS"):
    return client.post("/report", json={"reported_value": value, "reporter_note": note})


def test_public_can_submit_report(client):
    r = submit(client)
    assert r.status_code == 200
    assert r.json()["status"] == "pending"


def test_pending_requires_admin_key(client):
    submit(client)
    assert client.get("/report/pending").status_code == 403
    assert client.get("/report/pending", headers={"X-Admin-Key": "wrong"}).status_code == 403


def test_pending_lists_reports_for_admin(client):
    submit(client)
    r = client.get("/report/pending", headers=ADMIN)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_approve_requires_admin_key(client):
    report_id = submit(client).json()["id"]
    assert client.post(f"/report/{report_id}/approve").status_code == 403


def test_approve_adds_to_blocklist(client, db_session):
    report_id = submit(client, "fake-scam-site.com").json()["id"]
    r = client.post(f"/report/{report_id}/approve", headers=ADMIN)
    assert r.json()["status"] == "approved"
    hit = db_session.query(BlocklistEntry).filter_by(url="fake-scam-site.com").first()
    assert hit is not None
    assert hit.source == "user_report"


def test_reject_does_not_touch_blocklist(client, db_session):
    report_id = submit(client, "innocent-site.com").json()["id"]
    r = client.post(f"/report/{report_id}/reject", headers=ADMIN)
    assert r.json()["status"] == "rejected"
    assert db_session.query(BlocklistEntry).count() == 0


def test_approve_unknown_report_404(client):
    assert client.post("/report/9999/approve", headers=ADMIN).status_code == 404

def test_report_rejects_garbage_input(client):
    r = client.post("/report", json={"reported_value": "hello world"})
    assert r.status_code == 422