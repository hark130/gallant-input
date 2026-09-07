#!/usr/bin/env bash
#
# setup_env.sh — one-shot environment setup for the gallant-input / rf_capstone_v3
# custom RF protocol project.
#
# Companion script to GAIN_Protocol_Documentation.md, section 2.2.
#
# WHAT THIS DOES:
#   1. Installs the Ettus UHD driver + Python bindings (system-level, apt).
#   2. Downloads the FPGA/firmware images UHD needs for B200-series devices.
#   3. Creates a Python virtual environment (with access to system UHD bindings).
#   4. Installs the remaining Python dependencies into that venv, pinned to
#      the repo's own gallant_input/requirements.txt (matplotlib, numpy,
#      sigmf, scipy, scikit-learn, uhd).
#   5. Attempts to install this repo as an editable package so
#      `gallant_input` / `rxtx` imports resolve.
#   6. Runs a basic import sanity check.
#
# ASSUMPTIONS / THINGS TO VERIFY FOR YOUR REPO:
#   - You are on Ubuntu/Debian (apt-based). Adjust the package-manager section
#     for other distros.
#   - This script is run from the repository root (i.e. the directory that
#     contains gallant_input/, rxtx/, and rf_capstone_v3.py), so that
#     gallant_input/requirements.txt resolves relative to the current directory.
#   - The repo has a setup.py/pyproject.toml that supports `pip install -e .`.
#     If it doesn't, this script falls back to exporting PYTHONPATH instead —
#     confirm which applies to your actual repo layout.
#
# USAGE:
#   chmod +x setup_env.sh
#   ./setup_env.sh
#
set -euo pipefail

VENV_DIR=".venv"

echo "=== [1/6] Installing UHD driver + Python bindings (requires sudo) ==="
sudo apt update
sudo apt install -y libuhd-dev uhd-host python3-uhd python3-venv python3-pip

echo "=== [2/6] Downloading UHD FPGA/firmware images ==="
sudo uhd_images_downloader

echo "=== [3/6] Creating virtual environment at ${VENV_DIR} (with system site-packages, for UHD bindings) ==="
python3 -m venv --system-site-packages "${VENV_DIR}"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "=== [4/6] Installing Python dependencies (gallant_input/requirements.txt) ==="
pip install --upgrade pip
if [ -f "gallant_input/requirements.txt" ]; then
    pip install -r gallant_input/requirements.txt
else
    echo "gallant_input/requirements.txt not found relative to $(pwd)."
    echo "Falling back to a hardcoded package list — verify this matches the repo's actual requirements.txt."
    pip install matplotlib "numpy>=1.20.0" "sigmf>=1.7.0" "scipy>=1.3.0" scikit-learn uhd
fi

echo "=== [5/6] Installing repository package (gallant_input, rxtx) ==="
if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
    pip install -e .
else
    echo "No setup.py/pyproject.toml found in $(pwd)."
    echo "Falling back to PYTHONPATH. Add this line to your shell profile"
    echo "or re-export it each session:"
    echo "  export PYTHONPATH=\"$(pwd):\$PYTHONPATH\""
    export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
fi

echo "=== [6/6] Sanity check ==="
python3 -c "import uhd, numpy, scipy, matplotlib, sklearn, sigmf; print('Core dependencies: OK')"
python3 -c "from gallant_input.modem.fsk2 import FSK2; print('gallant_input import: OK')"
python3 -c "from rxtx.frame_receiver import FrameReceiver; print('rxtx import: OK')"

echo ""
echo "Setup complete."
echo "Next steps:"
echo "  1. Run 'uhd_find_devices' to confirm your USRP(s) are visible and note their serials."
echo "  2. See GAIN_Protocol_Documentation.md, section 2.3, to run the protocol."
