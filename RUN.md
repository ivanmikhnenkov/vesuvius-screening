# Running the PHerc. 0306B lane with these fixes

On 2026-11-07 I ran the PHerc0343 positive control end to end on a fresh rented box: one RTX 4090 (24 GB), root, a
CUDA image and at least 150 GB of disk. It took 2.67 h and downloaded about 46 GB from the open-data bucket. Stage
times in seconds: setup 220, data 874, fit 6,944, post 962, score 45, triage 232, cards 36. The window holding the
published letters ranked first of 113 (w046 x2600, with 8 of 18 letters within 0.1 mm of its mesh).

That run used an earlier state of this repository. The only change since in the code that runs is the post-stage
gate (`lane-fixes` row 10), which I tested with `lane-fixes/scripts/test_post_gate.sh`.

## 1. Get the lane at the pinned commit and apply the fixes

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

## 2. Configure and run

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

Each stage writes `/root/lane/stages/<stage>.ok`, and a re-run resumes after the last finished stage. A re-run also
retries any windings a failed post stage left behind. The lane ends with `/root/lane/DONE` or `/root/lane/FAILED`.
`logs/lane.log` has the planned, rendered and inked counts. `/root/lane/results.tar` has the ranking (`tri_rank.txt`,
`tri_rank.json`), the cards, flattened meshes, CT previews and logs. To copy results off the box while it runs:
`SYNC_HOST=user@host bash $PKG/lane-fixes/scripts/box_sync.sh /root/lane <ssh key> <dest dir> &`.

## 3. Score the control

```bash
cd /root && tar -xf lane/results.tar
python $PKG/vetting/eval_control.py results $PKG/vetting/p343_letters_xyz.json --hit-mm 0.1   # numpy, scipy, tifffile
```

This prints the top windows with the letters that lie within 0.1 mm of each window's mesh, and the rank of the first
window that holds any. It is a geometric check and reads no ink.

## A PHerc0175A band

Same steps, with `cp $PKG/pherc0175a/umb_PHerc0175A.json $W/x_recipe_erwin/umb/` and these settings in `lane.env`:
`SCROLL=PHerc0175A`, `SENSE=ACW`, `UMB=/home/liam/projects/vesuvius-work/x_recipe_erwin/umb/umb_PHerc0175A.json`,
`NEED_GB=100`, no `WCENTER`, and one of the bands in `pherc0175a/`:
- `Z0`/`Z1` = 6900/8400 or 8400/9900 with `MAXW=120`;
- 5400/6900 with `MAXW=40` and `INK_MODELS=hec:1,rv3:1`.

Each 120-winding band took 4.6-5 h on one RTX 4090.
