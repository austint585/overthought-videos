#!/usr/bin/env bash
# Hourly poster that uses no Claude usage: the same steps as the overthought-post task (sync, ops/publish.py, commit
# the queue), run by Windows Task Scheduler. publish.py enforces every guardrail (PAUSE, one post an hour, ready or
# approved only, never retries a failed item), so nothing here needs judgment. It never uses vidIQ: items that only
# vidIQ can post (Meta app blocked) wait for a Claude run.
#   bash ops/post_hourly.sh          post the earliest due item, if any
#   bash ops/post_hourly.sh status   say what it would do, post nothing
# Log: pipeline/out/post_hourly.log (gitignored).
cd /c/Users/austi/Desktop/Overthought || exit 1
PY=/c/Users/austi/AppData/Local/Programs/Python/Python313/python.exe
LOG=pipeline/out/post_hourly.log
G="git -c user.name=Claude -c user.email=noreply@anthropic.com"
export GIT_TERMINAL_PROMPT=0 GCM_INTERACTIVE=never PYTHONIOENCODING=utf-8
mode=${1:-next}
stamp=$($PY -c "import sys; sys.path.insert(0, 'ops'); import ig; print(ig.et_now().strftime('%Y-%m-%d %H:%M ET'))" 2>/dev/null || date "+%Y-%m-%d %H:%M")
log() { echo "$stamp $*" >> "$LOG"; echo "$*"; }

if ! $G pull --ff-only -q origin main 2>>"$LOG"; then
    log "pull failed, posted nothing"; exit 1
fi
out=$($PY ops/publish.py "$mode" 2>>"$LOG"); code=$?
log "publish.py $mode exit $code: $out"

if [ "$mode" = next ] && ! git diff --quiet -- ops/queue.json; then
    what=$(echo "$out" | $PY -c "import json,sys; d=json.loads(sys.stdin.read() or '{}'); print(d.get('result','update'), d.get('id',''))" 2>/dev/null)
    $G commit -q -m "Posting run $stamp (script): $what" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" ops/queue.json
    if ! git push -q origin main 2>>"$LOG"; then
        $G pull --no-rebase --no-edit -q origin main 2>>"$LOG" && git push -q origin main 2>>"$LOG" || log "push failed, queue committed locally"
    fi
fi
exit $code
