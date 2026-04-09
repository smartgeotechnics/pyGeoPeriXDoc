# Module-level functions

The `PyGeoPeriX` module exposes two functions at module level that provide direct access to objects stored in C++ memory. They do not require a reference to the `Model` instance — they reach into the global engine state.

---

## `PyGeoPeriX.Get_Node(id)` → `Node`

Retrieve a live reference to the `Node` object with the given ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | `int` | The node ID as assigned in `Add_Node`. Must be a valid ID in the current model |

Returns a {doc}`Node <node>` instance whose properties reflect the node's current state in C++ memory. The returned object is a view — it is not a copy. Querying it after calling `Run_Analysis` returns the final simulation state; querying it before returns the initial state.

```python
import PyGeoPeriX

# After model setup (and optionally Run_Analysis):
node = PyGeoPeriX.Get_Node(100)

print(f"Node ID:     {node.Get_Node_Id()}")
print(f"Position:    {node.Get_Position()}")
print(f"Stress (Syy):{node.Get_Stress()[4]:.2f} Pa")
print(f"Eq. pl. str: {node.Get_Eq_Plastic_Strain():.4e}")
```

**Common use cases**

- Inspecting the state of a specific node after `Run_Analysis` for debugging
- Building custom post-processing loops that iterate over a set of node IDs
- Comparing displacement at specific monitoring points across parametric studies

**Error behaviour**

If `id` is not a valid node ID in the current model, the engine raises a C++ exception that is propagated to Python as a `RuntimeError`.

---

## `PyGeoPeriX.Get_Material(tag)` → `Material`

Retrieve a live reference to the `Material` object with the given tag.

| Parameter | Type | Description |
|-----------|------|-------------|
| `tag` | `int` | The material tag as assigned in `Create_Material`. Must be a valid tag in the current model |

Returns a {doc}`Material <material>` instance. Like `Get_Node`, this is a view into C++ memory, not a copy.

```python
mat = PyGeoPeriX.Get_Material(3)

print(f"Material name: {mat.Get_Name()}")
print(f"Density:       {mat.Get_Density()} kg/m³")
```

**Error behaviour**

If `tag` does not correspond to a registered material, the engine raises a `RuntimeError`.

---

## Example: post-analysis inspection loop

```python
import PyGeoPeriX

# ... (full model setup and Run_Analysis) ...

# Find all nodes with equivalent plastic strain above a threshold
threshold = 1e-3
damaged_nodes = []

for nid in range(1, 2000):   # iterate over known node ID range
    try:
        node = PyGeoPeriX.Get_Node(nid)
    except RuntimeError:
        continue   # node ID does not exist (e.g., gap in numbering)

    if node.Get_Type() != 1:
        continue   # skip fictitious nodes

    eps_p = node.Get_Eq_Plastic_Strain()
    if eps_p > threshold:
        damaged_nodes.append((nid, node.Get_Position(), eps_p))

print(f"Nodes with ε_p > {threshold}: {len(damaged_nodes)}")
for nid, pos, eps_p in damaged_nodes[:5]:
    print(f"  Node {nid:5d}  pos={pos}  ε_p^eq={eps_p:.4e}")
```

---

## Example: calibrate material with `Compute_Stress`

```python
import PyGeoPeriX
import math

model = PyGeoPeriX.Model(dim=3, num_nodes=1, model_name="Calibration")
model.Create_Material(1, "DruckerPragerMaterial", {
    "density":           1800.0,
    "youngs_modulus":    50e6,
    "poissons_ratio":    0.3,
    "cohesion":          20e3,
    "friction_angle":    math.radians(30),
    "dilation_angle":    math.radians(10),
    "dp_hardening_mode": 0,
    "hardening_modulus": 0.0,
})

mat = PyGeoPeriX.Get_Material(1)

# Apply incremental strain and track stress path
strain = [0.0] * 9
eps_yy_list = []
sigma_yy_list = []

for step in range(100):
    inc = [0.0] * 9
    inc[4] = -5e-5   # compress in y
    stress = mat.Compute_Stress(strain, inc)
    for k in range(9):
        strain[k] += inc[k]
    eps_yy_list.append(strain[4])
    sigma_yy_list.append(stress[4])

import csv
with open("stress_path.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["eps_yy", "sigma_yy"])
    w.writerows(zip(eps_yy_list, sigma_yy_list))

print("Stress path written to stress_path.csv")
```
