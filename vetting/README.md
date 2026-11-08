# Vetting candidate windows from a screening lane

Row-periodicity triage over whole bands puts structure (cracks, folds, sheet contacts, fibre bundles) at the top as
often as text. These tools check a candidate before anyone spends time reading it. Prior work: `exp/e73_vet.py` of
[Jashann/vesuvius-scrolling](https://github.com/Jashann/vesuvius-scrolling) (2026-09-29) vets hotspots with
neighbouring windings, a depth profile and a 41-layer re-render; what is added here is the verso and shuffled-layer
ratios, calibrated on known text, and the own-sheet patch.

| tool | what it does |
|---|---|
| `auto_vet.py` | Reader v3 on the window at depths -6..+6, on the other face (verso) and with the 17 layers shuffled; reports the mean z over the window's hot pixels (z > 2 at d = 0) for each, as ratios to d = 0, and a flag |
| `vet_window.py` | the same runs for a hand-drawn ROI, with a figure of every run |
| `deepread.py` | one window read by Reader v3, TRACE v3B, v8-in and Reader v3 x v8-in, same contrast, with the CT layer, for judging letter shapes |
| `own_sheet.sh` | GrowPatch seeded at a candidate point on the m7 prediction, 41-layer render, reading face by the umbilicus, then `deepread.py` and `auto_vet.py` over the patch |
| `stroke_width.py` | stroke widths of the hot marks in `deepread.py`'s maps (z > 2, 2 x edge distance on the skeleton), median per model |
| `eval_control.py` | positive control: for every ranked window, the known letters (3-D points) within a distance of the window's mesh. Geometry only: it checks that the lane ranked a window whose mesh passes through the letters, not that its ink map shows them |

## Calibration on known text (PHerc0343, the published First Letters claim, windows w046 / w047 x2600)

| ratio to d = 0 | w046 | w047 |
|---|---|---|
| depth persistence, mean z at d = +-6 | 0.74 | 0.86 |
| verso | 0.306 | 0.330 |
| shuffled layers | 0.053 | -0.023 |
| median stroke width, Reader v3 / TRACE v3B / v8-in (`stroke_width.py`) | 0.33 / 0.19 / 0.09 mm | 0.27 / 0.16 / 0.07 mm |

- Reader v3 keeps its response on real text through +-6 layers: depth persistence does not separate text from
  structure for this model (as for ink_9um, trained with z-jitter).
- A window that fails the verso or shuffle ratio is structure: real text is face-specific (~0.3) and vanishes when the
  layers are shuffled (~0) (calibrated on two text windows). Passing them does not indicate text: 3 of the top 5 windows of PHerc0175A z 8400-9900 passed
  (w077, w128, w121) and none was text (w077 below). `auto_vet.py` flags a window `structural` when shuffled >= 0.2 or verso >= 0.5.

## Example: the top window of PHerc0175A z 6900-8400

The lane's top-ranked window in the band (w124 x1300, row score 21.3, above the PHerc0343 control's text windows; the
triage had auto-rejected one higher-scoring window, w016 x0 at 26.3, "rows not along winding") was:

| check | result |
|---|---|
| auto_vet on the lane render (x1300 / x2600) | verso 0.23 / 0.22, shuffled 0.30 / 0.31, persistence 0.79 / 0.78 -> structural |
| deep read on the lane render | the same ~3 cm diagonal chain of blobs in Reader v3, TRACE v3B and v8-in; no letter shapes |
| own-sheet patch (18.5 cm², 41 layers) | one continuous ~1 mm streak over several cm in all three models, following a linear CT feature; verso 0.62, shuffled 0.43 |

Verdict: a crack / fold line, not text; closed without a papyrological read.

## Example: the top window of PHerc0175A z 8400-9900

w077 x2600 (row score 14.2) passed the first step (verso -0.06, shuffled 0.06, response peaking at the surface) and
showed separate marks in the deep read, so it went to an own-sheet patch (14.2 cm², 41 layers): shuffled 0.14 over the
patch; Reader v3 and TRACE v3B share ~1 mm thick bars and blob clusters, v8-in diffuse clusters, no letter forms; the
patch runs into a sheared zone of the sheet beside the marks. Closed without a papyrological read. The first-step
numbers alone did not separate it from text: the own-sheet check did.
