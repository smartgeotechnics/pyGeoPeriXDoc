# Examples

The `examples/` directory in the repository contains 12 numbered benchmark problems, each with a complete Python script, a run script, and a post-processing script.

```{toctree}
:maxdepth: 1

compression_2d
triaxial_3d
```

---

## Example overview

| Number | Directory | Description |
|--------|-----------|-------------|
| 1 | `1_consolidation` | One-dimensional pore-pressure consolidation |
| 2 | `2_direct_shear_test` | Direct shear failure with fictitious boundary nodes |
| 3 | `3_plane_strain_triaxial` | Triaxial compression under plane-strain conditions |
| 4 | `4_plane_strain_triaxial_elastic_confinement` | Triaxial test with elastic lateral confinement |
| **5** | **`5_trial_2d`** | **Basic 2D compression benchmark** |
| 6 | `6_trial_2d_dp_model` | 2D compression with Drucker-Prager plasticity |
| 7 | `7_trial_3d` | 3D uniaxial compression |
| 8 | `8_trial_circular_2d` | Circular sample geometry |
| 9 | `9_triaxial_asymmetric_cylinder` | Asymmetric cylindrical sample |
| 10 | `10_triaxial_trial_randomness` | Randomized particle distribution |
| 11 | `11_triaxial_trial_smooth` | Smoothed boundary conditions |
| 12 | `12_triaxial_trial_star_grid` | Star-pattern nodal discretization |

---

## Running an example

Each example directory contains a `run.sh` script that builds (if necessary) and executes the simulation, then runs post-processing:

```bash
bash examples/5_trial_2d/run.sh
```

Output files are written to `examples/<N>_<name>/output/`.

To run only the Python version (no C++ compilation needed):

```bash
python examples/5_trial_2d/trial_2d.py
```

---

## Example directory layout

```
examples/<N>_<name>/
├── <name>.cpp        # C++ model definition (for compiled runs)
├── <name>.py         # Python equivalent using PyGeoPeriX
├── run.sh            # Build + run + post-process
├── process.py        # Post-process only (reads output/*.h5)
└── output/           # Generated .h5 and .xlsx files
```
