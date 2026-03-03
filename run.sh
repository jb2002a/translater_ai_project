#!/usr/bin/env bash
# 가상환경의 Python으로 앱 실행 (python3.12 사용 시 권장)
cd "$(dirname "$0")"
.venv/bin/python3 -m py_compile app.py || exit 1
.venv/bin/python3 app.py
