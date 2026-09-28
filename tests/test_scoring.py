from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.models import BlocklistEntry, CheckedEntry, InputType, Verdict
from app.tasks import check_domain_whois

URGENT_MESSAGE = "URGENT!!! Your account will be BLOCKED. Verify now to avoid suspension!"


def days_ago(n):
    return datetime.now(timezone.utc) - timedelta(days=n)


def fake_whois(monkeypatch, creation_date=None, registrar="Test Registrar", error=None):
    def _whois(domain):
        if error is not None:
            raise error
        return SimpleNamespace(creation_date=creation_date, registrar=registrar)

    monkeypatch.setattr("app.tasks.whois.whois", _whois)


def add_to_blocklist(db, url, source="openphish"):
    db.add(BlocklistEntry(url=url, source=source))
    db.commit()


@pytest.fixture()
def run(db_session, monkeypatch):
    """Create an entry, run the real scoring task on it, return the updated row."""
    # the task opens its own session via SessionLocal, so point it at the test DB
    monkeypatch.setattr("app.tasks.SessionLocal", lambda: db_session)

    def _run(value, input_type=InputType.url, message=None):
        entry = CheckedEntry(
            input_value=value,
            input_type=input_type,
            verdict=Verdict.unknown,
            risk_score=0.0,
            details={},
        )
        db_session.add(entry)
        db_session.commit()
        entry_id = entry.id
        check_domain_whois(entry_id, message)
        return db_session.get(CheckedEntry, entry_id)

    return _run


# ---------- WHOIS / domain signals ----------

def test_old_legit_domain_is_safe(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(10000))
    entry = run("google.com")
    assert entry.verdict == Verdict.safe
    assert entry.risk_score == 0.0
    assert entry.details["domain_age_days"] == 10000
    assert entry.details["blocklist_hit"] is False


def test_brand_new_domain_with_payment_keyword_is_high_risk(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(5))
    entry = run("kyc-update.com")
    # 0.5 (age < 30) + 0.3 (keyword) + 0.2 (combo bonus)
    assert entry.risk_score == 1.0
    assert entry.verdict == Verdict.high_risk


def test_new_domain_without_keywords_is_suspicious(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(5))
    entry = run("some-shop.com")
    assert entry.risk_score == 0.5
    assert entry.verdict == Verdict.suspicious


def test_domain_between_30_and_90_days_gets_small_bump(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(60))
    entry = run("some-shop.com")
    assert entry.risk_score == 0.2
    assert entry.verdict == Verdict.safe


def test_whois_failure_on_abuse_tld_is_suspicious(run, monkeypatch):
    fake_whois(monkeypatch, error=Exception("connection timed out"))
    entry = run("mystery-site.tk")
    # 0.25 (no WHOIS data) + 0.15 (.tk)
    assert entry.risk_score == 0.4
    assert entry.verdict == Verdict.suspicious
    assert "timed out" in entry.details["whois_error"]
    assert entry.details["domain_age_days"] is None


def test_missing_creation_date_with_keywords_is_high_risk(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=None)
    entry = run("paytm-refund-verify.tk")
    # 0.25 (no creation date) + 0.3 (keywords) + 0.15 (.tk)
    assert entry.risk_score == 0.7
    assert entry.verdict == Verdict.high_risk
    assert entry.details["whois_error"] == "No creation date found"


def test_naive_whois_datetime_is_treated_as_utc(run, monkeypatch):
    naive = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=5)
    fake_whois(monkeypatch, creation_date=naive)
    entry = run("some-shop.com")
    assert entry.details["domain_age_days"] == 5


def test_list_creation_date_uses_first_record(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=[days_ago(10000), days_ago(5)])
    entry = run("google.com")
    assert entry.details["domain_age_days"] == 10000


# ---------- blocklist ----------

def test_exact_host_blocklist_match_is_high_risk(run, db_session, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(10000))
    add_to_blocklist(db_session, "http://evil-site.com/login")
    entry = run("evil-site.com")
    assert entry.details["blocklist_hit"] is True
    assert entry.details["blocklist_source"] == "openphish"
    assert entry.risk_score == 0.9
    assert entry.verdict == Verdict.high_risk


def test_subdomain_blocklist_entry_does_not_flag_parent_domain(run, db_session, monkeypatch):
    """Regression test: a phishing page on sites.google.com must not flag google.com."""
    fake_whois(monkeypatch, creation_date=days_ago(10000))
    add_to_blocklist(db_session, "https://sites.google.com/view/abc123/home")
    entry = run("google.com")
    assert entry.details["blocklist_hit"] is False
    assert entry.risk_score == 0.0
    assert entry.verdict == Verdict.safe


def test_user_reported_entries_feed_scoring(run, db_session, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(10000))
    add_to_blocklist(db_session, "http://reported-scam.com", source="user_report")
    entry = run("reported-scam.com")
    assert entry.details["blocklist_source"] == "user_report"
    assert entry.verdict == Verdict.high_risk


# ---------- message urgency ----------

def test_urgent_message_on_upi_id_is_suspicious_without_whois(run, monkeypatch):
    def whois_must_not_run(domain):
        pytest.fail("WHOIS should not run for UPI IDs")

    monkeypatch.setattr("app.tasks.whois.whois", whois_must_not_run)
    entry = run("refund-desk@ybl", input_type=InputType.upi, message=URGENT_MESSAGE)
    assert entry.details["message_analysis"]["urgency_score"] == 0.8
    # 0.8 urgency * 0.5 weighting
    assert entry.risk_score == 0.4
    assert entry.verdict == Verdict.suspicious
    assert "domain_age_days" not in entry.details


def test_calm_message_adds_no_risk(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(10000))
    entry = run("google.com", message="Thanks for lunch yesterday, see you on Friday.")
    assert entry.details["message_analysis"]["urgency_keyword_hits"] == []
    assert entry.risk_score == 0.0
    assert entry.verdict == Verdict.safe


# ---------- edges ----------

def test_score_is_capped_at_one(run, monkeypatch):
    fake_whois(monkeypatch, creation_date=days_ago(2))
    entry = run("kyc-update.tk", message=URGENT_MESSAGE)
    assert entry.risk_score == 1.0
    assert entry.verdict == Verdict.high_risk


def test_unknown_entry_id_returns_quietly(db_session, monkeypatch):
    monkeypatch.setattr("app.tasks.SessionLocal", lambda: db_session)
    assert check_domain_whois(9999) is None