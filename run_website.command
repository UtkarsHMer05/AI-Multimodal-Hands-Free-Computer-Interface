#!/bin/zsh
set -e

project_dir="${0:A:h}"
cd "$project_dir"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Project environment is missing. Run the setup steps in README.md first."
  read -r "?Press Return to close..."
  exit 1
fi

if ! .venv/bin/python -c "import voice_cursor" >/dev/null 2>&1; then
  echo "Installing the project (first run only)..."
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -e . -q
fi

if [[ ! -f "website/out/index.html" ]]; then
  echo "Building the website (first run only)..."
  (cd website && npm install --silent && npm run build)
fi

echo ""
echo "  Starting the Voice Cursor engine + web dashboard."
echo "  Dashboard: http://localhost:8757/dashboard"
echo "  Press Ctrl+C here to stop the engine."
echo "  macOS permissions (Mic, Camera, Accessibility, Screen Recording)"
echo "  must be granted to Terminal — same as the desktop app."
echo ""
exec .venv/bin/python -m voice_cursor.web_server --open
