# Post-processing

GeoPeriX writes simulation results to HDF5 files. Three complementary approaches are available for analysing these files:

1. **Direct Python access** — query node state in-memory via `PyGeoPeriX.Get_Node()` immediately after `Run_Analysis`
2. **`tools/gpx_reader/Post_Processing.py`** — convert the HDF5 file to a formatted Excel workbook with averaged stress/strain histories and stress invariants
3. **ParaView plugin** — load the HDF5 file for interactive 3-D visualization with full temporal playback

---

## HDF5 output schema

Every `Run_Analysis` call writes one file named `<stage_name>.h5` in the working directory. The file follows this group/dataset layout:

### Static node data (`/Model/Nodes/`)

These datasets are written once at the start of the simulation and do not change.

| Dataset | Shape | Description |
|---------|-------|-------------|
| `/Model/Nodes/Id` | `[N]` | Node IDs (integer) |
| `/Model/Nodes/Position` | `[N, dim]` | Reference coordinates (m) |
| `/Model/Nodes/Material` | `[N]` | Material tag per node (integer) |
| `/Model/Nodes/Horizon` | `[N]` | Horizon radius per node (m) |
| `/Model/Nodes/Type` | `[N]` | Node type: `1`=real, `0`=fictitious |

### Time-series field data (`/Model/Analysis/`)

These datasets grow as the simulation progresses. The third dimension `steps` is the number of output steps written (determined by `output_step_freq` in `Run_Analysis`).

| Dataset | Shape | Description |
|---------|-------|-------------|
| `/Model/Analysis/time` | `[steps]` | Simulation time for each output step (s) |
| `/Model/Analysis/displacement` | `[N, dim, steps]` | Nodal displacement (m) |
| `/Model/Analysis/velocity` | `[N, dim, steps]` | Nodal velocity (m/s) |
| `/Model/Analysis/force` | `[N, dim, steps]` | Nodal internal force (N) |
| `/Model/Analysis/stress` | `[N, 9, steps]` | Cauchy stress tensor (Pa), flat row-major |
| `/Model/Analysis/strain` | `[N, 9, steps]` | Total strain tensor, flat row-major |
| `/Model/Analysis/volume` | `[N, 1, steps]` | Nodal volume (m² or m³) |
| `/Model/Analysis/plastic_strain` | `[N, 9, steps]` | Plastic strain tensor |
| `/Model/Analysis/acc_plastic_strain_mag` | `[N, 1, steps]` | Accumulated plastic strain magnitude |

The stress/strain component ordering is row-major 3×3:

```
index: 0   1   2   3   4   5   6   7   8
       xx  xy  xz  yx  yy  yz  zx  zy  zz
```

In 2-D analyses, out-of-plane components are zero (or represent plane-strain out-of-plane stress).

---

## Reading HDF5 from Python

### Using h5py directly

```python
import h5py
import numpy as np

file_path = "My_Stage.h5"

with h5py.File(file_path, "r") as f:
    # Static data
    ids       = f["/Model/Nodes/Id"][:]          # (N,)
    positions = f["/Model/Nodes/Position"][:]    # (N, dim)
    node_type = f["/Model/Nodes/Type"][:]        # (N,)  1=real

    # Time axis
    time = f["/Model/Analysis/time"][:]          # (steps,)

    # Field data at all steps
    disp   = f["/Model/Analysis/displacement"][:] # (N, dim, steps)
    stress = f["/Model/Analysis/stress"][:]       # (N, 9, steps)
    strain = f["/Model/Analysis/strain"][:]       # (N, 9, steps)

# Filter to real nodes only
real_mask = node_type == 1
real_disp = disp[real_mask]      # (N_real, dim, steps)

# Average vertical displacement over all real nodes vs time
avg_uy = np.mean(real_disp[:, 1, :], axis=0)   # (steps,)

# Mean stress p and deviatoric stress q
sigma = stress[real_mask]                       # (N_real, 9, steps)
# p = (s_xx + s_yy + s_zz) / 3
p = (sigma[:, 0, :] + sigma[:, 4, :] + sigma[:, 8, :]) / 3.0  # (N_real, steps)
avg_p = np.mean(p, axis=0)                     # (steps,)

print(f"Number of output steps: {len(time)}")
print(f"Final mean stress: {avg_p[-1]:.2f} Pa")
```

### Using the `GeoPeriXReader` class

The `tools/gpx_reader/Post_Processing.py` module provides a convenience class:

```python
import sys
sys.path.insert(0, "tools/gpx_reader")

from Post_Processing import GeoPeriXReader

reader = GeoPeriXReader("My_Stage.h5")
print(f"Nodes: {reader.num_nodes}, Dim: {reader.dim}, Steps: {reader.num_steps}")

time       = reader.get_time()              # (steps,)
positions  = reader.get_all_positions()     # (N, dim)
node_types = reader.get_all_node_types()    # (N,)  1=real, 0=fictitious
disp       = reader.get_all_displacement()  # (N, dim, steps)
stress     = reader.get_all_stress()        # (N, 9, steps)
strain     = reader.get_all_strain()        # (N, 9, steps)
```

---

## Live node access via `PyGeoPeriX.Get_Node()`

After `Run_Analysis` returns, all node states are still in C++ memory. You can query them directly without reading the HDF5 file:

```python
import PyGeoPeriX

# ... (model setup and Run_Analysis) ...

# Query a specific node
node = PyGeoPeriX.Get_Node(100)
print("Position:", node.Get_Position())
print("Displacement:", node.Get_Disp())
print("Stress:", node.Get_Stress())
print("Eq. plastic strain:", node.Get_Eq_Plastic_Strain())
print("Bond damage:", node.Get_Bond_Damage())

# Find the most-damaged node (brute-force loop)
max_eps_p = 0.0
max_node  = -1
for nid in range(1, total_nodes + 1):
    try:
        n = PyGeoPeriX.Get_Node(nid)
        if n.Get_Type() == 1:
            eps_p = n.Get_Eq_Plastic_Strain()
            if eps_p > max_eps_p:
                max_eps_p = eps_p
                max_node  = nid
    except RuntimeError:
        pass

print(f"Most damaged node: {max_node}  eps_p^eq = {max_eps_p:.4e}")
```

This approach is most useful for quick checks during script development. For systematic analysis of large datasets, use the HDF5 file and numpy/pandas.

---

## Excel export with `Post_Processing.py`

The script `tools/gpx_reader/Post_Processing.py` converts an HDF5 output file to a formatted Excel workbook with:

- A **Summary** sheet (node counts, simulation metadata)
- Averaged displacement, velocity, and acceleration vs time for all real nodes
- Averaged displacement, velocity, and acceleration for interior (centre) real nodes, excluding nodes within `--exclusion-distance` of the boundary
- Stress and strain sheets with full tensor components, mean stress p, deviatoric tensor, and von Mises stress q
- Volumetric strain vs axial strain sheets
- An optional single-node detail sheet (`--node-id`)

### Command-line usage

```bash
python tools/gpx_reader/Post_Processing.py \
    output/My_Stage.h5 \
    output/My_Stage.xlsx \
    --exclusion-distance 0.06 \
    --node-id 100
```

| Argument | Description |
|---------|-------------|
| `input_h5` | Path to the HDF5 output file |
| `output_xlsx` | Path for the Excel output (defaults to same name as input) |
| `--exclusion-distance` | Distance (m) from the real-node boundary to exclude when computing centre-node averages. Should be at least 1–2× the particle spacing |
| `--node-id` | Optional: write a detail sheet for this specific node |

### Batch processing

```bash
python process_example.py --output-dir examples/5_trial_2d/output/
```

This discovers all `.h5` files in the output directory and runs `Post_Processing.py` on each one.

---

## ParaView plugin

The plugin `tools/paraview_plugin/pvGeoPeriX.py` registers a custom HDF5 reader in ParaView that:

- Reads node positions from `/Model/Nodes/Position`
- Exposes displacement, velocity, force, stress, strain, plastic strain, bond damage, and volume as point data arrays at every time step
- Supports ParaView's built-in time animation

### Installation

1. Open ParaView (5.x or later)
2. Go to **Tools → Manage Plugins → Load New**
3. Navigate to `tools/paraview_plugin/pvGeoPeriX.py` and select it
4. Tick **Auto Load** if you want it available in future sessions

### Opening a file

1. **File → Open** — select your `.h5` file
2. ParaView detects the GeoPeriX reader and opens it
3. Click **Apply** in the Properties panel
4. Use the **Time** toolbar to step through the simulation

### Visualizing damage

Bond damage is stored as a per-node scalar (average bond damage fraction). To visualize:

1. In the Pipeline Browser, select your `.h5` source
2. In the Properties panel, choose `bond_damage_avg` in the **Point Arrays** list
3. Apply a color map (e.g., `Blue–Red Diverging`) with range 0–1

---

## HTML simulation report

The script `tools/gpx_reader/generate_report.py` parses a C++ model source file and generates an HTML parameter summary:

```bash
python tools/gpx_reader/generate_report.py examples/5_trial_2d/trial_2d.cpp
```

The output HTML table summarizes:
- Geometry parameters (domain size, particle spacing, horizon)
- Material properties for each material
- Boundary condition summary
- Analysis stage parameters (time range, step count)

This is useful for archiving simulation metadata alongside the HDF5 output files.
