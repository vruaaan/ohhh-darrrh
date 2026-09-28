# SIA Price Tracker (Stage 1)

This repo collects raw fare data from the **official Singapore Airlines (SIA) Flight Search API** on a schedule using GitHub Actions.

Stage 1 goal: **collect and store raw responses**. No alerts, no analysis, no booking.

## What it does

- Reads searches from `config/searches.json`
- Calls the SIA Flight Search API for each search
- Appends one JSON object per search to `data/prices-YYYY-MM-DD.jsonl`

Each JSONL line contains:

- `collected_at` (UTC ISO8601)
- `search` (the search config used)
- `response` (the complete raw API JSON response)

## Configuration

### Searches

Edit `config/searches.json` to define the routes/dates you want to collect.

Example:

```json
[
  {
    "name": "Singapore to Tokyo",
    "origin": "SIN",
    "destination": "NRT",
    "departure_date": "2027-03-10",
    "return_date": "2027-03-17",
    "cabin": "ECONOMY",
    "adults": 1
  }
]
```

Important:

- Use the **exact field formats required by SIA** (date formats, cabin values, passenger counts, etc.).

### Environment variables

The collector requires:

- `SIA_API_BASE_URL` (stored as GitHub Actions secret `SIA_API_BASE_URL`)
- `SIA_API_KEY` (stored as GitHub Actions secret `SIA_API_KEY`)

Do **not** commit credentials to the repo.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export SIA_API_BASE_URL="..."
export SIA_API_KEY="..."

python src/collect_prices.py
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:SIA_API_BASE_URL = "..."
$env:SIA_API_KEY = "..."

python src/collect_prices.py
```

## GitHub Actions schedule

Workflow: `.github/workflows/collect.yml`

- Runs every 6 hours at minute 17 (UTC): `17 */6 * * *`
- Also supports manual runs via `workflow_dispatch`
- Commits newly collected `data/` files back to the repo

## Setup checklist

1. Replace `YOUR_FLIGHT_SEARCH_ENDPOINT` and request fields in `src/collect_prices.py` with the **approved** SIA API endpoint + schema.
2. Add GitHub secrets:
   - `SIA_API_BASE_URL`
   - `SIA_API_KEY`
3. In GitHub: **Settings → Actions → General → Workflow permissions**
   - Select **Read and write permissions**
4. Manually run the workflow once and confirm a file appears under `data/`.

## Notes

- Keep raw responses during Stage 1 to support later normalization (fare, taxes, itinerary, cabin, booking class, offer IDs).
- If data volume grows, consider moving storage from git-committed JSONL to SQLite/Postgres/object storage.
