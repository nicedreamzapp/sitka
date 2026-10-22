#!/bin/bash
# Renders every PNG in renders/ from run_sit_exo.scad with the OpenSCAD CLI.
# Usage: bash render_all.sh      (needs openscad on PATH; tested with 2021.01)
cd "$(dirname "$0")"
OS=${OPENSCAD:-openscad}
CS="Tomorrow Night"
SZ=1200,1100
side="0,5200,1000,0,0,900";  front="5200,0,1000,0,0,900";  back="-5200,0,1000,0,0,900"; q3="3000,3400,1900,0,0,800"
r(){ "$OS" -D "mode=\"$1\"" $3 --imgsize=$SZ --camera=$2 --colorscheme="$CS" -o "renders/$4.png" run_sit_exo.scad >/dev/null 2>&1 && echo "renders/$4.png"; }
r stand "$side"  "" stand_side
r stand "$front" "" stand_front
r stand "$back"  "" stand_back
r stand "$q3" "-D show_body=false" exo_only_quarter
r stand "$q3" "-D show_body=false -D explode=1" exploded_quarter
for m in perch halfsit chair squat run; do r $m "$side" "" mode_${m}_side; done
r chair "$q3" "" mode_chair_quarter
r run   "$q3" "" mode_run_quarter
