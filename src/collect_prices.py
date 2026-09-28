import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import requests

def _raise_for_status_with_body(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        # Include response body to make debugging API entitlement/schema issues easier.
        # Avoid printing secrets: we never log headers.
        body = (response.text or "").strip()
        if len(body) > 2000:
            body = body[:2000] + "..."
        raise requests.HTTPError(
            f"{exc} (status={response.status_code}) body={body}",
            response=response,
        ) from None

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None
ENDPOINT_PATH = "/v1/commercial/flightavailability/get"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _normalize_cabin(value: str) -> str:
    """Map friendly cabin values to SIA cabinClass codes.

    SIA Flight Availability docs indicate cabinClass values like: Y, J, F, S.
    """

    value = (value or "").strip().upper()

    mapping = {
        "ECONOMY": "Y",
        "PREMIUM_ECONOMY": "S",
        "PREMIUM ECONOMY": "S",
        "BUSINESS": "J",
        "FIRST": "F",
        "SUITES": "F",
    }

    return mapping.get(value, value)


def main() -> None:
    if load_dotenv is not None:
        load_dotenv()

    base_url = _require_env("SIA_API_BASE_URL").rstrip("/")
    api_key = _require_env("SIA_API_KEY")

    searches_path = Path("config/searches.json")
    searches = json.loads(searches_path.read_text(encoding="utf-8-sig"))

    collected_at = datetime.now(timezone.utc).isoformat()
    records = []

    for search in searches:
        cabin_class = _normalize_cabin(str(search.get("cabin", "Y")))

        start_days_from_now = int(search.get("start_days_from_now", 0))
        next_days = int(search.get("next_days", 0))

        if next_days > 0:
            # Rolling window search: one request per day.
            base_date = datetime.now(timezone.utc).date()
            departure_dates = [
                (base_date.fromordinal(base_date.toordinal() + start_days_from_now + offset)).isoformat()
                for offset in range(next_days)
            ]
        else:
            # Single fixed date search.
            departure_dates = [search["departure_date"]]

        for departure_date in departure_dates:
            request_payload: dict = {
                "clientUUID": str(uuid4()),
                "request": {
                    "itineraryDetails": [
                        {
                            "originAirportCode": search["origin"],
                            "destinationAirportCode": search["destination"],
                            "departureDate": departure_date,
                        }
                    ],
                    "cabinClass": cabin_class,
                    "adultCount": int(search.get("adults", 1)),
                },
            }

            one_way = bool(search.get("one_way", False))
            if (not one_way) and search.get("return_date"):
                request_payload["request"]["itineraryDetails"][0]["returnDate"] = search["return_date"]

            response = requests.post(
                f"{base_url}{ENDPOINT_PATH}",
                headers={
                    "Content-Type": "application/json",
                    "apikey": api_key,
                },
                json=request_payload,
                timeout=60,
            )
            _raise_for_status_with_body(response)

            records.append(
                {
                    "collected_at": collected_at,
                    "search": search,
                    "request": request_payload,
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

