#!/bin/bash
# box_prep.sh : on a fresh rented box (root), after the lane code is rsynced to /home/liam/projects/vesuvius-work.
# Adds what the 306B lane expects but its repo doesn't ship: the old spiral fitter (villa 0fb38c45 + Erwin
# Nieuwlaar's shell-optional patch) as x_recipe_erwin/spiral_old, the native module sources, the 343 recipe, umbilici.
set -euo pipefail
W=/home/liam/projects/vesuvius-work; X=$W/x_recipe_erwin; C=/home/liam/projects/code
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq git rsync curl ca-certificates build-essential cmake ninja-build >/dev/null
mkdir -p $C $X/umb $W/third_party
if [ ! -d $C/villa_old/volume-cartographer ]; then
  git init -q $C/villa_old && cd $C/villa_old && git remote add origin https://github.com/ScrollPrize/villa.git
  git sparse-checkout init --cone && git sparse-checkout set volume-cartographer/scripts/spiral volume-cartographer/python/vc vesuvius/src/vc3d_fiber_format
  git fetch -q --depth 1 --filter=blob:none origin 0fb38c45b488e192566ea83ae36369cb6db92652 && git checkout -q FETCH_HEAD
fi
[ -d $W/third_party/pherc343-first-letters ] || git clone -q --depth 1 https://github.com/Nieuwlaar/pherc343-first-letters $W/third_party/pherc343-first-letters
if [ ! -f $X/spiral_old/fit_spiral.py ]; then
  cp -r $C/villa_old/volume-cartographer/scripts/spiral $X/spiral_old
  (cd $X/spiral_old && patch -p4 < $W/third_party/pherc343-first-letters/mesh/fit_spiral_shell_optional.patch)
fi
[ -d $X/spiral_old/vc3d_fiber_format ] || cp -r $C/villa_old/vesuvius/src/vc3d_fiber_format $X/spiral_old/
mkdir -p $X/native/src && cp $C/villa_old/volume-cartographer/python/vc/{track_crossings,track_store,spiral_sampling}.cpp $X/native/src/
cp $W/third_party/pherc343-first-letters/inputs/umbilicus_PHerc0343.json $X/umb/umb_PHerc0343.json
nproc; free -g | head -2; df -h / | tail -1; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo BOX_PREP_OK
