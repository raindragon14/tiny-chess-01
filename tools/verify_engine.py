#!/usr/bin/env python3
"""Comprehensive verification, calibration, and benchmarking suite for engine_src.py."""
import argparse
import ast
import base64
import lzma
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

import engine_src as E  # noqa: E402


PERFT_CASES = [
    ("startpos", E.SF, [(1, 20), (2, 400), (3, 8902), (4, 197281)]),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [(1, 48), (2, 2039), (3, 97862)]),
    ("kiwipete-mirror", "r3k2r/pppbbppp/2n2q1P/1P2p3/3pn3/BN2PNP1/P1PPQPB1/R3K2R b KQkq - 0 1", [(1, 48), (2, 2039), (3, 97862)]),
    ("pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [(1, 14), (2, 191), (3, 2812), (4, 43238)]),
    ("pos4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [(1, 6), (2, 264), (3, 9467)]),
    ("pos5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", [(1, 44), (2, 1486), (3, 62379)]),
    ("pos6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", [(1, 46), (2, 2079), (3, 89890)]),
]


def apply_uci(u):
    pr = max(0, E.PS.find(u[4:]))
    E.mk(E.U(u[:2]) | (E.U(u[2:4]) << 7) | (pr << 14))


def is_rep():
    return E.rs[-1] in E.rs[-3::-2][: E.hm // 2]


def insufficient_material():
    return E.ph < 3 and sum(1 + 9 * ((E.b[q] & 7) in (1, 4, 5)) for q in E.Q if 0 < E.b[q] & 7 < 6) < 2


def perft(depth):
    if depth == 0:
        return 1
    cnt = 0
    for m in E.gm(0):
        snap = E.mk(m)
        if not E.ic(1):
            cnt += perft(depth - 1)
        E.um(snap)
    return cnt


def assert_incremental_invariants():
    assert len(E.b) == 128
    wk = bk = 0
    for sq in range(128):
        p = E.b[sq]
        if sq & 0x88:
            assert p == 0, f"Non-zero off-board square {sq}: {p}"
        else:
            assert p == 0 or (1 <= p <= 6) or (9 <= p <= 14), f"Invalid piece {p} at {sq}"
            if p == 6:
                wk += 1
            elif p == 14:
                bk += 1
    assert wk == 1 and bk == 1, f"King count mismatch: wk={wk}, bk={bk}"
    assert E.rs[-1] == E._rk(), "Repetition stack top mismatch"
    assert E.hm >= 0


def run_perft():
    print("=== Gate 1: Perft (all 7 positions) + Incremental Invariants ===")
    t0 = time.perf_counter()
    for name, fen, checks in PERFT_CASES:
        E.lf(fen)
        assert_incremental_invariants()
        for d, expected in checks:
            got = perft(d)
            assert got == expected, f"PERFT FAIL {name} d{d}: got {got}, expected {expected}"
            assert_incremental_invariants()
            print(f"  [PASS] {name:16s} d{d} = {got:,}")
    print(f"Perft suite passed in {time.perf_counter() - t0:.2f}s")


def mirror_fen(fen):
    parts = fen.split()
    rows = parts[0].split("/")[::-1]
    mrows = ["".join(ch.lower() if ch.isupper() else (ch.upper() if ch.islower() else ch) for ch in r) for r in rows]
    side = "b" if parts[1] == "w" else "w"
    cr = parts[2]
    if cr != "-":
        ncr = ""
        for ch in ("K", "Q", "k", "q"):
            src = ch.lower() if ch.isupper() else ch.upper()
            if src in cr:
                ncr += ch
        cr = ncr or "-"
    ep = parts[3]
    if ep != "-":
        ep = ep[0] + ("6" if ep[1] == "3" else "3")
    return f"{'/'.join(mrows)} {side} {cr} {ep} {parts[4]} {parts[5]}"


def run_invariants():
    print("=== Gate 1b: Search, TT, Draw, Symmetry & Eval Invariants ===")
    for _, fen, _ in PERFT_CASES:
        E.lf(fen)
        s1 = E.ev()
        E.lf(mirror_fen(fen))
        s2 = E.ev()
        assert s1 == s2, f"Eval symmetry failed for {fen}: {s1} vs {s2}"
    print("  [PASS] Color-symmetry eval exact across all 7 positions")

    E.lf("6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1")
    bm, sc = E.sr(10000, 20000)
    assert E.M(bm) == "e1e8", f"Expected e1e8 mate, got {E.M(bm)}"
    assert sc >= E.MATE - 5
    print(f"  [PASS] Mate-in-1 found ({E.M(bm)}, score={sc})")

    E.lf("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
    bm, sc = E.sr(10000, 20000)
    assert E.M(bm) == "h5f7", f"Expected h5f7#, got {E.M(bm)}"
    print("  [PASS] Scholar's mate found")

    E.lf("3r2k1/5ppp/8/8/8/8/4QPPP/4R1K1 w - - 0 1")
    bm, sc = E.sr(20000, 40000)
    assert E.M(bm) == "e2e8", f"Expected e2e8 (M2), got {E.M(bm)}"
    print(f"  [PASS] Mate-in-2 found ({E.M(bm)}, score={sc})")

    E.lf("6k1/8/6K1/8/8/8/8/6R1 w - - 0 1")
    for um in ("g1h1", "g8f8", "h1g1", "f8g8"):
        apply_uci(um)
    assert is_rep(), "Expected repetition detected"
    print("  [PASS] Repetition stack detects 2-fold repetition")

    for fen in ("8/8/4k3/8/8/4K3/8/8 w - - 0 1", "8/8/4k3/8/4B3/4K3/8/8 w - - 0 1"):
        E.lf(fen)
        assert insufficient_material(), f"Expected insufficient material: {fen}"
    E.lf("8/8/4k3/4b3/4B3/4K3/8/8 w - - 0 1")
    assert not insufficient_material()
    print("  [PASS] Insufficient material")

    E.lf("4k3/8/8/8/8/8/4P3/4K3 w - - 0 1")
    E.gp = 10
    s_early = E.ev()
    E.gp = 160
    s_late = E.ev()
    assert s_late > s_early, f"Expected late-ply adjudication push bonus: {s_early} -> {s_late}"
    print(f"  [PASS] Adjudication awareness active (ply 10: {s_early}, ply 160: {s_late})")


def run_determinism():
    print("=== Gate 2: A/B Determinism & Static No-Clock/No-Hash Check ===")
    src_path = os.path.join(REPO_ROOT, "engine_src.py")
    with open(src_path, "r") as f:
        src = f.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "time", "Forbidden import time in engine_src.py"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "time", "Forbidden import from time in engine_src.py"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "hash", "Forbidden built-in hash() call in engine_src.py"
    print("  [PASS] Static AST check: zero time imports, zero built-in hash() calls")

    fens = [
        E.SF,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
    ]
    script = (
        "import json, sys; sys.path.insert(0, '.'); import engine_src as E; "
        "out = []; "
        f"fens = {fens!r}; "
        "[E.lf(f) or out.append((E.M(E.sr(30000, 60000)[0]), E.nd)) for f in fens]; "
        "print(json.dumps(out))"
    )
    env_a = dict(os.environ, PYTHONHASHSEED="1")
    env_b = dict(os.environ, PYTHONHASHSEED="987654321")
    r1 = subprocess.check_output([sys.executable, "-c", script], cwd=REPO_ROOT, env=env_a).decode().strip()
    r2 = subprocess.check_output([sys.executable, "-c", script], cwd=REPO_ROOT, env=env_b).decode().strip()
    assert r1 == r2, f"Determinism mismatch!\nA: {r1}\nB: {r2}"
    print(f"  [PASS] A/B Determinism identical across PYTHONHASHSEED: {r1}")


def run_bench():
    print("=== Gate 3: Worst-Case NPS Calibration ===")
    bench_fens = [
        ("startpos", E.SF),
        ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
        ("middlegame", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10"),
        ("check-evasion", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"),
    ]
    worst_nps = 1e9
    for name, fen in bench_fens:
        E.lf(fen)
        E.tt.clear()
        t0 = time.perf_counter()
        bm, sc = E.sr(80000, 120000)
        dt = time.perf_counter() - t0
        nps = E.nd / max(dt, 1e-6)
        worst_nps = min(worst_nps, nps)
        print(f"  {name:14s}: {E.nd:6d} nodes in {dt:.3f}s -> {nps:,.0f} NPS (move={E.M(bm)}, sc={sc})")
    b_base = int(2.0 * worst_nps)
    b_hard = int(4.0 * worst_nps)
    print(f"  Worst NPS = {worst_nps:,.0f} -> Recommended B_BASE={b_base}, B_HARDCAP={b_hard}")


def run_size():
    print("=== Gate 5: makefun compress Packed Size Gate ===")
    src_path = os.path.join(REPO_ROOT, "engine_src.py")
    with open(src_path, "rb") as f:
        raw = f.read()
    kit_cli = "/tmp/kit/tiny-chess-01-kit/cli/makefun.mjs"
    if os.path.exists(kit_cli):
        tmp_out = os.path.join(REPO_ROOT, ".tmp_packed_check.py")
        env = dict(os.environ, MAKEFUN_COMPRESS_STATE="/tmp/compress_check.json")
        subprocess.run(["node", kit_cli, "compress", "engine_src.py", "--out", ".tmp_packed_check.py"], cwd=REPO_ROOT, env=env, check=True, capture_output=True)
        total = os.path.getsize(tmp_out)
        os.remove(tmp_out)
    else:
        comp = lzma.compress(raw, preset=9)
        stub = b"import lzma,base64;exec(lzma.decompress(base64.b85decode(" + repr(base64.b85encode(comp).decode()).encode() + b")))\n"
        total = len(stub)
    print(f"  Source size : {len(raw):,} B")
    print(f"  Packed size : {total:,} B (target <= 3,950 B, hard cap <= 4,096 B)")
    assert total <= 4096, f"Packed size {total} exceeds 4,096 B hard cap!"
    if total > 3950:
        print("  [WARN] Packed size > 3,950 B target; trim source bytes")
    else:
        print("  [PASS] Packed size within 3,950 B target!")


def ab_baseline(depth):
    if depth == 0:
        return E.ev()
    best = -E.INF
    legal = 0
    for m in E.gm(0):
        snap = E.mk(m)
        if E.ic(1):
            E.um(snap)
            continue
        legal += 1
        sc = -ab_baseline(depth - 1)
        E.um(snap)
        if sc > best:
            best = sc
    if legal == 0:
        return -E.MATE if E.ic(0) else 0
    return best


def pick_baseline_move(depth=3):
    best_m = 0
    best_sc = -E.INF
    for m in E.lm():
        snap = E.mk(m)
        sc = -ab_baseline(depth - 1)
        E.um(snap)
        if sc > best_sc:
            best_sc = sc
            best_m = m
    return best_m


def run_strength():
    print("=== Gate 4: Tactical Puzzles & Match vs Baseline Depth-3 ===")
    puzzles = [
        ("mate-in-1", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1", {"e1e8"}),
        ("back-rank-m2", "3r2k1/5ppp/8/8/8/8/4QPPP/4R1K1 w - - 0 1", {"e2e8"}),
        ("win-queen-fork", "4k3/8/8/3q4/8/2N5/8/4K3 w - - 0 1", {"c3d5"}),
        ("promote-win", "8/3P2k1/8/8/8/8/8/4K3 w - - 0 1", {"d7d8q"}),
        ("greek-gift-like", "r1bq1rk1/ppp2ppp/2n1pn2/3p4/2PP4/2NBPN2/PP3PPP/R1BQK2R w KQ - 0 8", None),
    ]
    for name, fen, expected in puzzles:
        E.lf(fen)
        bm, sc = E.sr(25000, 50000)
        uci = E.M(bm)
        if expected:
            assert uci in expected, f"Puzzle {name} failed: got {uci}, expected {expected}"
        print(f"  [PASS] {name:16s} -> {uci} (score={sc})")

    openings = [
        E.SF,
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
    ]
    pts = 0.0
    games = 0
    sm = (0, 1, 3, 3, 5, 9, 0)
    for op in openings:
        for our_color in (0, 1):
            E.lf(op)
            E.tt.clear()
            plies = 0
            res = 0.5
            while plies < 140:
                if E.hm >= 100 or insufficient_material() or is_rep():
                    res = 0.5
                    break
                legal = E.lm()
                if not legal:
                    res = (0.0 if int(E.sd) == our_color else 1.0) if E.ic() else 0.5
                    break
                if int(E.sd) == our_color:
                    E.gp = plies
                    bm, _ = E.sr(20000, 40000)
                    uci = E.M(bm)
                else:
                    bm = pick_baseline_move(depth=3)
                    uci = E.M(bm)
                apply_uci(uci)
                plies += 1
            else:
                md = sum(sm[p & 7] * (1 if p < 8 else -1) for p in E.b if 0 < p & 7 < 6)
                if our_color == 1:
                    md = -md
                res = 1.0 if md >= 5 else (0.0 if md <= -5 else 0.5)
            pts += res
            games += 1
            print(f"  Game {games} (our_color={'W' if our_color == 0 else 'B'}): result={res} in {plies} plies")
    print(f"  Match score vs depth-3 baseline: {pts}/{games}")
    assert pts >= 3.0, f"Expected >= 3.0/4 vs depth-3 baseline, got {pts}/{games}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--perft", action="store_true")
    p.add_argument("--invariants", action="store_true")
    p.add_argument("--determinism", action="store_true")
    p.add_argument("--bench", action="store_true")
    p.add_argument("--strength", action="store_true")
    p.add_argument("--size", action="store_true")
    args = p.parse_args()
    if not any(vars(args).values()):
        args.perft = args.invariants = args.determinism = args.bench = args.strength = args.size = True

    if args.perft:
        run_perft()
    if args.invariants:
        run_invariants()
    if args.determinism:
        run_determinism()
    if args.bench:
        run_bench()
    if args.strength:
        run_strength()
    if args.size:
        run_size()


if __name__ == "__main__":
    main()
