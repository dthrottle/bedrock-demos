# Bedrock Demos / Amazon Comprehend

This folder contains a simple local FastAPI application demonstrating multiple Amazon Comprehend synchronous features.

Features Included:
- Sentiment
- Entity Recognition
- Key Phrases
- Syntax (summarized)
- Dominant Language
- PII Entities
- Targeted Sentiment
- Lightweight derived "categories" (entity type counts, key phrase length buckets, POS tag distribution) to satisfy the spec without asynchronous jobs.

Not Included:
- Asynchronous topic modeling or custom classification jobs (would require S3 + more setup).
- Export, persistence, or authentication (intentionally omitted per spec).

## Prerequisites
- Python 3.11+ recommended
- AWS credentials configured locally. Use the desired `AWS_PROFILE`.

## Install & Run
1. (One-time) Create virtual env & install deps:
```
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
```
2. Copy the provided `.env` (edit values as needed):
```
cp .env .env.local  # optional if you prefer a separate file you gitignore
```
Edit `.env` (or `.env.local`) to set at least `AWS_PROFILE` (export in your shell) and optionally `AWS_REGION`, `CHAR_LIMIT`, etc.

3. Ensure your AWS credentials/profile is configured (e.g. in `~/.aws/credentials`). You can export the profile for the shell session:
```
export AWS_PROFILE=your_profile_name
```
4. Run the app:
```
python -m app.main
```
Then open: http://127.0.0.1:8000 (or the host/port you configured in `.env`).

Environment variables recognized:
- `AWS_REGION` – overrides region for Comprehend client (falls back to default AWS resolution chain if unset).
- `CHAR_LIMIT` – overrides default 2000 character limit.
- `APP_HOST` / `APP_PORT` – uvicorn host & port (defaults 127.0.0.1:8000).
- `LOG_LEVEL` – logging level (INFO, DEBUG, etc.).

## Notes
- Input limited to 2000 characters client + server side.
- English (en) is assumed for most calls to keep implementation simple.
- Minimal error handling/logging by design; failures of individual Comprehend calls won't crash the page.
- Targeted sentiment and PII can increase latency; keep sample text moderate.

## Example Text
```
I loved the new phone I bought last week, but the battery life is disappointing. 
Amazon's customer support was helpful. My email is example@example.com.
```

## License
MIT (feel free to adjust as needed)
# bedrock-demos