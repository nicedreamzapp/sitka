# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report them privately through GitHub: go to the **Security** tab of this repo and click **Report a vulnerability** ([direct link](https://github.com/nicedreamzapp/sitka/security/advisories/new)). Only the maintainer sees the report.

Helpful details: what you found, which file or part it is in, how to reproduce it (or the numbers that show it), and which commit you looked at. If it is a design problem that could injure a wearer, say which module and pose it affects.

I aim to reply within 3 days and to ship a fix or a clear plan within 30 days, depending on severity. You will be credited in the advisory unless you ask not to be.

## Supported versions

Fixes go into the latest design on `main`. Please check against it before reporting, since parts and numbers change often.

## What matters most here

Sitka is a design, not a product yet, so the parts where a mistake could hurt someone are the numbers people would build from:

- the seat load path: `seat_torque_model.mjs`, `params.mjs` and the sit spring and clamp parts in `cad/parts/build_parts.py`, where a wrong number could let a seat give way under someone
- the walking and ankle clutches (`ea_clutch_*` and `m4_clutch_*` in `cad/parts/build_parts.py`), which must fail open so a spring cannot catch mid-swing and trip the wearer
- `parts_list.py` and the `PARTS_LIST.md` and `parts.csv` it writes, which name the materials and parts people buy
- `cad/build_all.sh` and the Python and Blender scripts it runs, if you rebuild the CAD on your own machine
