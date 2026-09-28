import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def main() -> None:
    base_url = _require_env("SIA_API_BASE_URL").rstrip("/")
    api_key = _require_env("SIA_API_KEY")

    searches_path = Path("config/searches.json")
    searches = json.loads(searches_path.read_text(encoding="utf-8-sig"))

    collected_at = datetime.now(timezone.utc).isoformat()
    records = []

    for search in searches:
        response = requests.post(
            f"{base_url}/YOUR_FLIGHT_SEARCH_ENDPOINT",
            headers={
                "Content-Type": "application/json",
                "apikey": api_key,
            },
            json={
                # Replace these fields with the exact SIA API request schema.
                "origin": search["origin"],
                "destination": search["destination"],
                "departureDate": search["departure_date"],
                "returnDate": search.get("return_date"),
                "cabin": search["cabin"],
                "adults": search["adults"],
            },
            timeout=60,
        )
        response.raise_for_status()

        records.append(
            {
                "collected_at": collected_at,
                "search": search,
                "response": response.json(),
            }
        )

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    output = data_dir / f"prices-{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
    with output.open("a", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()

