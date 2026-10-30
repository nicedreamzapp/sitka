#!/bin/bash
# Sitka render two: full rebuild. Body -> parts -> assembly (GLBs, fit report) -> animation (anatomy gate) ->
# connection gate -> viewer data [-> renders]
#   cad/build_all.sh            (no PNG renders)
#   cad/build_all.sh render     (also the 20 studio PNGs, Cycles)
set -e
CAD="$(cd "$(dirname "$0")" && pwd)"
BL=/opt/homebrew/bin/blender
cd /tmp
BLENDER_USER_RESOURCES="$CAD/.blender" $BL -b -noaudio --python-exit-code 1 --python "$CAD/body/make_body.py" > /tmp/sitka_body.log 2>&1
"$CAD/.venv/bin/python" "$CAD/parts/build_parts.py" > /tmp/sitka_parts.log 2>&1
$BL -b --factory-startup -noaudio --python-exit-code 1 --python "$CAD/assemble/assemble.py" -- --no-render > /tmp/sitka_asm.log 2>&1
# --anim runs the anatomy gate (cad/mocap/anatomy_gate.py) on every frame and exits 1 without writing on a fail
$BL -b --factory-startup -noaudio --python-exit-code 1 --python "$CAD/assemble/assemble.py" -- --anim > /tmp/sitka_anim.log 2>&1 \
  || { grep -A 30 "ANATOMY GATE (" /tmp/sitka_anim.log; echo "animation bake failed (log: /tmp/sitka_anim.log)"; exit 1; }
# connection gate (cad/assemble/connection_gate.py): every part on the part it hangs on, every cable end on its anchor,
# no part sunk into the body, struts planted / stowed in their clips, in every baked frame and every static pose
"$CAD/.venv/bin/python" "$CAD/assemble/connection_gate.py" > /tmp/sitka_gate.log 2>&1 \
  || { grep -v "only got\|checked" /tmp/sitka_gate.log | head -60; echo "connection gate failed (log: /tmp/sitka_gate.log)"; exit 1; }
grep "CONNECTION GATE" /tmp/sitka_gate.log
"$CAD/.venv/bin/python" "$CAD/viewer/build_viewer.py"
if [ "$1" = "render" ]; then
  $BL -b --factory-startup -noaudio --python-exit-code 1 --python "$CAD/assemble/assemble.py" -- --samples=128 > /tmp/sitka_render.log 2>&1
fi
echo "build_all OK"
