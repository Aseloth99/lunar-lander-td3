#!/usr/bin/env bash
# One-command install for Linux / WSL WITHOUT a virtual environment and without sudo: every Python package goes INTO
# this folder (./.pydeps). To uninstall, delete ./.pydeps. Prefer a venv? See "Installation" in README.md.
#   bash install.sh            (Python 3.10-3.12, ~1.5 GB, CPU-only PyTorch; needs a C++ compiler for Box2D)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
DEPS="$PWD/.pydeps"
PY="${PYTHON:-python3}"
"$PY" -c 'import sys; v = sys.version_info[:2]; assert (3, 10) <= v <= (3, 12), f"Python 3.10-3.12 required (torch 2.4.1), found {sys.version.split()[0]}"'
mkdir -p "$DEPS/bin"
export PYTHONPATH="$DEPS" PATH="$DEPS/bin:$PATH"

# 1) pip itself, if missing (e.g. Ubuntu without python3-pip / ensurepip)
if ! "$PY" -m pip --version > /dev/null 2>&1; then
  echo "pip not found, installing it into $DEPS ..."
  curl -fsSL -o "$DEPS/get-pip.py" https://bootstrap.pypa.io/get-pip.py
  "$PY" "$DEPS/get-pip.py" --target "$DEPS" --break-system-packages --no-warn-script-location
  rm -f "$DEPS/get-pip.py"
fi
PIP=("$PY" -m pip install --target "$DEPS" --no-warn-script-location)

# 2) SWIG first: box2d-py is compiled with it. With --target, pip does not put the swig program on PATH -> small wrapper.
"${PIP[@]}" swig==4.5.1
cat > "$DEPS/bin/swig" << EOF
#!/usr/bin/env bash
export SWIG_LIB="$DEPS/swig/data/share/swig/\$(ls "$DEPS/swig/data/share/swig" | head -1)"
exec "$DEPS/swig/data/bin/swig" "\$@"
EOF
chmod +x "$DEPS/bin/swig"

# 3) everything else (CPU build of PyTorch: no CUDA download)
"${PIP[@]}" --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple -r requirements.txt

# 4) check
"$PY" check_env.py
echo
echo "Done. Try:  python3 play.py   (watch the zero-crash agent)   |   python3 play.py --group td3/v4big@1600k   (the top scorer)   |   python3 verify.py   (check the numbers)"
