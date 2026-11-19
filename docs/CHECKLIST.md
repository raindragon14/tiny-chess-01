# Runbook for the recorded build session

Everything a recorded harness session (Claude Code / Codex / Cursor /
Cline, on the owner's machine) needs. Read BLUEPRINT.md first; this file
is the operational checklist. The final code-writing session MUST be a
recorded harness session (tiny-chess-01 sets handed_over_places = none,
so hand-over sessions take no paid place).

## 0. Environment setup (owner, once)

```bash
# kit (contains env, scorer, generator, starter, CLI, practice trials)
curl -sSL "https://make.fun/c/tiny-chess-01/kit" | tar xz
cd tiny-chess-01-kit

# repo with blueprint + tools
git clone https://github.com/raindragon14/tiny-chess-01 && cd tiny-chess-01
git checkout main   # docs/ and tools/ live on main (PR #1 merged)
```

## 1. Local rig (already validated by the design agent)

```bash
# from the kit dir, one terminal per trial; trial in 0..2
rm -rf /tmp/state0 && mkdir -p /tmp/state0
MAKEFUN_ENV_DATA_DIR=$PWD/practice/trial-0/input/env \
MAKEFUN_STATE_DIR=/tmp/state0 MAKEFUN_ENV_PORT=8077 \
node program/env/server.mjs &

# other terminal: run the engine (arg env url, trial engine path)
MAKEFUN_ENV_URL=http://127.0.0.1:8077 python3 PATH/TO/main.py

# after games finish: SIGTERM the env, then score
kill -TERM %1
MAKEFUN_OUTPUT_DIR=/tmp/state0/export \
MAKEFUN_REFERENCE_DIR=$PWD/practice/trial-0/reference \
MAKEFUN_SCORES_DIR=/tmp/scores0 node program/scorer/score.mjs
cat /tmp/scores0/scores.json            # {"elo":...,"wins":...}
```

House thinking inside the kit env is negligible (p50 1 ms; see
docs/MEASUREMENTS.md): the whole 1,800 s trial wall budget is ours.

## 2. Build loop (the recorded session's job)

1. Implement per BLUEPRINT.md. Validate with the perft suite FIRST
   (movegen bugs poison everything else).
2. Determinism A/B: two runs with different `PYTHONHASHSEED`, compare
   move lists byte-for-byte.
3. Measure `NPS_worst`, set `B_base` and `B_hardcap` (node-based only, no clocks).
4. Iterate: `tools/run_trial.sh` over trials 0,1,2 -> Elo >= 1,154 each,
   then push toward nodes-500k (1596) / nodes-1M/2M territory.
5. Pack: `node cli/makefun.mjs compress <source> --out main.py`
   (separate command, after the last edit; source stays uncommitted in
   the working tree beside the sessions).
6. Size gate: `main.py` <= 4,096 B (target <= 3,950 B); repo snapshot
   <= 8,192 B total (LICENSE MIT + minimal README only in the commit).
7. Commit on `main` exactly: `main.py`, `LICENSE`, `README.md`
   (+ `.makefun/owner.json` only if `GET /api/agents/me` shows the make.fun
   account's GitHub login differs from `raindragon14`).

## 3. Submit (needs the account connect)

```bash
cd tiny-chess-01-kit        # unpacked kit
node cli/makefun.mjs login  # prints "Open <link> and approve code XXXX-XXXX..."
# owner opens the link while signed in as @muhammad-reihan-pandanarang
# and approves (the agent wallet connects to the account)

node cli/makefun.mjs bundle --repo ../tiny-chess-01 \
  --harness <name> --harness-version <v> --provider <provider> \
  --model <model-id> --effort <level>
node cli/makefun.mjs submit --repo ../tiny-chess-01
```

- Bundle collects instruction files + system prompt + run record; pass
  `--mcp none` if the build session used no MCP servers.
- Quota: 5 submissions/day, 10 total; v1 goes in as soon as it passes the
  floor; the FINAL entry is the last one before 2026-11-24 17:00 UTC -
  keep >= 1 slot in reserve on the last day.
- Check the entry's practice Elo after intake
  (`node cli/makefun.mjs status`); a retry needs the same-day quota.

## 4. Definition of done

- [ ] perft suite green on all 7 positions (incl. Kiwipete-mirror & edge cases)
- [ ] no `time.` / `hash()` in search path; single fixed-seed PRNG
- [ ] draw checks before TT probe; no TT cutoffs in PV nodes; TT clear only between moves
- [ ] `qply` evasion cap, branch extension cap, and no-consecutive-NMP verified
- [ ] A/B determinism identical
- [ ] HTTP driver handles Node keep-alive disconnects & falls back to `legal_moves[0]`
- [ ] 3 practice trials each Elo >= 1,154 locally, then submitted
- [ ] packed main.py <= 4,096 B and snapshot <= 8,192 B
- [ ] transcripts bundled with a real run record; submitted; practice
      Elo confirmed >= 1,154 on the make.fun side before the deadline
