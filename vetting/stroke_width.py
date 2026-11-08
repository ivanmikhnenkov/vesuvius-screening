"""stroke_width.py MAPS.npz [X0 X1] : stroke widths of the hot marks in deepread.py's maps (_maps.npz).
Per model: z-score over the valid pixels, hot = z > 2, components < 40 px dropped, width = 2 x distance to the mark's
edge at its skeleton pixels. Prints median and quartiles in px and mm (8.64 um px). Optional column crop X0:X1."""
import sys, json, numpy as np, cv2
from skimage.morphology import skeletonize
d = np.load(sys.argv[1]); valid = d['valid']
sl = slice(int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else slice(None)
out = {}
for k in d.files:
    if k == 'valid':
        continue
    a = d[k].astype(np.float32)[:, sl]; v = valid[:, sl]
    z = (a - a[v].mean()) / (a[v].std() + 1e-6); hot = (z > 2) & v
    n, lab, st, _ = cv2.connectedComponentsWithStats(hot.astype(np.uint8), connectivity=8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 40; hot = keep[lab]
    dt = cv2.distanceTransform(hot.astype(np.uint8), cv2.DIST_L2, 5)
    w = 2 * dt[skeletonize(hot)]
    q = np.percentile(w, [25, 50, 75]) if w.size else [np.nan] * 3
    out[k] = {'hot_frac': round(float(hot.sum() / v.sum()), 4), 'marks': int(keep.sum()),
              'w_px_q25_q50_q75': [round(float(x), 1) for x in q], 'w_mm_q50': round(float(q[1]) * 0.00864, 3)}
print(json.dumps(out))
