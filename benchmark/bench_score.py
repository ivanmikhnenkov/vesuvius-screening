"""bench_score.py SEG DIR [DIR ...] : AUC, AP and false ink at 80% ink recall, inside the label certainty mask, for every
model map in out/ and for fusions (z-score means and products).  Writes out/SEG_scores.json."""
import glob, json, os, sys
import numpy as np, cv2, tifffile

seg, dirs = sys.argv[1], sys.argv[2:]
c = json.load(open(f'{seg}_crop.json'))
lab = cv2.imread(f'{seg}/labels/inklabels.png', cv2.IMREAD_GRAYSCALE)[c['y0']:c['y1'], c['x0']:c['x1']] > 127
msk = cv2.imread(f'{seg}/labels/mask.png', cv2.IMREAD_GRAYSCALE)[c['y0']:c['y1'], c['x0']:c['x1']] > 0
H, W = lab.shape


def load(f):
    a = tifffile.imread(f) if f.endswith('.tif') else cv2.imread(f, cv2.IMREAD_GRAYSCALE)
    a = a.astype(np.float32)
    if a.shape != (H, W):
        a = cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
    return a


def metrics_yp(y, p):
    """AUC, AP and false ink at 80 % recall with tied scores grouped: every pixel sharing a score takes one threshold
    (as sklearn's roc_auc_score / average_precision_score), so label order inside a tie never moves a number. False ink
    at 80 % recall is read on the ROC curve, linear across a tie (the expected value for a random order of tied pixels)."""
    o = np.argsort(-p, kind='stable'); ys = y[o]; ps = p[o]
    last = np.r_[np.flatnonzero(np.diff(ps)), len(ps) - 1]   # last index of each run of equal scores
    tp = np.cumsum(ys)[last].astype(np.float64); fp = np.cumsum(~ys)[last].astype(np.float64); P = tp[-1]; N = fp[-1]
    tpr = tp / P; fpr = fp / N
    auc = float(np.trapezoid(np.r_[0, tpr], np.r_[0, fpr]))
    ap = float((np.diff(np.r_[0, tpr]) * (tp / (tp + fp))).sum())
    T = np.r_[0, tpr]; F = np.r_[0, fpr]; i = int(np.searchsorted(T, 0.8))   # first point at >= 80 % recall; tied scores
    fa80 = float(F[i - 1] + (0.8 - T[i - 1]) * (F[i] - F[i - 1]) / (T[i] - T[i - 1]))   # lie on a straight ROC segment
    return dict(auc=round(auc, 4), ap=round(ap, 4), false_ink_at_80=round(fa80, 4))


def metrics(s):
    return metrics_yp(lab[msk], s[msk].astype(np.float64))


def z(a):
    v = a[msk]; return (a - v.mean()) / (v.std() + 1e-6)


res = {'seg': seg, 'mask_px': int(msk.sum()), 'ink_frac': round(float(lab[msk].mean()), 4)}
for d in dirs:
    maps = {}
    for f in sorted(glob.glob(f'out/{seg}_*_{d}.*')):
        if f.endswith(('.tif', '.png')):
            maps[os.path.basename(f).split('_')[1]] = load(f)
    for k, a in maps.items():
        res[f'{k}_{d}'] = metrics(a)
    ks = sorted(maps)
    if len(ks) >= 2:
        Z = {k: z(maps[k]) for k in ks}
        res[f'zmean_all_{d}'] = metrics(sum(Z.values()) / len(Z))
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                a, b = ks[i], ks[j]
                res[f'zmean_{a}+{b}_{d}'] = metrics((Z[a] + Z[b]) / 2)
                res[f'prod_{a}x{b}_{d}'] = metrics(maps[a] / 255 * (maps[b] / 255))
json.dump(res, open(f'out/{seg}_scores.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
