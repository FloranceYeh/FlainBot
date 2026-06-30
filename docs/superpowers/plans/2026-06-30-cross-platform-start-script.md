# Cross Platform Start Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Python startup script that launches the existing web chat server with portable defaults and clear API key checks.

**Architecture:** `start.py` is a thin wrapper around `scripts.web_chat.main()`. It parses cross-platform CLI arguments, validates the provider-specific API key environment variable, prints the chat URL, and delegates the actual server runtime to the existing implementation.

**Tech Stack:** Python standard library, `unittest`.

---

### Task 1: Startup Script Tests

**Files:**
- Create: `tests/test_start_script.py`

- [ ] Test that default arguments launch OpenAI through `scripts.web_chat.main()` with `openai`, default host, and default port.
- [ ] Test that Anthropic requires `ANTHROPIC_API_KEY`.
- [ ] Test that missing provider API keys return a non-zero code and do not launch the server.
- [ ] Test that the script prints the `/#chat` URL before delegating.

### Task 2: Python Startup Wrapper

**Files:**
- Create: `start.py`

- [ ] Add argparse options: `--provider`, `--host`, `--port`, `--model`, and `--base-url`.
- [ ] Validate `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` before launching.
- [ ] Build argv for `scripts.web_chat.main()` without duplicating server code.
- [ ] Return the delegated exit code.

### Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`

- [ ] Document `python start.py`.
- [ ] Run `python -m unittest -v`.
- [ ] Run `python -m py_compile start.py`.
- [ ] Commit only the startup-script change, leaving unrelated `TODO.md` untouched.
