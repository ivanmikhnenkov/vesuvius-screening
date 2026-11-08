# Lasagna-format normals from the m7 surface prediction

The spiral fitter (`villa/volume-cartographer/scripts/spiral`, and lanes built on it) needs sheet normals in the
format of the published Lasagna predictions: `las_008_nx.ome.zarr` and `las_008_ny.ome.zarr`, group `2` (4× down),
uint8 `round(n * 127 + 128)` with `nz >= 0`, `0` for invalid, and 32³ chunks. Eight of the twenty eligible First
Letters scrolls have no Lasagna prediction in the open-data bucket: PHerc0175A, 0175B, 0483A, 0483B, 0490A, 0490B,
0846A and 0846B (listing of 2026-11-08). As published, the fitter can't run on them.

`make_normals.py` writes those two stores from the m7 surface prediction, which every eligible scroll has. It takes
the principal eigenvector of the structure tensor of m7 level 2 (gradient sigma 1, tensor sigma 2.5 level-2 voxels)
and flips its sign so that `nz >= 0`. It masks voxels where no sheet is near or where the tensor isn't coherent
(coherence below 0.3). Tiles run in parallel and S3 reads are retried.

```bash
python make_normals.py <m7 zarr URL or path> <out dir> --z Z0 Z1 [--tile 192] [--workers 16] [--check <lasagna nx URL>]
```

## The lane's own make_normals.py, and prior work

With `NORMALS=syn`, the PHerc. 0306B lane runs `x_recipe_erwin/tools/make_normals.py $M $D/lasagna_inputs --z
$((Z0-128)) $((Z1+128)) --tile 512` (`x_recipe_erwin/remote/erwin_data.sh`, lines 44-68). That file was missing from
the lane until commit 9bb6cef (2026-11-08), when the authors added their own: a structure tensor of m7 level 1 on GPU,
pooled to level 2. I wrote this one independently before that, on 2026-11-03, and it runs on CPU. It reads m7 level 2,
which the lane doesn't download, so this repository's `erwin_data.sh` patch calls it on the bucket's m7 instead
(`make_normals.py <m7 URL> $D/lasagna_inputs --z ... --tile 192 --workers 16`). The positive control and the PHerc0175A
fits below used it. I haven't compared the two implementations with each other.

[neg-0/vesuvius-research](https://github.com/neg-0/vesuvius-research) `lasagna-normals-from-m7` (2026-10-29) computes
normals from m7 with the same structure-tensor method. It reports a 7.8° median angle to the Lasagna normals on a
PHerc1218 block, which is an angle check with no fit reported. It also writes drop-in stores in the fitter's layout,
plus `grad_mag`. What I add here: fits of three bands of an eligible scroll with these normals, and a positive control
on known text (below).

## Check against the published Lasagna normals (PHerc0343)

```bash
M7=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0343/representations/predictions/surfaces/20250521140437-surface-20260413222639-surface-m7-L0-th0.2.zarr
LN=https://vesuvius-challenge-open-data.s3.amazonaws.com/PHerc0343/representations/predictions/lasagna/20250521140437-lasagna-20260419180421/PHerc0343_nx.ome.zarr
python make_normals.py $M7 out --z 10100 10228 --workers 16 --check $LN
```

| | value |
|---|---|
| band (level 0) | z 10100-10228 (level-2 slab z 2512-2544 compared) |
| valid voxels, mine / Lasagna | 45,095,855 / 47,185,920 |
| both valid | 37,545,756 |
| angle between the two normal fields, median | 7.5° |
| angle, 90th percentile | 27.1° |

## Use on an eligible scroll without Lasagna (PHerc0175A, 8.64 µm / 116 keV)

I fitted three 1,500-slice bands of PHerc0175A with these normals (30,000 steps, anticlockwise), then snapped the
windings onto m7 and flattened them. The table gives the mean per-winding snap statistics: the median distance to the
nearest predicted sheet, and the share of rejected vertices. The first two rows are the like-for-like comparison, the
same PHerc0343 band and windings fitted with each normal field.

| fit | windings | mean median offset (vox) | mean rejected |
|---|---|---|---|
| PHerc0343 z 9500-11000, published Lasagna normals | 40 | 1.81 | 0.184 |
| PHerc0343 z 9500-11000, these normals (same band and windings) | 40 | 1.82 | 0.183 |
| PHerc0175A z 5400-6900, synthetic normals | 40 | 2.20 | 0.093 |
| PHerc0175A z 6900-8400, synthetic normals | 120 | 2.86 | 0.094 |
| PHerc0175A z 8400-9900, synthetic normals | 120 | 2.72 | 0.105 |

## Positive control: the published PHerc0343 text with these normals

I ran the lane end to end on PHerc0343 z 9500-11000 with these normals in place of the published Lasagna (`../RUN.md`,
Reader v3 alone, reading face only). It ranks the window holding the published letters first (w046 x2600, with 8 of 18
letters within 0.1 mm of its mesh). With the Lasagna normals the same window came second (6 of 18). The lane's triage
was tuned partly on this text, so this is a regression check on known text, not a held-out test.
