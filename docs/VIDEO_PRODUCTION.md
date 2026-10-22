# SITKA promo: production recipe (reusable formula)

A ~90 s narrated product film built entirely on the M5, from the real CAD, with no browser AI generation.
Final files: `final/sitka_promo.mp4`, `final/thumbnail.png`, `final/youtube.json`.

## 0. Rules this follows (from Matt's memory files)
- Real motion, never Ken Burns over stills (`feedback_kenburns_stills_read_as_boring`).
- Instrumental bed only; logo bug throughout; big logo on the end card (`feedback_video_ads_rules`).
- Ending: spoken tagline lands on a title slam (flash + hit), bed fades INTO the slam, a resolved chord sting rings out (`feedback_video_endings_must_land`).
- Narration in Matt's clone, exaggeration 0.40, cfg 0.5, pitch 0.92, +3 dB @180 Hz, -3 dB @5 kHz (`reference_matt_voice_clone_narration_settings`).
- On-screen numbers only when the narrator says them; everything lands on its word.
- Watch the whole thing (dense frame strips around every line) before showing it (`feedback_watch_video_before_showing`).
- Check Song Forge `127.0.0.1:8767/api/status` (`jobs_running == 0`) before ChatterBox / heavy GPU work.

## 1. Folder map
| Path | What |
|---|---|
| `script.md` | the 10 narration lines |
| `vo2/raw/` | ChatterBox renders; `vo2/final/vo0..9.wav` finished lines; `vo2/words.json` word timestamps |
| `timing/timeline.json` | where every line and every word sits in the film (drives everything) |
| `cadsnap/cad/` | read-only snapshot of `run-sit-exo/cad` (never write into the CAD folder) |
| `blender/engine.py` | motion engine (pose, parts, struts, cables, camera, Cycles/EEVEE render, 2D part tracking) |
| `blender/shots.py` | the shot list (one function per shot) |
| `edit/render_plan.json` | per-shot source range + render engine actually used in the cut |
| `renders/<shot>_final/` | PNG frames + `track.json` (projected part positions per frame) |
| `manim/` | physics diagrams (Manim CE venv, `scenes.py`, `render_all.sh`, `out/*.mov` ProRes 4444 alpha) |
| `music/bed_a.wav` | Song Forge instrumental bed (bed_b = unused alternative) |
| `edit/build_edl.py` | the edit: cuts, captions, callouts, lower thirds, flashes, sfx cues, all keyed to words |
| `remotion/` | picture assembly (React components in `src/Sitka.tsx`, data in `src/edit.json`) |
| `tools/` | `voice_finish.sh`, `whisper_words.py`, `mix_audio.py`, `level_check.sh`, `sheet.sh`, `snap_cad.sh` |

## 2. Narration
```bash
curl -s 127.0.0.1:8767/api/status          # jobs_running must be 0
echo '{"character":"matt2","lines":[...10 lines...],"out_dir":".../vo2/raw"}' \
  | CHATTERBOX_EXAG=0.40 CHATTERBOX_CFG=0.5 ~/chatterbox-env/bin/python ~/.local/bin/chatterbox-batch
for i in 0..9: tools/voice_finish.sh vo2/raw/part00$i.wav vo2/final/vo$i.wav
~/chatterbox-env/bin/python tools/whisper_words.py vo2/words.json vo2/final/vo*.wav
```
- `voice_finish.sh` = silenceremove (both ends, -45 dB) -> `asetrate=SR*0.92,aresample=SR,atempo=1/0.92` (no rubberband)
  -> `equalizer=f=180:g=+3`, `equalizer=f=5000:g=-3` -> 0.25 s pad -> `loudnorm=I=-16:TP=-1.5:LRA=11` -> 48 kHz mono.
- Check every line's transcript AFTER the finish chain (mlx-whisper large-v3-turbo). Line 5 came back "cam chair" after
  the pitch shift; 4 retakes were rendered and take 1 ("camp chair") replaced it. The original is kept in `vo2/retake/`.
- Line placement (`timing/timeline.json`): 0.5-0.85 s gaps; the end-card slam sits on "Come" of the last line.

## 3. Music
- `tools/make_bed.py OUT "style" SECONDS` posts `/api/song` to the local Song Forge with `lyrics:"[inst]"`,
  `private:true, video_only:true`, polls, downloads at once (the mini purges private songs).
- Two 96 s beds rendered; picked by analysis (RMS envelope every 4 s, librosa beats, chroma key):
  bed A = orchestral/piano build, C major, a breakdown then a big downbeat at 81.0 s.
- `mix_audio.py` skips the first 0.9 s of the bed so that downbeat lands exactly on the end-card slam (80.1 s).
- Whisper-check a bed for stray vocals (hallucinated "Thank you" on music = no real lyrics).

## 4. Motion from the CAD (Blender 5.1, headless)
`engine.py` execs the CAD agent's own `assemble.py` up to its main loop, so the rig, all parts, anchors and the cable
router are identical to the approved CAD. Per frame it:
1. interpolates POSE PARAMETERS (poses.py angles) between keys, so limbs never shrink (no vertex lerp);
2. grounds the body; walk/run shots use a foot-lock (stance-foot vertex stays put, the root travels);
3. places parts on segment frames (`common.py` math; knee frame = half-slerp thigh/shin);
4. deploys the struts (swing down, then telescope to the floor; they shorten as the hips drop);
5. re-routes every tendon/band/strap over the posed body with the CAD router (arc wrap, conform);
6. hides any small fastener left floating > 20 mm from skin, parts and cables (safety net; logs `HIDE floating`);
7. projects ~30 named parts to 2D with an occlusion ray (`track.json`) for callouts that follow the parts.

Materials: procedural carbon twill + clear coat, titanium anodized aluminium, orange anodize, woven technical fabric
(sheen + weave bump), open-cell foam, glossy glass-fibre leaf springs, matte grey mannequin; tendons and bands
get animated emission ("glow"). Environments: dark studio (Poly Haven `studio_small_09`, camera sees near-black,
orange/teal rims) and a golden-hour coastal bluff (`cape_hill` HDRI, rocky_trail ground fading into the HDRI).

```bash
cd blender
# previz everything fast (EEVEE, 640x360, every 3rd frame) and look at contact sheets
blender -b --factory-startup -noaudio --python engine.py -- --shot=s01_knee_macro,... --tag=pv --engine=EEVEE --res=640x360 --every=3
../tools/sheet.sh ../renders/s10_sit_wide_pv /tmp/s10.jpg 8 4
# finals: only the source ranges the cut uses (edit/render_plan.json), several shots per Blender session
blender -b --factory-startup -noaudio --python engine.py -- --shot=a,b,c --plan=../edit/render_plan.json --tag=final --samples=48
```
Speed on the M5 at 1080p: Cycles ~5-9 s/frame (48 spp, adaptive, OIDN), EEVEE ~1.5-3 s/frame incl. per-frame
cable routing. Cycles is used for the hero/beauty shots (macro open, hero reveal, bluff, lean-back, finale);
EEVEE for the rest. Coverage: 27 shots previzzed (wide/medium/close for each beat, ~140 s of footage for a 90 s cut).

Previz lessons: the wearer's hands hide the lateral knee in close-ups (use the `STAND_CLEAR` arm pose);
`shift_x` > 0 puts the subject on the LEFT (diagram cards sit on the right); backlit coast shots go to silhouette.

## 5. Diagrams (Manim CE)
`manim/.venv`, `scenes.py`, `render_all.sh`: five alpha overlays (strut weight split, knee spring energy, lift
15 kg / -12 kg / no motor, hamstring + calf bands, module tiles docking to the hub). t=0 of each clip = its narration
line start; every number appears on its spoken word. Manim writes premultiplied alpha; the script converts to straight.
For the edit they are unpacked to PNG sequences in `remotion/public/manim/`.

## 6. Edit (Remotion 4, image sequences)
```bash
python3 edit/build_edl.py            # -> remotion/src/edit.json + edit/sfx.json (TAG=final)
cd remotion && npx remotion render src/index.ts Sitka out/picture.mp4 --codec=h264 --crf=16 --concurrency=6
```
- Components (`src/Sitka.tsx`): Footage (PNG sequence + slow digital push), Flash, Kinetic text (rise / slam),
  CalloutView (dot + leader + label card following `track.json`), LowerThird, Bug ("SITKA" corner), TitleSlam,
  EndCard (SITKA + "Come build one with us." + github.com/nicedreamzapp/sitka).
- `build_edl.py` uses `W(line, word)` = the word's time from whisper, so cuts, captions and numbers land <= 1 frame.

## 7. Audio mix
```bash
~/chatterbox-env/bin/python tools/mix_audio.py   # -> final/mix.wav
tools/level_check.sh                              # voice stem vs ducked music stem
```
- Bed: -0.9 s offset, gain 0.55, `sidechaincompress` keyed by the voice (thr 0.015, ratio 8, attack 20, release 420),
  fades out 1.1 s after the slam over 1.6 s.
- SFX synthesised in numpy: hit (pitched boom + noise), whoosh, riser, blip, tick. Sting = C major (C2 C3 G3 C4 E4 G4 C5,
  bell-like partials) + string pad + sub boom + 3 s convolution reverb, at the slam.
- Whole mix `loudnorm I=-16 TP=-1.5 LRA=11 linear=true`.

## 8. Mux
```bash
ffmpeg -i remotion/out/picture.mp4 -i final/mix.wav -map 0:v -map 1:a -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -crf 17 -preset slow -r 30 -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest final/sitka_promo.mp4
```

## 9. QC (mandatory)
- Contact sheets of every shot (previz and final), frame strips around every narration line against its words,
  callout/number frame check against `timeline.json`, ebur128 on the final, `level_check.sh` for voice vs music,
  mlx-whisper transcript of the final mix against the script, last 10 s checked for the slam + sting.
- See the bottom of this file for the QC log of this cut.

## 10. Thumbnail
`npx remotion still src/index.ts Thumb final/thumb_1080.png` then `ffmpeg -vf scale=1280:720` -> `final/thumbnail.png`.

## QC log, this cut (2026-10-22)
- Final: `final/sitka_promo.mp4`, 89.25 s, 1920x1080 30 fps H.264 High, AAC 48 kHz (320k target).
- Loudness: whole mix -15.9 LUFS integrated, true peak -1.5 dBFS, LRA 3.8. Voice stem vs ducked music stem: music sits ~14 dB under the voice.
- mlx-whisper transcript of the final mix matches the script word for word (222/222 words matched, median offset 20 ms from the planned word times).
- Frame checks at -2/+1 frames around: title slam, "15", "12", "$1,300", "10 lb", "two straps", end slam: every element appears on its word.
- Ending: slam (bed downbeat + hit + flash) lands just AFTER "us" (81.05 s) so the hit never masks "Come"; whisper on the final mp4 reads "come build one with us"; C-major sting rings out under an 8.2 s end card.
- Fixes made after the first full watch: two callouts pointed at off-frame parts (re-targeted to the knee tendon and the EA clutch),
  "Two straps" now points at both straps, callout labels are clamped inside the frame, HILLS moved off the bright sky,
  an unreadable 0.3 s formula line was dropped, the end-card hold was cut from 9.4 s to 8.2 s, the dark strap close-up (s14) was cut.
- Known limits: the wearer is a matte MakeHuman mannequin; walking/running are procedural cycles (not mocap); the stairs beat is
  text over the motor shot (no stair set); the CAD snapshot is from 05:16 on 10/22 (re-run `tools/snap_cad.sh` + the render plan
  if the CAD changes).
