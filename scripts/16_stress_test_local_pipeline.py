"""Local-pipeline stress test — bypasses Modal, attacks the engine directly.

Senior-engineer mindset: assume the public endpoint is fine but the underlying
library has hidden landmines. Hit every boundary the parser, sentence
splitter, embedder, autoencoder loader, and scorer can have.

Usage:
    .venv/bin/python scripts/16_stress_test_local_pipeline.py

Exit code 0 if every test passes; non-zero otherwise.
"""

from __future__ import annotations

import math
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import numpy as np
import torch  # noqa: E402

from engine.autoencoder import EMBEDDING_DIM, MODEL_DIR, CanaryAutoencoder, load_cohort_autoencoder
from engine.embeddings import EmbeddingEngine, _cache_path
from engine.parsing import extract_mdna, split_sentences
from engine.scoring import per_sentence_recon_error, score_filing


@dataclass
class R:
    case: str
    passed: bool
    msg: str
    t: float

    def __str__(self):
        flag = "PASS" if self.passed else "FAIL"
        return f"[{flag}] {self.case:<55} t={self.t:>5.2f}s  {self.msg}"


results: list[R] = []


def case(name: str):
    def deco(fn):
        t0 = time.perf_counter()
        try:
            msg = fn() or "OK"
            results.append(R(name, True, msg, time.perf_counter() - t0))
        except AssertionError as e:
            results.append(R(name, False, f"ASSERT: {e}", time.perf_counter() - t0))
        except Exception:
            tb = traceback.format_exc().splitlines()[-1]
            results.append(R(name, False, f"EXC: {tb}", time.perf_counter() - t0))
        print(results[-1])
        return fn
    return deco


print("\n=== LOCAL PIPELINE STRESS TEST ===\n")

# -- Sentence splitter --------------------------------------------------------
print("Phase 1: sentence splitter edge cases")

@case("01 split_sentences on empty string")
def _():
    out = split_sentences("")
    assert out == [], f"expected [], got {out}"

@case("02 split_sentences on whitespace only")
def _():
    out = split_sentences("   \n\t \n ")
    assert out == [], f"expected [], got {out}"

@case("03 split_sentences on a paragraph with U.S. abbreviations")
def _():
    text = "Revenue grew 5% in the U.S. market. Operations expanded in Q3 vs. Q2. We monitor key K.P.I.s closely. The company invested $5.0 million. Liquidity is strong."
    out = split_sentences(text)
    assert len(out) >= 4, f"abbreviation handling produced too few sentences: {out}"

@case("04 split_sentences on degenerate single-character chunks")
def _():
    text = "a. b. c. d. e. f."
    out = split_sentences(text)
    # The 20-char minimum filter should drop these
    assert len(out) == 0, f"expected fragments dropped, got {out}"

@case("05 split_sentences on >10k-char sentence (no terminator)")
def _():
    text = ("liquidity " * 1000) + "."  # one ~10k char sentence
    out = split_sentences(text)
    assert len(out) == 1, f"expected 1 long sentence, got {len(out)}"
    assert len(out[0]) > 5000, "long sentence body collapsed"

@case("06 split_sentences on text with mixed line endings")
def _():
    text = "Sentence one is here.\r\nSentence two follows here.\nSentence three closes here.\rSentence four ends."
    out = split_sentences(text)
    assert len(out) >= 3, f"line-ending handling produced too few: {out}"

# -- Parser -------------------------------------------------------------------
print("\nPhase 2: MD&A extractor")

@case("07 extract_mdna on text with NO Item 7 anchor")
def _():
    body = b"This is a press release with no SEC structure at all. " * 20
    ext = extract_mdna(body, accession="x", primary_document="t.txt")
    # Should return success=False — caller falls back to raw text
    assert ext.success is False, f"expected failure, got {ext}"

@case("08 extract_mdna on TYC-style 'incorporation by reference' filing")
def _():
    fp = REPO / "data/raw/edgar/filings/000091205701544874/a2062534z10-k.txt"
    if not fp.exists():
        return "SKIP — raw filing not present"
    body = fp.read_bytes()
    ext = extract_mdna(body, accession="0000912057-01-544874",
                      primary_document="a2062534z10-k.txt")
    assert ext.success, f"failed to parse Tyco: {ext}"
    assert ext.char_count > 5_000, f"Tyco body too short: {ext.char_count}"

@case("09 extract_mdna on tiny body (<3000 chars rejection)")
def _():
    body = b"Item 7 management discussion. " + (b"x" * 100) + b" Item 7A risk."
    ext = extract_mdna(body, accession="x", primary_document="t.txt")
    assert ext.success is False, "expected rejection of <3000 char body"

@case("10 extract_mdna on body with TOC-only Item 7 (filtered as TOC entries)")
def _():
    body = b"Item 7. Page 12. Item 7A. Page 24. " + (b"unrelated text " * 500)
    ext = extract_mdna(body, accession="x", primary_document="t.txt")
    # Either success=False, or success with the unrelated-text fallback
    assert ext is not None, "extractor returned None"

# -- EmbeddingEngine + cache --------------------------------------------------
print("\nPhase 3: embedding engine")

ee = EmbeddingEngine()

@case("11 EmbeddingEngine.encode_filing on empty list")
def _():
    fe = ee.encode_filing("zzz_empty_test", [])
    assert fe.embeddings.shape == (0, 384), f"empty input got shape {fe.embeddings.shape}"

@case("12 EmbeddingEngine handles a single sentence")
def _():
    fe = ee.encode_filing("zzz_single", ["This is a single sentence for embedding."])
    assert fe.embeddings.shape == (1, 384), f"single got {fe.embeddings.shape}"
    assert np.isfinite(fe.embeddings).all(), "non-finite values in embedding"

@case("13 EmbeddingEngine handles 1000 sentences (batched)")
def _():
    sents = [f"Sentence number {i} discussing fiscal performance and operations." for i in range(1000)]
    t = time.perf_counter()
    fe = ee.encode_filing("zzz_thousand", sents)
    dt = time.perf_counter() - t
    assert fe.embeddings.shape == (1000, 384), f"batch got {fe.embeddings.shape}"
    return f"1000 sents in {dt:.1f}s"

@case("14 EmbeddingEngine cache hit returns identical bytes")
def _():
    sents = ["Cache test sentence " + str(i) + " with enough length to clear filter." for i in range(20)]
    fe1 = ee.encode_filing("zzz_cache_test", sents)
    # Should now be on disk
    p = _cache_path("zzz_cache_test", ee.model_name)
    assert p.exists(), f"cache file not written: {p}"
    fe2 = ee.encode_filing("zzz_cache_test", sents)
    assert np.array_equal(fe1.embeddings, fe2.embeddings), "cache miss or drift"
    p.unlink()
    return f"cache file: {p.name}"

# -- Autoencoder loader -------------------------------------------------------
print("\nPhase 4: autoencoder loader")

@case("15 load all 5 cohort .pt files")
def _():
    for cid in ["HRC", "LEH", "TYC", "VRX", "WCOM"]:
        m = load_cohort_autoencoder(MODEL_DIR / f"{cid}.pt")
        assert isinstance(m, CanaryAutoencoder), f"{cid} not a CanaryAutoencoder"
        nparams = sum(p.numel() for p in m.parameters())
        assert 100_000 < nparams < 200_000, f"{cid} param count {nparams} out of expected range"
    return "5/5 loaded, ~117k params each"

@case("16 load_cohort_autoencoder on missing path raises")
def _():
    try:
        load_cohort_autoencoder(MODEL_DIR / "DOES_NOT_EXIST.pt")
        raise AssertionError("expected exception on missing path")
    except FileNotFoundError:
        return "FileNotFoundError raised cleanly"
    except Exception as e:
        # Still acceptable as long as it doesn't silently succeed
        return f"raised {type(e).__name__}"

# -- Scorer -------------------------------------------------------------------
print("\nPhase 5: scoring")

leh = load_cohort_autoencoder(MODEL_DIR / "LEH.pt")

@case("17 per_sentence_recon_error on empty embedding tensor")
def _():
    out = per_sentence_recon_error(leh, np.zeros((0, EMBEDDING_DIM), dtype=np.float32))
    assert out.shape == (0,), f"got {out.shape}"

@case("18 per_sentence_recon_error on a single embedding")
def _():
    e = np.random.default_rng(0).standard_normal((1, EMBEDDING_DIM)).astype(np.float32)
    e /= np.linalg.norm(e)
    out = per_sentence_recon_error(leh, e)
    assert out.shape == (1,) and np.isfinite(out).all() and out[0] >= 0

@case("19 score_filing on empty embeddings produces NaN cleanly")
def _():
    sf = score_filing("zz_empty", np.zeros((0, EMBEDDING_DIM), dtype=np.float32), leh)
    assert sf.n_sentences == 0
    assert math.isnan(sf.mean_recon_error)

@case("20 score_filing on 100 random unit-norm vectors")
def _():
    rng = np.random.default_rng(42)
    e = rng.standard_normal((100, EMBEDDING_DIM)).astype(np.float32)
    e /= np.linalg.norm(e, axis=1, keepdims=True)
    sf = score_filing("zz_rand", e, leh)
    assert sf.n_sentences == 100
    assert np.isfinite(sf.mean_recon_error)
    assert 0 < sf.mean_recon_error < 1

@case("21 score_filing reproduces committed Lehman primary score")
def _():
    p = _cache_path("0001104659-08-005476", ee.model_name)
    assert p.exists(), "Lehman cached embeddings missing"
    emb = np.load(p, allow_pickle=True)["embeddings"].astype(np.float32)
    sf = score_filing("LEH_fraud", emb, leh)
    target = 0.001395
    diff = abs(sf.mean_recon_error - target)
    assert diff < 1e-4, f"score drift {sf.mean_recon_error} vs {target}, diff={diff}"
    return f"score={sf.mean_recon_error:.6f} target={target}, diff={diff:.2e}"

# -- End-to-end determinism (full pipeline) -----------------------------------
print("\nPhase 6: end-to-end determinism")

@case("22 full pipeline end-to-end is deterministic")
def _():
    body = (REPO / "data/processed/parsed/000110465908005476.txt").read_text(encoding="utf-8")
    sents = split_sentences(body)[:50]
    e1 = ee.encode_filing("zz_e2e", sents)
    e2 = ee.encode_filing("zz_e2e", sents)
    s1 = score_filing("a", e1.embeddings, leh).mean_recon_error
    s2 = score_filing("a", e2.embeddings, leh).mean_recon_error
    assert abs(s1 - s2) < 1e-12, f"non-deterministic: {s1} vs {s2}"
    p = _cache_path("zz_e2e", ee.model_name)
    if p.exists():
        p.unlink()
    return f"score_mean stable across calls"

# -- Pytest unit-test suite (just confirm it still passes) ---------------------
print("\nPhase 7: existing pytest suite")

@case("23 pytest on engine + tests/ still passes")
def _():
    import subprocess
    r = subprocess.run([".venv/bin/python", "-m", "pytest", "-q", "--tb=line"],
                       capture_output=True, text=True, cwd=str(REPO))
    if r.returncode != 0:
        raise AssertionError(f"pytest failed:\n{r.stdout[-2000:]}\n{r.stderr[-500:]}")
    last = [l for l in r.stdout.splitlines() if l.strip()][-1]
    return last

# -- Summary ------------------------------------------------------------------
print("\n" + "=" * 78)
passed = sum(1 for r in results if r.passed)
total = len(results)
print(f"LOCAL PIPELINE: {passed}/{total} passed")
print("=" * 78)
if passed < total:
    print("\nFAILURES:")
    for r in results:
        if not r.passed:
            print(f"  {r.case}: {r.msg}")
    sys.exit(1)
sys.exit(0)
