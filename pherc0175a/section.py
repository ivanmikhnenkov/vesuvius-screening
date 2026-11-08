"""section.py WINDINGS_DIR VOLUME_URL --z Z [--level 2] [--out FIG.png] [--crop X0 Y0 SIZE --crop-out FIG2.png]

Cross-section check of a set of tifxyz windings on one CT slice: does a winding stay on its own sheet? Every winding's
mesh is intersected with the plane z = Z and drawn over the CT. Where a winding jumps to the next sheet, it lands on its
neighbour, so the script also reports, per pair of consecutive windings, the spacing between their curves and the share
of each curve closer than --merge voxels to its neighbour.

WINDINGS_DIR holds one folder per winding (w010, w011, ...), each with x.tif, y.tif, z.tif (level-0 voxels, -1 = invalid).
"""
import argparse, glob, json, os
import numpy as np, tifffile, zarr
from scipy.spatial import cKDTree
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('windings'); ap.add_argument('volume')
ap.add_argument('--z', type=float, required=True); ap.add_argument('--level', type=int, default=2)
ap.add_argument('--out', default=None); ap.add_argument('--merge', type=float, default=5.0)
ap.add_argument('--crop', type=int, nargs=3, default=None, metavar=('X0', 'Y0', 'SIZE')); ap.add_argument('--crop-out', default=None)
ap.add_argument('--json', default=None)
a = ap.parse_args()


def section(folder, z0):
    """Polyline of the winding at z = z0, one point per grid column (the long grid axis runs around the scroll)."""
    x, y, z = (tifffile.imread(os.path.join(folder, f'{c}.tif')).astype(np.float64) for c in 'xyz')
    if x.shape[0] > x.shape[1]:
        x, y, z = x.T, y.T, z.T                                   # rows across the band, columns around the scroll
    ok = (x > 0) & (y > 0) & (z > 0)
    pts = []
    for j in range(x.shape[1]):
        v = np.nonzero(ok[:, j])[0]
        if len(v) < 2:
            continue
        zz = z[v, j]; cross = np.nonzero((zz[:-1] - z0) * (zz[1:] - z0) <= 0)[0]
        if len(cross) == 0:
            continue
        i = cross[0]; t = (z0 - zz[i]) / (zz[i + 1] - zz[i] + 1e-9)
        a0, a1 = v[i], v[i + 1]
        pts.append((j, x[a0, j] + t * (x[a1, j] - x[a0, j]), y[a0, j] + t * (y[a1, j] - y[a0, j])))
    return np.array(pts) if pts else np.zeros((0, 3))


def densify(p, step=2.0, gap=80.0):
    """Points every `step` voxels along the polyline; no bridge across a hole in the mesh (> gap voxels)."""
    out = []
    for q0, q1 in zip(p[:-1, 1:], p[1:, 1:]):
        d = np.linalg.norm(q1 - q0)
        if d > gap:
            continue
        n = max(1, int(d / step)); out.append(q0 + (q1 - q0) * np.arange(n)[:, None] / n)
    return np.concatenate(out) if out else np.zeros((0, 2))


names = sorted(os.path.basename(f) for f in glob.glob(os.path.join(a.windings, 'w[0-9]*')) if os.path.isdir(f))
C = {n: densify(section(os.path.join(a.windings, n), a.z)) for n in names}
C = {n: c for n, c in C.items() if len(c) > 10}
rows = []
ks = sorted(C)
for u, v in zip(ks[:-1], ks[1:]):
    if int(v[1:]) != int(u[1:]) + 1:
        continue
    d, _ = cKDTree(C[v]).query(C[u])
    rows.append({'pair': f'{u}-{v}', 'points': len(d), 'median_spacing_vox': round(float(np.median(d)), 1),
                 'frac_merged': round(float((d < a.merge).mean()), 4)})
med = [r['median_spacing_vox'] for r in rows]; mer = [r['frac_merged'] for r in rows]
res = {'z': a.z, 'windings': len(C), 'pairs': len(rows), 'median_spacing_vox': float(np.median(med)) if med else None,
       'merge_threshold_vox': a.merge, 'mean_frac_merged': round(float(np.mean(mer)), 4) if mer else None,
       'worst_pairs': sorted(rows, key=lambda r: -r['frac_merged'])[:5]}
print(json.dumps(res, indent=1))
if a.json:
    json.dump({**res, 'rows': rows}, open(a.json, 'w'), indent=1)

vol = zarr.open(a.volume, mode='r')


def draw(sub, level, x0, y0, sx, sy, out, lw):
    s = 2 ** level
    img = np.asarray(sub[int(a.z) // s, y0 // s:(y0 + sy) // s, x0 // s:(x0 + sx) // s])
    fig, ax = plt.subplots(figsize=(10, 10 * sy / sx), dpi=160)
    ax.imshow(img, cmap='gray', extent=(x0, x0 + sx, y0 + sy, y0), vmin=0, vmax=np.percentile(img[img > 0], 99.5) if (img > 0).any() else 255)
    for i, n in enumerate(ks):
        c = C[n]; m = (c[:, 0] >= x0) & (c[:, 0] < x0 + sx) & (c[:, 1] >= y0) & (c[:, 1] < y0 + sy)
        ax.scatter(c[m, 0], c[m, 1], s=lw, color='#ff4d00' if i % 2 else '#00d0ff', linewidths=0)
    ax.set_title(f'{os.path.basename(a.volume.rstrip("/"))[:32]}  z={a.z:.0f}  {len(ks)} windings'); ax.set_xlabel('x (voxels)'); ax.set_ylabel('y (voxels)')
    fig.tight_layout(); fig.savefig(out); plt.close(fig)


if a.out:
    xy = np.concatenate([C[n] for n in ks]); x0, y0 = (xy.min(0) - 100).astype(int).clip(0); x1, y1 = (xy.max(0) + 100).astype(int)
    draw(vol[str(a.level)], a.level, int(x0), int(y0), int(x1 - x0), int(y1 - y0), a.out, 0.15)
if a.crop and a.crop_out:
    draw(vol['0'], 0, a.crop[0], a.crop[1], a.crop[2], a.crop[2], a.crop_out, 1.5)
