# Boundary conditions

GeoPeriX supports four types of boundary conditions, all applied to named node groups and governed by constraint timers. This guide explains each type, when to use it, and how to combine them in realistic simulations.

---

## Constraint timers

Every boundary condition is associated with a constraint timer that defines the time window during which it is active. You must create at least one timer before applying any BCs.

```python
# Active for the full analysis
model.Create_Constraint_Timer(tag=1, start_time=0.0, end_time=2.0)

# A second stage that activates at t=0.5
model.Create_Constraint_Timer(tag=2, start_time=0.5, end_time=2.0)
```

**Design pattern for staged loading:**

1. Create a timer that covers the consolidation phase (e.g., `0.0` → `0.5`).
2. Apply self-weight or isotropic confinement to that timer.
3. Create a second timer for the shear phase (`0.5` → `2.0`).
4. Apply the deviatoric load to the second timer.

The engine evaluates all active timers at every step, so BCs from different timers can overlap.

---

## 1. Displacement and velocity fixity (`Apply_Fixity`)

`Apply_Fixity` is the workhorse BC. It prescribes either a fixed displacement or a constant velocity on one or more DOFs of a node group.

```python
model.Apply_Fixity(
    node_group_name,       # str
    dof_number,            # int or list[int]  (0=x, 1=y, 2=z)
    value,                 # float or list[float]
    is_const,              # bool: True=displacement, False=velocity
    constraint_timer_tag,  # int
    is_relative=False,     # bool: relative to initial position?
)
```

### Pin both DOFs (fully fixed support)

```python
model.Apply_Fixity("Bottom",           [0, 1], [0.0, 0.0], True, 1, False)
model.Apply_Fixity("Bottom_Ficticous", [0, 1], [0.0, 0.0], True, 1, False)
```

Both the real boundary nodes and their fictitious counterparts must be fixed. Fixing only the real nodes while leaving fictitious nodes unconstrained results in unphysical boundary forces.

### Prescribe a constant velocity (compression)

```python
# Downward velocity of -0.01 m/s on the top surface
model.Apply_Fixity("Top",           [0, 1], [0.0, -0.01], False, 1, False)
model.Apply_Fixity("Top_Ficticous", [0, 1], [0.0, -0.01], False, 1, False)
```

`is_const=False` means the engine interprets `value` as a velocity and integrates it at every time step, producing a linearly increasing displacement.

### Roller support (fix one DOF, free the other)

```python
# Fix horizontal displacement only (roller: free vertical)
model.Apply_Fixity("Left",  [0], [0.0], True, 1)
model.Apply_Fixity("Right", [0], [0.0], True, 1)
```

### Relative fixity

`is_relative=True` measures the prescribed displacement relative to the node's initial position. This is useful when you want to prescribe a fractional compression regardless of the initial coordinates.

```python
# Compress the top by 2% of its initial y-position
model.Apply_Fixity("Top", [1], [-0.02], False, 1, is_relative=True)
```

---

## 2. Body force (`Apply_Force`)

`Apply_Force` applies a distributed body force to every node in a group. The force is specified per node (N), not as a body force density (N/m³). Multiply the body force density by the node volume to obtain the per-node value.

```python
model.Apply_Force(
    node_group_name,       # str
    dof_number,            # int
    value,                 # float (N per node)
    is_const,              # bool
    constraint_timer_tag,  # int
)
```

### Self-weight (gravity)

```python
density = 2000.0        # kg/m³
g       = 9.81          # m/s²
spacing = 0.05          # m
vol_2d  = spacing**2    # m² per node in 2-D

# Force per node = ρ × g × V  (negative y = downward)
f_gravity = -density * g * vol_2d

model.Apply_Force("Soil", 1, f_gravity, True, 1)
```

`is_const=True` applies the same force at every time step. `is_const=False` ramps the force linearly from zero to `value` over the timer window.

---

## 3. Surface load (`Apply_Surface_Load`)

`Apply_Surface_Load` distributes a traction (force per unit area) across a surface node group. The engine computes the outward normal for each surface node using the `internal_point` argument, then converts the traction to equivalent nodal forces.

```python
model.Apply_Surface_Load(
    surface_node_group,    # str
    internal_point,        # list[float] — a point strictly inside the domain
    dof_number,            # int
    value,                 # float (Pa)
    is_const,              # bool
    constraint_timer_tag,  # int
    search_radius=0.0,     # float — for automatic surface detection
    constraint_axis=[],    # list[float] — optional projection axis
)
```

### Uniform vertical pressure on a flat top surface

```python
# Apply 100 kPa downward pressure on the top surface
model.Apply_Surface_Load(
    "Top",
    internal_point=[0.5, 1.0],   # a point inside the domain
    dof_number=1,
    value=-100e3,                 # Pa, negative = downward
    is_const=True,
    constraint_timer_tag=1,
)
```

The `internal_point` must be strictly inside the domain — the engine uses it to determine which direction is "inward". If the point lies on a boundary or outside the domain, the normal direction will be incorrect.

### Confining pressure on a cylindrical surface

For a circular or cylindrical geometry, use `constraint_axis` to project the outward normal onto the radial direction:

```python
# Radial confining pressure on a circular 2-D sample
model.Apply_Surface_Load(
    "CircularBoundary",
    internal_point=[0.0, 0.0],    # centre of the circle
    dof_number=0,
    value=-300e3,                  # Pa confining pressure
    is_const=True,
    constraint_timer_tag=1,
    constraint_axis=[1.0, 0.0],   # project onto x-direction (radial in 2-D)
)
```

---

## 4. Cylindrical load (`Apply_Cylindrical_Load`)

`Apply_Cylindrical_Load` applies a radially inward (or outward) pressure to nodes arranged on a cylindrical surface in 3-D. The pressure is automatically distributed in the radial direction for each node based on the cylinder axis.

```python
model.Apply_Cylindrical_Load(
    node_group_name,       # str
    center,                # list[float] — a point on the cylinder axis
    axis,                  # list[float] — unit vector along the cylinder axis
    pressure,              # float (Pa) — positive = inward (confining)
    is_const,              # bool
    constraint_timer_tag,  # int
)
```

### 3-D triaxial confining pressure

```python
# 300 kPa confining pressure on a vertical cylindrical sample
# The cylinder axis is vertical (z-direction); centre is at the origin.
model.Apply_Cylindrical_Load(
    "LateralSurface",
    center=[0.0, 0.0, 0.0],
    axis=[0.0, 0.0, 1.0],
    pressure=300e3,
    is_const=True,
    constraint_timer_tag=1,
)
```

Use this in combination with `Apply_Fixity` on the top and bottom caps to simulate a standard triaxial test.

---

## Combining boundary conditions

### 2-D direct shear test

```python
model.Create_Constraint_Timer(1, 0.0, 2.0)

# Fix base
model.Apply_Fixity("Bottom",           [0, 1], [0.0, 0.0], True,  1)
model.Apply_Fixity("Bottom_Ficticous", [0, 1], [0.0, 0.0], True,  1)

# Normal stress on top (constant)
model.Apply_Force("Top", 1, -100e3 * spacing**2, True, 1)

# Shear velocity on top
model.Apply_Fixity("Top",           [0], [0.005], False, 1)
model.Apply_Fixity("Top_Ficticous", [0], [0.005], False, 1)
```

### 3-D triaxial test (isotropic consolidation then shear)

```python
# Stage 1: isotropic confinement
model.Create_Constraint_Timer(1, 0.0, 0.5)
model.Apply_Cylindrical_Load("LateralSurface", [0,0,0], [0,0,1], 300e3, True,  1)
model.Apply_Fixity("Bottom", [0,1,2], [0.0, 0.0, 0.0], True, 1)

# Stage 2: axial compression (maintains confining pressure)
model.Create_Constraint_Timer(2, 0.5, 2.0)
model.Apply_Cylindrical_Load("LateralSurface", [0,0,0], [0,0,1], 300e3, True,  2)
model.Apply_Fixity("Bottom", [0,1,2], [0.0, 0.0, 0.0], True, 2)
model.Apply_Fixity("Top",    [2],     [-0.01],           False, 2)

model.Run_Analysis(0.0, 2.0, 2000, "Triaxial_Stage")
```

---

## Common mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Not applying BCs to fictitious nodes | Top/bottom surfaces move freely; incorrect stress at boundaries | Apply the same `Apply_Fixity` to both the real group and the `_Ficticous` group |
| `is_const=True` for a velocity BC | The velocity is only applied at the first step; subsequent steps use whatever velocity the node has | Use `is_const=False` for velocity prescriptions |
| Wrong sign on `value` | Compression appears as extension and vice versa | Negative `value` in DOF 1 (y) means downward; check your axis convention |
| Timer not covering full analysis | BC deactivates partway through | Ensure `end_time` of the timer is at least as large as `end_time` of `Run_Analysis` |
| Prescribing force in Pa instead of N | Boundary forces many orders of magnitude too large or too small | Multiply pressure (Pa) by node tributary area to get force (N) per node |
