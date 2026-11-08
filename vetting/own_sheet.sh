#!/bin/bash
# own_sheet.sh SCROLL X Y Z TAG UMB VOL_URL [GENS=120] : own-sheet check of a candidate: GrowPatch seeded at (X,Y,Z) on the
# m7 prediction (no snap), 41-layer render from the CT, reading face by the umbilicus rule, then deepread.py (Reader v3,
# TRACE v3B, v8-in) and auto_vet.py over the whole patch. Outputs in /root/own_$TAG; writes OWN_DONE, alerts on failure.
set -uo pipefail
S=$1; X=$2; Y=$3; Z=$4; T=$5; UMB=$6; VOL=$7; G=${8:-120}
W=${LANE_W:-/home/liam/projects/vesuvius-work}; O=${OUT_ROOT:-/root}/own_$T; mkdir -p $O/logs
alert() { echo "$(date -u +%FT%H:%M) own_sheet $T: $*" >> $O/ALERTS; exit 1; }
export PATH=$W/envs/vcpy/bin:$PATH PYTHONPATH=${VILLA:-/home/liam/projects/villa}/vesuvius/src OMP_NUM_THREADS=8
mkdir -p $O/vc3dcfg $O/vcache; printf '[viewer]\nremote_cache_dir=%s/vcache\n' $O > $O/vc3dcfg/VC3D.ini; export VC3D_CONFIG_DIR=$O/vc3dcfg
m=$(nice -n 10 python $W/fl/scripts/sqm_grow.py $S $X $Y $Z own_$T --gens $G --nosnap | tail -1)
[ -n "$m" ] && [ "$m" != NONE ] || alert "GrowPatch produced no mesh (see $W/fl/sqm/${S}_own_$T/grow.log)"
echo "mesh $m" > $O/mesh.txt
nice -n 10 $W/vc_build_main/bin/vc_render_tifxyz --volume $VOL --prefetch-remote --group-idx 0 --scale 1 --segmentation $m \
   --num-slices 41 --slice-step 1 --cache-gb 6 --zarr-output $O/patch.zarr > $O/logs/render.log 2>&1 || alert "render failed"
face=$(python - "$m" "$UMB" <<'PY'
import sys, json, numpy as np, tifffile
t, umb = sys.argv[1], sys.argv[2]
P = np.stack([tifffile.imread(f'{t}/{c}.tif') for c in 'xyz'], -1).astype(np.float64); P[P[..., 0] == -1] = np.nan
n = np.cross(P[1:-1, 2:] - P[1:-1, :-2], P[2:, 1:-1] - P[:-2, 1:-1])
d = json.load(open(umb)); cp = d['control_points'] if isinstance(d, dict) else d
cp = sorted((p['z'], p['x'], p['y']) for p in cp); uz, ux, uy = (np.array(v, float) for v in zip(*cp))
q = P[1:-1, 1:-1]; rad = np.stack([q[..., 0] - np.interp(q[..., 2], uz, ux), q[..., 1] - np.interp(q[..., 2], uz, uy), np.zeros(q.shape[:2])], -1)
s = np.sign((n * rad).sum(-1)); s = s[np.isfinite(s) & (s != 0)]
print('reverse' if (s > 0).mean() >= 0.5 else 'forward')    # the lane's rule: ink reads towards the umbilicus
PY
)
echo "face $face" >> $O/mesh.txt
Wd=$(python -c "import zarr; print(zarr.open('$O/patch.zarr', mode='r')['0'].shape[2])")
python $W/vet/deepread.py $O/patch.zarr 0 $Wd $face $O/deep_$T.jpg > $O/logs/deep.log 2>&1 || alert "deepread failed"
python $W/vet/auto_vet.py --one $O/patch.zarr 0 $face --win $Wd --out1 $O/vet_$T.json > $O/logs/vet.log 2>&1 || alert "auto_vet failed"
date +%s > $O/OWN_DONE
