#!/bin/bash
# bench1447.sh SEG [DIRS] : Reader v3, TRACE v3B (and Hecate with HEC=1) on a labelled PHerc1447 surface (8.64 um /
# 116 keV, the protocol of the 8.64 um eligible scrolls; none of these models trained on PHerc1447), cropped to the
# labelled box, plus the dataset's own v8-in prediction cropped the same way. Then bench_score.py: AUC, AP, false ink at
# 80% recall per model and per fusion. Run setup_bench.sh first (same BENCH_DIR). CPU or GPU (CUDA_VISIBLE_DEVICES).
set -uo pipefail
SEG=$1; DIRS=${2:-reverse}
B=$(realpath -m "${BENCH_DIR:-./bench1447}"); PY=$B/venv/bin/python; CK=$B/ckpt; H=$(cd "$(dirname "$0")" && pwd)
export PYTHONPATH=$B/code/villa/vesuvius/src
[ -x $PY ] && [ -d $B/data/$SEG/layers ] || { echo "run setup_bench.sh first (BENCH_DIR=$B)"; exit 1; }
cd $B/data; mkdir -p out tmp
[ -d $SEG.zarr/0 ] || $PY $H/bench_prep.py $SEG $SEG.zarr || exit 1
for d in $DIRS; do
  for m in reader-v3:reader-v3.pth trace:trace_v3B_best.pth; do
    n=${m%%:*}; [ -s out/${SEG}_${n}_$d.tif ] && continue
    t0=$(date +%s)
    (cd tmp && TMPDIR=$B/data/tmp $PY -m vesuvius.ink_detection.inference.infer $B/data/$SEG.zarr $CK/${m#*:} $B/data/out/${SEG}_${n}_$d.tif \
      --overlap 0.5 --blend-mode hann --batch-size 4 --direction $d --layer-start 4 --layer-end 21 --no-compile) > out/${SEG}_${n}_$d.log 2>&1
    rc=$?; echo "$n $d rc=$rc $(( $(date +%s) - t0 ))s"; [ $rc = 0 ] || { tail -5 out/${SEG}_${n}_$d.log; exit 1; }
  done
  [ "${HEC:-0}" = 1 ] || continue   # HEC=1: also Hecate (resampled to 9.6 um; ~70 min on 12 CPU threads)
  [ -s out/${SEG}_hecate_$d.png ] && continue
  t0=$(date +%s)
  $PY $B/code/pherc343-first-letters/ink/scripts/hecate_prep.py --src $SEG.zarr --out tmp/${SEG}_hec.zarr --native-um 8.64 --native-um-z 8.64 \
      --target-um 9.6 --z-center 11.5 --nz 16 > out/${SEG}_hecate_$d.log 2>&1 || { tail -5 out/${SEG}_hecate_$d.log; exit 1; }
  R=""; [ $d = reverse ] && R=--reverse
  (cd tmp && $PY $CK/hecate.py --checkpoint $CK/hecate_9.6um.pth --input $B/data/tmp/${SEG}_hec.zarr --spacing-um 9.6 \
      --output $B/data/out/${SEG}_hecate_$d.png --device ${HEC_DEVICE:-cpu} --batch-size 4 $R) >> out/${SEG}_hecate_$d.log 2>&1
  rc=$?; echo "hecate $d rc=$rc $(( $(date +%s) - t0 ))s"; [ $rc = 0 ] || { tail -5 out/${SEG}_hecate_$d.log; exit 1; }
done
$PY $H/bench_score.py $SEG $DIRS > out/${SEG}_score.log || { tail -5 out/${SEG}_score.log; exit 1; }
echo "scores: $B/data/out/${SEG}_scores.json"
echo BENCH DONE
