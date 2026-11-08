#!/bin/bash
# box_sync.sh LANE KEY DEST [EVERY_S=600] [END_FILE=DONE] : on a rented box, copy the lane's durable outputs to off-box storage
# (SYNC_HOST user@host, SYNC_PORT; DEST relative to the account root) every EVERY_S seconds, and once more when $LANE/END_FILE
# exists. A FAILED lane keeps being synced (it may be restarted); a failed sync is logged to $LANE/ALERTS.
# Durable = the fit (checkpoint + meshes), snapped and flattened meshes, results, timing and logs; never renders/caches.
LANE=$1; KEY=$2; DEST=$3; EVERY=${4:-600}; END=${5:-DONE}
S="ssh -p ${SYNC_PORT:-22} -i $KEY -o StrictHostKeyChecking=accept-new -o ConnectTimeout=30"
H=${SYNC_HOST:?set SYNC_HOST=user@host of the off-box storage}
$S $H "mkdir -p $DEST" 2>/dev/null
while true; do
  cd $LANE || exit 1
  src=$(ls -d fits out results results_rv3 timing.tsv best_tag logs DONE RV3_DONE FAILED 2>/dev/null)   # only what exists
  rsync -aRL --partial --timeout=300 -e "$S" $src $H:$DEST/ 2>> $LANE/logs/box_sync.err   # -L: copy what links point to
  rc=$?; echo "$(date -u +%H:%M) synced rc=$rc: $(echo $src)"
  [ $rc = 0 ] || echo "$(date -u +%FT%H:%M) box_sync: rsync rc=$rc" >> $LANE/ALERTS
  if [ -d fits ]; then                     # verify, don't trust rc: the fit must be off-box once it exists
    n=$($S $H "ls $DEST/fits/*/checkpoint_fitted.ckpt 2>/dev/null | wc -l" 2>/dev/null)
    [ -f fits/*/checkpoint_fitted.ckpt ] 2>/dev/null && [ "${n:-0}" -lt 1 ] && echo "$(date -u +%FT%H:%M) box_sync: fit checkpoint not off-box" >> $LANE/ALERTS
  fi
  [ -f $LANE/$END ] && break
  sleep $EVERY
done
