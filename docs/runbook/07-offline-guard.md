# 07 — The offline guard

## What this is

The demo never opens a socket; its only input is the committed CSV.
`--offline` does not *enable* that behaviour. It **enforces** it, so any later
code that tried to fetch something would fail with exit code 1 rather than
quietly depending on a website.

## What is blocked

`demo.assert_offline()` replaces two hooks:

- **`builtins.__import__`**: any import whose root module is `socket`, `ssl`,
  `http`, `urllib`, `ftplib` or `asyncio` raises `NetworkBlockedError`.
- **`socket.socket`**: constructing a socket raises `NetworkBlockedError`. This
  is needed because `demo.py` already imports `socket`, so an import ban alone
  would not catch it.

It prints `offline mode: network imports and socket construction are blocked`
and names the single input file.

## Lifecycle (in `__main__.main()`)

1. `demo.assert_offline()` runs **before** `demo.run_demo()`. It is idempotent.
2. The block stays in place for the whole walkthrough **and** the report build.
3. A `NetworkBlockedError` raised during the run becomes exit code 1, with
   `offline violation: …` printed on stderr.
4. `demo.release_offline()` restores both hooks in a `finally` block.

## How it is tested

In `tests/test_demo.py`:

- `test_assert_offline_holds_the_block_until_released` checks that the block is
  still active after `assert_offline()` returns and is gone after
  `release_offline()`.
- `test_a_network_import_during_the_run_exits_one` monkeypatches `run_demo` so
  it reaches for `urllib.request` *during* the run, then asserts exit code 1.

An earlier version restored the hooks inside `assert_offline()` itself, before
the run started. That made the promise false and left the exit-1 path as dead
code. If you edit this path, run:

```bash
python -m pytest -q tests/test_demo.py -k "offline or network"   # 2 tests
```
