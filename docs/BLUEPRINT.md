# tiny-chess-01 Blueprint (LOCKED)

Design agreed between owner and agent (Vibe Code session, 2026-11-18).
The recorded build session must implement exactly this. One amendment is
already locked in: **hard caps are node-based, never clock-based**.

## Goal

A chess engine in one `main.py`, committed size <= 4,096 bytes, repo total
<= 8,192 bytes (excl. `.git`), Python 3.13 stdlib only, deterministic
(node/depth budgets, no wall clock, no unseeded randomness), no model calls.
It speaks HTTP to the env at `$MAKEFUN_ENV_URL`:

- `POST /game {}` -> current game or `{"status":"done",...}`
- `POST /move {"game": n, "move": "<uci>"}` -> env answers with house move(s)
- `POST /resign {"game": n}` -> give up a game (we never resign)

Rebuild the internal position from the response's `moves` list each turn
(robust, cheap). Cross-check our chosen move against the response's
`legal_moves`; if absent (bug shield), play the first listed legal move.

Targets: practice Elo >= 1,154 (floor) minimum; realistic stretch:
beat nodes-500k (anchor 1596) and approach nodes-1M/2M (1667/1712).
House baseline (sunfish-4k) practice mean ~1,365 (6-game trials).

## 1. Board & State (0x88)

- `list` of 128 ints-or-chars; `sq = (row << 4) | col`; on-board iff
  `(sq & 0x88) == 0`; `file = sq & 7`, `rank = 7 - (sq >> 4)` for index 0 = a8.
- Attack generation may use the difference trick: `d = sq1 - sq2 + 0x77`
  injectively indexes (drow, dcol) pairs for a 240-entry attack table.
- Side: +1 / -1 (or 0/1). Castling rights: 4-bit mask; per-square rights
  masks applied on `make` (squares a1:e1:h1 / a8:e8:h8).
- Track: side, rights, ep square, halfmove clock (50-move = 100 plies),
  both king squares, Zobrist key 64-bit.

## 2. Zobrist & Determinism

- Zobrist keys from a fixed-seed PRNG (`random.Random(<const>)` or a
  hand-rolled LCG). NEVER use built-in `hash()` (PYTHONHASHSEED varies).
- Key covers piece-square, side-to-move, castling rights (16), ep file (9).
- Repetition: keep a Zobrist stack of the game history inside the search
  path; twofold-in-search scores 0 (house-scorer semantics), threefold at
  root is a draw by env rules anyway.
- Halfmove clock >= 100 -> score 0 inside search.
- Insufficient material (no pawn/rook/queen; <=1 minor; same-colour bishops)
  -> score 0 inside search (env adjudicates instantly; we must not
  "win" nothing while burning plies).

## 3. Incremental Evaluation (PeSTO tapered, O(1))

- PeSTO tables (mg/eg) for P,N,B,R,Q,K, expanded at startup to 128-length
  lists per piece code (both colours) with black mirror `sq ^ 112`.
- Incrementally maintained: `mg`, `eg`, `phase`, `key`, `mat_diff`
  (standard points 1/3/3/5/9). Restore from a snapshot tuple on unmake
  (snapshot: captured piece, rights, ep, key, mg, eg, phase, mat_diff).
- Leaf eval: `p = min(phase, 24); score = (mg*p + eg*(24-p)) // 24`
  plus cheap O(1) extras computed at leaf only: bishop pair +30,
  tempo +10.
- Adjudication awareness: env adjudicates at 200 plies for a material
  lead >= 5 standard points. When game ply >= 150 and our lead is
  +1..+4, add a small eval bonus for increasing the lead (push toward
  >= +5); when we are the side behind at late plies, prefer maximum
  resistance. Game ply is derived from the env's `plies` field
  (deterministic, no clock).
- Asymmetric contempt: draws score +0 normally, -25 cp for the side with
  a material lead (encourages avoiding dead draws when ahead).

## 4. Move Generation

- Pseudo-legal generation, fast (piece-delta loops over offsets);
  legality via `in_check()` after `make` (validation, not prevention),
  except castling which is generated only when fully legal:
  rights present, path empty, king not currently in check, path squares
  not attacked.
- Full rules: en passant, promotions q/r/b/n (generate all; ordering
  prefers q then n), 50-move, insufficient material, threefold (per 2).
- Worm-hole to checkmate soundness: after any move the opponent must be
  able to capture the king (score +/-MATE) - standard pseudo-legal trick
  is acceptable inside search, but root moves are fully validated.

## 5. Search (5-layer, non-generic, node-budgeted)

### Budgets (all deterministic)
- Forced move (exactly 1 legal): play it, 0 nodes.
- Narrow (<= 4 legal): 0.4 x B_base.
- Midgame phase 10..22: 1.3 x B_base.
- Inter-iteration score swing > 80 cp: extend +40% next iteration.
- `B_hardcap = floor(NPS_worst * 3.0 s)` measured OFFLINE on a
  1-CPU-pruned run (`taskset -c 0`), two-digit safety against the 10 s
  move limit and ~3 s average target. Design margin: worst move under
  7.5 s-equivalent node count. **No time.time()/perf_counter anywhere.**
- Iterative deepening from 1; an iteration cut off mid-way by the node
  budget is DISCARDED entirely (house semantics: last whole depth stands);
  keep best move from the last completed depth; if depth-1 itself aborts,
  fall back to the first root legal move.

### Core
- Negamax + alpha-beta; PVS (full window for move 1, zero-window
  `(-alpha-1, -alpha)` for the rest; re-search on fail-high).
- Aspiration windows +/-50 cp from depth >= 4, widen on fail (standard
  doubling), no root aborts.
- TT: `dict` keyed by Zobrist -> `(depth, flag, score, best_move)`, flags
  EXACT/LOWER/UPPER; store mate scores normalized as `MATE - ply` (and
  adjust on read) so mates are chosen fastest -> feeds the
  *plies-to-spare* tie-break. Verify the TT move is pseudo-legal before
  using it for ordering. RAM guard: if `len(tt) > 1_000_000: tt.clear()`
  (dict entry ~120 B; 1 M entries is safely under 512 MB).

### Stack pruning / extensions
- IIR: TT miss at depth >= 4 -> `depth -= 1`.
- Check extension: +1 ply when in check (cap total extensions per branch).
- RFP at depth <= 3 (static eval >= beta + margin, non-PV, not in check).
- Razoring at depth <= 2 (eval + margin < alpha -> drop to qsearch).
- NMP: `R = 2 + (depth >= 6)` only when depth >= 3, non-PV, not in check,
  side has a non-pawn piece, and static eval >= beta.
- Futility pruning for quiet moves at shallow depth.
- LMR via a precomputed log table `LMR[d][m]` (built once at startup;
  `math.log` is stdlib and deterministic); re-search on fail-high.

### Move ordering (5 tiers) + SEE-lite
1. TT move.
2. Good captures (SEE >= 0) & promotions, ordered MVV-LVA.
3. 2 killer moves (per ply) + counter-move (last opponent move table).
4. Quiet moves: gravity history + PeSTO PST delta.
5. Bad captures (SEE < 0).
- SEE-lite: victim/attacker swap algorithm on 0x88 with cheapest-first
  attacker sets; if bytes get tight, downgrade to MVV-LVA only.

### Quiescence
- Stand-pat + delta pruning + skip bad captures (SEE < 0); generate
  captures and queen promotions only; in-check qsearch nodes search all
  evasions (no stand-pat when in check).

## 6. HTTP driver

- `http.client.HTTPConnection` (keep-alive) to `$MAKEFUN_ENV_URL`; POST
  JSON, read timeout > 10 s. Loop: `/game` -> (rebuild position from
  `start_fen` + `moves`) -> search (node budget from section 5) -> `/move`
  -> repeat until `status == "over"` for the game, then `/game` again
  until done. Env failures: a 4xx changes nothing and the move clock keeps
  running -> never spam; crash-safety: any exception in one game must not
  kill the loop (catch, resign that game only).
- Parse `move_limit_ms` and `max_plies` from the env answer; use `plies`
  for adjudication awareness.

## 7. Byte budget & packing

- Write the source clean (target 9-12 KB readable), then pack with the
  kit CLI only: `node cli/makefun.mjs compress <source> --out main.py`
  (lzma). Expected packed size ~2,600-3,300 B. The kit compress command
  MUST be run as its own step after the last source edit (this is a
  transcript-check requirement), and the source stays beside the sessions
  (need not be committed).
- Submitted snapshot: `main.py` + `LICENSE` (MIT) + minimal README only.
  Check sizes: main.py <= 4,096 B, total (excl. `.git`) <= 8,192 B.
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
   46/2,079/89,890.
2. **Determinism A/B**: two separate processes, different
   `PYTHONHASHSEED`, same positions -> byte-identical move lists.
3. **Speed**: measure NPS worst-case (dense perft + deep check-evasion
   positions) with `taskset -c 0`; set B_base = floor(3.0 s x NPS_worst x
   0.8) conservatively (the 0.8 guards a slower grading CPU).
4. **Local Elo**: run `tools/run_trial.sh` on all 3 practice trials
   (`practice/trial-{0,1,2}`). Targets: >= 1,154 on each; then beat the
   baseline practice spread (1,253-1,451 on 8-game set; ~1,365 mean on
   the 6-game practice set).
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
