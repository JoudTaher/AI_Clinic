#!/bin/zsh
set -e

cd "${0:A:h}"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

if ! .venv/bin/python -c 'import streamlit, pytest, docx, lxml; import torch, transformers' 2>/dev/null; then
  .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python -m streamlit run app.py
