import os
import time
from pathlib import Path

import requests
import yaml

from src.shared.discord import send_discord_message, send_job_alert
from src.shared.scoring import calculate_score, detect_source
from src.shared.storage import load_seen, save_seen


CONFIG_PATH = Path("config/jobs.yml")
SEEN_PATH = "data/seen_jobs.json"

SERPAPI_URL = "https://serpapi.com/search.json"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def search_serpapi(query: str, max_results: int, api_key: str) -> list[dict]:
    response = requests.get(
        SERPAPI_URL,
        params={
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": max_results,
            "hl": "pt-br",
            "gl": "br",
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    jobs = []

    for item in data.get("organic_results", []):
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        snippet = item.get("snippet", "").strip()

        if not link:
            continue

        jobs.append(
            {
                "title": title,
                "link": link,
                "snippet": snippet,
            }
        )

    return jobs


def main() -> None:
    serpapi_key = os.environ["SERPAPI_KEY"]
    discord_webhook_jobs = os.environ["DISCORD_WEBHOOK_SKYLER_JOBS"]

    config = load_config()
    seen_urls = load_seen(SEEN_PATH)
    run_seen_urls = set()

    min_score = int(config.get("min_score", 4))
    max_results_per_query = int(config.get("max_results_per_query", 10))
    max_alerts_per_run = int(config.get("max_alerts_per_run", 15))
    delay_seconds = int(config.get("search_delay_seconds", 2))

    alerts = []

    for query in config.get("queries", []):
        print(f"Searching query: {query}")

        try:
            results = search_serpapi(
                query=query,
                max_results=max_results_per_query,
                api_key=serpapi_key,
            )
        except Exception as error:
            print(f"Search error: {error}")
            continue

        for job in results:
            link = job["link"]

            if link in seen_urls or link in run_seen_urls:
                continue

            score, matched_positive, matched_negative = calculate_score(
                title=job["title"],
                snippet=job["snippet"],
                link=job["link"],
                config=config,
            )

            if score >= min_score:
                job["score"] = score
                job["matched_keywords"] = matched_positive
                job["source"] = detect_source(link)
                alerts.append(job)
                run_seen_urls.add(link)

        time.sleep(delay_seconds)

    alerts = sorted(alerts, key=lambda item: item["score"], reverse=True)
    alerts = alerts[:max_alerts_per_run]

    if not alerts:
        print("No new matching jobs found.")
        save_seen(SEEN_PATH, seen_urls)
        return

    for job in alerts:
        try:
            send_job_alert(
                webhook_url=discord_webhook_jobs,
                title=job["title"],
                link=job["link"],
                snippet=job["snippet"],
                source=job["source"],
                score=job["score"],
                matched_keywords=job["matched_keywords"],
            )

            seen_urls.add(job["link"])
            time.sleep(1)

        except Exception as error:
            print(f"Discord send error: {error}")

    save_seen(SEEN_PATH, seen_urls)

    summary = f"✅ Skyler Jobs Radar finalizou. {len(alerts)} nova(s) vaga(s) enviada(s)."

    try:
        send_discord_message(
            webhook_url=discord_webhook_jobs,
            content=summary,
        )
    except Exception as error:
        print(f"Summary send error: {error}")

    print(summary)


if __name__ == "__main__":
    main()
