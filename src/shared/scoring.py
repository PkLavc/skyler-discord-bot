import re
import unicodedata


def normalize_text(value: str) -> str:
    value = value or ""
    value = value.lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def detect_source(link: str) -> str:
    link = normalize_text(link)

    if "linkedin.com" in link:
        return "LinkedIn"

    if "gupy.io" in link:
        return "Gupy"

    if "catho.com.br" in link:
        return "Catho"

    return "Outro"


def calculate_score(title: str, snippet: str, link: str, config: dict) -> tuple[int, list[str], list[str]]:
    text = normalize_text(f"{title} {snippet} {link}")

    matched_negative = []

    for keyword in config.get("negative_keywords", []):
        normalized_keyword = normalize_text(keyword)

        if normalized_keyword and normalized_keyword in text:
            matched_negative.append(keyword)

    if matched_negative:
        return -999, [], matched_negative

    score = 0
    matched_positive = []

    for keyword in config.get("positive_keywords", []):
        normalized_keyword = normalize_text(keyword)

        if normalized_keyword and normalized_keyword in text:
            score += 1
            matched_positive.append(keyword)

    return score, matched_positive, matched_negative
