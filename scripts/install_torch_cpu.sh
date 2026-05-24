#!/usr/bin/env bash
# Reinstall a known-stable CPU build of PyTorch (2.6.x).
# Avoids segfaults seen with torch 2.12 on macOS arm64 + lightgbm/xgboost.
set -euo pipefail
pip install --force-reinstall "torch==2.6.*" --index-url https://download.pytorch.org/whl/cpu
python -c "import torch; print('torch version:', torch.__version__)"
