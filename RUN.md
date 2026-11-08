# Running the PHerc. 0306B lane with these fixes

How the PHerc0343 positive control was run end to end on a fresh rented box on 2026-11-07: one RTX 4090 (24 GB), root,
CUDA image, >= 150 GB disk. 2.67 h and ~46 GB downloaded from the open-data bucket; stages (s): setup 220, data 874,
fit 6,944, post 962, score 45, triage 232, cards 36. Result: the window holding the published letters ranked first of
113 (w046 x2600, 8 of 18 letters within 0.1 mm of its mesh). That run used an earlier
state of this repository; the one change since in what runs is the post-stage gate (`lane-fixes` row 10), tested
with `lane-fixes/scripts/test_post_gate.sh`.

## 1. The lane at the pinned commit, with the fixes

```bash
apt-get update -qq && apt-get install -y -qq git patch curl
git clone -q https://github.com/ivanmikhnenkov/vesuvius-screening /root/vesuvius-screening
PKG=/root/vesuvius-screening              # this repository
W=/home/liam/projects/vesuvius-work       # the lane's own root (W in x_vast_plan/lane_box.sh)
git clone -q https://github.com/SirProdigle/pherc0306b-first-letters /root/up && git -C /root/up checkout -q 3f60827
mkdir -p $(dirname $W) && cp -r /root/up/discovery $W
cd $W && for p in $PKG/lane-fixes/patches/*.patch; do patch -p1 < $p; done
cp $PKG/normals/make_normals.py $W/x_recipe_erwin/tools/      # NORMALS=syn calls it (the lane ships its own from 9bb6cef)
bash $PKG/lane-fixes/scripts/box_prep.sh                     # old fitter + vc3d_fiber_format, native sources, 343 umbilicus
```

## 2. Config and run

```bash
cat > /root/lane.env <<'EOF'
SCROLL=PHerc0343
Z0=9500
Z1=11000
TB=b1
UM=8.64
SENSE=CW
TRACKS=published
UMB=/home/liam/projects/vesuvius-work/x_recipe_erwin/umb/umb_PHerc0343.json
MAXW=40
WCENTER=48
FACE_GATE=1
CACHE_GB=30
NEED_GB=150
export NORMALS=syn        # sheet normals from m7 (../normals), not the published Lasagna
export INK_MODELS=rv3:1   # Reader v3 alone
export WS_PROCS=6
EOF
nohup bash $W/x_vast_plan/lane_box.sh > /root/lane_box.out 2>&1 &
```

Each stage leaves `/root/lane/stages/<stage>.ok`, and a re-run resumes after the last one (it also retries windings a
failed post stage left). The lane ends with `/root/lane/DONE` or `/root/lane/FAILED`; `logs/lane.log` holds the
planned / rendered / inked counts, and `/root/lane/results.tar` the ranking (`tri_rank.txt`, `tri_rank.json`), cards,
flattened meshes, CT previews and logs. Off-box copies while it runs: `SYNC_HOST=user@host bash
$PKG/lane-fixes/scripts/box_sync.sh /root/lane <ssh key> <dest dir> &`.

## 3. Score the control

```bash
cd /root && tar -xf lane/results.tar
python $PKG/vetting/eval_control.py results $PKG/vetting/p343_letters_xyz.json --hit-mm 0.1   # numpy, scipy, tifffile
```

It prints the top windows with the letters within 0.1 mm of each window's mesh, and the rank of the first that holds
any (a geometric check: it reads no ink).

## A PHerc0175A band

The same, with `cp $PKG/pherc0175a/umb_PHerc0175A.json $W/x_recipe_erwin/umb/` and, in `lane.env`: `SCROLL=PHerc0175A`,
`SENSE=ACW`, `UMB=/home/liam/projects/vesuvius-work/x_recipe_erwin/umb/umb_PHerc0175A.json`, `Z0`/`Z1` = 6900/8400 or 8400/9900 with
`MAXW=120`, or 5400/6900 with `MAXW=40` and `INK_MODELS=hec:1,rv3:1` (the bands in `pherc0175a/`), no `WCENTER`,
`NEED_GB=100`. Each 120-winding band took ~4.6-5 h on one RTX 4090.
