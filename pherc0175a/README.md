# PHerc0175A: scroll axis and screened bands

PHerc0175A (volume 20250521115057, 8.64 um / 116 keV) has the clearest scan of the 8.64 um First Letters scrolls by the
[Scan-Quality-Map](https://github.com/jcooperkai-sys/Scan-Quality-Map) atlas (median 0.50; 768-slice rows with
median >= 0.40 from z 3840 to 11520), and no published umbilicus or Lasagna normals.

## Axis (`umb_PHerc0175A.json`)

`vc_gen_umbilicus` on the bucket's xy normal grids every 100 slices from z 500 to 12500 (5 repeats, seed 7), points
farther than 400 voxels from a running median dropped (95 of 121 kept, z 1700-11200), Savitzky-Golay smoothed
(`build_umb.py` of the 0306B lane). Checked by eye at z 6100: on the innermost windings. VC3D control-points format.

## Screened bands

Spiral fit (anticlockwise, 30,000 steps, synthetic normals from `../normals`), windings snapped to m7, flattened,
31-layer renders, ink on the face towards the umbilicus, windows of 2,600 px (2.2 cm) ranked by the lane's triage
(with the fixes in `../lane-fixes`), the top windows vetted (`../vetting`).

| band (z) | windings screened | ink | windows (REVIEW) | top row scores | verdict |
|---|---|---|---|---|---|
| 5400-6900 | 40 of 120 (w050-w089) | Hecate + Reader v3, and Reader v3 alone | 213 (42 / 38) | 5.64, 5.17, 4.36 / 8.69, 6.35, 2.42 | null: edge blobs, speckle, bars at the mesh edge; a 7 mm diagonal blob scatter (w066) not along rows |
| 6900-8400 | 120 (w010-w129) | Reader v3 | 681 (77) | 21.29, 7.62, 4.68, 3.12, 2.95 | null after vetting: w124 (21.3) is a crack / fold line (see `../vetting`); the rest edge blobs, speckle, haze spanning windings |
| 8400-9900 | 120 (w010-w129) | Reader v3 | 680 (123) | 14.20, 10.69, 10.59, 7.23, 6.71 | null after vetting: w077 (14.2) closed by its own-sheet patch (see `../vetting`); the rest a blob cluster, edge blobs, a blob on a CT crack |

For scale, the same lane gives the windows holding the published PHerc0343 text row scores of 14.0-16.6 with Reader v3
and the published Lasagna normals (w046 and w047 x2600; 14.6 with Hecate + Reader v3), and 9.25 and 8.72 with the
synthetic normals used here (the end-to-end run in `../RUN.md`).

What "null" covers here: the top windows of the triage's REVIEW tier were vetted. Windows the triage demoted
(REVIEW-2) or auto-rejected were not; the three highest-scoring of them in each 120-winding band (others also
outscore some vetted windows): z 6900-8400 w016 x0 (26.32,
auto-reject: rows not along winding), w118 x13000 (14.52, REVIEW-2: on cracks, round blobs), w067 x1300 (9.35,
REVIEW-2); z 8400-9900 w106 x6500 (11.72, REVIEW-2), w095 x7800 (10.90, auto-reject), w113 x9100 (9.95, auto-reject).
The same rules demoted the control's richest text window (PHerc0343 w047 x2600, 13 of 18 letters, 16.61) to REVIEW-2
("repeats on w+-2") in both Reader v3 runs, so a demoted window can hold text.

## What the null covers (`section.py`)

Fibres are visible on the winding renders (`figures/render_w060.jpg`: z 8400-9900 band, winding w060, the middle
layer of the 31, ~1/4 scale). In cross-section (`figures/section_z9150.jpg`: the 120 rendered windings of that band
in alternating colours over the CT slice at z 9150) the windings follow the scroll, but after the snap onto m7
consecutive windings share a predicted sheet in places. Share of each
consecutive-winding curve within 5 voxels of its neighbour, mean over pairs, at three z per band:

| mesh | z | share within 5 vox of the next winding |
|---|---|---|
| z 8400-9900, fitted (before the snap) | 8700 / 9150 / 9600 | 0.064 / 0.045 / 0.046 |
| z 8400-9900, snapped | same | 0.257 / 0.255 / 0.227 |
| z 8400-9900, flattened (rendered) | same | 0.258 / 0.250 / 0.225 |
| z 6900-8400, flattened | 7200 / 7650 / 8100 | 0.241 / 0.239 / 0.239 |
| z 5400-6900 (40 windings), flattened | 5700 / 6150 / 6600 | 0.221 / 0.211 / 0.204 |
| PHerc0343 z 9500-11000 control, Lasagna normals, flattened | 9800 / 10250 / 10700 | 0.182 / 0.160 / 0.173 |

The snap moves each vertex to the nearest predicted sheet, winding by winding, so two windings can take one sheet; it
does so with Lasagna normals too. These are curve proximities in three cross-sections per band, not areas, and whether
m7 or the fit is wrong where they meet is not known (no ground-truth sheets here). Read the null as covering fewer
distinct sheets than "280 windings" says: roughly a fifth to a quarter of each winding's curve lies on a neighbour's
sheet in these sections.

## Other searches of PHerc0175A (public, all without text)

An ink-first sweep with Reader v2 ([skuzbucket1/scroll-prize](https://github.com/skuzbucket1/scroll-prize)), 40
traced patches at z 9408-12508 ([AndreasHad04/villa-apple-silicon](https://github.com/AndreasHad04/villa-apple-silicon)),
clean-sheet patches ([Ahggggg/first-letters-clean-sheets](https://github.com/Ahggggg/first-letters-clean-sheets)) and
sheet patches ([Bullo27/first-letters-survey](https://github.com/Bullo27/first-letters-survey)). These bands add
spiral-fit windings over z 5400-9900, inked winding by winding.
