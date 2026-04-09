# Model

The `Model` class is the central object in every GeoPeriX simulation. It manages the node mesh, material assignments, boundary conditions, and the time-stepping engine. A single `Model` instance represents one complete simulation.

```python
import PyGeoPeriX

model = PyGeoPeriX.Model(dim=2, num_nodes=10000, model_name="MyModel")
```

---

## Constructor

### `__init__(dim=3, num_nodes=10000, model_name="Model")`

Create a new simulation model.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dim` | `int` | `3` | Spatial dimension: `2` for 2-D or `3` for 3-D |
| `num_nodes` | `int` | `10000` | Upper bound on the number of nodes (used to pre-allocate memory; the actual count can be lower) |
| `model_name` | `str` | `"Model"` | Name used as the prefix for output files |

```python
# 2-D model
model = PyGeoPeriX.Model(dim=2, num_nodes=5000, model_name="Compression_2D")

# 3-D model
model = PyGeoPeriX.Model(dim=3, num_nodes=50000, model_name="Triaxial_3D")
```

---

## Node management

### `Add_Node(node_id, position, node_group_name="All")`

Add a single material point to the model.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_id` | `int` | Unique positive integer ID for this node. IDs must start at 1 and be contiguous |
| `position` | `list[float]` | Coordinates `[x, y]` (2-D) or `[x, y, z]` (3-D) |
| `node_group_name` | `str` | Name of an existing node group to add this node to. Defaults to `"All"` (the built-in group that contains every node) |

```python
node_id = 1
for i in range(21):
    for j in range(41):
        model.Add_Node(node_id, [i * 0.05, j * 0.05], "Soil")
        node_id += 1
```

**Note:** All nodes are automatically added to the `"All"` group regardless of the `node_group_name` argument. Additional group membership can be set with `Add_Node_Group`.

---

### `Add_Node_Group(node_group_name, nodes=[])`

Create a named group of nodes. This is the standard way to define boundary surfaces, material zones, or any subset you want to apply conditions to uniformly.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Name for the new group |
| `nodes` | `list[int]` | List of node IDs to include in the group |

```python
bottom_ids = [i * 41 + 1 for i in range(21)]   # first row
model.Add_Node_Group("Bottom", bottom_ids)

top_ids = [(i + 1) * 41 for i in range(21)]     # last row
model.Add_Node_Group("Top", top_ids)
```

**Note:** When `Generate_Ficticious_Nodes("Bottom", ...)` is called, GeoPeriX automatically creates the group `"Bottom_Ficticous"` (note the spelling). You can reference this auto-generated group in `Apply_Fixity` and `Set_Material` calls.

---

## Discretization

### `Set_Node_Spacing(node_group_name, spacing)`

Set the particle spacing `δx` for all nodes in a group. This value is used in volume calculations and influences function evaluations.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Target node group |
| `spacing` | `float` | Particle spacing (m) |

```python
model.Set_Node_Spacing("All", 0.05)
```

---

### `Set_Horizon(node_group_name, horizon)`

Set the peridynamic horizon radius `δ` for nodes in a group. The horizon defines the nonlocal neighbourhood — only nodes within distance `δ` of a given node interact with it.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Target node group |
| `horizon` | `float` | Horizon radius (m) |

Typical values: `horizon = (3.0 to 4.0) × spacing`. The small fractional offset `4.000015 × spacing` avoids floating-point boundary cases in the neighbour search.

```python
spacing = 0.05
model.Set_Horizon("All", spacing * 4.000015)
```

---

### `Set_Volume(node_group_name, volume)`

Override the volume of every node in a group with a fixed value. This bypasses the geometric volume computation. Useful when you have an analytical expression for particle volume.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Target node group |
| `volume` | `float` | Volume (m² in 2-D, m³ in 3-D) |

---

### `Compute_Volume(node_group_name)`

Compute nodal volumes geometrically using Voronoi tessellation (via CGAL). Call this **after** `Generate_Ficticious_Nodes`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Node group to process. Use `"All"` to process all nodes |

```python
model.Compute_Volume("All")
```

---

### `Compute_Neighbours(node_group_name)`

Build the neighbour list for each node: every node whose centre lies within the horizon of a given node becomes its neighbour. Call this **after** `Compute_Volume`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Node group to process. Use `"All"` to process all nodes |

```python
model.Compute_Neighbours("All")
```

---

### `Compute_Global_Strain()`

Compute the global (volume-averaged) strain tensor across the entire domain. Useful as a diagnostic after the analysis is complete.

```python
model.Compute_Global_Strain()
```

---

## Fictitious nodes

### `Generate_Ficticious_Nodes(surface_node_group, internal_point, m_factor, volume_node_group="All")`

Generate fictitious (ghost) boundary nodes for the surface identified by `surface_node_group`. Fictitious nodes are mirror images of the real boundary nodes reflected away from the interior. They allow the nonlocal integral operator to be evaluated at boundary nodes without truncation.

**This method must be called before `Compute_Volume` and `Compute_Neighbours`.**

| Parameter | Type | Description |
|-----------|------|-------------|
| `surface_node_group` | `str` | Name of the boundary node group (e.g., `"Top"`, `"Bottom"`) |
| `internal_point` | `list[float]` | A point strictly inside the domain, used to determine the inward normal direction |
| `m_factor` | `int` | Number of fictitious node layers to generate. Typically 3–4 |
| `volume_node_group` | `str` | The group whose Voronoi domain is used for volume computation of fictitious nodes. Default: `"All"` |

After this call, a new group named `<surface_node_group>_Ficticous` is automatically available.

```python
# The internal point [0.0, 1.0] is inside the domain (somewhere mid-height).
model.Generate_Ficticious_Nodes("Top",    [0.0, 1.0], 4, "Soil")
model.Generate_Ficticious_Nodes("Bottom", [0.0, 1.0], 4, "Soil")
```

---

## Material management

### `Create_Material(mat_tag, mat_name, mat_prop)`

Register a constitutive material model with the engine.

| Parameter | Type | Description |
|-----------|------|-------------|
| `mat_tag` | `int` | Unique positive integer tag identifying this material |
| `mat_name` | `str` | Name of the material model class: `"LinearElasticMaterial"`, `"KinematicHardeningMaterial"`, or `"DruckerPragerMaterial"` |
| `mat_prop` | `dict[str, float]` | Material property dictionary. Keys depend on `mat_name` — see {doc}`../guides/materials` |

```python
model.Create_Material(1, "LinearElasticMaterial", {
    "density":        2000.0,
    "youngs_modulus": 100e6,
    "poissons_ratio": 0.25,
})

model.Create_Material(2, "DruckerPragerMaterial", {
    "density":           1800.0,
    "youngs_modulus":    50e6,
    "poissons_ratio":    0.3,
    "cohesion":          15e3,
    "friction_angle":    0.5236,   # 30° in radians
    "dilation_angle":    0.1745,   # 10° in radians
    "dp_hardening_mode": 0,
    "hardening_modulus": -5e4,
})
```

---

### `Set_Material(node_group_name, material_tag)`

Assign a previously created material to all nodes in a group.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Target node group |
| `material_tag` | `int` | Tag of the material (must have been created with `Create_Material`) |

```python
model.Set_Material("All",              2)   # soil material everywhere
model.Set_Material("Top_Ficticous",    1)   # elastic for fictitious nodes
model.Set_Material("Bottom_Ficticous", 1)
```

---

## Constraint timers

### `Create_Constraint_Timer(tag=1, start_time=0.0, end_time=1.0)`

Create a time window during which a boundary condition is active. Every `Apply_Fixity`, `Apply_Force`, or `Apply_Surface_Load` call references a timer tag. BCs outside their timer window are not applied.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tag` | `int` | `1` | Unique positive integer tag |
| `start_time` | `float` | `0.0` | Time (s) at which the BC becomes active |
| `end_time` | `float` | `1.0` | Time (s) at which the BC is deactivated |

```python
model.Create_Constraint_Timer(1, 0.0, 2.0)   # active for the full analysis
model.Create_Constraint_Timer(2, 0.5, 1.0)   # a second stage starting at t=0.5
```

---

## Boundary conditions

### `Apply_Fixity(node_group_name, dof_number, value, is_const, constraint_timer_tag, is_relative=False)`

Apply a displacement or velocity constraint to a group of nodes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Target node group |
| `dof_number` | `int` or `list[int]` | Degree(s) of freedom: `0`=x, `1`=y, `2`=z |
| `value` | `float` or `list[float]` | Prescribed displacement (if `is_const=True`) or velocity (if `is_const=False`) for each DOF |
| `is_const` | `bool` | `True` → displacement fixity; `False` → velocity ramp |
| `constraint_timer_tag` | `int` | Tag of the constraint timer controlling when this BC is active |
| `is_relative` | `bool` | `False` → absolute value; `True` → value relative to initial position |

```python
# Fix base: zero displacement in both x and y
model.Apply_Fixity("Bottom", [0, 1], [0.0, 0.0], True, 1)

# Apply downward velocity to the top
model.Apply_Fixity("Top", [1], [-0.01], False, 1)
```

---

### `Apply_Force(node_group_name, dof_number, value, is_const, constraint_timer_tag)`

Apply a body force to a group of nodes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Target node group |
| `dof_number` | `int` | Degree of freedom: `0`=x, `1`=y, `2`=z |
| `value` | `float` | Force magnitude (N) per node |
| `is_const` | `bool` | `True` → constant force; `False` → ramp from 0 to `value` over the timer window |
| `constraint_timer_tag` | `int` | Timer tag |

```python
# Gravity in the -y direction (2-D): 9.81 m/s² × density × volume
model.Apply_Force("Soil", 1, -9.81 * 2000 * 0.05**2, True, 1)
```

---

### `Apply_Surface_Load(surface_node_group, internal_point, dof_number, value, is_const, constraint_timer_tag, search_radius=0.0, constraint_axis=[])`

Apply a distributed load to a surface. The engine uses the surface geometry and the internal point to compute the outward normal and distribute the load as equivalent nodal forces.

| Parameter | Type | Description |
|-----------|------|-------------|
| `surface_node_group` | `str` | Name of the surface node group |
| `internal_point` | `list[float]` | A point strictly inside the domain |
| `dof_number` | `int` | DOF to load |
| `value` | `float` | Load magnitude (Pa for pressure, N/m² in 2-D, N/m² in 3-D) |
| `is_const` | `bool` | Constant or ramped |
| `constraint_timer_tag` | `int` | Timer tag |
| `search_radius` | `float` | Radius for detecting surface nodes when the group is not pre-defined. Default: `0.0` (use the group as-is) |
| `constraint_axis` | `list[float]` | Optional axis vector to project the load direction |

```python
# Apply 100 kPa vertical load to the top surface
model.Apply_Surface_Load("Top", [0.5, 1.0], 1, -100e3, True, 1)
```

---

### `Apply_Cylindrical_Load(node_group_name, center, axis, pressure, is_const, constraint_timer_tag)`

Apply a radial pressure load to nodes arranged on a cylindrical surface. The load direction is radially inward (or outward, depending on the sign of `pressure`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Node group forming the cylindrical surface |
| `center` | `list[float]` | A point on the axis of the cylinder |
| `axis` | `list[float]` | Unit vector defining the cylinder axis |
| `pressure` | `float` | Pressure magnitude (Pa). Positive = inward confining pressure |
| `is_const` | `bool` | Constant or ramped |
| `constraint_timer_tag` | `int` | Timer tag |

```python
# 300 kPa confining pressure on a vertical cylindrical sample
model.Apply_Cylindrical_Load(
    "LateralSurface",
    center=[0.0, 0.0, 0.0],
    axis=[0.0, 0.0, 1.0],
    pressure=300e3,
    is_const=True,
    constraint_timer_tag=1,
)
```

---

### `Balance_External_Forces()`

Compute and store the initial out-of-balance force due to body loads or pre-applied stresses so that the first step starts from (near) equilibrium. Call this after all `Apply_Force` calls but before `Run_Analysis`.

```python
model.Balance_External_Forces()
```

---

### `Add_Rotational_Damping(damping_coeff=0.01)`

Add rotational (algorithmic) damping to reduce high-frequency oscillations in explicit dynamics simulations. A coefficient of 0.01 provides light damping; values above 0.1 can significantly slow down wave propagation.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `damping_coeff` | `float` | `0.01` | Dimensionless damping coefficient |

```python
model.Add_Rotational_Damping(0.02)
```

---

## Cavity processing

### `Process_Cavity(cavity_function, max_depth=20, tolerance=1e-7)`

Remove nodes that lie inside a cavity described by `cavity_function`. The function is called recursively with bisection to locate the cavity boundary precisely.

| Parameter | Type | Description |
|-----------|------|-------------|
| `cavity_function` | `callable` | A Python function `f(position) → bool` that returns `True` if `position` is inside the cavity |
| `max_depth` | `int` | Maximum bisection depth. Default: `20` |
| `tolerance` | `float` | Convergence tolerance. Default: `1e-7` |

```python
def cylindrical_cavity(pos):
    """Return True if the point is inside a cylinder of radius 0.1 m centred at (0.5, 0.5)."""
    r = ((pos[0] - 0.5)**2 + (pos[1] - 0.5)**2) ** 0.5
    return r < 0.1

model.Process_Cavity(cylindrical_cavity)
```

---

## Diagnostics

### `Print_Nodes()`

Print a summary of all nodes to stdout. Useful for debugging small models.

```python
model.Print_Nodes()
```

---

### `Print_Node_Group(node_group_name)`

Print a summary of all nodes in the specified group.

| Parameter | Type | Description |
|-----------|------|-------------|
| `node_group_name` | `str` | Name of the group to print |

```python
model.Print_Node_Group("Bottom")
```

---

## Running the simulation

### `Run_Analysis(start_time, end_time, num_steps, stage_name="Stage", output_step_freq=0)`

Execute the time-stepping simulation. This is the final call in the setup sequence.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_time` | `float` | — | Start time (s) |
| `end_time` | `float` | — | End time (s) |
| `num_steps` | `int` | — | Number of time steps (time step size = `(end_time - start_time) / num_steps`) |
| `stage_name` | `str` | `"Stage"` | Name prefix for the output HDF5 file (`<stage_name>.h5`) |
| `output_step_freq` | `int` | `0` | Write output every `output_step_freq` steps. `0` means write every step |

```python
# Simulate 1000 steps from t=0 to t=0.018, writing output every step.
model.Run_Analysis(0.0, 0.018, 1000, "My_Stage", 0)

# Write output every 10 steps to reduce file size.
model.Run_Analysis(0.0, 0.018, 1000, "My_Stage", 10)
```

Results are written to `<stage_name>.h5` in the working directory. See {doc}`../guides/postprocessing` for the HDF5 schema and post-processing tools.
