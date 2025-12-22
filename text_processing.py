from collections import Counter
import re

# ---------- CLEAN TEXT ----------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    return text


# ---------- EXTRACT KEY PHRASES ----------
def extract_keywords(text):
    words = text.split()
    phrases = []

    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        if len(w1) > 3 and len(w2) > 3:
            phrases.append(f"{w1} {w2}")

    freq = Counter(phrases)
    return [p for p, _ in freq.most_common(10)]


# ---------- SMART MAIN TOPIC DETECTION ----------
def detect_main_topic(text, keywords):
    """
    Detect main topic using:
    1. Heading-like phrases
    2. Domain keywords
    3. Frequency fallback
    """

    # 1️⃣ Heading-style detection (short & strong)
    for phrase in keywords:
        if len(phrase.split()) <= 2:
            if any(word in phrase for word in ["ethic", "justice", "behavior", "learning", "system"]):
                return phrase.title()

    # 2️⃣ Domain-aware detection
    DOMAIN_TOPICS = [
        "ethics",
        "ethical behavior",
        "justice",
        "machine learning",
        "data science",
        "artificial intelligence"
    ]

    text_lower = text.lower()
    for topic in DOMAIN_TOPICS:
        if topic in text_lower:
            return topic.title()

    # 3️⃣ Fallback: most frequent phrase
    if keywords:
        return keywords[0].title()

    return "Main Topic"
