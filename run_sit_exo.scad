// Run + Sit Exo — parametric CAD, prototype one (P1)
// CERN-OHL-S-2.0 — see LICENSE.
//
// Pose is a parameter. Render any mode from the command line, e.g.
//   openscad -D 'mode="chair"' -o chair.png run_sit_exo.scad
// mode: "stand" | "perch" | "halfsit" | "chair" | "squat" | "run"
//
// Units: mm, degrees. x = forward, y = left, z = up. Origin = floor under the
// right... no: under the midpoint between the ankles (stance ankle for "run").
//
// v2 TRIPOD SEAT (2026-10-22 audit): each leg stands on heel + toes + a REAR LEG
// hinged at the top of the thigh rail. Shank lean ≤ 20°, pad proximal (0.75·Lt from
// the knee), free ankle pivot, one-way ratchet. Geometry = seat_torque_model.mjs.

mode        = "chair";
show_body   = true;    // the wearer (95th pct US man, NHANES stature 1874 mm)
explode     = 0;       // 0..1 pulls the exo parts off the body
body_alpha  = 0.35;

$fn = 40;

// ---------- wearer (Winter segment fractions; params.mjs) ----------
H   = 1874;
Lt  = 0.245 * H;        // thigh  459
Ls  = 0.246 * H;        // shank  461
ankleH = 80;            // ankle axis above floor in a shoe (EST)
footL  = 0.152 * H;     // foot length, visual only
hipW   = 190;           // hip-joint spacing, visual (EST)
s_pad  = 0.75 * Lt;     // seat pad CoP from knee, proximal (params.mjs)
heelX = -55; toeX = 210; // foot contacts vs the ankle axis (params.mjs)
muMax = 0.30;            // rear-foot friction design cap (params.mjs)

// ---------- exo ----------
act_d = 98; act_w = 62;    // CubeMars AK10-9 V2.0: Ø98 x 61.7 mm
bar_t = 8;  bar_h = 28;    // 7075 lateral uprights (seat_torque_model.mjs)
lat   = hipW/2 + 75;       // lateral offset of the uprights from the midline

// ---------- pose table (params.mjs SEAT.modes) ----------
// [knee flexion, shank lean phi, trunk lean, rear leg used]
function seatRow(m) = m=="perch"?[25,10,4,0] : m=="halfsit"?[60,15,10,1] : m=="chair"?[90,15,18,1] : m=="squat"?[120,20,32,1] : [0,0,0,0];
row  = seatRow(mode);
isSeat = row[0] > 0;
thS = row[0]; phiS = row[1]; rearOn = row[3] == 1;

R = mode=="run" ? [ 18, 38] : [thS - phiS, thS];   // run: right = stance leg
Lg= mode=="run" ? [ 48, 100] : [thS - phiS, thS];  // run: left = swing leg
trunk = mode=="run" ? 12 : row[2];

function ankleRel(a) = [ Lt*sin(a[0]) - Ls*sin(a[1]-a[0]), -Lt*cos(a[0]) - Ls*cos(a[1]-a[0]) ];
ar   = ankleRel(R);
hipX = -ar[0];
hipZ = ankleH - ar[1];

pad_deploy = isSeat ? 1 : 0;
locked     = isSeat;

// rear leg: hinge 0.85·Lt from the knee (34 mm behind the rail), foot as far back as
// 0.42 m behind the heel allows while the friction it needs stays ≤ muMax
hF = thS - phiS;
hingeLoc = [-34, -(1 - 0.85) * Lt];
Hr = [hipX + hingeLoc[0]*cos(hF) - hingeLoc[1]*sin(hF), hipZ + hingeLoc[0]*sin(hF) + hingeLoc[1]*cos(hF)];
HrAx = [hipX + 0.15*Lt*sin(hF), hipZ - 0.15*Lt*cos(hF)];   // hinge on the rail axis, as in the model
RfX = max(heelX - 420, HrAx[0] - muMax * HrAx[1]);
Rf = [RfX, 15];

// ---------- colours ----------
C_body  = [0.80,0.78,0.74, body_alpha];
C_alu   = [0.72,0.75,0.80];
C_act   = [0.12,0.13,0.15];
C_ring  = locked ? [0.95,0.30,0.25] : [0.37,0.83,0.66];
C_pad   = [0.17,0.20,0.26];   // charcoal foam (the amber is reserved for the battery packs)
C_trim  = [0.95,0.72,0.29];
C_cuff  = [0.20,0.24,0.30];
C_sens  = [0.37,0.83,0.66];
C_batt  = [0.95,0.72,0.29];

module limb(a, b, r1, r2) { hull() { translate(a) sphere(r1); translate(b) sphere(r2); } }
module ex(v) { translate(explode * v) children(); }

// ---------------- one leg, built in hip frame ----------------
// side = +1 left, -1 right.  In the thigh frame: x forward, y lateral, z along the thigh (down = -z).
L75 = lat - hipW/2;          // lateral rail offset from the leg axis (75)
med = -66;                   // medial bar offset (× side)
module bar(a, b, r=4) hull() { translate(a) sphere(r); translate(b) sphere(r); }
module leg(ang, side) {
  hipF = ang[0]; knee = ang[1];
  rotate([0, -hipF, 0]) {
    if (show_body) color(C_body) limb([0,0,0], [0,0,-Lt], 78, 58);
    // lateral thigh rail (rail top at -58) + medial thigh bar (0.36 m) + anterior bridge above the patella
    ex([0, side*120, 0]) color(C_alu) translate([-bar_h/2, side*L75 - bar_t/2, -Lt+10]) cube([bar_h, bar_t, Lt-68]);
    ex([0, -side*100, 0]) color(C_alu) translate([-10, side*med - 3, -Lt]) cube([20, 6, 360]);
    ex([120, 0, 0]) color(C_alu) translate([0,0,-Lt+120]) for (i=[0:8]) bar([80*sin(i*20), side*L75*cos(i*20)*(i<=4?1:0.88), 0], [80*sin((i+1)*20), side*L75*cos((i+1)*20)*(i<4?1:0.88), 0], 4);
    // thigh shell cuff (distal) + haptic
    ex([60, side*60, 0]) color(C_cuff) translate([0,0,-Lt*0.58]) difference() {
      cylinder(r=90, h=70, center=true); cylinder(r=80, h=72, center=true);
      translate([90,0,0]) cube([90,90,80], center=true); }
    ex([60, side*60, 0]) color(C_sens) translate([-88, 0, -Lt*0.58]) rotate([0,90,0]) cylinder(r=10, h=4);
    // seat pad 200 x 180, proximal; stowed flat on the rail
    ex([-140, side*80, 0]) translate([0, 0, -(Lt - s_pad)]) {
      color(C_alu) translate([-bar_h/2 - 2, side*L75 - 6, -35]) cube([30, 12, 70]);
      if (pad_deploy > 0.5) {
        color(C_pad)  translate([-104, side > 0 ? L75 - 180 + 10 : -L75 - 10, -100]) cube([18, 180, 200]);
        color(C_trim) translate([-105, side > 0 ? L75 + 4 : -L75 - 14, -102]) cube([20, 10, 204]);
        color(C_alu)  translate([-100, side*med - 4, -40]) cube([100, 8, 14]);         // medial support arm
      } else {
        color(C_pad)  translate([-110, side > 0 ? L75 + 7 : -L75 - 25, -100]) cube([180, 18, 200]);
        color(C_trim) translate([62, side > 0 ? L75 + 6 : -L75 - 26, -102]) cube([10, 20, 204]);
      }
    }
    // rear leg STOWED along the outside of the rail (deployed legs are drawn in world space)
    if (!rearOn) ex([-120, side*160, 0]) translate([hingeLoc[0], side*(L75+30), hingeLoc[1]]) {
      color(C_alu) rotate([90,0,0]) cylinder(r=14, h=22, center=true);
      color(C_act) translate([0,0,-350]) cylinder(r=12, h=350);
      color([0.1,0.1,0.1]) translate([0,0,-356]) sphere(13);
    } else ex([-120, side*160, 0]) color(C_alu) translate([hingeLoc[0], side*(L75+30), hingeLoc[1]]) rotate([90,0,0]) cylinder(r=14, h=22, center=true);
    // suspension yoke at the rail top
    ex([0, side*160, 120]) color(C_cuff) translate([-26, side*(L75+8) - 6, -62]) cube([44, 12, 24]);
    // cable sleeve along the rail front edge
    color([0.05,0.06,0.07]) translate([bar_h/2 + 3, side*(L75+6), -Lt+70]) cylinder(r=4, h=Lt-150);

    translate([0,0,-Lt]) {
      // KNEE ACTUATOR (AK10-9) + output-flange bolts
      ex([0, side*200, 0]) translate([0, side*(L75+bar_t/2+act_w/2), 0]) rotate([90,0,0]) {
        color(C_act) cylinder(d=act_d, h=act_w, center=true);
        for (i=[0:7]) color([0.85,0.87,0.9]) rotate([0,0,i*45]) translate([36,0,-side*(act_w/2+1)]) cylinder(r=2.6, h=3, center=true);
      }
      // pawl housing (thigh side) — 3-tooth pawl
      ex([-80, side*200, 0]) color(locked ? [0.95,0.30,0.25] : C_act) translate([-82, side*(L75+80), 6]) cube([34, 18, 56], center=true);
      // single-axis medial hinge + the knee axis (thin rod)
      ex([0, -side*90, 0]) color(C_alu) translate([0, side*med, 0]) rotate([90,0,0]) cylinder(d=48, h=10, center=true);
      color([0.49,1,0.82]) rotate([90,0,0]) cylinder(r=1.2, h=2*(L75+130), center=true);
      if (show_body) color(C_body) sphere(60);

      rotate([0, knee, 0]) {
        if (show_body) color(C_body) limb([0,0,0], [0,0,-Ls], 56, 40);
        // ONE-WAY RATCHET SECTOR, bolted to the shank side, r = 50 mm, 140°
        ex([0, side*260, 0]) color(C_ring) translate([0, side*(L75+80), 0]) rotate([90,0,0])
          rotate([0,0,175]) rotate_extrude(angle=140, $fn=60) translate([30,-6]) square([25, 12]);
        // lateral shank rail to the ankle pivot, medial shank bar, posterior bridge
        ex([0, side*120, -40]) color(C_alu) translate([-bar_h/2, side*L75 - bar_t/2, -Ls]) cube([bar_h, bar_t, Ls-20]);
        ex([0, -side*100, 0]) color(C_alu) translate([-10, side*med - 3, -110]) cube([20, 6, 110]);
        ex([-120, 0, 0]) color(C_alu) translate([0,0,-110]) for (i=[0:8]) bar([-68*sin(i*20), side*L75*cos(i*20)*(i<=4?1:0.88), 0], [-68*sin((i+1)*20), side*L75*cos((i+1)*20)*(i<4?1:0.88), 0], 4);
        // shin shell cuff (tibial crest)
        ex([90, side*50, -30]) color(C_cuff) translate([0,0,-Ls*0.33]) difference() {
          cylinder(r=66, h=60, center=true); cylinder(r=56, h=62, center=true);
          translate([-75,0,0]) cube([80,80,70], center=true); }
        // shank IMU on the rail
        color(C_act) translate([22, side*(L75+12), -Ls*0.5]) cube([14, 22, 26], center=true);
        // free ANKLE PIVOT at the lateral malleolus
        ex([0, side*200, -120]) color([0.85,0.87,0.9]) translate([0, side*(L75+7), -Ls]) rotate([90,0,0]) cylinder(r=17, h=12, center=true);
        translate([0,0,-Ls]) rotate([0, -(knee-hipF), 0]) {   // foot frame (level with the floor)
          // heel stirrup hangs from the pivot: vertical bar, heel plate, heel pad below the pivot
          ex([0, side*60, -140]) {
            color(C_alu) translate([-11, side*L75 - 4, -ankleH]) cube([22, 8, ankleH]);
            color(C_alu) translate([-70, side > 0 ? -40 : -L75 - 30, -ankleH - 4]) cube([100, L75 + 70, 6]);
            color([0.1,0.1,0.12]) translate([-45, -32, -ankleH + 2]) cube([70, 64, 6]);
          }
          if (show_body) color(C_body) translate([footL*0.25, 0, -ankleH+35]) scale([1, 0.38, 0.22]) sphere(footL*0.6);
          ex([0, 0, -160]) translate([0,0,-ankleH+2]) {
            color([0.15,0.17,0.2]) translate([-55, -45, 0]) cube([footL, 90, 3]);
            for (p = [[-30,0],[120,-25],[120,25],[190,0]]) color(C_sens) translate([p[0], p[1], 3]) cylinder(r=9, h=2);
          }
        }
      }
    }
  }
}

// ---------------- rear legs, deployed (world space) ----------------
// 24 / 20 / 16 x 1.5 mm three-section carbon tube, pivoting rubber foot
module rearLeg(side) {
  y = side * (hipW/2 + L75 + 30);
  a = [Hr[0], y, Hr[1]]; b = [Rf[0], y, Rf[1]];
  d = b - a;
  ex([-200, side*160, 0]) {
    color(C_act) bar(a, a + d*0.42, 12);
    color(C_act) bar(a + d*0.35, a + d*0.75, 10);
    color(C_act) bar(a + d*0.68, b, 8);
    color(C_alu) translate(a + d*0.40) sphere(13.5);
    color(C_alu) translate(a + d*0.73) sphere(11.5);
    color([0.1,0.1,0.1]) translate([Rf[0], y, 3]) cylinder(r1=26, r2=22, h=10);   // pivoting foot pad
  }
}

// ---------------- belt: battery packs + controller + strap anchors ----------------
module belt() {
  ex([-200, 0, 120]) color(C_cuff) translate([0,0,60]) difference() {
    scale([1, 1.55, 1]) cylinder(r=125, h=55, center=true);
    scale([1, 1.55, 1]) cylinder(r=112, h=57, center=true); }
  for (sd = [-1, 1]) ex([-320, sd*80, 140]) color(C_batt) translate([-128, sd*72, 60]) cube([44, 110, 80], center=true);
  ex([-320, 0, 260]) color(C_act) translate([-130, 0, 115]) cube([40, 60, 40], center=true);
  ex([200, 0, 120]) color([0.9,0.2,0.2]) translate([118, -90, 60]) rotate([0,90,0]) cylinder(r=14, h=12);
}
// suspension straps: belt rear → over the glute → yoke at the rail top (no rigid hip joint)
module straps(ang, side) {
  hf = ang[0];
  yoke = [-4*cos(hf) + 50*sin(hf), side*(hipW/2 + L75 + 8), -4*sin(hf) - 50*cos(hf)];
  for (an = [[-93, side*120, 80], [-52, side*168, 80]]) {
    mid = (an + yoke)/2 + [-60, side*25, 0];
    color([0.15,0.19,0.25]) { bar(an, mid, 3.2); bar(mid, yoke, 3.2); }
  }
  // sleeved cable: controller → belt side → rail top
  color([0.05,0.06,0.07]) { bar([-110, side*30, 140], [-40, side*190, 82], 4); bar([-40, side*190, 82], yoke + [30, 0, 0], 4); }
}

module torso() {
  rotate([0, trunk, 0]) {
    color(C_body) limb([0,0,40], [0,0,520], 120, 135);
    color(C_body) translate([0,0,680]) sphere(105);
  }
}

// ---------------- assemble ----------------
translate([hipX, 0, hipZ]) {
  if (show_body) torso();
  belt();
  if (explode < 0.02) { straps(R, -1); straps(Lg, 1); }
  translate([0, -hipW/2, 0]) leg(R, -1);
  translate([0,  hipW/2, 0]) leg(Lg, +1);
}
if (rearOn) { rearLeg(-1); rearLeg(1); }
// floor
color([0.16,0.18,0.22]) translate([-900,-500,-2]) cube([1700,1000,2]);
echo(str("mode=", mode, " knee=", thS, " shank lean=", phiS, " hip height=", hipZ, " rear foot behind heel=", heelX - RfX, " rear leg length (axis)=", norm([RfX,0] - HrAx)));
