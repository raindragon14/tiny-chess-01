#!/usr/bin/env bash
# run_trial.sh <trial 0|1|2> <path-to-main.py> [port]
# Runs one full practice trial locally: env -> engine -> export -> score.
# Requires the unpacked kit (cwd anywhere; env server is found relative to
# KIT_DIR below). Works on Linux/macOS with node 18+ and python3.13.
set -u

TRIAL="${1:?trial 0|1|2}"
ENGINE="${2:?path to main.py}"
PORT="${3:-8077}"
KIT_DIR="${KIT_DIR:-$HOME/tiny-chess-01-kit}"
TRIAL_DIR="$KIT_DIR/practice/trial-$TRIAL"
WORK="${WORK:-/tmp/tiny-chess-rig-$TRIAL}"

[ -x /usr/bin/time ] && true  # no-op portability guard
[ -f "$TRIAL_DIR/input/env/gauntlet.json" ] || { echo "kit not found at $KIT_DIR" >&2; exit 2; }

rm -rf "$WORK" && mkdir -p "$WORK"
MAKEFUN_ENV_DATA_DIR="$TRIAL_DIR/input/env" \
MAKEFUN_STATE_DIR="$WORK/state" \
MAKEFUN_ENV_PORT="$PORT" \
node "$KIT_DIR/program/env/server.mjs" &
ENV_PID=$!
sleep 1.5

START_S=$(date +%s)
MAKEFUN_ENV_URL="http://127.0.0.1:$PORT" python3 "$ENGINE" >/dev/null 2>&1
RC=$?
END_S=$(date +%s)
echo "engine exit=$RC wall=$((END_S-START_S))s"

kill -TERM "$ENV_PID" 2>/dev/null; sleep 1

MAKEFUN_OUTPUT_DIR="$WORK/state/export" \
MAKEFUN_REFERENCE_DIR="$TRIAL_DIR/reference" \
MAKEFUN_SCORES_DIR="$WORK/scores" \
node "$KIT_DIR/program/scorer/score.mjs" 2>&1 | tail -2

cat "$WORK/scores/scores.json" 2>/dev/null || echo "score json missing"
echo "state kept in $WORK"
