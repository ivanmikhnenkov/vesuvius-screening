# Vetting candidate windows from a screening lane

Row-periodicity triage over whole bands puts structure (cracks, folds, sheet contacts, fibre bundles) at the top as
often as text. These tools check a candidate before anyone spends time reading it.

Prior work: `exp/e73_vet.py` of [Jashann/vesuvius-scrolling](https://github.com/Jashann/vesuvius-scrolling)
(2026-09-29) vets hotspots with neighbouring windings, a depth profile and a 41-layer re-render. What I add is the
verso and shuffled-layer ratios, calibrated on known text, and the own-sheet patch.

| tool | what it does |
|---|---|
| `auto_vet.py` | Runs Reader v3 on the window at depths -6 to +6, on the other face (verso) and with the 17 layers shuffled. For each run it reports the mean z over the window's hot pixels (z > 2 at d = 0) as a ratio to d = 0, and sets a flag. |
| `vet_window.py` | The same runs for a hand-drawn ROI, with a figure of every run. |
| `deepread.py` | Reads one window with Reader v3, TRACE v3B, v8-in and Reader v3 × v8-in at the same contrast, next to the CT layer, for judging letter shapes. |
| `own_sheet.sh` | Grows a GrowPatch from a candidate point on the m7 prediction, renders it with 41 layers, picks the reading face by the umbilicus, then runs `deepread.py` and `auto_vet.py` over the patch. |
| `stroke_width.py` | Stroke widths of the hot marks in `deepread.py`'s maps (z > 2, twice the edge distance on the skeleton), median per model. |
| `eval_control.py` | Positive control: for every ranked window, the known letters (3-D points) within a given distance of the window's mesh. It checks geometry only, that the lane ranked a window whose mesh passes through the letters, not that its ink map shows them. |

## Calibration on known text (PHerc0343, the published First Letters claim, windows w046 and w047 x2600)

| ratio to d = 0 | w046 | w047 |
|---|---|---|
| depth persistence, mean z at d = ±6 | 0.74 | 0.86 |
| verso | 0.306 | 0.330 |
| shuffled layers | 0.053 | -0.023 |
| median stroke width, Reader v3 / TRACE v3B / v8-in (`stroke_width.py`) | 0.33 / 0.19 / 0.09 mm | 0.27 / 0.16 / 0.07 mm |

Reader v3 keeps its response on real text through ±6 layers, so depth persistence doesn't separate text from
structure for this model. The same holds for ink_9um, which was trained with z-jitter.

Real text is face-specific (verso about 0.3) and disappears when the layers are shuffled (about 0). So a window that
fails the verso or shuffle ratio is structure. This calibration rests on two text windows. Passing the ratios doesn't
mean text: 3 of the top 5 windows of PHerc0175A z 8400-9900 passed (w077, w128, w121) and none of them was text (w077
below). `auto_vet.py` flags a window `structural` when shuffled >= 0.2 or verso >= 0.5.

## Example: the top window of PHerc0175A z 6900-8400

The lane's top-ranked window in this band was w124 x1300, with a row score of 21.3, above the PHerc0343 control's text
windows. The triage had auto-rejected one window that scored higher, w016 x0 at 26.3, as "rows not along winding".

| check | result |
|---|---|
| auto_vet on the lane render (x1300 / x2600) | verso 0.23 / 0.22, shuffled 0.30 / 0.31, persistence 0.79 / 0.78: structural |
| deep read on the lane render | the same diagonal chain of blobs, about 3 cm long, in Reader v3, TRACE v3B and v8-in; no letter shapes |
| own-sheet patch (18.5 cm², 41 layers) | one continuous streak of about 1 mm over several cm in all three models, following a linear CT feature; verso 0.62, shuffled 0.43 |

Verdict: a crack or fold line, not text. I closed it without a papyrological read.

## Example: the top window of PHerc0175A z 8400-9900

w077 x2600 (row score 14.2) passed the first step: verso -0.06, shuffled 0.06, and a response that peaks at the
surface. It also showed separate marks in the deep read, so I grew an own-sheet patch for it (14.2 cm², 41 layers).
Over the patch the shuffled ratio was 0.14. Reader v3 and TRACE v3B share bars about 1 mm thick and blob clusters,
v8-in shows diffuse clusters, and there are no letter forms. The patch runs into a sheared zone of the sheet beside the
marks. I closed it without a papyrological read. The first-step numbers alone didn't separate it from text; the
own-sheet check did.
