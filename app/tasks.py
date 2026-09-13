import whois
from datetime import datetime, timezone
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import CheckedEntry, Verdict, InputType
import requests
from app.models import BlocklistEntry
from app.nlp import analyze_message

def extract_domain(url: str) -> str:
    """Strip protocol/path to get bare domain for WHOIS lookup."""
    domain = url.strip()
    domain = domain.replace("http://", "").replace("https://", "")
    domain = domain.split("/")[0]
    domain = domain.split(":")[0]  # strip port if present
    return domain


@celery_app.task(name="app.tasks.check_domain_whois")
def check_domain_whois(entry_id: int):

    db = SessionLocal()
    try:
        entry = db.query(CheckedEntry).filter(CheckedEntry.id == entry_id).first()
        if not entry:
            return

        domain = extract_domain(entry.input_value)
        details = dict(entry.details or {})

        try:
            w = whois.whois(domain)
            creation_date = w.creation_date

            # whois can return a list if multiple records exist
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
            

            # check against cached blocklist
            blocklist_hit = db.query(BlocklistEntry).filter(BlocklistEntry.url.ilike(f"%{domain}%")).first()
            details["blocklist_hit"] = bool(blocklist_hit)
            if blocklist_hit:
                details["blocklist_source"] = blocklist_hit.source

        except Exception as e:
            details["whois_error"] = str(e)
            details["domain_age_days"] = None

        # basic scoring logic for now — will expand in later steps
        score = 0.0
        payment_keywords = ["paytm", "upi", "refund", "verify", "kyc", "bank", "otp"]
        domain_lower = domain.lower()

        if details.get("blocklist_hit"):
            score += 0.6  # strong signal — known phishing site

        if details.get("domain_age_days") is not None:
            if details["domain_age_days"] < 30:
                score += 0.5
            elif details["domain_age_days"] < 90:
                score += 0.2
        else:
            # missing WHOIS data is itself a signal — privacy-guarded or
            # unregistered-looking domains are disproportionately used in scams
            score += 0.25

        if any(kw in domain_lower for kw in payment_keywords):
            score += 0.3

        if details.get("domain_age_days") is not None and details["domain_age_days"] < 30 and any(kw in domain_lower for kw in payment_keywords):
            score += 0.2  # combo bonus

        # known-abuse TLDs — free/low-cost TLDs disproportionately used in phishing
        suspicious_tlds = [".tk", ".ml", ".ga", ".cf", ".gq"]
        if any(domain_lower.endswith(tld) for tld in suspicious_tlds):
            score += 0.15

        score = min(score, 1.0)

        # blocklist hit is authoritative — a confirmed phishing URL is high risk
        # regardless of what other heuristics say
        if details.get("blocklist_hit"):
            score = max(score, 0.9)

        if score >= 0.7:
            verdict = Verdict.high_risk
        elif score >= 0.3:
            verdict = Verdict.suspicious
        else:
            verdict = Verdict.safe

        if score >= 0.7:
            verdict = Verdict.high_risk
        elif score >= 0.3:
            verdict = Verdict.suspicious
        else:
            verdict = Verdict.safe

        entry.details = details
        entry.risk_score = score
        entry.verdict = verdict
        db.commit()

    finally:
        db.close()


@celery_app.task(name="app.tasks.refresh_blocklist")
def refresh_blocklist():
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

    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

        
@celery_app.task(name="app.tasks.check_domain_whois")
def check_domain_whois(entry_id: int, message_text: str = None):
    db = SessionLocal()
    try:
        entry = db.query(CheckedEntry).filter(CheckedEntry.id == entry_id).first()
        if not entry:
            return

        details = dict(entry.details or {})
        score = 0.0

        # --- URL enrichment (only for url type) ---
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

            blocklist_hit = db.query(BlocklistEntry).filter(
                BlocklistEntry.url.ilike(f"%{domain}%")
            ).first()
            details["blocklist_hit"] = bool(blocklist_hit)
            if blocklist_hit:
                details["blocklist_source"] = blocklist_hit.source
                score += 0.6

        # --- Message urgency/sentiment (any input type) ---
        if message_text:
            msg_analysis = analyze_message(message_text)
            details["message_analysis"] = msg_analysis
            score += msg_analysis["urgency_score"] * 0.5  # weighted contribution

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