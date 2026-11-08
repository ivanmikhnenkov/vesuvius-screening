"""deepread.py RENDER.zarr X0 X1 FACE OUT.jpg : read one window of a 31-layer lane render with Reader v3, v8-in and TRACE v3B
(and Reader v3 x v8-in, the best pair on PHerc1447), each stretched from its median to its 99.5th percentile over the
window, dark = ink, stacked with the CT layer; for judging letter shapes by eye. The raw maps go to OUT_maps.npz."""
import os, sys
import numpy as np, cv2, zarr
LANE_W = os.environ.get('LANE_W', '/home/liam/projects/vesuvius-work')   # the 306B lane's work tree
sys.path.insert(0, f'{LANE_W}/x_research2/speed')
import fastink as FI

import torch, os
render, x0, x1, face, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
W = f'{LANE_W}/models/community'
src = zarr.open(render, mode='r')['0']; D = src.shape[0]; c = D // 2
crop = os.path.splitext(out)[0] + '_crop.zarr'          # the window only: small inputs, little GPU memory next to a fit
g0 = zarr.open_group(crop, mode='w', zarr_format=2); g0.create_array('0', data=np.asarray(src[:, :, x0:x1]), chunks=(D, 128, 128))
ct = np.asarray(src[c])[:, x0:x1].astype(np.float32); valid = ct > 0
maps = {}
for name, ck in (('reader-v3', f'{W}/reader-v3/reader-v3.pth'), ('trace-v3B', f'{W}/trace/v3B_best.pth')):
    m = FI.VillaFast(ck); maps[name] = m.predict(crop, c - 8, face, overlap=0.5, batch=2)[0].astype(np.float32) / 255
    del m; torch.cuda.empty_cache()
v8 = FI.V8Fast('fp16'); st = v8.stack(crop, 2)
p, _ = v8.predict(st, reverse=(face == 'reverse'), stride=32, batch=4)
maps['v8-in'] = p.astype(np.float32)
maps['rv3 x v8-in'] = maps['reader-v3'] * maps['v8-in']
np.savez_compressed(os.path.splitext(out)[0] + '_maps.npz', valid=valid, **{k.replace(' ', '_'): a.astype(np.float16) for k, a in maps.items()})
tiles = []
for k, a in maps.items():
    lo, hi = np.percentile(a[valid], [50, 99.5]); u = np.clip((a - lo) / (hi - lo + 1e-6), 0, 1)
    t = (255 * (1 - u)).astype(np.uint8); t[~valid] = 60
    t = cv2.cvtColor(t, cv2.COLOR_GRAY2BGR); cv2.putText(t, k, (12, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3); tiles.append(t)
g = np.clip((ct - np.percentile(ct[valid], 1)) / (np.percentile(ct[valid], 99.5) - np.percentile(ct[valid], 1)), 0, 1)
g = cv2.cvtColor((g * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR); cv2.putText(g, 'CT', (12, 44), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 0, 255), 3)
tiles.append(g)
img = np.concatenate(tiles, 0)
cv2.imwrite(out, cv2.resize(img, (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
print('written', out, img.shape)
