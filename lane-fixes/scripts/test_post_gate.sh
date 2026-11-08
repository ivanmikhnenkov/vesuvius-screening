#!/bin/bash
# test_post_gate.sh LANE_BOX_SH : runs s_post from a (patched) lane_box.sh with snap, render, ink and scoring stubbed, on
# 10 planned windings, and prints the gate line and exit code for three cases:
#   fail   - w003 has no snap, w005's render fails every time, w009's fails once (retried), w007's ink fails
#            -> expected "planned 10 rendered 8 inked 7 missing: w003 w005 w007", rc=1
#   sparse - only w005 renders -> expected rc=1 (the unpatched gate passes: "rendered 1 inked 1", rc=0)
#   ok     - all 10 render and ink -> expected "planned 10 rendered 10 inked 10", rc=0
SRC=$(realpath "$1"); T=$(mktemp -d); trap 'rm -rf $T' EXIT
mkdir -p $T/W/envs/vcpy/bin && cat > $T/W/envs/vcpy/bin/python <<'EOF'
#!/bin/bash
case $(basename $1) in   # ink_lane.py: after post.done, ink every finished render except INK_FAIL; window_score.py: no-op
  ink_lane.py) R=$2; M=$3; PD=$(echo "$@" | sed 's/.*--post-done \([^ ]*\).*/\1/')
    while [ ! -f $PD ]; do sleep 0.2; done
    for r in $R/*.zarr; do [ -f $r/.done ] || continue; n=$(basename $r .zarr)
      case " $INK_FAIL " in *" $n "*) continue;; esac; mkdir -p $M/$n; touch $M/$n/done_d0; done;;
esac
EOF
chmod +x $T/W/envs/vcpy/bin/python
eval "$(sed -n '/^s_post() {/,/^}/p' "$SRC")"
snap_tag() { :; }; cache_trim() { :; }; sleep() { command sleep 0.2; }
one_winding() {   # NOSNAP never renders, RFAIL fails every call, FLAKY fails its first call only
  local w=$1 R=$LANE/renders/$2_$1.zarr; [ -f $R/.done ] && return 0
  case " $NOSNAP " in *" $w "*) return 0;; esac
  case " $RFAIL " in *" $w "*) mkdir -p $R; return 0;; esac
  case " $FLAKY " in *" $w "*) [ -f $LANE/flaky_$w ] || { touch $LANE/flaky_$w; mkdir -p $R; return 0; };; esac
  mkdir -p $R; touch $R/.done
}
export -f one_winding
export W=$T/W P=/nonexistent UM=8.64 NICE= TH=4 CORES=4 DRY= FAST_VRAM_GB=3 DS=x S=x Z0=0 Z1=1 V=x VOL=x CACHE_GB=1
for c in fail sparse ok; do
  export LANE=$T/lane_$c NOSNAP= RFAIL= FLAKY= INK_FAIL=
  case $c in
    fail) NOSNAP=w003 RFAIL=w005 FLAKY=w009 INK_FAIL=T_w007;;
    sparse) NOSNAP="w001 w002 w003 w004 w006 w007 w008 w009 w010";;
  esac
  mkdir -p $LANE/out/T/logs $LANE/logs; echo T > $LANE/best_tag
  for i in $(seq -w 1 10); do echo w0$i; done > $LANE/out/T/windings.txt
  s_post; rc=$?
  echo "$c: $(grep -h 'inked' $LANE/logs/lane.log) -> rc=$rc"
done
