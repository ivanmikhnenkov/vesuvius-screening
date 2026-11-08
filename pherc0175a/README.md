# PHerc0175A: scroll axis and screened bands

PHerc0175A (volume 20250521115057, 8.64 µm / 116 keV) is the clearest of the 8.64 µm First Letters scans by the
[Scan-Quality-Map](https://github.com/jcooperkai-sys/Scan-Quality-Map) atlas: median 0.50, with 768-slice rows at a
median of 0.40 or more from z 3840 to 11520. It has no published umbilicus and no Lasagna normals.

## Axis (`umb_PHerc0175A.json`)

I ran `vc_gen_umbilicus` on the bucket's xy normal grids every 100 slices from z 500 to 12500 (5 repeats, seed 7).
Points more than 400 voxels from a running median were dropped, which kept 95 of 121 (z 1700-11200), and the rest were
Savitzky-Golay smoothed (`build_umb.py` of the 0306B lane). I checked it by eye at z 6100, where it sits on the
innermost windings. The file is in VC3D control-points format.

## Screened bands

Each band was spiral-fitted (anticlockwise, 30,000 steps, with the synthetic normals from `../normals`). The windings
were snapped to m7, flattened, rendered with 31 layers and inked on the face towards the umbilicus. The lane's triage,
with the fixes in `../lane-fixes`, ranked windows of 2,600 px (2.2 cm), and I vetted the top windows (`../vetting`).

| band (z) | windings screened | ink | windows (REVIEW) | top row scores | verdict |
|---|---|---|---|---|---|
| 5400-6900 | 40 of 120 (w050-w089) | Hecate + Reader v3, and Reader v3 alone | 213 (42 / 38) | 5.64, 5.17, 4.36 / 8.69, 6.35, 2.42 | null: edge blobs, speckle, bars at the mesh edge; a 7 mm diagonal blob scatter (w066), not along rows |
| 6900-8400 | 120 (w010-w129) | Reader v3 | 681 (77) | 21.29, 7.62, 4.68, 3.12, 2.95 | null after vetting: w124 (21.3) is a crack or fold line (see `../vetting`); the rest edge blobs, speckle, haze spanning windings |
| 8400-9900 | 120 (w010-w129) | Reader v3 | 680 (123) | 14.20, 10.69, 10.59, 7.23, 6.71 | null after vetting: w077 (14.2) closed by its own-sheet patch (see `../vetting`); the rest a blob cluster, edge blobs, a blob on a CT crack |

For scale: in the same lane, the windows holding the published PHerc0343 text score 14.0-16.6 with Reader v3 and the
published Lasagna normals (w046 and w047 x2600; 14.6 with Hecate + Reader v3). With the synthetic normals used here
they score 9.25 and 8.72 (the end-to-end run in `../RUN.md`).

## What the null covers

Null here means: I vetted the top windows of the triage's REVIEW tier and found no text. I did not vet the windows the
triage demoted (REVIEW-2) or auto-rejected, and several of them, not only the three below, score higher than some of
the vetted windows. The three highest-scoring in each 120-winding band:
- z 6900-8400: w016 x0 (26.32, auto-reject: rows not along winding), w118 x13000 (14.52, REVIEW-2: on cracks, round
  blobs), w067 x1300 (9.35, REVIEW-2).
- z 8400-9900: w106 x6500 (11.72, REVIEW-2), w095 x7800 (10.90, auto-reject), w113 x9100 (9.95, auto-reject).

The same rules demoted the control's richest text window (PHerc0343 w047 x2600, 13 of 18 letters, 16.61) to REVIEW-2
("repeats on w±2") in both Reader v3 runs. So a demoted window can hold text.

## Windings that share a sheet (`section.py`)

The winding renders show fibres (`figures/render_w060.jpg`: band z 8400-9900, winding w060, the middle layer of the 31,
about 1/4 scale). In cross-section (`figures/section_z9150.jpg`: the band's 120 rendered windings in alternating
colours over the CT slice at z 9150) the windings follow the scroll. But after the snap onto m7, consecutive windings
share a predicted sheet in places. I measured the share of each consecutive-winding curve that lies within 5 voxels of
its neighbour, as a mean over pairs, at three z per band:

| mesh | z | share within 5 vox of the next winding |
|---|---|---|
| z 8400-9900, fitted (before the snap) | 8700 / 9150 / 9600 | 0.064 / 0.045 / 0.046 |
| z 8400-9900, snapped | same | 0.257 / 0.255 / 0.227 |
| z 8400-9900, flattened (rendered) | same | 0.258 / 0.250 / 0.225 |
| z 6900-8400, flattened | 7200 / 7650 / 8100 | 0.241 / 0.239 / 0.239 |
| z 5400-6900 (40 windings), flattened | 5700 / 6150 / 6600 | 0.221 / 0.211 / 0.204 |
| PHerc0343 z 9500-11000 control, Lasagna normals, flattened | 9800 / 10250 / 10700 | 0.182 / 0.160 / 0.173 |

The snap moves each vertex to the nearest predicted sheet, one winding at a time, so two windings can land on one
sheet. It does this with Lasagna normals too. These numbers are curve proximities in three cross-sections per band, not
areas. There are no ground-truth sheets here, so I can't tell whether m7 or the fit is wrong where two windings meet.
Read the null as covering fewer distinct sheets than "280 windings" says: in these sections, roughly a fifth to a
quarter of each winding's curve lies on a neighbour's sheet.

## Other public searches of PHerc0175A, all without text

An ink-first sweep with Reader v2 ([skuzbucket1/scroll-prize](https://github.com/skuzbucket1/scroll-prize)), 40 traced
patches at z 9408-12508 ([AndreasHad04/villa-apple-silicon](https://github.com/AndreasHad04/villa-apple-silicon)),
clean-sheet patches ([Ahggggg/first-letters-clean-sheets](https://github.com/Ahggggg/first-letters-clean-sheets)) and
sheet patches ([Bullo27/first-letters-survey](https://github.com/Bullo27/first-letters-survey)). These bands add
spiral-fit windings over z 5400-9900, inked winding by winding.
