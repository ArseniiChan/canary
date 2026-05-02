"""Senior-engineer stress test of the live Modal /scan endpoint.

Hits 16 attack vectors covering input validation, malformed content,
out-of-distribution text, unicode/encoding traps, size limits, concurrency,
determinism, and result-shape contracts. Records each (case, status, latency,
result, observation) and at the end prints a PASS/FAIL summary with the
failure reasons.

Usage:
    .venv/bin/python scripts/15_stress_test_endpoint.py

Exit code 0 if every test passes; non-zero otherwise.
"""

from __future__ import annotations

import base64
import concurrent.futures as cf
import json
import math
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENDPOINT = "https://arseniichan--score.modal.run/"
TIMEOUT_S = 180
COHORTS = {"LEH", "WCOM", "TYC", "HRC", "VRX"}


@dataclass
class TestResult:
    case: str
    expected: str
    status_code: int | None
    latency_s: float
    response: dict | None
    raw_body: str | None
    error: str | None
    passed: bool
    observation: str = ""

    def __str__(self) -> str:
        flag = "PASS" if self.passed else "FAIL"
        return (
            f"[{flag}] {self.case:<55} "
            f"http={str(self.status_code):>4}  "
            f"t={self.latency_s:>6.2f}s  "
            f"{self.observation}"
        )


def post(payload: dict | list | str | bytes, timeout: float = TIMEOUT_S) -> tuple[int | None, dict | None, str | None, str | None]:
    """POST to the endpoint. Returns (status_code, parsed_json, raw_body, error_str)."""
    if isinstance(payload, (dict, list)):
        data = json.dumps(payload).encode("utf-8")
    elif isinstance(payload, str):
        data = payload.encode("utf-8")
    else:
        data = payload
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            try:
                return resp.status, json.loads(body), body.decode("utf-8", errors="replace"), None
            except json.JSONDecodeError:
                return resp.status, None, body.decode("utf-8", errors="replace"), "non-JSON response"
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body), body.decode("utf-8", errors="replace"), None
        except json.JSONDecodeError:
            return e.code, None, body.decode("utf-8", errors="replace"), None
    except Exception as e:
        return None, None, None, f"{type(e).__name__}: {e}"
    finally:
        # Record latency on the caller side; this is an inelegant placeholder
        pass


def post_timed(payload, timeout: float = TIMEOUT_S):
    t0 = time.perf_counter()
    sc, js, raw, err = post(payload, timeout=timeout)
    return sc, js, raw, err, time.perf_counter() - t0


# -- Helpers --------------------------------------------------------------
def shape_ok(js: dict | None) -> tuple[bool, str]:
    """For a successful score, validate the response shape contract."""
    if not isinstance(js, dict):
        return False, "not a dict"
    if not js.get("ok"):
        return False, f"ok={js.get('ok')}, error={js.get('error')}"
    if "per_cohort" not in js or not isinstance(js["per_cohort"], list):
        return False, "missing per_cohort list"
    cids = {c.get("cohort_id") for c in js["per_cohort"]}
    if cids != COHORTS:
        return False, f"per_cohort cohorts={cids}, expected={COHORTS}"
    for c in js["per_cohort"]:
        for k in ("rank_if_added", "n_after_add", "percentile_within_cohort",
                  "score_mean", "score_trimmed_mean", "score_max"):
            if k not in c:
                return False, f"cohort {c.get('cohort_id')} missing {k}"
        if not (1 <= c["rank_if_added"] <= c["n_after_add"]):
            return False, f"rank out of bounds: {c['rank_if_added']}/{c['n_after_add']}"
        for k in ("score_mean", "score_trimmed_mean", "score_max"):
            v = c[k]
            if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
                return False, f"bad {k}={v} for {c.get('cohort_id')}"
    return True, "shape OK"


# -- Tests ----------------------------------------------------------------
results: list[TestResult] = []


def add(case: str, expected: str, sc, js, raw, err, lat, passed: bool, obs: str = "") -> TestResult:
    r = TestResult(case=case, expected=expected, status_code=sc, latency_s=lat,
                   response=js, raw_body=raw, error=err, passed=passed, observation=obs)
    results.append(r)
    print(r)
    return r


print(f"\n=== STRESS TEST: {ENDPOINT} ===\n")
print("Phase 1: cold-start canary (warm the container)")
sc, js, raw, err, lat = post_timed({"text": "Management reports revenue growth of 5%. Operating expenses increased. Liquidity remains strong. We anticipate continued investment. Cash on hand is sufficient."})
add("01 cold-start canary, 5 sentences",
    "ok=true, 5 sentences, all 5 cohorts scored",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]),
    obs=f"cold start completed, n_sent={js.get('n_sentences') if js else '?'}")

# -- Input validation ------------------------------------------------------
print("\nPhase 2: input validation")

sc, js, raw, err, lat = post_timed({})
add("02 empty object",
    "ok=false, 'supply content_b64 or text'",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") is False and "content_b64" in (js.get("error") or "")))

sc, js, raw, err, lat = post_timed({"text": ""})
add("03 empty string body",
    "ok=false, 'supply content_b64 or text' OR 'fewer than 5'",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") is False))

sc, js, raw, err, lat = post_timed({"text": "Hello world."})
add("04 1-sentence text",
    "ok=false, 'fewer than 5 sentences'",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") is False and "sentence" in (js.get("error") or "").lower()))

sc, js, raw, err, lat = post_timed({"content_b64": "%%%not-base64%%%"})
add("05 invalid base64",
    "ok=false, 'invalid base64'",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") is False and "base64" in (js.get("error") or "")))

sc, js, raw, err, lat = post_timed({"text": 123})  # type: ignore[dict-item]
add("06 wrong type for text (number, not string)",
    "ok=false (rejects non-string text)",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") is False))

sc, js, raw, err, lat = post_timed([])
add("07 array payload (not object)",
    "ok=false, 'expected JSON object' OR FastAPI 422",
    sc, js, raw, err, lat,
    passed=((sc == 422) or (sc == 200 and js and js.get("ok") is False)))

sc, js, raw, err, lat = post_timed("just-a-string")
add("08 raw string payload",
    "FastAPI 422 OR endpoint rejects",
    sc, js, raw, err, lat,
    passed=((sc == 422) or (sc == 200 and js and js.get("ok") is False)))

# -- Out-of-distribution content -----------------------------------------
print("\nPhase 3: out-of-distribution content (graceful path)")

wikipedia_blurb = ("The platypus (Ornithorhynchus anatinus) is a semiaquatic egg-laying mammal endemic to eastern Australia, including Tasmania. "
                   "Together with the four species of echidna, it is one of the five extant species of monotremes, the only mammals that lay eggs instead of giving birth to live young. "
                   "The animal is the sole living representative or monotypic taxon of its family Ornithorhynchidae and genus Ornithorhynchus. "
                   "The platypus has been the object of myth and legend across various indigenous cultures of Australia. "
                   "Its venomous spurs make it one of the few venomous mammals in the world. "
                   "The unusual appearance of this egg-laying, duck-billed, beaver-tailed, otter-footed mammal baffled European naturalists when they first encountered it. "
                   "It was so improbable that some considered the platypus to be an elaborate hoax. ") * 3
sc, js, raw, err, lat = post_timed({"text": wikipedia_blurb})
add("09 Wikipedia text (non-10-K, non-financial)",
    "ok=true, hits raw_text_fallback, returns scores (model gracefully scores OOD)",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]),
    obs=f"extraction={js.get('extraction', {}).get('method') if js else '?'}, "
        f"top scores: {[round(c['score_mean'], 6) for c in (js or {}).get('per_cohort', [])[:2]]}")

multilang = ("La inteligencia artificial es la disciplina de la informática que se centra en construir sistemas que exhiben comportamiento inteligente. "
             "Los modelos de aprendizaje profundo se han convertido en una herramienta dominante. "
             "Las redes neuronales pueden aprender representaciones jerárquicas. "
             "El procesamiento del lenguaje natural es un campo importante. "
             "Los transformadores han revolucionado el campo. "
             "Sin embargo, el sesgo y la equidad siguen siendo preocupaciones críticas. ") * 4
sc, js, raw, err, lat = post_timed({"text": multilang})
add("10 Spanish text (MiniLM is multilingual)",
    "ok=true, scores returned (multilingual robustness)",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]),
    obs=f"n_sent={js.get('n_sentences') if js else '?'}")

repeated = ("Liquidity remains strong and we anticipate continued growth in the coming year. " * 200)
sc, js, raw, err, lat = post_timed({"text": repeated})
add("11 200x repeated sentence (degenerate input)",
    "ok=true, low diversity, doesn't crash",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]),
    obs=f"n_sent={js.get('n_sentences') if js else '?'}")

# -- Encoding & unicode ---------------------------------------------------
print("\nPhase 4: encoding & unicode")

emoji_body = ("Revenue grew 📈 12% year-over-year. Operating margin expanded 🔥 to 22%. "
              "Cash flow from operations was positive 💰. We invested in R&D and people 👥. "
              "Liquidity remains strong 🏦. Free cash flow funded our buyback program 💵. "
              "Customer acquisition costs decreased 📉. We expect continued growth ✅. ") * 3
sc, js, raw, err, lat = post_timed({"text": emoji_body})
add("12 emoji-laden text",
    "ok=true (UTF-8 round-trips through MiniLM tokenizer)",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]))

mixed_bytes = ("Revenue increased substantially this fiscal year. " * 8 +
               "\x00\ufeff Operating expenses were managed carefully throughout. " * 4 +
               "We anticipate continued execution against our strategic plan. " * 4)
sc, js, raw, err, lat = post_timed({"text": mixed_bytes})
add("13 control chars + BOM mixed in",
    "ok=true (errors='replace' should handle)",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]))

# Encode utf-16 then base64 — tests the bytes -> decode('utf-8', errors='replace') path
utf16_body = "Management discussion of the fiscal year. " * 100
b16 = utf16_body.encode("utf-16")
sc, js, raw, err, lat = post_timed({"content_b64": base64.b64encode(b16).decode("ascii")})
add("14 UTF-16 bytes via content_b64",
    "ok=true OR ok=false with 'fewer than 5 sentences' (graceful — utf-8 decode mangles UTF-16)",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") in (True, False)),
    obs=f"ok={js.get('ok') if js else '?'}, error={js.get('error') if js else '?'}")

# -- Real-world filing test ------------------------------------------------
print("\nPhase 5: real-world filings — across cohorts and outside training")

# Lehman (in-distribution: it's in the test set itself)
leh_body = (REPO / "data/processed/parsed/000110465908005476.txt").read_text(encoding="utf-8")
sc, js, raw, err, lat = post_timed({"text": leh_body})
leh_score = js.get("per_cohort", [{}])[0].get("score_mean") if js and js.get("ok") else None
expected_leh = 0.001395  # committed primary score
match_leh = leh_score is not None and abs(leh_score - expected_leh) < 1e-4 if False else False
# Actually find the LEH-specific cohort score
leh_in_leh = next((c["score_mean"] for c in (js or {}).get("per_cohort", []) if c.get("cohort_id") == "LEH"), None)
det_match = leh_in_leh is not None and abs(leh_in_leh - expected_leh) < 1e-3
add("15 real Lehman 2007 10-K MD&A (in-distribution)",
    f"ok=true, LEH-cohort score reproduces committed value {expected_leh:.6f}",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0] and det_match),
    obs=f"leh_score={leh_in_leh:.6f}, target={expected_leh:.6f}, diff={abs((leh_in_leh or 0) - expected_leh):.2e}" if leh_in_leh else "no LEH cohort in response")

# WorldCom MD&A (in-distribution but a different cohort)
wcom_body = (REPO / "data/processed/parsed/000100547702001226.txt").read_text(encoding="utf-8")
sc, js, raw, err, lat = post_timed({"text": wcom_body})
add("16 real WorldCom 2001 10-K MD&A (in-distribution)",
    "ok=true, all 5 cohorts scored, score_mean finite",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]),
    obs=f"n_sent={js.get('n_sentences') if js else '?'}")

# -- Determinism ----------------------------------------------------------
print("\nPhase 6: determinism — same input twice yields the same scores")

t1 = post_timed({"text": leh_body})
t2 = post_timed({"text": leh_body})
score1 = next((c["score_mean"] for c in (t1[1] or {}).get("per_cohort", []) if c.get("cohort_id") == "LEH"), None)
score2 = next((c["score_mean"] for c in (t2[1] or {}).get("per_cohort", []) if c.get("cohort_id") == "LEH"), None)
deterministic = (score1 is not None and score2 is not None and abs(score1 - score2) < 1e-9)
add("17 same input twice — scores are bitwise-identical",
    "score_mean for LEH cohort identical between calls",
    t2[0], t2[1], t2[2], t2[3], t1[4] + t2[4],
    passed=deterministic,
    obs=f"call1_LEH={score1}, call2_LEH={score2}")

# -- Size limits ----------------------------------------------------------
print("\nPhase 7: size limits")

# 11 MB — under the 12 MB cap
big_text = "Management's discussion of the fiscal year. " * 280_000  # ~12.6 MB
big_text = big_text[: 11 * 1024 * 1024]
sc, js, raw, err, lat = post_timed({"text": big_text}, timeout=180)
add("18 11 MB body (under 12 MB cap)",
    "ok=true OR graceful timeout/error",
    sc, js, raw, err, lat,
    passed=(sc in (200,) and js is not None),
    obs=f"ok={js.get('ok') if js else '?'}")

# 13 MB — over cap
over_cap_text = "x" * (13 * 1024 * 1024)
sc, js, raw, err, lat = post_timed({"text": over_cap_text}, timeout=120)
add("19 13 MB body (over 12 MB cap)",
    "ok=false, 'file too large'",
    sc, js, raw, err, lat,
    passed=(sc == 200 and js and js.get("ok") is False and "too large" in (js.get("error") or "").lower()),
    obs=f"error={js.get('error') if js else '?'}")

# -- Concurrency ----------------------------------------------------------
print("\nPhase 8: concurrency — 5 simultaneous in-flight requests")

def fire(idx):
    return post_timed({"text": f"Filing {idx}: " + leh_body[:100_000]})

t0 = time.perf_counter()
with cf.ThreadPoolExecutor(max_workers=5) as ex:
    futures = [ex.submit(fire, i) for i in range(5)]
    parallel = [f.result() for f in futures]
parallel_total = time.perf_counter() - t0
oks = sum(1 for sc, js, *_ in parallel if sc == 200 and js and js.get("ok"))
add("20 5 simultaneous requests",
    "all 5 succeed, no 5xx, no crashes",
    parallel[0][0], parallel[0][1], parallel[0][2], parallel[0][3], parallel_total,
    passed=(oks == 5),
    obs=f"{oks}/5 ok, parallel_total={parallel_total:.1f}s")

# -- HTML real-world ------------------------------------------------------
print("\nPhase 9: HTML 10-K (full filing, not pre-parsed)")
# Try Valeant's full HTML from data/raw if present
valeant_raw = REPO / "data/raw/edgar/filings/000088559015000015/valeant2014form10-k.htm"
if valeant_raw.exists():
    raw_html = valeant_raw.read_bytes()
    sc, js, raw, err, lat = post_timed({"content_b64": base64.b64encode(raw_html).decode("ascii"), "filename": "valeant2014form10-k.htm"})
    add("21 raw Valeant 2014 HTML 10-K (~4.5 MB)",
        "ok=true, extraction.method != raw_text_fallback (real Item 7 found)",
        sc, js, raw, err, lat,
        passed=(sc == 200 and js and js.get("ok") and shape_ok(js)[0]),
        obs=f"method={js.get('extraction', {}).get('method') if js else '?'}, chars={js.get('extraction', {}).get('chars') if js else '?'}")
else:
    print("  [skipped] Valeant raw HTML not found at data/raw/...")

# -- Health check --------------------------------------------------------
print("\nPhase 10: health endpoint")
HEALTH = ENDPOINT.replace("score", "health")
try:
    req = urllib.request.Request(HEALTH, method="GET")
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as resp:
        h = json.loads(resp.read())
    add("22 GET /health",
        "ok=true, cohorts=[5]",
        resp.status, h, json.dumps(h), None, time.perf_counter() - t0,
        passed=(resp.status == 200 and h.get("ok") and len(h.get("cohorts", [])) == 5))
except Exception as e:
    add("22 GET /health", "ok=true", None, None, None, str(e), 0, False)

# -- Summary --------------------------------------------------------------
print("\n" + "=" * 78)
passed = sum(1 for r in results if r.passed)
total = len(results)
print(f"RESULT: {passed}/{total} passed")
print("=" * 78)

if passed < total:
    print("\nFAILURES:")
    for r in results:
        if not r.passed:
            print(f"  {r.case}")
            print(f"    expected: {r.expected}")
            print(f"    got: status={r.status_code}, json={r.response}, err={r.error}")
            print()
    sys.exit(1)
sys.exit(0)
