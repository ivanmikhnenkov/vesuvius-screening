"""bench_prep.py SEG OUT.zarr : 24 layer TIFFs of a PHerc1447 surface -> zarr (group, array "0", Z,Y,X uint8), cropped to
the bounding box of the label certainty mask (+128 px); writes SEG_crop.json with the crop."""
import json, sys
import numpy as np, tifffile, cv2, zarr

seg, out = sys.argv[1], sys.argv[2]
mask = cv2.imread(f'{seg}/labels/mask.png', cv2.IMREAD_GRAYSCALE) > 0
ys, xs = np.nonzero(mask)
H, W = mask.shape
y0, y1 = max(0, ys.min() - 128), min(H, ys.max() + 129); x0, x1 = max(0, xs.min() - 128), min(W, xs.max() + 129)
vol = np.stack([tifffile.imread(f'{seg}/layers/{i:02d}.tif')[y0:y1, x0:x1] for i in range(24)])
assert vol.dtype == np.uint8, vol.dtype
g = zarr.open_group(out, mode='w', zarr_format=2)
g.create_array('0', data=vol, chunks=(24, 128, 128))
json.dump({'y0': int(y0), 'y1': int(y1), 'x0': int(x0), 'x1': int(x1), 'full': [H, W]}, open(f'{seg}_crop.json', 'w'))
# the dataset's v8-in base-model prediction (run by its author with --reverse), cropped the same way
v8 = cv2.imread(f'{seg}/predictions/v8in.png', cv2.IMREAD_GRAYSCALE)
if v8 is not None:
    assert v8.shape == (H, W), v8.shape
    cv2.imwrite(f'out/{seg}_v8in_reverse.png', v8[y0:y1, x0:x1])
print(seg, 'crop', y0, y1, x0, x1, 'of', H, W, 'mask px', int(mask.sum()))
