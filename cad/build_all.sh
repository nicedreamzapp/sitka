#!/bin/bash
# Sitka render two: full rebuild. Body -> parts -> assembly (GLBs, fit report) -> animation -> viewer data [-> renders]
#   cad/build_all.sh            (no PNG renders)
#   cad/build_all.sh render     (also the 20 studio PNGs, Cycles)
set -e
CAD="$(cd "$(dirname "$0")" && pwd)"
BL=/opt/homebrew/bin/blender
cd /tmp
BLENDER_USER_RESOURCES="$CAD/.blender" $BL -b -noaudio --python-exit-code 1 --python "$CAD/body/make_body.py" > /tmp/sitka_body.log 2>&1
"$CAD/.venv/bin/python" "$CAD/parts/build_parts.py" > /tmp/sitka_parts.log 2>&1
$BL -b --factory-startup -noaudio --python-exit-code 1 --python "$CAD/assemble/assemble.py" -- --no-render > /tmp/sitka_asm.log 2>&1
$BL -b --factory-startup -noaudio --python-exit-code 1 --python "$CAD/assemble/assemble.py" -- --anim > /tmp/sitka_anim.log 2>&1
"$CAD/.venv/bin/python" "$CAD/viewer/build_viewer.py"
if [ "$1" = "render" ]; then
  $BL -b --factory-startup -noaudio --python-exit-code 1 --python "$CAD/assemble/assemble.py" -- --samples=128 > /tmp/sitka_render.log 2>&1
fi
echo "build_all OK"
