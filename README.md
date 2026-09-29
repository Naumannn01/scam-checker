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

The Scam Checker follows an asynchronous processing architecture using FastAPI, Celery, and a frontend polling mechanism.

```text
User submits a check
        │
        ▼
FastAPI creates a database row
        │
        │  verdict: "unknown"
        ▼
Celery processes the task in the background
        │
        ├── WHOIS Lookup
        │     ├── Domain age analysis
        │     ├── TLD scoring
        │     └── Keyword scoring
        │
        ├── Blocklist Cross-Reference
        │     └── Exact host match
        │
        ├── Message Analysis (if provided)
        │     └── Urgency / Sentiment analysis
        │
        ▼
Combine all signals
        │
        ▼
Calculate final risk score
        │
        ▼
Generate final verdict
        │
        ▼
Frontend polls GET /check/{id}
        │
        ▼
Display the final result
```

A separate Celery Beat schedule refreshes the OpenPhish blocklist every 6 hours, with automatic retry and exponential backoff on transient network failures.

## API overview

| Endpoint | Description |
|---|---|
| `POST /check` | Submit a URL, UPI ID, or phone number for scoring |
| `GET /check/{id}` | Get the result of a check |
| `POST /check/{id}/recheck` | Force a fresh re-score of an existing entry |
| `GET /check/history` | List past checks, filterable by verdict, input type, and score range |
| `POST /report` | Publicly submit a report for a suspected scam |
| `GET /report/pending` | *(admin)* List reports awaiting review |
| `POST /report/{id}/approve` | *(admin)* Approve a report — adds it to the live blocklist |
| `POST /report/{id}/reject` | *(admin)* Reject a report |

`POST /check` is rate-limited to 10 requests per minute per IP. Admin endpoints require an `X-Admin-Key` header.

## Running it locally

**Backend:**
```bash
docker-compose up -d          # Postgres + Redis
python -m venv venv
venv\Scripts\activate         # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

In a separate terminal:
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`.

## Roadmap

- [ ] UPI ID and phone number scoring (pending dedicated research/data)
- [ ] Automated test suite (backend + frontend)
- [ ] Input validation hardening
- [ ] Production deployment

## Motivation

Built as a step toward real-time, citizen-level cyber incident response tooling — the kind of infrastructure that's largely missing for everyday scam and phishing threats in India today.
