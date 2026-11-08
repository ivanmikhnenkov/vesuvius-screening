"""eval_control.py RESULTS_DIR LETTERS_JSON [--top 20] [--win 2600] [--hit-mm 2.0] [--um 8.64]

Positive-control check for a lane on PHerc0343: for every window in RESULTS_DIR/tri_rank.json (ranked as the lane
ranked it), find the mesh nodes of that window (columns x0..x0+win of its winding's flattened tifxyz in
RESULTS_DIR/flat/<wNNN>/tifxyz/flatten.tifxyz) and count the known letters (3-D points) within --hit-mm of them.
Prints the top windows with their letter hits and the rank of the first window that holds letters."""
import argparse, glob, json, os
import numpy as np, tifffile
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument('results'); ap.add_argument('letters')
ap.add_argument('--top', type=int, default=20); ap.add_argument('--win', type=int, default=2600)
ap.add_argument('--hit-mm', type=float, default=2.0); ap.add_argument('--um', type=float, default=8.64)
a = ap.parse_args()
L = json.load(open(a.letters)); P = np.array([l['xyz'] for l in L], float)
rows = json.load(open(os.path.join(a.results, 'tri_rank.json')))
hit_vox = a.hit_mm * 1000 / a.um
cache = {}


def mesh(w):
    if w not in cache:
        d = glob.glob(os.path.join(a.results, 'flat', w, 'tifxyz', '*.tifxyz')) or glob.glob(os.path.join(a.results, 'flat', w, 'tifxyz'))
        d = d[0]
        XYZ = np.stack([tifffile.imread(os.path.join(d, f'{c}.tif')).astype(np.float64) for c in 'xyz'], -1)
        s = json.load(open(os.path.join(d, 'meta.json'))).get('scale', [0.05, 0.05])
        s = s[0] if isinstance(s, (list, tuple)) else s
        cache[w] = (XYZ, float(s))
    return cache[w]


first = None
print(f'{len(rows)} ranked windows; hit = letter within {a.hit_mm} mm ({hit_vox:.0f} vox) of the window mesh')
for i, r in enumerate(rows):
    w = r['name'].rsplit('_', 1)[-1]
    try:
        XYZ, s = mesh(w)
    except Exception as e:
        print(i + 1, r['name'], 'no mesh', repr(e)[:80]); continue
    c0, c1 = int(r['x0'] * s), int((r['x0'] + a.win) * s) + 1
    pts = XYZ[:, c0:c1].reshape(-1, 3); pts = pts[(pts > 0).all(1)]
    if not len(pts):
        continue
    d, _ = cKDTree(pts).query(P)
    hits = int((d <= hit_vox).sum())
    if hits and first is None:
        first = i + 1
    if i < a.top or hits:
        print(f"{i + 1:4d} {r['name']:<14} {r['side']} x{r['x0']:<6} score {r.get('score', 0):6.2f} tier {r.get('tier', r.get('via', ''))} "
              f"letters within {a.hit_mm} mm: {hits:2d}/{len(P)} (nearest {d.min() * a.um / 1000:.1f} mm)")
print('FIRST_HIT_RANK', first)
