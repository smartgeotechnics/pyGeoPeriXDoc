# User Guides

These guides explain the *why* behind GeoPeriX's design — the peridynamic formulation enforces constraints on how you set up a simulation, and understanding those constraints makes it much easier to build correct models and debug problems when they arise.

```{toctree}
:maxdepth: 1

setup_order
boundary_conditions
materials
postprocessing
```

---

## Guide overview

| Guide | What it covers |
|-------|---------------|
| {doc}`setup_order` | The mandatory call sequence and what breaks if you deviate from it |
| {doc}`boundary_conditions` | All four constraint types with complete examples |
| {doc}`materials` | Property reference for all three material models and calibration tips |
| {doc}`postprocessing` | Reading HDF5 output, Excel export, ParaView plugin, and the report generator |
