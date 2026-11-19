# tiny-chess-01 Blueprint (REFINED / LOCKED v2)

Design agreed between owner and agent (Vibe Code session, 2026-11-18; refined
and hardened 2026-11-19). The recorded build session must implement this
spec. **Hard caps are node-based, never clock-based.**

## Goal

A chess engine in one `main.py`, committed size <= 4,096 bytes, repo total
<= 8,192 bytes (excl. `.git`), Python 3.13 stdlib only, deterministic
(node/depth budgets, no wall clock, no unseeded randomness), no model calls.
It speaks HTTP to the env at `$MAKEFUN_ENV_URL`:

- `POST /game {}` -> current game or `{"status":"done",...}`
- `POST /move {"game": n, "move": "<uci>"}` -> env answers with house move(s)
- `POST /resign {"game": n}` -> give up a game (last-resort unrecoverable fallback only)

Rebuild the internal position from the response's `start_fen` + `moves` list
each turn (robust, cheap, and reconstructs exact repetition/halfmove state).
Cross-check our chosen move against the response's `legal_moves`; if absent
(bug shield), play the first listed legal move.

Targets: practice Elo >= 1,154 (floor) minimum; realistic stretch:
beat nodes-500k (anchor 1596) and challenge/beat nodes-1M/2M (1667/1712).
House baseline (sunfish-4k) practice mean ~1,365 (6-game trials).

## 1. Board & State (0x88 + Piece Lists)

- `list` of 128 ints; `sq = (row << 4) | col`; on-board iff `(sq & 0x88) == 0`;
  `file = sq & 7`, `rank = 7 - (sq >> 4)` for index 0 = a8.
- **Lightweight piece lists**: maintain per-side active piece-square lists
  (or compact bitmask/index table) updated in O(1) on `make`/`unmake` so
  movegen and leaf eval iterate only active pieces (~16-32) instead of
  scanning all 128 squares.
- Attack generation may use the difference trick: `d = sq1 - sq2 + 0x77`
  injectively indexes `(drow, dcol)` pairs for a 240-entry attack table,
  or reverse ray/offset checks from the king square in `in_check()`.
- Side: +1 / -1 (or 0/1). Castling rights: 4-bit mask; per-square rights
  masks applied on `make` (squares a1:e1:h1 / a8:e8:h8).
- Track: side, rights, ep square, halfmove clock (50-move = 100 plies),
  both king squares, Zobrist key 64-bit, and pawn file-occupancy bitmasks
  (for fast pawn-structure / open-file eval).

## 2. Zobrist & Determinism

- Zobrist keys from a fixed-seed PRNG (`random.Random(<const>)` or a
  hand-rolled LCG). NEVER use built-in `hash()` (`PYTHONHASHSEED` varies).
- Key covers piece-square, side-to-move, castling rights (16), ep file (9).
- **Draw checks BEFORE TT probe**: inside search, check 50-move
  (`halfmove >= 100`), insufficient material (no pawn/rook/queen; <= 1 minor;
  or same-colour bishops only), and repetition (twofold in search path via
  Zobrist history stack; threefold at root) BEFORE probing TT so TT hits
  from other move histories never blind the search to draws.

## 3. Incremental Evaluation (PeSTO + High-ROI Leaf Terms)

- PeSTO tables (mg/eg) for P,N,B,R,Q,K, expanded at startup to 128-length
  lists per piece code (both colours) with black mirror `sq ^ 112`.
- Incrementally maintained: `mg`, `eg`, `phase`, `key`, `mat_diff`
  (standard points 1/3/3/5/9). Restore from a snapshot tuple on `unmake`.
- Tapered base: `p = min(phase, 24); score = (mg*p + eg*(24-p)) // 24`
  plus cheap leaf extras:
  - Bishop pair `+30`, tempo `+10`.
  - **Passed pawns**: rank-scaled bonus (with extra weight in endgame +
    unblocked/king-proximity bonus).
  - **Pawn structure & rook files**: doubled/isolated pawn penalties via
    cheap pawn-file masks; rook on open/semi-open file and 7th rank bonuses.
  - **King safety**: middlegame pawn-shield / open-file penalty near king.
  - **Mop-up eval**: when winning decisively with few/no opponent pawns,
    reward driving the enemy king to edges/corners and closing king distance
    (accelerates mates for the *plies-to-spare* tie-break).
- **Eval-based asymmetric contempt**: draws score `-20 cp` when our side
  has `mat_diff > 0` OR root/static eval > `+30 cp` (avoids cheap draws
  against weaker rungs even at equal material); `+0` otherwise.
- **Adjudication awareness** (env adjudicates at 200 plies for material
  lead >= 5 standard points; game ply derived from env `plies` field):
  - When `plies >= 150` and `mat_diff` is `+1..+4`, add a small bonus for
    pushing material lead toward `>= +5`.
  - When `plies >= 150` and `mat_diff <= -5`, avoid passive lines that let
    the clock hit 200 plies (prefer complications/material recovery; value a
    draw at `0` strongly over an adjudicated loss).

## 4. Move Generation & Legality

- Pseudo-legal generation over active piece lists (piece-delta loops over
  offsets); **clean `in_check()` validation everywhere** (`make` + `in_check`
  check for all moves; no king-capture worm-hole inside search, keeping
  check extensions, NMP/RFP, qsearch evasions, and stalemate fully sound).
- Castling is generated only when fully legal: rights present, path empty,
  king not currently in check, path squares not attacked.
- Full rules: en passant (including discovered-check legality), promotions
  q/r/b/n (generate all; ordering prefers q then n), 50-move, insufficient
  material, threefold repetition.

## 5. Search (5-layer, non-generic, node-budgeted)

### Budgets (all deterministic, no wall clock)
- Measure `NPS_worst` offline on a 1-CPU-pruned run (`taskset -c 0`, dense
  perft + deep check-evasion positions). Include a `0.8` grading-CPU factor:
  - `B_base = floor(2.5 s * NPS_worst * 0.8)` (~400 moves across an 8-game
    trial stays comfortably under the 1,800 s trial limit).
  - `B_hardcap = floor(5.0 s * NPS_worst * 0.8)` (strict ceiling on every
    move, giving >2x margin against the 10 s per-move timeout).
- Deterministic per-move budget modifiers:
  - Forced move (exactly 1 legal): play immediately, `0` nodes.
  - Narrow (`<= 4` legal): `0.4 * B_base`.
  - Midgame phase `10..22`: `1.3 * B_base`.
  - Inter-iteration score swing `> 80 cp`: extend `+40%` for next iteration.
  - Always clamp final move budget: `budget = min(budget, B_hardcap)`.
- **Iterative deepening, soft stop & safe partial iterations**:
  - **Soft stop**: before starting `depth + 1`, if `nodes_used >= 0.45 * budget`,
    stop cleanly and return the completed `depth` move.
  - **Partial-iteration handling**: if an iteration hits `budget` mid-way,
    **keep** the partial iteration's `best_move` only if root move 1 finished
    without aborting OR another root move finished and strictly raised `alpha`
    above the previous iteration's score; otherwise discard the partial
    iteration and return the last completed depth's best move. If depth 1
    itself aborts, fall back to `legal_moves[0]`.
- **No `time.time()` / `perf_counter()` anywhere.**

### Core & TT Safety
- Negamax + alpha-beta; PVS (full window for move 1, zero-window
  `(-alpha-1, -alpha)` for the rest; re-search on fail-high).
- Aspiration windows `+/-50 cp` from `depth >= 4`, widen on fail (standard
  doubling), no root aborts below depth 1.
- TT: `dict` keyed by Zobrist -> `(depth, flag, score, best_move)`, flags
  EXACT/LOWER/UPPER; store mate scores normalized as `MATE - ply` (and
  adjust on read) so fastest mates are chosen (maximizes *plies to spare*).
- **TT safety rules**:
  - **No TT value cutoffs in PV nodes** (`is_pv`): probe TT only for move
    ordering in PV nodes so exact PV lines and repetition draws are sound.
  - Verify TT `best_move` is valid/pseudo-legal for the current side/square
    before ordering it first.
  - **Between-moves RAM guard**: check `if len(tt) > 800_000: tt.clear()`
    **only at root between moves** (never mid-search, which wipes the PV).
    Reset/clear killer, history, and counter-move tables when `game` id changes.

### Stack pruning / extensions
- IIR: TT miss at `depth >= 4` -> `depth -= 1`.
- Check extension: `+1` ply when in check (cap total extensions per branch,
  e.g. `<= 8` or `ply < 2 * root_depth`).
- RFP at `depth <= 3` (`static_eval >= beta + margin`, non-PV, not in check).
- Razoring at `depth <= 2` (`eval + margin < alpha` -> drop to qsearch).
- NMP: `R = 2 + (depth >= 6)` only when `can_null` is True (**no consecutive
  null moves**), `depth >= 3`, non-PV, not in check, side has a non-pawn
  piece, and `static_eval >= beta`.
- Futility pruning for quiet moves at shallow depth.
- LMR via precomputed log table `LMR[d][m]` (built once at startup using
  stdlib `math.log`, deterministic); re-search on fail-high.

### Move ordering (5 tiers) + Gated SEE-lite
1. TT move (verified valid).
2. Good captures (`SEE >= 0`) & promotions, ordered MVV-LVA.
3. 2 killer moves (per ply) + counter-move (last opponent move table).
4. Quiet moves: gravity history + PeSTO PST delta.
5. Bad captures (`SEE < 0`).
- **Gated SEE-lite**: only invoke the victim/attacker swap evaluator when
  `attacker_val > victim_val` (captures with `victim_val >= attacker_val` are
  trivially `SEE >= 0`), keeping Python per-node overhead minimal.

### Quiescence
- Stand-pat + delta pruning + skip bad captures via gated SEE-lite (`SEE < 0`);
  generate captures and queen promotions only.
- **Bounded check evasions**: when in check in qsearch and `qply < 6`,
  search all evasions (no stand-pat); at `qply >= 6`, cap evasion expansion
  (return static eval / captures only) to prevent zig-zag check explosions.

## 6. HTTP driver & Resilience

- Talk to `$MAKEFUN_ENV_URL` using `http.client.HTTPConnection` with read
  timeout `> 10 s` (e.g., `15 s`).
- **Node.js `keepAliveTimeout` protection**: Node's `http.Server` closes idle
  keep-alive sockets after 5 s; use fresh connections per request (or
  `Connection: close`, `< 0.2 ms` on localhost) OR auto-reconnect & retry once
  on `RemoteDisconnected` / `ConnectionResetError` / `BrokenPipeError`
  (re-querying `/game` if a `/move` reply drops so we never double-submit or
  resign a live game).
- Loop: `/game` -> rebuild position from `start_fen` + `moves` -> search ->
  cross-check `legal_moves` -> `/move` -> repeat until `status == "over"`,
  then `/game` until `status == "done"`.
- Parse `move_limit_ms`, `max_plies`, and `plies` from the env response.
- **Crash-safety without needless resigns**: a 4xx changes nothing and the
  move clock keeps running (never spam). If search raises an unexpected
  exception in one game, catch it and fall back to `legal_moves[0]` rather
  than resigning; only `/resign` that game if move submission itself fails
  unrecoverably, and keep the outer trial loop alive.

## 7. Byte budget & packing

- Write the source clean (~10-14 KB readable, compactly encoded PeSTO tables),
  then pack with the kit CLI only:
  `node cli/makefun.mjs compress <source> --out main.py` (lzma).
  Expected packed size ~2,800-3,800 B. The kit compress command MUST be run
  as its own step after the last source edit (transcript-check requirement),
  and the source stays beside the sessions (need not be committed).
- **Explicit byte-trim fallback order** if packed `main.py > 3,950 B`:
  1. Compact PeSTO table encoding / identifier & whitespace minification.
  2. Drop counter-move table (keep 2 killers + gravity history).
  3. Simplify king pawn-shield / rook-file eval (keep PeSTO + passed pawns + mop-up).
  4. Downgrade gated SEE-lite to MVV-LVA + simple recapture/defended check.
- Submitted snapshot: `main.py` + `LICENSE` (MIT) + minimal `README.md` only.
  Check sizes: `main.py <= 4,096 B`, total (excl. `.git`) <= 8,192 B.
- `.makefun/owner.json` only if the repo owner is not the make.fun
  account's GitHub login (verify with `GET /api/agents/me` after the
  account connect).

## 8. Validation gates (all local, before first submission)

1. **Perft**: startpos 20/400/8,902/197,281 (d4 optional 4,865,609);
   Kiwipete 48/2,039/97,862; Kiwipete-mirror (same counts); pos3
   `8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -` 14/191/2,812/43,238; pos4
   `r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1`
   6/264/9,467; pos5 `rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8`
   44/1,486/62,379; pos6 `r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10`
   46/2,079/89,890 (verify underpromotions, EP discovered checks, castling).
2. **Determinism A/B**: two separate processes, different
   `PYTHONHASHSEED`, same positions -> byte-identical move lists.
3. **Speed**: measure `NPS_worst` (dense perft + deep check-evasion
   positions) with `taskset -c 0`; set `B_base = floor(2.5 s * NPS_worst * 0.8)`
   and `B_hardcap = floor(5.0 s * NPS_worst * 0.8)`.
4. **Local Elo**: run `tools/run_trial.sh` on all 3 practice trials
   (`practice/trial-{0,1,2}`). Targets: >= 1,154 on each; then beat the
   baseline practice spread (1,253-1,451 on 8-game set; ~1,365 mean on
   the 6-game practice set) and push toward nodes-1M/2M.
5. **t-test gate** (for the final reward claim, not before submit): mean
   Elo over 6 scored instances must beat sunfish-4k with 90% paired
   t-interval > 0 => paired t > 2.015 (df = 5). Track per-instance
   paired leads during local rehearsal against a local sunfish-4k clone
   (reference: github.com/thomasahle/sunfish @e396948, nnue_4k/pst_entry.py)
   run under a small driver against the same protocol - for testing only,
   its GPL code never enters our repository.

## 9. Known traps (all bitten by earlier entrants)

- Payload packed by anything other than `makefun compress` fails the
  authorship check. Run it as the agent's own separate command.
- Any wall-clock use (search stop, "safety timers") risks replay failure.
- Built-in `hash()` breaks TT across processes.
- Repo files over the caps are refused at intake (sizes are reported).
- README or About with make.fun branding is refused (does not burn quota).
- A move taking > 10 s loses on time; a move near 10 s is a replay risk.
- Submit quota: 5/day, 10 total; the LAST submission before the deadline
  (2026-11-24 17:00 UTC) is the final entry - submit v1 early for a
  practice benchmark, keep >= 1 slot in reserve on the final day.
