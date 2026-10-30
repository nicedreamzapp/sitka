// node brain/brain_cli.mjs features <tracks.json> <out.json>
//   joint tracks (from train_mode_model.py) -> 50 Hz feature rows, using the same sitka_brain.js the viewer runs
// node brain/brain_cli.mjs viewer [--json out.json]
//   runs the whole brain (simulated sensors -> model -> safety layer) on the viewer's mocap animation
//   and prints what mode it called for each sequence
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const B = createRequire(import.meta.url)('./sitka_brain.js');
const [cmd, a1, a2] = process.argv.slice(2);

function loadModel() { return JSON.parse(readFileSync(join(here, 'mode_model.json'), 'utf8')); }

if (cmd === 'features') {
  const J = JSON.parse(readFileSync(a1, 'utf8'));
  const out = {};
  for (const [name, tr] of Object.entries(J)) {
    const S = B.synth(tr, { pad: tr.pad ?? 1.0, cycles: 1 });
    out[name] = { t0: S.t0, X: S.X.map(r => r.map(v => Math.round(v * 1e5) / 1e5)) };
  }
  writeFileSync(a2, JSON.stringify(out));
} else if (cmd === 'viewer') {
  const src = readFileSync(join(here, '..', 'cad', 'viewer', 'sitka_anim.js'), 'utf8');
  const A = JSON.parse(src.slice(src.indexOf('=') + 1).trim().replace(/;$/, ''));
  const M = loadModel();
  const res = {};
  for (const name of Object.keys(A.seqs)) {
    const tr = B.tracksFromViewer(A, name);
    const R = B.run(M, tr, { cycles: 3, pad: 1.0 });
    const sum = B.summarize(R);
    const modes = R.D.slice(R.S.t0).map(d => d.mode), raw = R.D.slice(R.S.t0).map(d => d.raw);
    const vetoes = {}; for (const d of R.D.slice(R.S.t0)) for (const v of d.vetoes) vetoes[v] = (vetoes[v] || 0) + 1;
    res[name] = { ...sum, vetoes, modes, rawModes: raw, conf: R.D.slice(R.S.t0).map(d => Math.round(d.conf * 100) / 100) };
    console.log(name.padEnd(8), JSON.stringify(sum.mode), 'raw', JSON.stringify(sum.raw), `veto ${sum.vetoPct}% lockL ${sum.lockPctL}% lockR ${sum.lockPctR}% motor ${sum.motorPct}%`, JSON.stringify(vetoes));
  }
  const k = process.argv.indexOf('--json');
  if (k > 0) writeFileSync(process.argv[k + 1], JSON.stringify(res));
} else {
  console.log('usage: node brain/brain_cli.mjs features <tracks.json> <out.json> | viewer [--json out.json]');
  process.exit(1);
}
