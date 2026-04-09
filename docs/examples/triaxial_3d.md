# 3D Triaxial Test

**Directory:** `examples/9_triaxial_asymmetric_cylinder/` (and `examples/10_triaxial_trial_randomness/`)
**Reference scripts:** `triaxial_trial_randomness.py`, `plane_strain_triaxial.py`

The standard geotechnical triaxial test is one of the most important benchmarks for soil and rock models. A cylindrical sample is confined laterally under a cell pressure σ₃, then compressed axially until failure. GeoPeriX reproduces this test in full 3-D with the Drucker-Prager constitutive model.

---

## Physical setup

```
        ┌────┐  ← Top cap: prescribed downward velocity (axial load)
        │    │
      z │ ○──┤  ← Lateral surface: cylindrical confining pressure σ₃
        │    │
        └────┘  ← Bottom cap: fully fixed

  Cylinder: radius R=0.05 m, height H=0.1 m
  Particle spacing: δ ≈ 0.005 m (regular or randomized grid)
  Horizon: δ_h = 0.005 × 4.000015 m
  Confining pressure: σ₃ = 300 kPa
  Axial velocity: v_z = -0.0005 m/s
```

The lateral surface is loaded with `Apply_Cylindrical_Load` — the engine automatically computes the radial inward direction for each node on the cylinder surface.

---

## Script walkthrough

```python
import math
import PyGeoPeriX

# ─── Geometry ─────────────────────────────────────────────────────────────────
R       = 0.05      # cylinder radius (m)
H       = 0.10      # cylinder height (m)
spacing = 0.005     # particle spacing (m)
horizon = spacing * 4.000015

# ─── Model ────────────────────────────────────────────────────────────────────
model = PyGeoPeriX.Model(dim=3, num_nodes=80000, model_name="Triaxial_3D")

# ─── Add nodes on a regular Cartesian grid, keeping only those inside the cylinder
node_id = 0
top_ids    = []
bottom_ids = []
lateral_ids = []

nx = int(2 * R / spacing) + 1
ny = int(2 * R / spacing) + 1
nz = int(H / spacing) + 1

for ix in range(nx):
    for iy in range(ny):
        for iz in range(nz):
            x = -R + ix * spacing
            y = -R + iy * spacing
            z =       iz * spacing
            r = math.sqrt(x**2 + y**2)
            if r > R:
                continue   # outside the cylinder
            node_id += 1
            model.Add_Node(node_id, [x, y, z], "Soil")

            # Classify by position
            if iz == 0:
                bottom_ids.append(node_id)
            elif iz == nz - 1:
                top_ids.append(node_id)
            if abs(r - R) < spacing * 0.6:
                lateral_ids.append(node_id)

print(f"Nodes inside cylinder: {node_id}")

model.Add_Node_Group("Bottom", bottom_ids)
model.Add_Node_Group("Top",    top_ids)
model.Add_Node_Group("Lateral", lateral_ids)

# ─── Discretization ───────────────────────────────────────────────────────────
model.Set_Node_Spacing("All", spacing)
model.Set_Horizon("All", horizon)

# ─── Fictitious nodes ──────────────────────────────────────────────────────────
# The internal point [0, 0, H/2] is at the axis of the cylinder, mid-height.
model.Generate_Ficticious_Nodes("Top",    [0.0, 0.0, H / 4], 4, "Soil")
model.Generate_Ficticious_Nodes("Bottom", [0.0, 0.0, H * 3/4], 4, "Soil")

# ─── Compute volumes and neighbours ───────────────────────────────────────────
model.Compute_Volume("All")
model.Compute_Neighbours("All")

# ─── Materials ────────────────────────────────────────────────────────────────
model.Create_Material(1, "LinearElasticMaterial", {
    "density":        2000.0,
    "youngs_modulus": 100e6,
    "poissons_ratio": 0.3,
})

model.Create_Material(3, "DruckerPragerMaterial", {
    "density":           1800.0,
    "youngs_modulus":    50e6,
    "poissons_ratio":    0.3,
    "cohesion":          15e3,
    "friction_angle":    math.radians(30.0),
    "dilation_angle":    math.radians(5.0),
    "dp_hardening_mode": 0,
    "hardening_modulus": -5e4,
})

model.Set_Material("All",              3)
model.Set_Material("Soil",             3)
model.Set_Material("Top_Ficticous",    1)
model.Set_Material("Bottom_Ficticous", 1)

# ─── Boundary conditions ──────────────────────────────────────────────────────
model.Create_Constraint_Timer(1, 0.0, 1.0)

# Fix base: zero displacement in all three DOFs
model.Apply_Fixity("Bottom",           [0, 1, 2], [0.0, 0.0, 0.0], True,  1)
model.Apply_Fixity("Bottom_Ficticous", [0, 1, 2], [0.0, 0.0, 0.0], True,  1)

# Prescribe downward velocity on the top cap
model.Apply_Fixity("Top",           [2], [-0.0005], False, 1)
model.Apply_Fixity("Top_Ficticous", [2], [-0.0005], False, 1)

# Confining pressure on the lateral surface
# pressure > 0 = inward (confining); axis = vertical (z)
model.Apply_Cylindrical_Load(
    "Lateral",
    center=[0.0, 0.0, 0.0],
    axis=[0.0, 0.0, 1.0],
    pressure=300e3,
    is_const=True,
    constraint_timer_tag=1,
)

# ─── Run ──────────────────────────────────────────────────────────────────────
print("Running triaxial simulation …")
model.Run_Analysis(
    start_time=0.0,
    end_time=1.0,
    num_steps=5000,
    stage_name="Triaxial_300kPa",
    output_step_freq=10,     # write every 10 steps to manage file size
)
print("Done.")
```

---

## Running the example

```bash
bash examples/9_triaxial_asymmetric_cylinder/run.sh
# or
python examples/9_triaxial_asymmetric_cylinder/trial_3d.py
```

---

## Interpreting triaxial results

### Stress path in p–q space

The standard triaxial stress path should be a straight vertical line (increasing q at constant p) until the yield surface is reached, then follow the yield surface to failure.

```python
import h5py
import numpy as np
import matplotlib.pyplot as plt

with h5py.File("Triaxial_300kPa.h5", "r") as f:
    node_type = f["/Model/Nodes/Type"][:]
    stress    = f["/Model/Analysis/stress"][:]    # (N, 9, steps)
    time      = f["/Model/Analysis/time"][:]

real = node_type == 1
s    = stress[real]    # (N_real, 9, steps)

# Mean stress p = (σ_xx + σ_yy + σ_zz) / 3
p = (s[:, 0, :] + s[:, 4, :] + s[:, 8, :]) / 3.0

# Deviatoric stress and q
sigma_m = p[:, np.newaxis, :]   # broadcast for subtraction
s_dev   = s.copy()
for k in [0, 4, 8]:
    s_dev[:, k, :] -= sigma_m[:, 0, :]

J2 = 0.5 * np.sum(s_dev**2, axis=1)   # (N_real, steps)
q  = np.sqrt(3.0 * J2)

avg_p = np.mean(p, axis=0)   # (steps,)
avg_q = np.mean(q, axis=0)   # (steps,)

plt.figure()
plt.plot(avg_p / 1e3, avg_q / 1e3)
plt.xlabel("Mean stress p (kPa)")
plt.ylabel("von Mises stress q (kPa)")
plt.title("Stress path — Triaxial test (σ₃ = 300 kPa)")
plt.grid(True)
plt.savefig("stress_path.png", dpi=150)
```

### Expected values

For a Drucker-Prager material with φ = 30°, c = 15 kPa, σ₃ = 300 kPa:

```text
Initial p₀ = σ₃ = 300 kPa
At failure:
  Mohr-Coulomb: σ₁/σ₃ = (1 + sin φ)/(1 - sin φ) = 3.0  →  σ₁ = 900 kPa
  q_peak ≈ σ₁ - σ₃ = 600 kPa (plus cohesion contribution)
  p_peak = (σ₁ + 2σ₃)/3 ≈ 500 kPa
```

If `hardening_modulus` is negative, the peak is followed by softening as cohesion reduces toward zero.

---

## Comparing confining pressures

Run the simulation three times with different confining pressures (100, 300, 500 kPa) and plot the resulting failure envelope in p–q space. The slope of the failure line gives the Drucker-Prager η parameter, which is related to the friction angle by:

```
η = 6 sin(φ) / (3 - sin(φ))   [outer cone, circumscribed]
η = 6 sin(φ) / (3 + sin(φ))   [inner cone, inscribed]
```

For φ = 30°: η_outer ≈ 1.20, η_inner ≈ 0.69.

---

## Randomized particle distribution

The `10_triaxial_trial_randomness` example adds small random perturbations to the regular grid positions. This breaks the symmetry of the regular grid and triggers more realistic, non-symmetric shear bands:

```python
import random
random.seed(42)

for ix in range(nx):
    for iy in range(ny):
        for iz in range(nz):
            x_nom = -R + ix * spacing
            y_nom = -R + iy * spacing
            z_nom =       iz * spacing
            # Add random jitter of ±20% of spacing
            x = x_nom + random.uniform(-0.2, 0.2) * spacing
            y = y_nom + random.uniform(-0.2, 0.2) * spacing
            z = z_nom + random.uniform(-0.2, 0.2) * spacing
            if math.sqrt(x**2 + y**2) > R:
                continue
            node_id += 1
            model.Add_Node(node_id, [x, y, z], "Soil")
```

The randomized distribution produces more diffuse failure zones that better match experimental observations in loose soils.
