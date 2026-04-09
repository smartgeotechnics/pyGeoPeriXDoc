# Node

The `Node` class is a read-only view of a single material point's state. You obtain a `Node` instance by calling the module-level function `PyGeoPeriX.Get_Node(id)` after the model has been set up (or after `Run_Analysis` has returned).

All state arrays (stress, strain, displacement, etc.) reflect the current state at the time of the call — they are live references into C++ memory, not snapshots.

```python
import PyGeoPeriX

node = PyGeoPeriX.Get_Node(42)
print(node.Get_Position())
print(node.Get_Stress())
```

---

## Identity and geometry

### `Get_Node_Id()` → `int`

Return the node's unique integer ID as assigned in `Add_Node`.

```python
nid = node.Get_Node_Id()   # e.g. 42
```

---

### `Get_Position()` → `list[float]`

Return the reference (initial) position of the node in metres.

| Dimension | Return value |
|-----------|-------------|
| 2-D | `[x, y]` |
| 3-D | `[x, y, z]` |

```python
pos = node.Get_Position()
print(f"x={pos[0]:.4f}, y={pos[1]:.4f}")
```

---

### `Get_Mirror_Position()` → `list[float]`

Return the mirrored (fictitious) position. For real nodes this is the reflected position used in the nonlocal boundary correction. For fictitious nodes this equals their actual position.

---

### `Get_Horizon()` → `float`

Return the peridynamic horizon radius `δ` (m) assigned to this node.

---

### `Get_Volume()` → `float`

Return the nodal volume (m² in 2-D, m³ in 3-D) as computed by `Compute_Volume`.

---

### `Get_Type()` → `int`

Return the node type:

| Value | Meaning |
|-------|---------|
| `1` | Real node — participates in the constitutive model and stores physical state |
| `2` | Fictitious boundary node — used to complete the nonlocal integral near boundaries |

```python
if node.Get_Type() == 1:
    print("Real node")
```

---

### `Get_Boundary_Node()` → `bool`

Return `True` if this node is on a boundary surface (i.e., it belongs to at least one user-defined boundary group).

---

### `Get_Material()` → `int`

Return the material tag assigned to this node via `Set_Material`.

---

## Kinematic state

### `Get_Disp()` → `list[float]`

Return the current displacement vector (m).

---

### `Get_Vel()` → `list[float]`

Return the current velocity vector (m/s).

---

### `Get_Acc()` → `list[float]`

Return the current acceleration vector (m/s²).

---

### `Get_Trial_Disp()` → `list[float]`

Return the trial displacement vector used in the predictor step of the time integrator.

---

### `Get_Mirror_Disp()` → `list[float]`

Return the displacement of the corresponding fictitious (mirror) node.

---

### `Get_Mirror_Vel()` → `list[float]`

Return the velocity of the corresponding fictitious (mirror) node.

---

## Force state

### `Get_Force()` → `list[float]`

Return the total internal force vector acting on this node (N).

---

### `Get_Ext_Force()` → `list[float]`

Return the external (applied) force vector (N). This includes contributions from `Apply_Force`, `Apply_Surface_Load`, and `Apply_Cylindrical_Load`.

---

## Stress and strain

All stress and strain arrays are stored as flat 9-component vectors representing the full 3×3 tensor in row-major order, even in 2-D simulations. Component ordering:

| Index | Component |
|-------|-----------|
| 0 | σ_xx |
| 1 | σ_xy |
| 2 | σ_xz |
| 3 | σ_yx |
| 4 | σ_yy |
| 5 | σ_yz |
| 6 | σ_zx |
| 7 | σ_zy |
| 8 | σ_zz |

In 2-D plane-strain analyses the out-of-plane components (σ_xz, σ_yz, σ_zx, σ_zy) are zero and σ_zz represents the out-of-plane confinement stress.

---

### `Get_Stress()` → `list[float]`

Return the current Cauchy stress tensor as a flat 9-component vector (Pa).

```python
s = node.Get_Stress()
sigma_xx = s[0]
sigma_yy = s[4]
p_mean   = (s[0] + s[4] + s[8]) / 3.0
```

---

### `Get_Strain()` → `list[float]`

Return the current total strain tensor as a flat 9-component vector (dimensionless).

---

### `Get_Prev_Stress()` → `list[float]`

Return the stress tensor at the start of the current time step (before the stress update). Useful for computing stress increments.

---

### `Get_Shape_Tensor()` → `list[float]`

Return the shape tensor **K** used in the nonlocal deformation gradient computation. Stored as a flat 9-component vector.

---

### `Get_Shape_Tensor_Inv()` → `list[float]`

Return the inverse of the shape tensor **K⁻¹**.

---

### `Get_Def_Grad()` → `list[float]`

Return the deformation gradient tensor **F** as a flat 9-component vector.

---

## Plasticity

### `Get_Plastic_Strain()` → `list[float]`

Return the plastic strain tensor as a flat 9-component vector.

---

### `Get_Back_Stress()` → `list[float]`

Return the back-stress tensor (kinematic hardening). Returns a flat 9-component vector.

---

### `Get_Acc_Plastic_Strain()` → `list[float]`

Return the accumulated plastic strain tensor (flat 9-component vector). This is the integral of the plastic strain rate over the deformation history.

---

### `Get_Acc_Plastic_Strain_Mag()` → `float`

Return the scalar magnitude of the accumulated plastic strain: the Frobenius norm of the accumulated plastic strain tensor.

---

### `Get_Eq_Plastic_Strain()` → `float`

Return the equivalent (von Mises) plastic strain scalar:

```
ε_p^eq = √(2/3 · ε_p : ε_p)
```

This is the quantity plotted in shear-band visualizations.

```python
node = PyGeoPeriX.Get_Node(100)
eps_p_eq = node.Get_Eq_Plastic_Strain()
print(f"Equivalent plastic strain: {eps_p_eq:.4e}")
```

---

## Damage

### `Get_Bond_Damage()` → `list[float]`

Return a list of damage scalars for each bond (connection to a neighbour). Each value is in `[0.0, 1.0]`:

| Value | Meaning |
|-------|---------|
| `0.0` | Bond fully intact |
| `1.0` | Bond fully broken |

The length of the returned list equals the number of neighbours (see `Get_Neighbors()`).

```python
damages = node.Get_Bond_Damage()
broken  = sum(1 for d in damages if d >= 1.0)
total   = len(damages)
print(f"Bond damage: {broken}/{total} bonds broken")
```

---

## Neighbour topology

### `Get_Neighbors()` → `list[int]`

Return the list of neighbour node IDs. These are the real nodes within the horizon of this node.

```python
nbrs = node.Get_Neighbors()
print(f"Node {node.Get_Node_Id()} has {len(nbrs)} neighbours")
```

---

### `Get_Mirror_Neighbors()` → `list[int]`

Return the list of fictitious (mirror) neighbour node IDs. Mirror neighbours are used in the boundary correction of the nonlocal integral.

---

## Example: post-analysis state inspection

```python
import PyGeoPeriX

model = PyGeoPeriX.Model(dim=2, num_nodes=1000, model_name="Demo")
# ... (full setup and Run_Analysis) ...

# Inspect a specific node after the simulation
node = PyGeoPeriX.Get_Node(100)

print("=== Node 100 state ===")
print(f"  Type:              {'Real' if node.Get_Type() == 1 else 'Fictitious'}")
print(f"  Position:          {node.Get_Position()}")
print(f"  Displacement:      {node.Get_Disp()}")
print(f"  Stress [Sxx,Syy]:  {node.Get_Stress()[0]:.2f}, {node.Get_Stress()[4]:.2f} Pa")
print(f"  Eq. plastic strain:{node.Get_Eq_Plastic_Strain():.4e}")
print(f"  Neighbours:        {len(node.Get_Neighbors())}")
broken = sum(1 for d in node.Get_Bond_Damage() if d >= 1.0)
print(f"  Broken bonds:      {broken}/{len(node.Get_Bond_Damage())}")
```
