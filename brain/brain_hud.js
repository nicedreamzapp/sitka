// Live mode readout for sitka_viewer.html. While a motion-capture sequence plays, the brain runs on
// SIMULATED sensors (thigh/shin/hub IMU + insoles computed from the animated skeleton): the model calls
// the mode, the plain-code safety layer decides each clutch and the motor. Read-only: it never changes
// the animation. Needs brain/sitka_brain.js and brain/mode_model.js loaded first.
(function () {
  'use strict';
  const B = window.SitkaBrain, M = window.SITKA_BRAIN_MODEL;
  const el = document.getElementById('brain');
  if (!B || !M || !el) return;
  const $ = id => document.getElementById(id);
  const cache = {};
  const stats = {};                       // per-sequence summary, for tests (window.SITKA_BRAIN_HUD.stats)
  const PLAIN = { STAND: 'Standing', WALK: 'Walking', RUN: 'Running', SIT: 'Sit', LIFT: 'Lift', CLIMB: 'Stairs up', DESCEND: 'Downhill' };
  $('bSize').textContent = (B.modelSize(M) / 1000).toFixed(1) + 'k';

  function get(seq) {
    if (cache[seq]) return cache[seq];
    const A = window.SITKA_ANIM;
    if (!A || !A.seqs || !A.seqs[seq]) return null;
    try {
      const R = B.run(M, B.tracksFromViewer(A, seq), { cycles: 3, pad: 1.0 });
      stats[seq] = B.summarize(R);
      cache[seq] = R;
    } catch (e) { console.warn('brain:', e.message); cache[seq] = { failed: true }; }
    return cache[seq];
  }
  el.addEventListener('click', () => el.classList.toggle('mini'));

  let last = '';
  function tick() {
    requestAnimationFrame(tick);
    const api = window.SITKA_ANIM_API, a = api && api.anim;
    const show = !!(a && a.on && a.seq && a.seq !== 'kit' && window.SITKA_ANIM && !document.documentElement.classList.contains('touring'));
    el.classList.toggle('show', show);
    if (!show) return;
    const R = get(a.seq);
    if (!R || R.failed) { el.classList.remove('show'); return; }
    const S = R.S, span = S.T - S.t0;
    let k = Math.round(a.t * S.hz);
    k = S.loop ? ((k % span) + span) % span : Math.max(0, Math.min(span - 1, k));
    const i = S.t0 + k, d = R.D[i], st = S.steps[i];
    // a veto stays lit for 0.4 s so the eye can catch it
    let veto = '';
    for (let j = i; j >= Math.max(S.t0, i - 20); j--) if (R.D[j].veto) { veto = R.D[j].vetoes[0]; break; }
    const key = [a.seq, i, veto].join('|');
    if (key === last) return; last = key;
    $('bMode').textContent = d.mode;
    $('bModeP').textContent = PLAIN[d.mode] || '';
    $('bConf').textContent = Math.round(d.conf * 100) + '%';
    $('bConf').title = 'how sure the model is of its top guess';
    const ph = d.phase === 'L' || d.phase === 'R' || d.phase === 'L+R' ? 'foot down: ' + d.phase : d.phase;
    $('bPhase').textContent = d.raw !== d.mode ? 'model says ' + d.raw + ', not accepted yet' : ph;
    for (const s of ['L', 'R']) {
      const c = $('bC' + s); c.textContent = d.clutch[s]; c.classList.toggle('lk', d.clutch[s] === 'LOCKED');
      $('bI' + s).style.width = Math.round(Math.min(1, st.side[s].insole / 1.3) * 100) + '%';
    }
    const m = $('bMot'); m.textContent = d.motor === 'off' ? 'off' : d.motor === 'assist' ? 'ASSIST' : 'REGEN'; m.classList.toggle('on', d.motor !== 'off');
    const c = $('bCam'); c.textContent = d.cam === 'HOLDS' ? 'HOLDS' : 'free'; c.title = d.cam === 'HOLDS' ? 'mechanical cam, holds with the power off' : ''; c.classList.toggle('lk', d.cam === 'HOLDS');
    $('bVeto').textContent = veto ? 'VETO: ' + veto : '';
    el.classList.toggle('veto', !!veto);
  }
  requestAnimationFrame(tick);
  window.SITKA_BRAIN_HUD = { stats, cache, get };
})();
