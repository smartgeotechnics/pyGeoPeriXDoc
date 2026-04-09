# 2D Compression Test

**Directory:** `examples/5_trial_2d/`
**Script:** `trial_2d.py`

This is the primary 2D benchmark. A 1 m × 2 m rectangular soil sample is compressed axially from the top while the base is held fixed. A Drucker-Prager constitutive model with cohesion softening captures the progressive failure of the soil.

---

## Physical setup

```
 x ∈ [0, 1.0 m]    y ∈ [0, 2.0 m]
 particle spacing: δx = δy = 0.05 m
 horizon: δ = 4.000015 × 0.05 = 0.2000008 m

 ←1.0 m→
 ┌──────────┐  ← Top:    velocity = [0, -0.01] m/s   (downward)
 │          │
 │  soil    │  2.0 m      Drucker-Prager material
 │  nodes   │
 │          │
 └──────────┘  ← Bottom: fully fixed [0, 0]
```

The top and bottom boundaries each have 4 layers of fictitious nodes generated outside the domain to enforce the displacement boundary conditions via the nonlocal formulation.

---

## Expected behaviour

1. **Elastic loading** (early steps): axial stress increases linearly; no plastic strain develops.
2. **Yield initiation**: the Drucker-Prager yield surface is reached at the corners (stress concentration sites).
3. **Strain localisation**: a diagonal shear band forms as cohesion softens with accumulated plastic strain. The shear band angle is controlled by the friction and dilation angles.
4. **Post-peak softening**: axial load drops as the shear band widens and cohesion reduces toward its residual value.

---

## Complete annotated script

```python
import os
import sys
import math
import PyGeoPeriX

# ─── 1. Geometry ──────────────────────────────────────────────────────────────
length_x = 1.0
length_y = 2.0
del_x    = 0.05
del_y    = 0.05

nx = int(length_x / del_x)   # 20 intervals → 21 columns of nodes
ny = int(length_y / del_y)   # 40 intervals → 41 rows of nodes

# ─── 2. Model creation ────────────────────────────────────────────────────────
# num_nodes is an upper bound; actual count = (nx+1)*(ny+1) = 861
model = PyGeoPeriX.Model(dim=2, num_nodes=1200, model_name="Py_Compression_Test")

# ─── 3. Add nodes ─────────────────────────────────────────────────────────────
# Column-major ordering: outer loop over x (i), inner over y (j).
# Node 1 is at (0, 0); node 2 at (0, del_y); node ny+1 at (0, length_y); etc.
node_id = 0
for i in range(nx + 1):
    for j in range(ny + 1):
        node_id += 1
        model.Add_Node(node_id, [i * del_x, j * del_y], "Soil")

print(f"Nodes created: {node_id}")   # should be 861

# ─── 4. Boundary groups ────────────────────────────────────────────────────────
# With column-major ordering:
#   Bottom row (j=0): node IDs 1, ny+2, 2*(ny+1)+1, …
#   Top row    (j=ny): node IDs ny+1, 2*(ny+1), …
Bottom, Top, Left, Right = [], [], [], []

for i in range(nx + 1):
    Bottom.append(i * (ny + 1) + 1)
    Top.append((i + 1) * (ny + 1))

for j in range(ny + 1):
    Left.append(j + 1)
    Right.append(Bottom[-1] + j)   # rightmost column starts at Bottom[-1]

model.Add_Node_Group("Bottom", Bottom)
model.Add_Node_Group("Top",    Top)
model.Add_Node_Group("Left",   Left)
model.Add_Node_Group("Right",  Right)

# ─── 5. Discretization ────────────────────────────────────────────────────────
model.Set_Node_Spacing("All", del_x)
model.Set_Horizon("All", del_x * 4.000015)

# ─── 6. Fictitious nodes ──────────────────────────────────────────────────────
# MUST precede Compute_Volume and Compute_Neighbours.
# The internal point must be strictly inside the domain.
# m_factor=4 generates 4 layers of ghost nodes outside each surface.
model.Generate_Ficticious_Nodes("Top",    [0.0, 0.5], 4, "Soil")
model.Generate_Ficticious_Nodes("Bottom", [0.0, 1.5], 4, "Soil")

# ─── 7. Volumes and neighbours ────────────────────────────────────────────────
model.Compute_Volume("All")
model.Compute_Neighbours("All")

# ─── 8. Boundary conditions ───────────────────────────────────────────────────
model.Create_Constraint_Timer(1, 0.0, 2.0)

# Base: fixed in both DOFs
model.Apply_Fixity("Bottom",           [0, 1], [0.0, 0.0],   True,  1, False)
model.Apply_Fixity("Bottom_Ficticous", [0, 1], [0.0, 0.0],   True,  1, False)

# Top: constant downward velocity of -0.01 m/s
model.Apply_Fixity("Top",           [0, 1], [0.0, -0.01], False, 1, False)
model.Apply_Fixity("Top_Ficticous", [0, 1], [0.0, -0.01], False, 1, False)

# ─── 9. Materials ──────────────────────────────────────────────────────────────
# Material 1: elastic — assigned to fictitious nodes so they do not yield
model.Create_Material(1, "LinearElasticMaterial", {
    "density":        2235.0,
    "youngs_modulus": 50e6,
    "poissons_ratio": 0.3,
})

# Material 3: Drucker-Prager with cohesion softening (dp_hardening_mode=0)
# friction_angle and dilation_angle are in RADIANS
model.Create_Material(3, "DruckerPragerMaterial", {
    "density":           2235.0,
    "youngs_modulus":    50e6,
    "poissons_ratio":    0.3,
    "cohesion":          100e3,
    "friction_angle":    math.radians(30.0),
    "dilation_angle":    math.radians(10.0),
    "dp_hardening_mode": 0,
    "hardening_modulus": -1.5e6,     # softening: cohesion drops with κ
})

# Assignment order matters: later calls overwrite earlier ones for the same nodes
model.Set_Material("All",              3)
model.Set_Material("Soil",             3)
model.Set_Material("Top_Ficticous",    1)   # elastic for fictitious nodes
model.Set_Material("Bottom_Ficticous", 1)

# ─── 10. Run ──────────────────────────────────────────────────────────────────
print("Starting analysis …")
model.Run_Analysis(
    start_time=0.0,
    end_time=0.018,
    num_steps=1000,
    stage_name="Py_DP_test_1",
    output_step_freq=0,
)
print("Done. Output written to Py_DP_test_1.h5")

# ─── 11. Post-analysis inspection ─────────────────────────────────────────────
node = PyGeoPeriX.Get_Node(100)
pos  = node.Get_Position()
s    = node.Get_Stress()
eps  = node.Get_Eq_Plastic_Strain()
print(f"Node 100  pos=({pos[0]:.4f}, {pos[1]:.4f})")
print(f"  Stress Sxx={s[0]:.2f} Pa  Syy={s[4]:.2f} Pa")
print(f"  Eq. plastic strain = {eps:.4e}")

mat = PyGeoPeriX.Get_Material(3)
print(f"Material 3: {mat.Get_Name()}, density={mat.Get_Density()} kg/m³")
```

---

## Running the example

```bash
# Using the provided run script (handles Python path and output directory)
bash examples/5_trial_2d/run.sh

# Or run directly
python examples/5_trial_2d/trial_2d.py
```

Output: `Py_DP_test_1.h5` in the working directory (or `examples/5_trial_2d/output/` if the run script sets up the output directory).

---

## Post-processing

Convert the HDF5 to Excel:

```bash
python tools/gpx_reader/Post_Processing.py \
    examples/5_trial_2d/output/Py_DP_test_1.h5 \
    examples/5_trial_2d/output/Py_DP_test_1.xlsx \
    --exclusion-distance 0.06
```

The Excel workbook will contain:
- Average axial stress σ_yy and axial strain ε_yy vs time → stress-strain curve
- Volumetric strain ε_vol = ε_xx + ε_yy vs axial strain ε_yy → volume change curve
- Full stress tensor history for interior nodes

---

## Interpreting results

| Quantity | Expected range | What it tells you |
|---------|---------------|------------------|
| Peak σ_yy | ~200–400 kPa (depends on c, φ) | Compressive strength of the sample |
| Axial strain at peak | 0.5–2% | Brittleness indicator |
| Shear band angle θ | ~45° + φ/2 = 60° | Consistent with Mohr-Coulomb theory |
| Post-peak σ_yy | Residual when c → 0 | Frictional residual strength |

If the simulation diverges (displacements become very large), reduce `end_time` or increase `num_steps` to use a smaller time step.

---

## Variations

- Replace `DruckerPragerMaterial` with `LinearElasticMaterial` (material tag 1) and verify that the stress-strain response is linear up to the end of the analysis.
- Increase `hardening_modulus` toward zero to see the transition from softening to perfectly plastic behaviour.
- Increase `del_x` to 0.1 m to run faster with fewer nodes — the shear band will be coarser but still visible.
- Add `model.Add_Rotational_Damping(0.02)` before `Run_Analysis` to suppress high-frequency oscillations if the stress-strain curve is noisy.
