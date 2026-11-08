"""vet_window.py RENDER.zarr OUT_PREFIX Y0 Y1 X0 X1 [--face forward|reverse] [--ckpt reader-v3.pth]

Vetting checks for one candidate window of a lane render (31 layers, centre 15), with Reader v3:
  - depth profile: the model on 17-layer windows centred at d = -6..+6; real surface ink peaks near d = 0;
  - other face: the same window read in the other layer order (the verso should be blank);
  - depth shuffle: the 17 layers in a fixed random order (the signal should vanish).
Score per run: d' = (mean in the ROI - mean of the rest of the valid sheet) / std of the rest. Writes OUT_PREFIX.json and
OUT_PREFIX.jpg (ROI crops of every run, same contrast)."""
import argparse, json, os, sys
import numpy as np, cv2, zarr
LANE_W = os.environ.get('LANE_W', '/home/liam/projects/vesuvius-work')   # the 306B lane's work tree
sys.path.insert(0, f'{LANE_W}/x_research2/speed')
import fastink as FI

ap = argparse.ArgumentParser()
ap.add_argument('render'); ap.add_argument('out')
ap.add_argument('y0', type=int); ap.add_argument('y1', type=int); ap.add_argument('x0', type=int); ap.add_argument('x1', type=int)
ap.add_argument('--face', default='forward'); ap.add_argument('--ckpt', default=f"{os.environ.get('LANE_W', '/home/liam/projects/vesuvius-work')}/models/community/reader-v3/reader-v3.pth")
a = ap.parse_args()
other = 'reverse' if a.face == 'forward' else 'forward'
m = FI.VillaFast(a.ckpt)
vol = zarr.open(a.render, mode='r')['0']; D = vol.shape[0]; c = D // 2
ct = np.asarray(vol[c]).astype(np.float32); valid = ct > 0
roi = np.zeros(valid.shape, bool); roi[a.y0:a.y1, a.x0:a.x1] = True; roi &= valid
pad = 600; cy0, cy1, cx0, cx1 = max(0, a.y0 - pad), min(valid.shape[0], a.y1 + pad), max(0, a.x0 - pad), min(valid.shape[1], a.x1 + pad)
ctx = np.zeros(valid.shape, bool); ctx[cy0:cy1, cx0:cx1] = True; rest = ctx & valid & ~roi


def dprime(p):
    p = p.astype(np.float32); r = p[rest]
    return round(float((p[roi].mean() - r.mean()) / (r.std() + 1e-6)), 3)


runs, crops = {}, {}
for d in range(-6, 7, 2):
    o, _ = m.predict(a.render, c + d - 8, a.face, overlap=0.5, batch=8)
    runs[f'd{d:+d}'] = dprime(o); crops[f'd{d:+d}'] = o[cy0:cy1, cx0:cx1]
o, _ = m.predict(a.render, c - 8, other, overlap=0.5, batch=8)
runs[f'{other}_d+0'] = dprime(o); crops[f'{other}'] = o[cy0:cy1, cx0:cx1]
root, win = m.load_window(a.render, c - 8, a.face)
perm = np.random.default_rng(0).permutation(win.shape[0])
o, _ = m.predict(a.render, c - 8, a.face, overlap=0.5, batch=8, window=(root, np.ascontiguousarray(win[perm])))
runs['shuffled_d+0'] = dprime(o); crops['shuffled'] = o[cy0:cy1, cx0:cx1]
json.dump({'render': a.render, 'roi_yx': [a.y0, a.y1, a.x0, a.x1], 'face': a.face, 'dprime': runs}, open(a.out + '.json', 'w'), indent=1)
print(json.dumps(runs))
ref = crops['d+0'].astype(np.float32); lo, hi = np.percentile(ref, [50, 99.5])
tiles = []
for k, im in crops.items():
    u = np.clip((im.astype(np.float32) - lo) / (hi - lo + 1e-6), 0, 1); t = (255 * (1 - u)).astype(np.uint8)
    t = cv2.resize(t, (t.shape[1] // 3, t.shape[0] // 3), interpolation=cv2.INTER_AREA)
    t = cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)
    cv2.rectangle(t, ((a.x0 - cx0) // 3, (a.y0 - cy0) // 3), ((a.x1 - cx0) // 3, (a.y1 - cy0) // 3), (0, 0, 255), 2)
    cv2.putText(t, f'{k}  d\'={runs.get(k, runs.get(k + "_d+0"))}', (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
    tiles.append(t)
cv2.imwrite(a.out + '.jpg', np.concatenate(tiles, 0), [cv2.IMWRITE_JPEG_QUALITY, 85])
