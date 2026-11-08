"""make_normals.py M7_URL_OR_DIR OUT_DIR --z Z0 Z1 [--tile 256] [--workers 16] [--check LASAGNA_NX_URL]

Synthetic Lasagna-format sheet normals from the m7 surface prediction, for scrolls without published Lasagna outputs.
Reads m7 level 2 (4x down, the grid of Lasagna's group 2), takes the structure tensor of the smoothed prediction
(gradient sigma 1, tensor sigma 2.5 voxels of level 2) and writes its principal eigenvector, sign-flipped so nz >= 0,
as OUT_DIR/las_008_{nx,ny}.ome.zarr/2: uint8 round(n * 127 + 128), 0 = invalid (no sheet nearby or incoherent), chunks
32^3, the shape of m7 level 2. Only z in [Z0 - 128, Z1 + 128] (level 0) is written.
--check: compare with a real Lasagna nx/ny pair (URL of the nx store; ny is next to it) over the band and print the
median angle between the two normal fields where both are valid.
"""
import argparse, json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np, zarr
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument('m7'); ap.add_argument('out')
ap.add_argument('--z', type=int, nargs=2, required=True)
ap.add_argument('--tile', type=int, default=256)
ap.add_argument('--workers', type=int, default=16)
ap.add_argument('--sigma-g', type=float, default=1.0); ap.add_argument('--sigma-t', type=float, default=2.5)
ap.add_argument('--min-coh', type=float, default=0.3); ap.add_argument('--min-p', type=float, default=8.0)
ap.add_argument('--check', default=None)
a = ap.parse_args()
M = 32  # tile margin (level-2 voxels)


def open_m7():
    return zarr.open(a.m7, mode='r')['2']


def tile_normals(job, tries=6):
    """tile_normals_once with retries: S3 reads over HTTP drop now and then (ServerDisconnectedError)."""
    import time
    for t in range(tries):
        try:
            return tile_normals_once(job)
        except Exception as e:
            if t == tries - 1:
                raise
            print(f'retry {t + 1} tile {job}: {repr(e)[:120]}', flush=True); time.sleep(5 * (t + 1))


def tile_normals_once(job):
    z0, z1, y0, y1, x0, x1 = job
    src = open_m7(); Z, Y, X = src.shape
    lz0, lz1 = max(0, z0 - M), min(Z, z1 + M); ly0, ly1 = max(0, y0 - M), min(Y, y1 + M); lx0, lx1 = max(0, x0 - M), min(X, x1 + M)
    p = np.asarray(src[lz0:lz1, ly0:ly1, lx0:lx1]).astype(np.float32)
    out = np.zeros((2, z1 - z0, y1 - y0, x1 - x0), np.uint8)
    if p.max() < a.min_p:
        return job, out
    ps = ndimage.gaussian_filter(p, a.sigma_g)
    g = [ndimage.sobel(ps, axis=i) for i in range(3)]          # z, y, x
    J = np.empty(p.shape + (3, 3), np.float32)
    for i in range(3):
        for j in range(i, 3):
            J[..., i, j] = J[..., j, i] = ndimage.gaussian_filter(g[i] * g[j], a.sigma_t)
    sl = (slice(z0 - lz0, z0 - lz0 + z1 - z0), slice(y0 - ly0, y0 - ly0 + y1 - y0), slice(x0 - lx0, x0 - lx0 + x1 - x0))
    Jc = J[sl]; near = ndimage.gaussian_filter(p, a.sigma_t)[sl] >= a.min_p
    if not near.any():
        return job, out
    w, v = np.linalg.eigh(Jc[near])                            # ascending eigenvalues
    n = v[..., :, 2]                                           # zyx principal direction
    coh = (w[:, 2] - w[:, 1]) / (w[:, 2] + w[:, 1] + 1e-6)
    n = n * np.where(n[:, 0] < 0, -1.0, 1.0)[:, None]          # nz >= 0, as Lasagna's decoder assumes
    ok = coh >= a.min_coh
    enc = np.clip(np.rint(n * 127 + 128), 1, 255).astype(np.uint8)   # columns z, y, x; never 0 where valid
    enc[~ok] = 0
    out[0][near] = enc[:, 2]                                   # nx
    out[1][near] = enc[:, 1]                                   # ny
    return job, out


def write_store(path, shape, name):
    os.makedirs(path, exist_ok=True)
    json.dump({'zarr_format': 2}, open(os.path.join(path, '.zgroup'), 'w'))
    json.dump({'multiscales': [{'version': '0.4', 'name': name,
                                'axes': [{'name': ax, 'type': 'space', 'unit': 'pixel'} for ax in 'zyx'],
                                'datasets': [{'path': '2', 'coordinateTransformations': [{'type': 'scale', 'scale': [4.0, 4.0, 4.0]}]}]}]},
              open(os.path.join(path, '.zattrs'), 'w'))
    arr = os.path.join(path, '2'); os.makedirs(arr, exist_ok=True)
    if not os.path.exists(os.path.join(arr, '.zarray')):
        json.dump({'zarr_format': 2, 'shape': list(shape), 'chunks': [32, 32, 32], 'dtype': '|u1', 'fill_value': 0, 'order': 'C',
                   'filters': None, 'dimension_separator': '/',
                   'compressor': {'id': 'blosc', 'cname': 'lz4', 'clevel': 5, 'shuffle': 1, 'blocksize': 0}},
                  open(os.path.join(arr, '.zarray'), 'w'))
    return zarr.open_array(arr, mode='r+')


def main():
    src = open_m7(); Z, Y, X = src.shape
    zl0, zl1 = max(0, (a.z[0] - 128) // 4 // 32 * 32), min(Z, -(-(a.z[1] + 128) // 4 // 32) * 32)
    T = a.tile
    jobs = [(z, min(z + T, zl1), y, min(y + T, Y), x, min(x + T, X))
            for z in range(zl0, zl1, T) for y in range(0, Y, T) for x in range(0, X, T)]
    nx = write_store(os.path.join(a.out, 'las_008_nx.ome.zarr'), (Z, Y, X), 'nx')
    ny = write_store(os.path.join(a.out, 'las_008_ny.ome.zarr'), (Z, Y, X), 'ny')
    done = 0
    with ProcessPoolExecutor(a.workers) as ex:
        for (z0, z1, y0, y1, x0, x1), o in ex.map(tile_normals, jobs, chunksize=1):
            if o.any():
                nx[z0:z1, y0:y1, x0:x1] = o[0]; ny[z0:z1, y0:y1, x0:x1] = o[1]
            done += 1
            if done % 50 == 0:
                print(f'{done}/{len(jobs)} tiles', flush=True)
    print('normals written', zl0, zl1, flush=True)
    if a.check:
        rx = zarr.open(a.check, mode='r')['2']; ry = zarr.open(a.check.replace('_nx.', '_ny.'), mode='r')['2']
        zc = (zl0 + zl1) // 2; sl = (slice(zc - 16, zc + 16), slice(0, Y), slice(0, X))
        sx, sy = np.asarray(nx[sl]).astype(np.float32), np.asarray(ny[sl]).astype(np.float32)
        tx, ty = np.asarray(rx[sl]).astype(np.float32), np.asarray(ry[sl]).astype(np.float32)
        both = ((sx > 0) | (sy > 0)) & ((tx > 0) | (ty > 0))
        def vec(ex, ey):
            x = (ex[both] - 128) / 127; y = (ey[both] - 128) / 127; z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
            v = np.stack([z, y, x], -1); return v / np.linalg.norm(v, axis=-1, keepdims=True)
        cosang = np.abs((vec(sx, sy) * vec(tx, ty)).sum(-1))
        ang = np.degrees(np.arccos(np.clip(cosang, 0, 1)))
        print(json.dumps({'check_slab_z_level2': [zc - 16, zc + 16], 'ours_valid': int(((sx > 0) | (sy > 0)).sum()),
                          'lasagna_valid': int(((tx > 0) | (ty > 0)).sum()), 'both': int(both.sum()),
                          'angle_deg_median': float(np.median(ang)), 'angle_deg_p90': float(np.percentile(ang, 90))}), flush=True)


if __name__ == '__main__':
    main()
