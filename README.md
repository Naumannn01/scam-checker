# Scam Checker

Paste a URL, UPI ID, or phone number before you trust it. Scam Checker runs live threat-intelligence checks and returns a clear, explained risk verdict — not a black-box score.

**Stay alert. Stay safe.**

## What it does

- Paste a link, UPI ID, or phone number, optionally with an accompanying message (e.g. an SMS or WhatsApp text)
- Get back a verdict — **Safe**, **Suspicious**, or **High risk** — with a plain-language breakdown of *why*
- Every check runs asynchronously against multiple independent signals, combined into a single risk score

## How it decides

For URLs:
- **WHOIS lookup** — domain age and registration data; missing/unavailable WHOIS data is itself treated as a risk signal
- **Suspicious TLD detection** — flags free, abuse-prone TLDs (`.tk`, `.ml`, `.ga`, `.cf`, `.gq`)
- **Payment-keyword matching** — domain names containing terms like "verify", "kyc", "refund", "otp"
- **Live blocklist cross-reference** — checked against OpenPhish's real-time phishing feed, refreshed automatically every 6 hours, plus a community-reported blocklist fed by user submissions after moderation review
- **Exact host matching** — avoids false positives from naive substring matching (e.g. correctly distinguishes `google.com` from an unrelated phishing page hosted at `sites.google.com/...`)

For any accompanying message text:
- **Urgency/pressure-tactic detection** — VADER sentiment analysis plus custom rules for scam-pattern keywords, excessive capitalization, and exclamation-mark spam

A confirmed blocklist match is treated as authoritative — it can't be diluted by weaker signals pointing the other way.

## Community reporting

Anyone can report a suspicious URL, UPI ID, or phone number. Reports are held for admin review before they're trusted — approved reports feed directly into the same blocklist used for live scoring, so the system improves from real user reports over time.

## Tech stack

**Backend**
- FastAPI
- Celery + Redis — async background scoring so a slow WHOIS lookup never blocks the API response
- PostgreSQL — caches checked entries and the live blocklist
- Alembic — database migrations
- VADER (`vaderSentiment`) — message urgency/sentiment analysis
- `slowapi` — rate limiting

**Frontend**
- React + Vite
- Tailwind CSS v4
- Live polling UI — since scoring runs asynchronously, the frontend polls for the result and shows a loading state until the verdict is ready

## Architecture