import json
from pathlib import Path


def load_seen(path: str) -> set[str]:
    file_path = Path(path)

    if not file_path.exists():
        return set()

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data.get("seen_urls", []))


def save_seen(path: str, seen_urls: set[str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            {"seen_urls": sorted(seen_urls)},
            file,
            ensure_ascii=False,
            indent=2,
        )
