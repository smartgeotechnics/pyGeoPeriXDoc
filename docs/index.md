---
myst:
  html_meta:
    "description": "GeoPeriX — a high-performance peridynamics engine for geomechanics with Python bindings"
    "keywords": "peridynamics, geomechanics, C++, Python, fracture, Drucker-Prager"
---

# GeoPeriX Documentation

**GeoPeriX** is a high-performance computational framework for geomechanics research and engineering. It implements the *peridynamic* theory of nonlocal mechanics — replacing classical partial differential equations with integral equations — making it naturally suited to problems that involve fracture, damage, and progressive failure without the need for remeshing.

The core engine is written in optimized C++17. Full simulation control is available from Python through the `PyGeoPeriX` module, which is built with [pybind11](https://pybind11.readthedocs.io/).

---

## What GeoPeriX can do

- Simulate spontaneous crack initiation and propagation in 2D and 3D
- Model progressive damage and material softening in geomaterials
- Handle multiple interacting fractures without mesh updates
- Apply realistic constitutive models: linear elastic, kinematic hardening, and Drucker-Prager plasticity
- Output rich field data (displacement, stress, strain, bond damage, plastic strain) at every time step to HDF5
- Post-process results directly in Python or load them into ParaView through the built-in plugin

---

## Getting started

```{toctree}
:maxdepth: 1
:caption: Getting Started

installation
quickstart
```

```{toctree}
:maxdepth: 2
:caption: User Guides

guides/index
```

```{toctree}
:maxdepth: 2
:caption: Python API Reference

api/index
```

```{toctree}
:maxdepth: 2
:caption: Examples

examples/index
```

---

## At a glance

| Feature | Details |
|---------|---------|
| Language | C++17 engine, Python 3.9+ bindings |
| Theory | Peridynamics (nonlocal continuum mechanics) |
| Dimensions | 2D and 3D |
| Material models | Linear elastic, Kinematic hardening, Drucker-Prager |
| Output format | HDF5 (chunked, time-series) |
| Visualization | ParaView plugin, Excel exporter |
| License | Apache 2.0 |
| Version | {{ version }} |
