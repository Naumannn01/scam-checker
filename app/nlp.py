from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

URGENCY_KEYWORDS = [
    "urgent", "immediately", "act now", "verify now", "suspended",
    "blocked", "account will be", "final notice", "expire", "expires",
    "limited time", "click here", "confirm your", "otp", "kyc update",
    "failure to", "last warning", "unauthorized", "security alert",
]

def analyze_message(text: str) -> dict:
    text_clean = text.strip()
    vader_scores = _analyzer.polarity_scores(text_clean)

    lower = text_clean.lower()
    keyword_hits = [kw for kw in URGENCY_KEYWORDS if kw in lower]

    # excessive caps is a classic pressure-tactic signal
    letters = [c for c in text_clean if c.isalpha()]
    caps_ratio = (sum(1 for c in letters if c.isupper()) / len(letters)) if letters else 0.0

    exclamation_count = text_clean.count("!")

    urgency_score = 0.0
    urgency_score += min(len(keyword_hits) * 0.15, 0.6)
    if caps_ratio > 0.3:
        urgency_score += 0.2
    if exclamation_count >= 2:
        urgency_score += 0.2
    urgency_score = min(urgency_score, 1.0)

    return {
        "vader_compound": vader_scores["compound"],
        "urgency_keyword_hits": keyword_hits,
        "caps_ratio": round(caps_ratio, 2),
        "exclamation_count": exclamation_count,
        "urgency_score": round(urgency_score, 2),
    }