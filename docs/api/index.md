# Python API Reference

The `PyGeoPeriX` module exposes the full GeoPeriX simulation API to Python. It is built as a C++ extension module using [pybind11](https://pybind11.readthedocs.io/) and provides three classes and two module-level accessor functions.

```python
import PyGeoPeriX
```

---

## Classes

```{toctree}
:maxdepth: 1

model
node
material
```

## Module-level functions

```{toctree}
:maxdepth: 1

functions
```

---

## Class overview

| Class / function | Purpose |
|-----------------|---------|
| {doc}`Model <model>` | Define geometry, materials, BCs, and run the simulation |
| {doc}`Node <node>` | Read-only view of a material point's current state |
| {doc}`Material <material>` | Constitutive model interface |
| {doc}`Get_Node(id) <functions>` | Retrieve a live `Node` reference from C++ memory |
| {doc}`Get_Material(tag) <functions>` | Retrieve a live `Material` reference from C++ memory |

---

## Required call order

The `Model` API must be called in a specific order. Calling methods out of sequence produces incorrect results or runtime errors. See {doc}`../guides/setup_order` for the full explanation.

```text
Model()
  └─ Add_Node / Add_Node_Group
       └─ Set_Node_Spacing / Set_Horizon
            └─ Generate_Ficticious_Nodes   ← MUST precede Compute_*
                 └─ Compute_Volume
                      └─ Compute_Neighbours
                           └─ Create_Material / Set_Material
                                └─ Create_Constraint_Timer
                                     └─ Apply_Fixity / Apply_Force / Apply_Surface_Load
                                          └─ Run_Analysis
```
