# Measured facts & anchors (from the kit + local rig, 2026-11-18)

## House ladder anchors (from practice/trial-*/reference/gauntlet.json)

| rung | opponent    | anchor | rule                                    |
|------|-------------|--------|-----------------------------------------|
| 1    | depth-2     | 855    | alpha-beta, fixed depth 2               |
| 2    | depth-3     | 1073   | fixed depth 3                           |
| 3    | depth-4     | 1199   | fixed depth 4                           |
| 4    | nodes-100k  | 1392   | deepen while next depth <= 100k nodes   |
| 5    | nodes-250k  | 1497   | idem, 250k                              |
| 6    | nodes-500k  | 1596   | idem, 500k                              |
| 7    | nodes-1M    | 1667   | idem, 1M (final only)                   |
| 8    | nodes-2M    | 1712   | idem, 2M (final only)                   |

Below the ladder: random 0, greedy 348, depth-1 696.

- House search behaviour: capture+promotion and every-check-reply
  extensions at leaves; ordering by TT, captures, killers; eval =
  material (P100 N320 B330 R500 Q900) + piece-square terms + bishop pair;
  repetition/50-move inside search score 0. No clock.
- Elo anchors come from a 2,720-game Bradley-Terry round-robin
  (kit: program/generator/calibration.json).

## Baseline (house) = sunfish-4k

- Source: github.com/thomasahle/sunfish @e396948, nnue_4k/pst_entry.py,
  GPL-3.0, stripped + lzma-packed = 3,649 B, fixed 50k nodes/move.
- Practice ratings on the 3 instances: 1,326 / 1,396 / 1,253
  (8-game set, mean 1,325); on the 6-game practice trials:
  1,364 / 1,451 / 1,279 (mean 1,365). It lost ALL games vs nodes-1M
  and nodes-2M on practice.

## Timing (local kit env, measured 2026-11-18, starter engine, trial-0)

- House thinking per env call: p50 = 1 ms, p95 = 3 ms, max = 6 ms
  (n = 100 env calls, one 6-game trial). Total house think in a 6-game
  trial: 0.14 s. The rules confirm the env runs the house fast; plan as
  if the whole 1,800 s trial wall budget is ours.
- Rig round-trip cost per env call: < 2 ms (localhost).
- Starter entry (1-ply maybe-capture): Elo 0 on trial-0 (0/6, all by
  checkmate) - a floor, not a target.

## Competition facts

- Practice floor to reach the final: Elo >= 1,154.
- Reward gate: mean Elo over the 6 scored instances > baseline mean with
  90% paired t-interval > 0 => paired t > 2.015 (df = 5).
- Games: 8 per trial (6 in practice), one per opponent, colours
  alternating; 40 book openings x 8 plies; adjudication at 200 plies for
  a >= 5-point material lead (P1 N3 B3 R5 Q9).
- Move limit 10 s; trials of contenders are replayed byte-for-byte.
- Quota: 5 submissions/day, 10 total; deadline 2026-11-24 17:00 UTC =
  2026-11-25 00:00 WIB.
- Elo formula: trial Elo = R maximizing sum over games of
  1/(1+10^((anchor-R)/400)) = scored points; floor 0, cap 2,112.
- Tie-break: plies to spare (sum of 200-ply cap minus game length over
  won games), then earlier receipt.

## Leaderboard snapshot (2026-11-18, practice phase)

- Top ~24 entries all at Elo 2,110 (cap; rounded display) - practice
  phase is saturated; ranks currently separated only by plies to spare
  (leader 1,082). The final (6 fresh drand openings + replay) is where
  the tournament is decided; opening-trap books overfit to the 3
  practice instances do not transfer - search + eval quality does.
- 18,235 agents on the bounty; submission count 18,324.
