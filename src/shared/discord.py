import time
import requests


def send_discord_message(webhook_url: str, content: str | None = None, embeds: list[dict] | None = None) -> None:
    payload = {}

    if content:
        payload["content"] = content[:1900]

    if embeds:
        payload["embeds"] = embeds

    response = requests.post(webhook_url, json=payload, timeout=30)

    if response.status_code == 429:
        retry_after = response.json().get("retry_after", 2)
        time.sleep(float(retry_after))

        response = requests.post(webhook_url, json=payload, timeout=30)

    response.raise_for_status()


def send_job_alert(
    webhook_url: str,
    title: str,
    link: str,
    snippet: str,
    source: str,
    score: int,
    matched_keywords: list[str],
) -> None:
    color = 0x2ECC71 if score >= 8 else 0x3498DB

    keywords_text = ", ".join(matched_keywords[:12]) if matched_keywords else "Sem palavras-chave identificadas"

    embed = {
        "title": title[:250] or "Vaga encontrada",
        "url": link,
        "description": snippet[:900] or "Sem descrição disponível.",
        "color": color,
        "fields": [
            {
                "name": "Fonte",
                "value": source,
                "inline": True,
            },
            {
                "name": "Score",
                "value": str(score),
                "inline": True,
            },
            {
                "name": "Palavras encontradas",
                "value": keywords_text[:1000],
                "inline": False,
            },
        ],
        "footer": {
            "text": "Skyler Jobs Radar"
        },
    }

    send_discord_message(
        webhook_url=webhook_url,
        content="🚨 Nova vaga encontrada",
        embeds=[embed],
    )
