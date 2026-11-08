# Screening First Letters scrolls without Lasagna normals

Tools and measurements from screening PHerc0175A, the clearest 8.64 um First Letters scan, with the public spiral-fit
screening lane of the PHerc. 0306B team: what it took to run it there, which ink model to screen with at this scan
protocol, and how to tell a strong-scoring window from text.

| part | what | evidence |
|---|---|---|
| [`normals/`](normals) | Lasagna-format sheet normals from the m7 surface prediction, on CPU, so the spiral fitter can run on the 8 of 20 eligible scrolls without published Lasagna (shown on PHerc0175A) | 7.5 deg median angle to the published Lasagna normals on PHerc0343; with them the lane ranks the published PHerc0343 text first of 113 windows; three PHerc0175A bands fitted |
| [`benchmark/`](benchmark) | the public 9 um ink models on 8.64 um / 116 keV known text (PHerc1447 w058, w060), alone and in pairs, plus their cost per winding and a positive control | Reader v3 with v8-in best (AUC 0.883 / 0.819); adding Hecate or TRACE v3B to Reader v3 lowers every score; Reader v3 alone a median 4 s of model time per winding vs ~300 s with v8-in |
| [`vetting/`](vetting) | automatic vetting of top windows (depth, verso, shuffled layers), deep read with three models, own-sheet patch, positive-control scorer | calibrated on the published PHerc0343 text: verso ~0.3 and shuffled ~0 for text, so failing them rules text out (passing does not rule it in); depth persistence does not separate text from structure for Reader v3 |
| [`lane-fixes/`](lane-fixes) | ten changes to the 0306B lane (seven fixes, two additions, one review find), as patches and scripts; [`RUN.md`](RUN.md) runs the lane with them | evidence per fix: renders bit-identical to the PHerc0343 claim; ACW fits that died now complete; truncated downloads caught; the post stage gated on planned windings; triage stage 2-3x faster with identical output |
| [`pherc0175a/`](pherc0175a) | PHerc0175A axis (umbilicus) and the screened bands | three 1,500-slice bands, 280 windings, null in the triage's top tier after vetting (demoted windows not vetted); after the snap ~20-26 % of each winding's curve lies on a neighbour's sheet in cross-section, so the null covers fewer distinct sheets |

All parts were run on rented single RTX 4090 boxes and CPU. Data: the Vesuvius Challenge open-data bucket and the
PHerc1447 surfaces dataset (CC BY-NC 4.0). Models: Reader v3, Reader v2, v8-in, Hecate, TRACE v3B, ink_9um (all MIT).
Code here: MIT.

## Credits

The lane is [SirProdigle/pherc0306b-first-letters](https://github.com/SirProdigle/pherc0306b-first-letters)
`discovery/` (MIT, Liam Warner and Nicola Bodill; `licenses/pherc0306b-first-letters.LICENSE`): `lane-fixes/patches`
are diffs of its files. The PHerc0343 letter positions in `vetting/p343_letters_xyz.json` come from Erwin Nieuwlaar's
claim mesh and letter boxes ([Nieuwlaar/pherc343-first-letters](https://github.com/Nieuwlaar/pherc343-first-letters), MIT;
`licenses/pherc343-first-letters.LICENSE`). Related work: m7 structure-tensor normals in
[neg-0/vesuvius-research](https://github.com/neg-0/vesuvius-research) (`lasagna-normals-from-m7`, drop-in stores with
`grad_mag`) and in the lane itself from 9bb6cef; hotspot vetting with neighbouring windings and depth profiles in
[Jashann/vesuvius-scrolling](https://github.com/Jashann/vesuvius-scrolling) (`exp/e73_vet.py`); the Reader v3 README ([DomRusso2/reader-v3](https://github.com/DomRusso2/reader-v3)) compares Reader v3,
Reader v2, v8-in and Hecate on the same PHerc1447 labels, and the v8-in numbers here match the dataset card's.
