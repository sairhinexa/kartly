# Kartly

Kartly is a realistic online marketplace — product catalogue, user accounts,
reviews, seller tools, a shopping cart and checkout, invoices and an API. Your
job is to **assess it like a real target**: explore every feature, map the
attack surface, and see what you can get it to do that it shouldn't.

There are no hints, no checklist and no labels. Treat it exactly like an
unfamiliar application you've been asked to security-test.

> ⚠️ **This application is a security-training target and contains intentional
> weaknesses.** Run it only on your own machine (localhost) or an isolated lab
> network. **Never expose it to the internet.** By default it binds to
> `127.0.0.1` only.

## Install & run

All methods serve the app at <http://127.0.0.1:5000/>.

**Docker (simplest):**
```bash
docker compose up --build
```
or:
```bash
docker build -t kartly . && docker run --rm -p 127.0.0.1:5000:5000 kartly
```

**One command, no Docker:**
- Windows: double-click **`run.bat`**
- macOS / Linux: `./run.sh`

**Manual:**
```bash
pip install -r requirements.txt
python app.py
```

Requires Python 3.10+ (3.12 recommended). Each start rebuilds a fresh database,
so **restarting resets everything** — a clean slate whenever you want one.
Optional environment variables: `KARTLY_HOST`, `KARTLY_PORT`.

## Starter accounts

You can register your own account, or use one of these shopper logins to begin:

- `wiener / peter`
- `carlos / montoya`

## Rules of engagement

- **Scope:** only the Kartly app you are running locally. Nothing else.
- Use a browser plus an intercepting proxy (e.g. Burp Suite / OWASP ZAP).
- Work at a normal pace. Do not attempt denial-of-service.
- Keep **proof** of anything you find (request/response, screenshot, or the
  value you recovered) and notes on the exact steps to reproduce it.

Good hunting.
