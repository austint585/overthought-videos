#!/usr/bin/env bash
# One-time setup for a fresh machine: Python libs, fonts (OFL, via Fontsource) and flag images (MIT, flag-icons).
set -euo pipefail
cd "$(dirname "$0")"
pip install --break-system-packages -q skia-python pymunk cairosvg fonttools brotli numpy pillow
mkdir -p vendor/fonts
cd vendor
[ -f package.json ] || npm init -y >/dev/null
npm install --silent @fontsource/bricolage-grotesque @fontsource/jetbrains-mono flag-icons
python3 - <<'PY'
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
