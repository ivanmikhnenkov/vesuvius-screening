# Public 9 µm ink models on 8.64 µm / 116 keV known text (PHerc1447 w058, w060)

Nine of the twenty eligible First Letters scrolls were scanned at 8.64 µm / 116 keV: PHerc0175A, 0175B, 0268, 0483A,
0483B, 0490A, 0490B, 0800 and 1218. So were PHerc0343 and 0306B, the two read in October. PHerc1447 has refined human
ink labels on two windings at that protocol
([YoussefMoNader/ink-8um-pherc1447-surfaces](https://huggingface.co/datasets/YoussefMoNader/ink-8um-pherc1447-surfaces),
CC BY-NC 4.0), and none of the models below was trained on PHerc1447. It isn't in the organisers' ink-labels sets
(2026-07: PHercParis4, 0009b, 0139, 0500p2, 1667, 814, 841). I use it for its labels at the eligible scrolls' 8.64 µm
protocol. Here I compare the models, alone and in pairs, on the same pixels with the same metric.

## Setup

- Inputs: the dataset's 24-layer renders, cropped to the bounding box of the label certainty mask plus 128 px
  (`bench_prep.py`). w058 has 3,862,224 scored pixels (24.2 % ink), w060 has 3,231,085 (26.0 % ink).
- Reader v3 ([domenicor046/reader-v3](https://huggingface.co/domenicor046/reader-v3)) and TRACE v3B
  ([Jashann/vesuvius-scrolling](https://github.com/Jashann/vesuvius-scrolling) v1.0): villa
  `vesuvius.ink_detection.inference.infer`, layers 4-20, `--direction reverse`, overlap 0.5, hann blending.
- Hecate 9.6 µm ([scrollprize/hecate](https://huggingface.co/scrollprize/hecate)), on w058 only: the render resampled
  to 9.6 µm (`hecate_prep.py` of github.com/Nieuwlaar/pherc343-first-letters), 16 planes centred on layer 11.5,
  `--reverse`.
- v8-in ([YoussefMoNader/ink-8um-v8in](https://huggingface.co/YoussefMoNader/ink-8um-v8in)): the dataset's own
  published base-model prediction (`predictions/v8in.png`, 64 px tiles, stride 21, `--reverse`), cropped the same way.
- Pairs: the mean of per-map z-scores (z-mean, `zmean` in the score files) and the product of probabilities (×,
  `prod`).
- Metrics (`bench_score.py`), inside the certainty mask: pixel AUC, average precision (AP), and false ink at 80 %
  recall, which is the share of non-ink pixels above the threshold that keeps 80 % of the ink pixels.
- Ties: every map is 8-bit, so many pixels share a score. Pixels with the same score share one threshold, as in
  scikit-learn's `roc_auc_score` and `average_precision_score`. False ink is read off the ROC curve at 80 % recall,
  linear across a tie, which is the expected value for a random order of the tied pixels. The v8-in rows equal the
  dataset card's numbers (0.862 / 0.693 on w058, 0.810 / 0.677 on w060).

```bash
bash setup_bench.sh                   # torch, villa, checkpoints and data at pinned revisions into ./bench1447 (Reader v3, TRACE sha256-checked)
HEC=1 bash bench1447.sh w058 reverse  # Reader v3, TRACE v3B, Hecate (HEC=1 adds it: about 70 min on 12 CPU threads), v8-in; then the scores
bash bench1447.sh w060 reverse        # without Hecate
```

Scores land in `bench1447/data/out/<seg>_scores.json`. CPU is enough, and `TORCH_INDEX` selects a CUDA build.

## Results (`results/w058_scores.json`, `results/w060_scores.json`)

| model | w058 AUC | w058 AP | w058 false ink @80 % | w060 AUC | w060 AP | w060 false ink @80 % |
|---|---|---|---|---|---|---|
| Hecate 9.6 µm | 0.773 | 0.577 | 43.1 % |  |  |  |
| TRACE v3B | 0.792 | 0.632 | 42.0 % | 0.708 | 0.497 | 56.1 % |
| Reader v3 | 0.855 | 0.727 | 26.8 % | 0.760 | 0.605 | 48.7 % |
| v8-in | 0.862 | 0.693 | 24.1 % | 0.810 | 0.677 | 38.4 % |
| Reader v3 × v8-in | **0.883** | **0.764** | **21.0 %** | **0.819** | 0.684 | **34.0 %** |
| Reader v3 + v8-in (z-mean) | 0.881 | 0.762 | 21.4 % | 0.819 | **0.685** | 34.0 % |
| all four (z-mean) | 0.872 | 0.747 | 23.5 % |  |  |  |
| Hecate + Reader v3 (z-mean) | 0.850 | 0.711 | 28.0 % |  |  |  |
| Reader v3 × TRACE v3B | 0.842 | 0.714 | 30.2 % | 0.751 | 0.577 | 50.8 % |

At this protocol Reader v3 and v8-in lead, and pairing them gives the best map on both windings. Their product and
their z-mean are within 0.002 in AUC and AP and 0.4 points of false ink: the product is ahead on w058, and the z-mean
on w060's AP. Adding Hecate or TRACE v3B to Reader v3 lowers every score here.

## Cost per winding in a screening lane

Timed on an RTX 4090, on 31-layer renders of PHerc0175A windings of about 16,000 × 2,300 px.

| model | seconds per winding |
|---|---|
| Reader v3 (384 px tiles) | median 4, max 9.5, model time (240 windings logged) |
| Reader v3 + v8-in (v8-in at 64 px tiles, stride 32) | about 300 (timed on 6 windings) |

A 120-winding band takes about 8 min of model time with Reader v3 alone and about 10 h with v8-in added. So I screen
with Reader v3 and confirm candidates with v8-in.

## Positive control in a screening lane (PHerc0343 z 9500-11000, 40 windings, the published First Letters text)

The lane's row-periodicity triage ranks the windows. I take the rank of the first window whose mesh passes within
0.1 mm of a letter of the published claim (`../vetting/eval_control.py`, with letter positions from the claim's mesh
and letter boxes).

| ink in the lane (published Lasagna normals unless noted) | first rank holding the claim's letters | letters on that window |
|---|---|---|
| Hecate + Reader v3 (z-mean) | 1 (w046) and 3 (w047) | 6 / 18 and 13 / 18 |
| Reader v3 alone | 2 (w046) | 6 / 18 (more at ranks 6 and 10) |
| Reader v3 alone, synthetic normals (`../normals`), run end to end as in `../RUN.md` | 1 (w046) of 113 | 8 / 18 |

This checks geometry only. It confirms that the lane ranked a window whose mesh passes through the letters, but it reads
no ink there. The triage was tuned partly on this text, so these are regression checks, not held-out tests.
