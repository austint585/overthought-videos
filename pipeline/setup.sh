#!/usr/bin/env bash
# One-time setup for a fresh machine: Python libs, fonts (OFL, via Fontsource) and flag images (MIT, flag-icons).
set -euo pipefail
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python)
PIPPKGS="skia-python pymunk fonttools brotli numpy pillow kokoro-onnx soundfile"
$PY -m pip install -q $PIPPKGS 2>/dev/null || $PY -m pip install -q --break-system-packages $PIPPKGS
command -v ffmpeg >/dev/null || echo 'WARNING: ffmpeg not found. Windows: winget install Gyan.FFmpeg  (or: conda install -c conda-forge ffmpeg)'
command -v npm >/dev/null || { echo 'ERROR: npm not found. Install Node.js LTS (winget install OpenJS.NodeJS.LTS), then re-run.'; exit 1; }
# free narration voice (Kokoro, Apache-2.0), hosted on GitHub
mkdir -p vendor/tts
[ -f vendor/tts/kokoro-v1.0.onnx ] || curl -sL -o vendor/tts/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f vendor/tts/voices-v1.0.bin ] || curl -sL -o vendor/tts/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
mkdir -p vendor/fonts
cd vendor
[ -f package.json ] || npm init -y >/dev/null
npm install --silent @fontsource/bricolage-grotesque @fontsource/jetbrains-mono flag-icons
$PY - <<'PY'
from fontTools.ttLib import TTFont
src = "node_modules/@fontsource"
for out, p in {
    "Bricolage-800": "bricolage-grotesque/files/bricolage-grotesque-latin-800-normal.woff2",
    "Bricolage-700": "bricolage-grotesque/files/bricolage-grotesque-latin-700-normal.woff2",
    "Bricolage-500": "bricolage-grotesque/files/bricolage-grotesque-latin-500-normal.woff2",
    "JetBrainsMono-800": "jetbrains-mono/files/jetbrains-mono-latin-800-normal.woff2",
    "JetBrainsMono-700": "jetbrains-mono/files/jetbrains-mono-latin-700-normal.woff2",
    "JetBrainsMono-500": "jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff2",
}.items():
    f = TTFont(f"{src}/{p}"); f.flavor = None; f.save(f"fonts/{out}.ttf")
print("fonts ready")
PY
# Blender for the 3D formats: portable build from an official blender.org mirror (blender.org itself
# sits behind a bot check that blocks curl and winget), verified against the published SHA-256
BV=5.2.3
BM="https://mirrors.ocf.berkeley.edu/blender/release/Blender${BV%.*}"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) BZ="blender-$BV-windows-x64.zip" ;;
  Linux) BZ="blender-$BV-linux-x64.tar.xz" ;;
  *) BZ="" ; echo "Install Blender $BV yourself and set BLENDER=/path/to/blender" ;;
esac
BD="${BZ%.zip}"; BD="${BD%.tar.xz}"
if [ -n "$BZ" ] && [ ! -d "blender_dl/$BD" ]; then
  curl -sL -o "$BZ" "$BM/$BZ"
  want=$(curl -sL "$BM/blender-$BV.sha256" | grep "$BZ" | cut -d' ' -f1)
  [ "$want" = "$(sha256sum "$BZ" | cut -d' ' -f1)" ] || { echo "ERROR: Blender checksum mismatch"; rm -f "$BZ"; exit 1; }
  mkdir -p blender_dl
  case "$BZ" in *.zip) unzip -q "$BZ" -d blender_dl ;; *) tar -xf "$BZ" -C blender_dl ;; esac
  rm -f "$BZ"
  echo "blender ready"
fi
