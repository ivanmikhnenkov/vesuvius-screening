# Screening First Letters scrolls without Lasagna normals

I ran the PHerc. 0306B team's public spiral-fit screening lane on PHerc0175A, the clearest of the 8.64 µm First Letters
scans. This repository has what it took to run the lane there, which public ink model to screen with at this scan
protocol, and how I tell a high-scoring window from text.

| part | what it is | what it shows |
|---|---|---|
| [`normals/`](normals) | Lasagna-format sheet normals computed on CPU from the m7 surface prediction. With them the spiral fitter runs on the 8 of 20 eligible scrolls that have no published Lasagna (shown on PHerc0175A). | The median angle to the published Lasagna normals on PHerc0343 is 7.5°. With these normals the lane ranks the published PHerc0343 text first of 113 windows. Three PHerc0175A bands fitted. |
| [`benchmark/`](benchmark) | The public 9 µm ink models on known text scanned at 8.64 µm / 116 keV (PHerc1447 w058 and w060), alone and in pairs, with their cost per winding and a positive control. | Reader v3 × v8-in scores best (AUC 0.883 and 0.819). Adding Hecate or TRACE v3B to Reader v3 lowers every score. Reader v3 alone takes a median 4 s of model time per winding, and about 300 s with v8-in added. |
| [`vetting/`](vetting) | Automatic checks for top windows (depth, verso, shuffled layers), a deep read with three models, an own-sheet patch and a positive-control scorer. | Calibrated on the published PHerc0343 text: text gives a verso ratio near 0.3 and a shuffled ratio near 0. A window that fails these is not text, but passing them doesn't make it text. Depth persistence doesn't separate text from structure for Reader v3. |
| [`lane-fixes/`](lane-fixes) | Ten changes to the 0306B lane as patches and scripts: seven fixes, two additions and one fix found in review. [`RUN.md`](RUN.md) runs the lane with them. | Evidence for each. Renders are bit-identical to the PHerc0343 claim. Anticlockwise fits that died now finish. Truncated downloads get caught. The post stage checks against the planned windings. Triage runs 2-3 times faster with identical output. |
| [`pherc0175a/`](pherc0175a) | The PHerc0175A axis (umbilicus) and the screened bands. | Three 1,500-slice bands, 280 windings, and no text found in the triage's top tier after vetting. Windows the triage demoted were not vetted. After the snap, about 20-26 % of each winding's curve lies on a neighbour's sheet in cross-section, so the null covers fewer distinct sheets than the winding count suggests. |

Everything ran on rented single RTX 4090 boxes and on CPU.

## Data, models and licence

Data: the Vesuvius Challenge open-data bucket and the PHerc1447 surfaces dataset (CC BY-NC 4.0). Models: Reader v3,
Reader v2, v8-in, Hecate, TRACE v3B and ink_9um, all MIT. The code here is MIT.

## Credits

The lane is [SirProdigle/pherc0306b-first-letters](https://github.com/SirProdigle/pherc0306b-first-letters)
`discovery/` by Liam Warner and Nicola Bodill (MIT, `licenses/pherc0306b-first-letters.LICENSE`). The files in
`lane-fixes/patches` are diffs of its files. The PHerc0343 letter positions in `vetting/p343_letters_xyz.json` come from
Erwin Nieuwlaar's claim mesh and letter boxes ([Nieuwlaar/pherc343-first-letters](https://github.com/Nieuwlaar/pherc343-first-letters),
MIT, `licenses/pherc343-first-letters.LICENSE`).

Related work:
- [neg-0/vesuvius-research](https://github.com/neg-0/vesuvius-research) (`lasagna-normals-from-m7`) computes m7
  structure-tensor normals and writes drop-in stores with `grad_mag`. The lane itself has m7 normals since 9bb6cef.
- [Jashann/vesuvius-scrolling](https://github.com/Jashann/vesuvius-scrolling) (`exp/e73_vet.py`) vets hotspots with
  neighbouring windings and depth profiles.
- The Reader v3 README ([DomRusso2/reader-v3](https://github.com/DomRusso2/reader-v3)) compares Reader v3, Reader v2,
  v8-in and Hecate on the same PHerc1447 labels. My v8-in numbers match the dataset card's.
