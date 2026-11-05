#!/usr/bin/env bash
# Reproducible check: fake harness on bare Python, then the test suite in a
# project-local virtualenv. The sandbox image ships Python without pip, so the
# venv is created without it and pip is bootstrapped on first run.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== fake harness (stdlib only) =="
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else "Python 3.10+ required")'
python3 -m music.harness

if [ ! -x .venv/bin/python ] || ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
    echo "== creating .venv =="
    rm -rf .venv
    if ! python3 -m venv .venv 2>/dev/null; then
        rm -rf .venv
        python3 -m venv --without-pip .venv
    fi
fi

if ! .venv/bin/python -c "import pip" >/dev/null 2>&1; then
    echo "== bootstrapping pip =="
    curl -fsSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python -
fi

echo "== installing pinned requirements =="
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt

echo "== tests =="
.venv/bin/python -m unittest discover -s tests -t . -v
