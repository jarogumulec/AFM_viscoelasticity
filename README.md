# AFM signals and contractility (quick guide)

## Signal relationships
- Deflection (m): vertical bending of the cantilever measured by the optical lever.
  - force (N) = spring_constant (N/m) × deflection (m)
- Height (piezo) (m): Z position commanded to the piezo.
- Height (measured) (m): effective tip position relative to the undeflected cantilever.
  - height (measured) = height (piezo) − deflection

Notes
- Signs can vary by setup; the equations above follow the common convention used in this repo.
- All signals should be in SI units after calibration (m, N, s).

## Indentation (δ)
Indentation is how much the tip has pressed into the sample after contact.

Equivalent formulas (pick one consistent with your data):
- Using “measured”:
  - δ(t) = max(0, h_contact − h_measured(t))
- Using piezo and deflection explicitly:
  - δ(t) = [z_piezo(t) − z_piezo_contact] − [defl(t) − defl_contact]

How to find the contact point
1) On the approach segment, find the first index where force > threshold (e.g., 2–3× noise std).
2) Record contact values: h_contact = height (measured)[i_c], z_piezo_contact, defl_contact.
3) Set δ=0 at contact and compute δ(t) with one of the formulas above for t ≥ contact.

Tip
- For stress, estimate contact area A from δ and tip geometry (e.g., spherical Hertz: a ≈ sqrt(R·δ), A = πa², stress = F/A).

## Contractility vs viscoelastic creep (using myosin-inhibited data)
Goal: separate passive viscoelastic response from active contractility by using a passive reference measured under myosin inhibition (e.g., blebbistatin).

Two clamp regimes:

### A) Force clamp (constant force during hold)
- What changes: displacement (height) over time; force stays near setpoint.
- Model: h_live(t) = h0 + F · J_passive(t) + h_active(t)
- Steps:
  1) Acquire myosin-inhibited force-clamp data at the same force setpoint and timing.
  2) Fit a passive creep compliance J_passive(t) on inhibited data (e.g., power law J(t)=J0·(t/t_ref)^α).
  3) For each live curve, predict passive displacement: h_passive(t) = h0 + F · J_passive(t).
  4) Active residual: h_active(t) = h_live(t) − h_passive(t).
  5) Report contractility metrics:
     - Δh_active = h_active(t_end) − h_active(t_start)  [m]
     - Last-window rate dh_active/dt  [m/s]
     - Optional normalization by load: Δh_active/F  [m/N], (dh_active/dt)/F  [m/(N·s)]

### B) Height/indentation clamp (constant geometry during hold)
- What changes: force over time; geometry (height or δ) is held constant.
- Model: F_live(t) = F_passive(t) + F_active(t)
- Steps:
  1) Acquire myosin-inhibited height- (or indentation-) clamp data with the same indentation history.
  2) Fit a passive force relaxation model on inhibited data (e.g., power-law or SLS) to get F_passive(t).
  3) For each live curve, predict F_passive(t) under the same δ(t) and subtract:
     - F_active(t) = F_live(t) − F_passive(t)
  4) Report contractility metrics:
     - Steady active force (mean over last window)  [N]
     - Active buildup/relaxation amplitude  [N]
     - Optional time constants if fitting kinetics

## Practical checklist
- Match protocols: same setpoint/indentation, dwell time, rate, temperature.
- Calibrate: spring constant and sensitivity (invOLS) to get force/deflection in SI units.
- Clamp quality: low force CV (%) in force clamp; stable height/δ in height clamp.
- Choose consistent sign conventions and zero levels (contact).
- Normalize metrics (per N or per area) when comparing across maps/experiments.

## Minimal formulas recap
- deflection = force / spring_constant
- height (measured) = height (piezo) − deflection
- indentation δ(t) = (h_contact − h_measured(t)) = [z_piezo(t) − z_piezo_contact] − [defl(t) − defl_contact]
- Force-clamp active residual: h_active = h_live − (h0 + F · J_passive)
- Height-clamp active residual: F_active = F_live − F_passive


