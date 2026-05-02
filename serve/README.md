# Canary Inference Service

Modal-deployed FastAPI behind the dashboard's `/scan` page. Loads MiniLM and
all 5 cohort autoencoders into one container; POST a 10-K and get back where
its MD&A would rank in each cohort's reconstruction-error distribution.

## Deploy

One-time Modal setup (free tier; no credit card required):

```bash
.venv/bin/pip install modal
.venv/bin/python -m modal token new
```

Then from the canary repo root:

```bash
.venv/bin/python -m modal deploy serve/modal_app.py
```

Output ends with two URLs (one per endpoint). Copy the `score` URL — it looks
like:

```
https://<your-username>--canary-inference-score.modal.run
```

Drop it into `dashboard/.env.local`:

```
NEXT_PUBLIC_CANARY_API=https://<your-username>--canary-inference-score.modal.run
```

Rebuild the dashboard:

```bash
cd dashboard
npm run build
```

That's it.

## Local test (before deploying)

```bash
.venv/bin/python -m modal serve serve/modal_app.py
# → prints a temporary URL while you have the process running
curl -X POST https://<temp-url>/ -H 'content-type: application/json' \
     -d '{"text":"Management discusses revenue. Our liquidity is strong. ..."}'
```

## What the endpoint does

1. Decodes the upload (base64 file or raw text).
2. Runs the same MD&A parser the academic pipeline used (multi-strategy
   `engine/parsing.py`). If the input has no Item 7 boundary, falls back to
   treating the whole thing as MD&A text.
3. Sentence-tokenizes (drops fragments < 20 chars, mostly-digit lines).
4. Embeds with `sentence-transformers/all-MiniLM-L6-v2`.
5. Scores against each of the 5 cohort autoencoders.
6. For each cohort, computes the rank the input would hold if added —
   compared against the cached `scores.csv` from the academic run.

This is **not** a fraud detector. The output answers a narrow question:
"how anomalous does this MD&A look against five different industry-and-year
peer baselines?" — nothing more.

## Cost

- Free tier covers ~$30/month of compute.
- Each scan takes 2-10 seconds of CPU time + cold-start (~10-20s).
- Container scales to zero after 5 minutes idle.
- Practical cost for portfolio traffic: **$0**.
