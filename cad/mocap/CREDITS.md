# Motion capture credits

The wearer's motion in the 3D viewer (walk, run, sit down, stand up, stoop lift) is real human motion
capture from the **CMU Graphics Lab Motion Capture Database**, http://mocap.cs.cmu.edu/

"The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding
from NSF EIA-0196217."

The BVH files in `src/` are the CMU BVH conversion (120 fps) mirrored at
https://github.com/una-dinosauria/cmu-mocap (`data/<subject>/<trial>.bvh`). They are retargeted onto the
MPFB rig of the Sitka wearer by `retarget.py` (direction-exact limbs, leg IK, foot-contact clean-up) and
sequenced for the viewer by `sequences.py`. The same clips drive the Sitka promo film.

| Viewer sequence | Subject | Trial | CMU description | Portion used |
|---|---|---|---|---|
| Walk | 35 | 01 | walk | one stride looped, 1.125-2.25 s |
| Run | 35 | 17 | run/jog | one stride looped, 0.375-1.125 s |
| Sit down | 86 | 09 | walking, sitting, looking, stand up | 8.45-10.8 s (turn ends, sit; feet held where they settle) |
| Stand up | 86 | 09 | walking, sitting, looking, stand up | 23.2-25.0 s |
| Lift (stoop) | 115 | 01 | pick up box, bend from waist | 0.35-2.15 s |
