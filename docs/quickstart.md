# Quick Start

This guide walks through a complete 2D uniaxial compression test — the simplest meaningful simulation in GeoPeriX. By the end you will have a working script, an HDF5 output file, and a basic understanding of the setup sequence that all simulations follow.

---

## What we are modelling

A rectangular soil sample: 1 m wide, 2 m tall, discretized with a 0.05 m particle spacing. The bottom boundary is fully fixed. A downward velocity is applied to the top boundary. The soil is modelled as a Drucker-Prager elastoplastic material.

```
 ← 1.0 m →
 ┌─────────┐  ← top: prescribed downward velocity
 │  soil   │
 │  nodes  │  2.0 m tall
 │         │
 └─────────┘  ← bottom: fully fixed
```

---

## Complete script

Save this as `compression_2d.py` and run it with `python compression_2d.py`.

```python
import math
import PyGeoPeriX

# ── 1. Geometry parameters ────────────────────────────────────────────────────
length_x = 1.0      # m
length_y = 2.0      # m
del_x    = 0.05     # particle spacing (m)
del_y    = 0.05

nx = int(length_x / del_x)   # number of intervals in x → 20
ny = int(length_y / del_y)   # number of intervals in y → 40

# ── 2. Create the model ───────────────────────────────────────────────────────
# dim=2 for a 2-D simulation; num_nodes is an upper-bound reservation.
model = PyGeoPeriX.Model(dim=2, num_nodes=5000, model_name="Compression_2D")

# ── 3. Add nodes ─────────────────────────────────────────────────────────────
# Nodes are numbered 1 … (nx+1)*(ny+1). The inner loop is over y so that
# consecutive node IDs share the same x-column — this is the convention used
# in the boundary-group index arithmetic below.
node_id = 0
for i in range(nx + 1):
    for j in range(ny + 1):
        node_id += 1
        model.Add_Node(node_id, [i * del_x, j * del_y], "Soil")

print(f"Nodes created: {node_id}")

# ── 4. Define boundary groups ─────────────────────────────────────────────────
# Bottom row: j=0 → node IDs 1, ny+2, 2*(ny+1)+1, …
# Top row:    j=ny → node IDs ny+1, 2*(ny+1), …
bottom_ids = []
top_ids    = []
left_ids   = []
right_ids  = []

for i in range(nx + 1):
    bottom_ids.append(i * (ny + 1) + 1)
    top_ids.append((i + 1) * (ny + 1))

for j in range(ny + 1):
    left_ids.append(j + 1)
    right_ids.append(bottom_ids[-1] + j)

model.Add_Node_Group("Bottom", bottom_ids)
model.Add_Node_Group("Top",    top_ids)
model.Add_Node_Group("Left",   left_ids)
model.Add_Node_Group("Right",  right_ids)

# ── 5. Set discretization parameters ─────────────────────────────────────────
# The horizon is typically 3–4× the particle spacing. The small fractional
# offset (4.000015) ensures that nodes exactly on the horizon boundary are
# included consistently in the neighbour search.
model.Set_Node_Spacing("All", del_x)
model.Set_Horizon("All", del_x * 4.000015)

# ── 6. Generate fictitious nodes ──────────────────────────────────────────────
# THIS MUST HAPPEN BEFORE Compute_Volume and Compute_Neighbours.
# Fictitious nodes are mirror copies of real boundary nodes used to enforce
# boundary conditions in the nonlocal formulation. The second argument is a
# point strictly inside the domain — it tells the engine which side is
# "inside". The third argument (m_factor=4) controls how many layers of
# fictitious nodes are generated.
model.Generate_Ficticious_Nodes("Top",    [0.0, 0.5], 4, "Soil")
model.Generate_Ficticious_Nodes("Bottom", [0.0, 1.5], 4, "Soil")

# ── 7. Compute volumes and neighbours ────────────────────────────────────────
model.Compute_Volume("All")
model.Compute_Neighbours("All")

# ── 8. Create materials ───────────────────────────────────────────────────────
# Material 1: linear elastic — used for the fictitious boundary nodes so they
# transmit forces without yielding.
model.Create_Material(
    1, "LinearElasticMaterial",
    {
        "density":        2235.0,
        "youngs_modulus": 50e6,
        "poissons_ratio": 0.3,
    }
)

# Material 3: Drucker-Prager — the actual soil model.
# dp_hardening_mode=0 means cohesion softening: c(κ) = c₀ + H·κ.
# A negative hardening_modulus produces softening.
model.Create_Material(
    3, "DruckerPragerMaterial",
    {
        "density":           2235.0,
        "youngs_modulus":    50e6,
        "poissons_ratio":    0.3,
        "cohesion":          100e3,
        "friction_angle":    math.radians(30.0),   # must be in radians
        "dilation_angle":    math.radians(10.0),   # must be in radians
        "dp_hardening_mode": 0,
        "hardening_modulus": -1.5e6,               # negative → softening
    }
)

# Assign materials: real soil nodes get material 3; fictitious boundary
# nodes get material 1 (elastic) so they do not yield.
model.Set_Material("All",              3)
model.Set_Material("Soil",             3)
model.Set_Material("Top_Ficticous",    1)
model.Set_Material("Bottom_Ficticous", 1)

# ── 9. Boundary conditions ────────────────────────────────────────────────────
# A constraint timer defines the time window over which a BC is active.
# Timer tag=1 is active from t=0 to t=2.0 s.
model.Create_Constraint_Timer(1, start_time=0.0, end_time=2.0)

# Fix the bottom surface: both DOFs (0=x, 1=y) are set to zero.
# is_const=True → displacement is pinned, not a velocity ramp.
model.Apply_Fixity("Bottom",           [0, 1], [0.0, 0.0], True,  1, False)
model.Apply_Fixity("Bottom_Ficticous", [0, 1], [0.0, 0.0], True,  1, False)

# Drive the top surface downward at a constant velocity of -0.01 m/s.
# is_const=False → velocity BC (applied every step, not just at t=0).
model.Apply_Fixity("Top",           [0, 1], [0.0, -0.01], False, 1, False)
model.Apply_Fixity("Top_Ficticous", [0, 1], [0.0, -0.01], False, 1, False)

# ── 10. Run the analysis ──────────────────────────────────────────────────────
# Simulate from t=0 to t=0.018 s in 1000 steps.
# output_step_freq=0 writes output at every step.
print("Starting analysis …")
model.Run_Analysis(
    start_time=0.0,
    end_time=0.018,
    num_steps=1000,
    stage_name="Compression_Stage",
    output_step_freq=0,
)
print("Done. Results written to Compression_Stage.h5")
```

---

## What happens during the run

1. The engine integrates the peridynamic equations of motion using an explicit time-stepping scheme.
2. At each output step the nodal displacement, velocity, force, stress, strain, and plastic strain fields are written to the HDF5 file.
3. Bonds between nodes that exceed the damage threshold are progressively broken, reducing the effective stiffness in the damage zone.

---

## Inspecting results at runtime

You can query any node's state directly from Python after `Run_Analysis` returns:

```python
node = PyGeoPeriX.Get_Node(100)
print("Position:", node.Get_Position())
print("Displacement:", node.Get_Disp())
print("Stress tensor:", node.Get_Stress())
print("Equivalent plastic strain:", node.Get_Eq_Plastic_Strain())

mat = PyGeoPeriX.Get_Material(3)
print("Material name:", mat.Get_Name())
print("Density:", mat.Get_Density())
```

---

## Post-processing the HDF5 output

Convert the output file to an Excel workbook with averaged stress, strain, and displacement histories:

```bash
python tools/gpx_reader/Post_Processing.py \
    Compression_Stage.h5 \
    Compression_Stage.xlsx \
    --exclusion-distance 0.06
```

Load the file in ParaView for 3D visualization:

1. Open ParaView → **Tools → Manage Plugins → Load New**
2. Select `tools/paraview_plugin/pvGeoPeriX.py`
3. Open `Compression_Stage.h5` — all time steps and fields are available immediately.

---

## Next steps

- See {doc}`guides/setup_order` for a full explanation of why the call sequence matters.
- See {doc}`guides/materials` for parameter reference for all material models.
- See {doc}`guides/boundary_conditions` for all four constraint types with examples.
- See {doc}`examples/compression_2d` for an annotated version of this script with expected output.
