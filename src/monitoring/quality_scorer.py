# src/monitoring/quality_scorer.py
# Answer quality evlonnu score panrom
# Sentiment - positive/negative/neutral detect panrom

from textblob import TextBlob


def analyze_sentiment(text: str) -> dict:
    """
    # User query-oda sentiment detect panrom
    # Frustrated user kekirana vs happy user kekirananu theriyum
    #
    # TextBlob polarity: -1 (very negative) to +1 (very positive)
    # Udharanam:
    # "This is terrible!" → negative
    # "Great service!"    → positive
    # "What is policy?"   → neutral
    """

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1

    # Label assign pannu
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {
        "sentiment_label": label,
        "sentiment_score": round(polarity, 3)
    }


def calculate_quality_score(answer: str,
                            has_citation: bool,
                            num_sources: int) -> float:
    """
    # Answer quality 0-1 scale-la score panrom
    #
    # Factors:
    # 1. Citation irukka? (+0.3)
    # 2. Answer length reasonable-ah irukka? (+0.3)
    # 3. Sources use pannangala? (+0.2)
    # 4. "cannot find" sollalaiya? (+0.2)
    """

    score = 0.0

    # Factor 1: Citation check (+0.3)
    if has_citation:
        score += 0.3

    # Factor 2: Answer length check (+0.3)
    # Too short = bad, Too long = OK, Good length = best
    answer_words = len(answer.split())
    if answer_words >= 20:
        score += 0.3
    elif answer_words >= 10:
        score += 0.15

    # Factor 3: Sources used (+0.2)
    if num_sources >= 3:
        score += 0.2
    elif num_sources >= 1:
        score += 0.1

    # Factor 4: Not a fallback answer (+0.2)
    # "cannot find" = poor retrieval
    fallback_phrases = ["cannot find", "not found", "no information"]
    has_fallback = any(phrase in answer.lower() for phrase in fallback_phrases)
    if not has_fallback:
        score += 0.2

    return round(min(score, 1.0), 3)  # Maximum 1.0