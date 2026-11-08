"""auto_vet.py RENDERS_DIR TRI_RANK_JSON OUT.json [--top 10] [--win 2600] [--face-from FLAT UMB] | --one RENDER X0 FACE

Automatic vetting of the top windows of a lane, with Reader v3 (cheap: ~10 s per map). For each window:
  hot   = pixels of the window with z > 2 in the d = 0 map (z-scored over the window's valid sheet);
  depth = mean z over `hot` in maps centred at d = -6, -4, -2, 0, +2, +4, +6;
  verso = mean z over `hot` read in the other layer order;
  shuf  = mean z over `hot` with the 17 layers shuffled.
Real surface ink fades away from d = 0 and is absent on the verso; a structural band (crease, fibre bundle, sheet
contact) persists through depth and shows on both faces. Ratios to d = 0: persist = mean(z at d = +-6) / z(0),
verso = z_verso / z(0), shuf = z_shuffled / z(0). Calibration on PHerc0343's known text (w046/w047 x2600): persist
0.74/0.86 (Reader v3 is depth-tolerant, so persistence is reported but does not flag), verso 0.31/0.33, shuf 0.05/-0.02.
Flag 'structural' when shuf >= S (0.2) or verso >= V (0.5)."""
import argparse, json, os, sys
import numpy as np
LANE_W = os.environ.get('LANE_W', '/home/liam/projects/vesuvius-work')   # the 306B lane's work tree
sys.path.insert(0, f'{LANE_W}/x_research2/speed')
import fastink as FI
import zarr

ap = argparse.ArgumentParser()
ap.add_argument('renders', nargs='?'); ap.add_argument('tri', nargs='?'); ap.add_argument('out', nargs='?')
ap.add_argument('--top', type=int, default=10); ap.add_argument('--win', type=int, default=2600)
ap.add_argument('--one', nargs=3, metavar=('RENDER', 'X0', 'FACE'))
ap.add_argument('--out1', default=None)
ap.add_argument('--S', type=float, default=0.2); ap.add_argument('--V', type=float, default=0.5)
ap.add_argument('--ckpt', default=f"{os.environ.get('LANE_W', '/home/liam/projects/vesuvius-work')}/models/community/reader-v3/reader-v3.pth")
a = ap.parse_args()
M = FI.VillaFast(a.ckpt)


def zwin(o, valid, x0):
    o = o[:, x0:x0 + a.win].astype(np.float32); v = valid[:, x0:x0 + a.win]
    return (o - o[v].mean()) / (o[v].std() + 1e-6), v


def vet(render, x0, face):
    vol = zarr.open(render, mode='r')['0']; c = vol.shape[0] // 2
    valid = np.asarray(vol[c]) > 0
    other = 'reverse' if face == 'forward' else 'forward'
    z0, v = zwin(M.predict(render, c - 8, face, overlap=0.5, batch=8)[0], valid, x0)
    hot = (z0 > 2) & v
    if hot.sum() < 500:
        return dict(render=render, x0=x0, face=face, hot_px=int(hot.sum()), note='too few hot pixels')
    prof = {}
    for d in (-6, -4, -2, 2, 4, 6):
        if c + d - 8 < 0 or c + d + 9 > vol.shape[0]:
            continue
        zd, _ = zwin(M.predict(render, c + d - 8, face, overlap=0.5, batch=8)[0], valid, x0)
        prof[d] = float(zd[hot].mean())
    prof[0] = float(z0[hot].mean())
    zv, _ = zwin(M.predict(render, c - 8, other, overlap=0.5, batch=8)[0], valid, x0)
    root, win = M.load_window(render, c - 8, face)
    perm = np.random.default_rng(0).permutation(win.shape[0])
    zs, _ = zwin(M.predict(render, c - 8, face, overlap=0.5, batch=8, window=(root, np.ascontiguousarray(win[perm])))[0], valid, x0)
    far = [prof[d] for d in (-6, 6) if d in prof]
    persist = float(np.mean(far) / prof[0]) if far else None
    verso = float(zv[hot].mean() / prof[0]); shuf = float(zs[hot].mean() / prof[0])
    flag = 'structural' if shuf >= a.S or verso >= a.V else 'surface-like'
    return dict(render=render, x0=x0, face=face, hot_px=int(hot.sum()), depth={str(k): round(v, 3) for k, v in sorted(prof.items())},
                persist=round(persist, 3) if persist is not None else None, verso=round(verso, 3), shuffled=round(shuf, 3), flag=flag)


if a.one:
    r = vet(a.one[0], int(a.one[1]), a.one[2]); print(json.dumps(r))
    if a.out1: json.dump(r, open(a.out1, 'w'), indent=1)
    sys.exit(0)
rows = json.load(open(a.tri))[:a.top]
res = []
for r in rows:
    face = 'reverse' if r['side'] == 'rev' else 'forward'
    out = vet(f"{a.renders}/{r['name']}.zarr", r['x0'], face); out.update(rank_score=r['score'], name=r['name'])
    print(json.dumps(out), flush=True); res.append(out)
json.dump(res, open(a.out, 'w'), indent=1)
