#!/bin/zsh
set -e

project_dir="${0:A:h}"
cd "$project_dir"

if [[ ! -x ".venv/bin/voice-cursor" ]]; then
  echo "Project environment is missing. Run the setup steps in README.md first."
  read -r "?Press Return to close..."
  exit 1
fi

echo "Starting LIVE voice cursor control."
echo "Say movement commands, or target a visible interactive control:"
echo '  click Submit | double click Settings | right click Downloads | move to Sign In'
echo "Visible browser text and desktop folder names are also searchable."
echo "Target names are exact: Project and Projects are different."
echo "Optional in-app Head Tracking, Eye Gaze, and Tongue Clicks are available."
echo "The Voice Cursor transcript area is always excluded."
echo "Wait until the app says 'Listening with MacParakeet' before speaking."
echo "Do not close this Terminal window while the application is running."
.venv/bin/voice-cursor \
  --start-enabled \
  --movement-pixels 180 \
  --speech-engine parakeet \
  --input-device "MacBook Air Microphone"
