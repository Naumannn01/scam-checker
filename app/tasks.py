import whois
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import CheckedEntry, Verdict, InputType, BlocklistEntry
from app.nlp import analyze_message


def extract_domain(url: str) -> str:
    """Strip protocol/path to get bare domain for WHOIS lookup."""
    domain = url.strip()
    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]
    return domain


def extract_host(url: str) -> str:
    """Extract the actual host from a URL, for exact-match blocklist comparison."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
    return urlparse(url).netloc.lower()


@celery_app.task(name="app.tasks.check_domain_whois")
def check_domain_whois(entry_id: int, message_text: str = None):
    db = SessionLocal()
    try:
        entry = db.query(CheckedEntry).filter(CheckedEntry.id == entry_id).first()
        if not entry:
            return

        details = dict(entry.details or {})
        score = 0.0

        if entry.input_type == InputType.url:
            domain = extract_domain(entry.input_value)

            try:
                w = whois.whois(domain)
                creation_date = w.creation_date
                if isinstance(creation_date, list):
                    creation_date = creation_date[0]

                if creation_date:
                    if creation_date.tzinfo is None:
                        creation_date = creation_date.replace(tzinfo=timezone.utc)
                    age_days = (datetime.now(timezone.utc) - creation_date).days
                    details["domain_age_days"] = age_days
                    details["registrar"] = w.registrar
                else:
                    details["domain_age_days"] = None
                    details["whois_error"] = "No creation date found"
            except Exception as e:
                details["whois_error"] = str(e)
                details["domain_age_days"] = None

            payment_keywords = ["paytm", "upi", "refund", "verify", "kyc", "bank", "otp"]
            domain_lower = domain.lower()

            if details.get("domain_age_days") is not None:
                if details["domain_age_days"] < 30:
                    score += 0.5
                elif details["domain_age_days"] < 90:
                    score += 0.2
            else:
                score += 0.25

            if any(kw in domain_lower for kw in payment_keywords):
                score += 0.3

            if details.get("domain_age_days") is not None and details["domain_age_days"] < 30 and any(kw in domain_lower for kw in payment_keywords):
                score += 0.2

            suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq"]
            if any(domain_lower.endswith(tld) for tld in suspicious_tlds):
                score += 0.15

            candidates = db.query(BlocklistEntry).filter(
                BlocklistEntry.url.ilike(f"%{domain}%")
            ).all()

            blocklist_hit = next(
                (c for c in candidates if extract_host(c.url) == domain.lower()),
                None
            )

            details["blocklist_hit"] = bool(blocklist_hit)
            if blocklist_hit:
                details["blocklist_source"] = blocklist_hit.source
                score += 0.6

        if message_text:
            msg_analysis = analyze_message(message_text)
            details["message_analysis"] = msg_analysis
            score += msg_analysis["urgency_score"] * 0.5

        score = min(score, 1.0)

        if details.get("blocklist_hit"):
            score = max(score, 0.9)

        if score >= 0.7:
            verdict = Verdict.high_risk
        elif score >= 0.3:
            verdict = Verdict.suspicious
        else:
            verdict = Verdict.safe

        entry.details = details
        entry.risk_score = round(score, 2)
        entry.verdict = verdict
        db.commit()

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.refresh_blocklist",
    bind=True,
    autoretry_for=(requests.exceptions.RequestException,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def refresh_blocklist(self):
    db = SessionLocal()
    try:
        resp = requests.get("https://openphish.com/feed.txt", timeout=30)
        resp.raise_for_status()
        urls = [line.strip() for line in resp.text.splitlines() if line.strip()]

        added = 0
        for url in urls:
            exists = db.query(BlocklistEntry).filter(BlocklistEntry.url == url).first()
            if not exists:
                db.add(BlocklistEntry(url=url, source="openphish"))
                added += 1

        db.commit()
        return {"total_fetched": len(urls), "new_added": added}

    except requests.exceptions.RequestException:
        raise
    finally:
        db.close()