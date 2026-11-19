#!/usr/bin/env python3
"""End-to-end Node.js HTTP mock env test (keepAliveTimeout drops, multi-game, replay, fallbacks)."""
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NODE_SERVER_JS = r"""
const http = require('http');

const GAMES = [
  {
    id: 1,
    start_fen: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    steps: [
      { moves: [], legal_moves: ["e2e4", "d2d4", "g1f3", "c2c4"], plies: 0 },
      { reply: "e7e5", legal_moves: ["g1f3", "f1c4", "d2d4"], plies: 2 },
      { reply: "b8c6", legal_moves: ["f1b5"], plies: 4 }, // forced move test (1 legal)
      { over: true, plies: 5 }
    ]
  },
  {
    id: 2,
    start_fen: "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1",
    steps: [
      { moves: [], legal_moves: ["e1e8", "e1e7", "g1f1"], plies: 152 },
      { over: true, plies: 153 }
    ]
  }
];

let gIdx = 0;
let sIdx = 0;
let history = [];
let moveCalls = 0;
let resignCalls = 0;
let droppedOnce = false;

const server = http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    const data = body ? JSON.parse(body) : {};
    if (req.url === '/game') {
      if (gIdx >= GAMES.length) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'done', moveCalls, resignCalls }));
        return;
      }
      const g = GAMES[gIdx];
      const st = g.steps[sIdx];
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: st.over ? 'over' : 'active',
        game: g.id,
        start_fen: g.start_fen,
        moves: history,
        legal_moves: st.legal_moves || [],
        plies: st.plies,
        move_limit_ms: 10000,
        max_plies: 200
      }));
      return;
    }

    if (req.url === '/move') {
      moveCalls++;
      // Simulate an abrupt Node keep-alive socket drop once on first move
      if (!droppedOnce) {
        droppedOnce = true;
        req.socket.destroy();
        return;
      }
      const g = GAMES[gIdx];
      if (!g || data.game !== g.id) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'wrong game' }));
        return;
      }
      history.push(data.move);
      sIdx++;
      const st = g.steps[sIdx];
      if (st.reply) {
        history.push(st.reply);
      }
      if (st.over) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'over', game: g.id, moves: history, plies: st.plies }));
        gIdx++;
        sIdx = 0;
        history = [];
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'active',
        game: g.id,
        start_fen: g.start_fen,
        moves: history,
        legal_moves: st.legal_moves,
        plies: st.plies,
        move_limit_ms: 10000,
        max_plies: 200
      }));
      return;
    }

    if (req.url === '/resign') {
      resignCalls++;
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'over' }));
      gIdx++;
      sIdx = 0;
      history = [];
      return;
    }

    res.writeHead(404);
    res.end();
  });
});

// Aggressive keepAliveTimeout to stress-test Node socket expiry
server.keepAliveTimeout = 200;
const port = parseInt(process.env.MOCK_PORT || '18077', 10);
server.listen(port, '127.0.0.1', () => {
  console.log('MOCK_READY', port);
});
"""


def main():
    port = 18077
    env = dict(os.environ, MOCK_PORT=str(port))
    srv = subprocess.Popen(
        ["node", "-e", NODE_SERVER_JS],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        ready = srv.stdout.readline().strip()
        assert "MOCK_READY" in ready, f"Mock server failed to start: {ready}"

        eng_env = dict(os.environ, MAKEFUN_ENV_URL=f"http://127.0.0.1:{port}")
        t0 = time.perf_counter()
        rc = subprocess.run(
            [sys.executable, os.path.join(REPO_ROOT, "engine_src.py")],
            env=eng_env,
            timeout=30,
            capture_output=True,
            text=True,
        )
        dt = time.perf_counter() - t0
        assert rc.returncode == 0, f"Engine exited with {rc.returncode}: {rc.stderr}"

        # Query final /game state from mock server to verify all games finished with 0 resigns
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("POST", "/game", b"{}", {"Content-Type": "application/json"})
        resp = json.loads(conn.getresponse().read().decode())
        conn.close()
        assert resp["status"] == "done", f"Expected done, got {resp}"
        assert resp["resignCalls"] == 0, f"Expected 0 resigns, got {resp['resignCalls']}"
        assert resp["moveCalls"] >= 5, f"Expected >= 5 move calls (incl. 1 retry), got {resp['moveCalls']}"
        print(f"[PASS] Mock HTTP env test passed in {dt:.2f}s: {resp}")
    finally:
        srv.terminate()
        srv.wait(timeout=5)


if __name__ == "__main__":
    main()
