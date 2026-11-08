#!/bin/bash
# setup_bench.sh [BENCH_DIR=./bench1447] : everything bench1447.sh needs in one folder (torch, villa, checkpoints, data pinned).
#   - a Python env (uv) with torch and the villa `vesuvius` package at a329895 (ink inference: vesuvius.ink_detection)
#   - checkpoints at fixed revisions: Reader v3 and TRACE v3B sha256-checked, Hecate 9.6 um (+ its hecate.py) pinned by revision
#   - PHerc1447 w058 and w060 from YoussefMoNader/ink-8um-pherc1447-surfaces (layers, labels, v8-in prediction)
#   - Erwin Nieuwlaar's pherc343-first-letters (hecate_prep.py, for the optional Hecate run)
# CPU is enough (torch CPU wheels by default; TORCH_INDEX=https://download.pytorch.org/whl/cu130 for CUDA).
set -euo pipefail
B=$(realpath -m "${BENCH_DIR:-./bench1447}"); mkdir -p "$B"/ckpt "$B"/code "$B"/data
command -v uv >/dev/null || { echo "needs uv (https://docs.astral.sh/uv/)"; exit 1; }
[ -x "$B/venv/bin/python" ] || uv venv -q -p 3.14 "$B/venv"
TI=${TORCH_INDEX:-https://download.pytorch.org/whl/cpu}
# torch and torchvision first, from one index (timm would otherwise pull a PyPI torchvision built for another torch)
uv pip install -q -p "$B/venv/bin/python" torch==2.14.1 torchvision==0.29.2 --index-url "$TI"
uv pip install -q -p "$B/venv/bin/python" zarr==3.4.1 "numpy>=2" tifffile timm einops fsspec aiohttp huggingface_hub \
  numcodecs opencv-python-headless scipy safetensors requests pynrrd imagecodecs scikit-image
if [ ! -d "$B/code/villa/vesuvius/src" ]; then
  git init -q "$B/code/villa" && cd "$B/code/villa" && git remote add origin https://github.com/ScrollPrize/villa.git
  git sparse-checkout init --cone && git sparse-checkout set vesuvius/src
  git fetch -q --depth 1 --filter=blob:none origin a329895ea5e9bde78752e60dbc0a4878dd2ab909 && git checkout -q FETCH_HEAD
fi
[ -d "$B/code/pherc343-first-letters" ] || git clone -q https://github.com/Nieuwlaar/pherc343-first-letters "$B/code/pherc343-first-letters"
(cd "$B/code/pherc343-first-letters" && git checkout -q e8370f1f)
getck() {   # getck PATH URL SHA256
  [ -s "$1" ] && echo "$3  $1" | sha256sum -c --quiet 2>/dev/null && return 0
  curl -fsSL --retry 3 -o "$1" "$2" && echo "$3  $1" | sha256sum -c --quiet || { rm -f "$1"; echo "BAD CHECKSUM $1"; exit 1; }
}
getck "$B/ckpt/reader-v3.pth" https://huggingface.co/domenicor046/reader-v3/resolve/aee1d64bced4eb35546348f3d276b9e2a0b99c46/reader-v3.pth \
  ea405417450abd8ace1b8ff79ebce3adb646c5e48ab95da46844d77efe984d8a
getck "$B/ckpt/trace_v3B_best.pth" https://github.com/Jashann/vesuvius-scrolling/releases/download/v1.0/v3B_best.pth \
  812ffe2b42b3293974052ebbee60a0fe939ca2bfc3f03a517a0bc2e2339e5da2
HEC=https://huggingface.co/scrollprize/hecate/resolve/9cb86e500e944b11a06a7020403cde5dffb5bcb2
[ -s "$B/ckpt/hecate.py" ] || curl -fsSL --retry 3 -o "$B/ckpt/hecate.py" $HEC/hecate.py
[ -s "$B/ckpt/hecate_9.6um.pth" ] || curl -fsSL --retry 3 -o "$B/ckpt/hecate_9.6um.pth" $HEC/hecate_9.6um.pth
DS=https://huggingface.co/datasets/YoussefMoNader/ink-8um-pherc1447-surfaces/resolve/7e4d918712a8d8642a6fdeee45b80217c1e98317
for s in w058 w060; do
  mkdir -p "$B/data/$s/layers" "$B/data/$s/labels" "$B/data/$s/predictions"
  for i in $(seq -w 0 23); do [ -s "$B/data/$s/layers/$i.tif" ] || curl -fsSL --retry 3 -o "$B/data/$s/layers/$i.tif" $DS/$s/layers/$i.tif; done
  for f in labels/inklabels.png labels/mask.png predictions/v8in.png; do [ -s "$B/data/$s/$f" ] || curl -fsSL --retry 3 -o "$B/data/$s/$f" $DS/$s/$f; done
done
PYTHONPATH="$B/code/villa/vesuvius/src" "$B/venv/bin/python" -c "import vesuvius.ink_detection.inference.infer" && echo "SETUP OK: $B"
