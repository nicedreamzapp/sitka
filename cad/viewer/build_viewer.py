"""Pack the GLBs + pose transforms into cad/viewer/sitka_data.js (base64), so sitka_viewer.html opens
from file:// with no server. Then bundle src/viewer.js (three r170) into sitka_viewer.bundle.js:
  npx esbuild cad/viewer/src/viewer.js --bundle --format=iife --minify --outfile=cad/viewer/sitka_viewer.bundle.js
"""
import base64, json, os
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(CAD, "glb")
P = json.load(open(os.path.join(CAD, "build", "poses.json")))
b = lambda f: base64.b64encode(open(os.path.join(G, f), "rb").read()).decode()
poses = list(P["poses"].keys())
data = dict(parts=b("sitka_parts.glb"), bodies={p: b(f"sitka_body_{p}.glb") for p in poses},
            cables={p: b(f"sitka_cables_{p}.glb") for p in poses},
            poses=dict(parts=P["parts"], cables={p: {k: dict(module=v["module"], state=v["state"]) for k, v in P["cables"][p].items()} for p in poses},
                       poses=P["poses"], parts_meta=P["parts_meta"]))
out = os.path.join(CAD, "viewer", "sitka_data.js")
open(out, "w").write("window.SITKA_DATA=" + json.dumps(data, separators=(",", ":")) + ";\n")
print(out, round(os.path.getsize(out) / 1e6, 1), "MB")
