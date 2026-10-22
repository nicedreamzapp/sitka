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
// The geometry and the seat-lean equation are the SAME as seat_torque_model.mjs:
//   balanced shank lean phi: tan(phi) = s*sin(theta) / (Ls + s*cos(theta)), capped at 35°.

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
s_pad  = 0.65 * Lt;     // seat pad CoP from knee (EST, params.mjs)

// ---------- exo ----------
act_d = 98; act_w = 62;    // CubeMars AK10-9 V2.0: Ø98 x 61.7 mm
bar_t = 8;  bar_h = 28;    // 7075 lateral uprights (seat_torque_model.mjs)
lat   = hipW/2 + 75;       // lateral offset of the uprights from the midline

// ---------- pose table ----------
// knee = flexion (0 straight). phi = forward shank lean. hip = thigh angle forward of vertical.
function lean(th) = min(35, atan2(s_pad*sin(th), Ls + s_pad*cos(th)));
function seatKnee(m) = m=="perch"?25 : m=="halfsit"?60 : m=="chair"?90 : m=="squat"?120 : 0;
isSeat = seatKnee(mode) > 0;
thS  = seatKnee(mode);
phiS = isSeat ? lean(thS) : 0;

// per-leg [hipFlex, kneeFlex] for right (y<0) and left (y>0)
R = mode=="run" ? [ 18, 38] : [thS - phiS, thS];   // run: right = stance leg
Lg= mode=="run" ? [ 48, 100] : [thS - phiS, thS];  // run: left = swing leg
trunk = mode=="run" ? 12 : mode=="perch" ? 4 : mode=="halfsit" ? 10 : mode=="chair" ? 18 : mode=="squat" ? 32 : 0;

// hip position so the (stance) ankle sits at x=0, z=ankleH
function ankleRel(a) = [ Lt*sin(a[0]) - Ls*sin(a[1]-a[0]), -Lt*cos(a[0]) - Ls*cos(a[1]-a[0]) ];
ar   = ankleRel(R);
hipX = -ar[0];
hipZ = ankleH - ar[1] + (mode=="run" ? 0 : 0);

pad_deploy = isSeat ? 1 : 0;   // seat pads fold down only in seat modes
locked     = isSeat;

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
// side = +1 left, -1 right
module leg(ang, side) {
  hipF = ang[0]; knee = ang[1];
  rotate([0, -hipF, 0]) {                       // thigh hangs along -z, swung forward by hipF
    if (show_body) color(C_body) limb([0,0,0], [0,0,-Lt], 78, 58);
    // thigh upright (lateral)
    ex([0, side*120, 0]) color(C_alu) translate([-bar_h/2, side*(lat-hipW/2) - bar_t/2, -Lt+10]) cube([bar_h, bar_t, Lt-90]);
    // thigh cuff (proximal-mid thigh) — open C ring
    ex([60, side*60, 0]) color(C_cuff) translate([0,0,-Lt*0.45]) difference() {
      cylinder(r=92, h=70, center=true); cylinder(r=80, h=72, center=true);
      translate([90,0,0]) cube([90,90,80], center=true); }
    // fold-down seat pad: a charcoal foam cushion with an amber trim edge.
    // STOWED: flat on the outside of the thigh rail. DEPLOYED (seat modes): swung under the thigh.
    ex([-140, side*80, 0]) translate([0, 0, -(Lt - s_pad)]) {
      color(C_alu) translate([-bar_h/2 - 2, side*(lat-hipW/2) - 6, -35]) cube([30, 12, 70]);       // hinge block
      if (pad_deploy > 0.5) {
        color(C_pad)  translate([-93, -75 + side*5, -75]) cube([18, 150, 150]);                 // under the thigh
        color(C_trim) translate([-94, side > 0 ? 72 : -82, -77]) cube([20, 10, 154]);
      } else {
        color(C_pad)  translate([-95, side > 0 ? (lat-hipW/2) + 7 : -(lat-hipW/2) - 25, -75]) cube([150, 18, 150]);   // flush on the rail
        color(C_trim) translate([52, side > 0 ? (lat-hipW/2) + 6 : -(lat-hipW/2) - 26, -77]) cube([10, 20, 154]);
      }
    }
    // haptic disc on the cuff
    ex([60, side*60, 0]) color(C_sens) translate([-88, 0, -Lt*0.45]) rotate([0,90,0]) cylinder(r=10, h=4);

    translate([0,0,-Lt]) {
      // KNEE ACTUATOR, lateral, axis = y
      ex([0, side*200, 0]) translate([0, side*(lat-hipW/2+bar_t/2+act_w/2), 0]) rotate([90,0,0]) {
        color(C_act) cylinder(d=act_d, h=act_w, center=true);
        color(C_ring) translate([0,0,side*(act_w/2+4)]) difference() {      // toothed lock ring
          cylinder(d=78, h=8, center=true); cylinder(d=50, h=10, center=true); }
        color(C_alu) translate([0,0,-side*(act_w/2+2)]) cylinder(d=40, h=6, center=true);
      }
      // pawl + latching solenoid housing, on the thigh side of the joint
      ex([0, side*200, 0]) color(locked ? [0.95,0.30,0.25] : C_act)
        translate([-act_d/2 - 14, side*(lat-hipW/2+bar_t+act_w+6), 30]) cube([26, 18, 46], center=true);
      // medial passive hinge
      ex([0, -side*90, 0]) color(C_alu) translate([0, -side*(hipW/2 - 10 - 40), 0]) rotate([90,0,0]) cylinder(d=46, h=10, center=true);
      if (show_body) color(C_body) sphere(60);

      rotate([0, knee, 0]) {                    // shank, flexed back by the knee angle
        if (show_body) color(C_body) limb([0,0,0], [0,0,-Ls], 56, 40);
        // shank upright
        ex([0, side*120, -40]) color(C_alu) translate([-bar_h/2, side*(lat-hipW/2) - bar_t/2, -Ls+20]) cube([bar_h, bar_t, Ls-70]);
        // shin cuff (anterior, below the knee)
        ex([90, side*50, -30]) color(C_cuff) translate([0,0,-Ls*0.32]) difference() {
          cylinder(r=68, h=60, center=true); cylinder(r=57, h=62, center=true);
          translate([-75,0,0]) cube([80,80,70], center=true); }
        // heel stirrup: upright → down past the ankle → under the heel
        ex([0, side*60, -140]) color(C_alu) translate([0,0,-Ls]) {
          translate([-bar_h/2, side*(lat-hipW/2) - bar_t/2, -ankleH+6]) cube([bar_h, bar_t, ankleH+30]);
          // (the heel plate is drawn level, in the foot frame below)
        }
        translate([0,0,-Ls]) rotate([0, -(knee-hipF), 0]) {   // foot stays level with the floor
          // heel plate of the stirrup: level, under the heel, ties into the lateral bar
          ex([0, side*60, -140]) color(C_alu) translate([-70, side > 0 ? -50 : -(lat-hipW/2) - 20, -ankleH - 4])
            cube([120, lat-hipW/2 + 70, 6]);
          if (show_body) color(C_body) translate([footL*0.25, 0, -ankleH+35]) scale([1, 0.38, 0.22]) sphere(footL*0.6);
          // FSR insole: 4 sensors
          ex([0, 0, -160]) translate([0,0,-ankleH+2]) {
            color([0.15,0.17,0.2]) translate([-55, -45, 0]) cube([footL, 90, 3]);
            for (p = [[-30,0],[120,-25],[120,25],[190,0]]) color(C_sens) translate([p[0], p[1], 3]) cylinder(r=9, h=2);
          }
        }
      }
    }
  }
}

// ---------------- belt: battery packs + controller ----------------
module belt() {
  ex([-200, 0, 120]) color(C_cuff) translate([0,0,60]) difference() {
    scale([1, 1.55, 1]) cylinder(r=125, h=55, center=true);
    scale([1, 1.55, 1]) cylinder(r=112, h=57, center=true); }
  for (sd = [-1, 1]) ex([-320, sd*80, 140]) color(C_batt) translate([-128, sd*72, 60]) cube([44, 120, 80], center=true);   // 2 x 6S1P packs
  ex([-320, 0, 260]) color(C_act) translate([-130, 0, 115]) cube([40, 60, 40], center=true);  // Teensy + CAN box
  ex([200, 0, 120]) color([0.9,0.2,0.2]) translate([118, -90, 60]) rotate([0,90,0]) cylinder(r=14, h=12);   // E-stop / tap
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
  translate([0, -hipW/2, 0]) leg(R, -1);
  translate([0,  hipW/2, 0]) leg(Lg, +1);
}
// floor
color([0.16,0.18,0.22]) translate([-700,-500,-2]) cube([1500,1000,2]);
echo(str("mode=", mode, " knee=", thS, " shank lean=", phiS, " hip height=", hipZ));
