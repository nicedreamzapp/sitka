#!/bin/sh
# Extra CMU motion capture for training and held-out testing of the mode model (not committed: ~13 MB).
# Same source and credit as cad/mocap/CREDITS.md: "The data used in this project was obtained from
# mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217." (BVH conversion mirror below)
set -e
cd "$(dirname "$0")"; mkdir -p mocap_extra
for c in 035/35_02 035/35_03 035/35_18 035/35_19 035/35_20 086/86_10 115/115_02 115/115_03; do
  f=mocap_extra/$(basename $c).bvh
  [ -s "$f" ] || curl -sfL -o "$f" "https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/$c.bvh"
  echo "$f"
done
