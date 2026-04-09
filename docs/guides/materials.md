# Materials

GeoPeriX provides three constitutive material models. All are registered with the engine using `Create_Material` and assigned to node groups with `Set_Material`. This guide explains the physics behind each model, lists all required parameters, and provides calibration guidance.

---

## Common parameters

All three materials share a common set of base parameters:

| Key | Type | Unit | Description |
|-----|------|------|-------------|
| `density` | `float` | kg/m³ | Mass density. Used in the equation of motion (inertia term). For quasi-static analyses with velocity BCs, the density mainly controls the stable time step |
| `youngs_modulus` | `float` | Pa | Young's modulus E |
| `poissons_ratio` | `float` | — | Poisson's ratio ν (must satisfy 0 < ν < 0.5) |

---

## LinearElasticMaterial

Isotropic linear elasticity with Hooke's law:

```
σ = λ tr(ε) I + 2μ ε
```

where λ and μ are the Lamé parameters computed from E and ν.

### Parameters

| Key | Type | Unit | Required |
|-----|------|------|---------|
| `density` | `float` | kg/m³ | yes |
| `youngs_modulus` | `float` | Pa | yes |
| `poissons_ratio` | `float` | — | yes |

### Example

```python
model.Create_Material(1, "LinearElasticMaterial", {
    "density":        2000.0,
    "youngs_modulus": 100e6,
    "poissons_ratio": 0.25,
})
```

### When to use it

- For the fictitious boundary nodes in any simulation (elastic behaviour avoids yielding artifacts at boundaries).
- For soil or rock in the elastic regime (before yield is reached).
- For verification — the analytical solution is exact, so it provides a clean check of the discretization.

### Derived quantities

```text
λ = E ν / ((1+ν)(1-2ν))
μ = E / (2(1+ν))
Bulk modulus K = E / (3(1-2ν))
Constrained modulus M = E(1-ν) / ((1+ν)(1-2ν))
```

---

## KinematicHardeningMaterial

Von Mises plasticity with linear kinematic hardening (Prager's rule). The yield criterion:

```
f(σ, α) = √(3/2) |s - α| - σ_y ≤ 0
```

where **s** is the deviatoric stress and **α** is the back-stress tensor (kinematic hardening variable).

### Parameters

| Key | Type | Unit | Required |
|-----|------|------|---------|
| `density` | `float` | kg/m³ | yes |
| `youngs_modulus` | `float` | Pa | yes |
| `poissons_ratio` | `float` | — | yes |
| `yield_stress` | `float` | Pa | yes |
| `hardening_modulus` | `float` | Pa | yes |

### Example

```python
model.Create_Material(2, "KinematicHardeningMaterial", {
    "density":           7800.0,
    "youngs_modulus":    200e9,
    "poissons_ratio":    0.3,
    "yield_stress":      250e6,
    "hardening_modulus": 10e9,    # kinematic hardening modulus H
})
```

### Hardening modulus

- `hardening_modulus > 0`: the yield surface translates as plastic strain accumulates, producing kinematic hardening (Bauschinger effect). Larger values give a stiffer post-yield response.
- `hardening_modulus = 0`: perfect plasticity with no hardening.
- `hardening_modulus < 0`: kinematic softening (rarely physical; use with caution).

### When to use it

Metals and metal-like materials in cyclic loading (the kinematic back-stress correctly captures the Bauschinger effect). For monotonic loading without cyclic reversal, isotropic hardening is equivalent; use `DruckerPragerMaterial` with `dp_hardening_mode=0` as an approximation.

---

## DruckerPragerMaterial

Pressure-dependent elastoplastic model suited to soils, rocks, and concrete. The yield surface is a cone in principal stress space:

```
f(σ) = q + η p - ξ c ≤ 0
```

where `p` is mean stress, `q` is von Mises stress, and η, ξ are functions of the friction angle φ and dilation angle ψ. The hardening/softening behaviour is controlled by `dp_hardening_mode`.

### Parameters

| Key | Type | Unit | Required |
|-----|------|------|---------|
| `density` | `float` | kg/m³ | yes |
| `youngs_modulus` | `float` | Pa | yes |
| `poissons_ratio` | `float` | — | yes |
| `cohesion` | `float` | Pa | yes |
| `friction_angle` | `float` | **radians** | yes |
| `dilation_angle` | `float` | **radians** | yes |
| `dp_hardening_mode` | `int` | — | yes |
| `hardening_modulus` | `float` | Pa | yes |

**Important:** `friction_angle` and `dilation_angle` must be given in **radians**, not degrees. Use `math.radians()` or `numpy.radians()` to convert.

### Hardening modes

| `dp_hardening_mode` | Behaviour |
|--------------------|-----------|
| `0` | **Cohesion softening/hardening**: `c(κ) = c₀ + H·κ`. A negative `hardening_modulus` produces softening (c decreasing). φ and ψ remain constant. |
| `1` | **Friction angle hardening**: φ increases with accumulated plastic strain κ. Dilation angle tapers towards zero as φ approaches its peak. c remains constant. |
| `2` | **Combined**: cohesion softening and friction angle hardening simultaneously. |

### Example: cohesion-softening soil

```python
import math

model.Create_Material(3, "DruckerPragerMaterial", {
    "density":           1800.0,
    "youngs_modulus":    50e6,
    "poissons_ratio":    0.3,
    "cohesion":          20e3,          # initial cohesion c₀ = 20 kPa
    "friction_angle":    math.radians(30.0),
    "dilation_angle":    math.radians(5.0),
    "dp_hardening_mode": 0,
    "hardening_modulus": -5e4,          # softening rate: c reduces as κ grows
})
```

### Example: friction hardening (contractant soil)

```python
model.Create_Material(4, "DruckerPragerMaterial", {
    "density":           2100.0,
    "youngs_modulus":    80e6,
    "poissons_ratio":    0.28,
    "cohesion":          5e3,           # small initial cohesion
    "friction_angle":    math.radians(20.0),   # initial friction angle
    "dilation_angle":    math.radians(0.0),    # non-dilative
    "dp_hardening_mode": 1,
    "hardening_modulus": 2e6,           # positive: friction angle grows with κ
})
```

### Calibration from triaxial test data

A standard triaxial test gives you peak and residual strength at several confining pressures. From this data:

1. Plot failure points in p–q space.
2. Fit a straight line: `q = M p + k`. This gives the slope M and intercept k.
3. Convert to Drucker-Prager parameters:
   - For the circumscribed cone (outer bound): `η = 6 sin(φ) / (3 - sin(φ))`
   - For the inscribed cone (inner bound): `η = 6 sin(φ) / (3 + sin(φ))`
4. The intercept k = `ξ c` gives you cohesion once ξ is known.

For `dp_hardening_mode=0`, set `hardening_modulus` to the rate of change of cohesion with accumulated plastic strain. A value of `−H (Pa)` means cohesion drops by `H` per unit of accumulated plastic strain. Typical laboratory values for loose sand range from `-50 kPa` to `-500 kPa`.

---

## Assigning materials

Always assign an elastic material to fictitious boundary nodes. Fictitious nodes should not yield because they are not physical material points — they exist only to complete the nonlocal integral near the boundary.

```python
# Real soil nodes: Drucker-Prager
model.Set_Material("All",              3)
model.Set_Material("Soil",             3)

# Fictitious nodes: elastic (tags 1)
model.Set_Material("Top_Ficticous",    1)
model.Set_Material("Bottom_Ficticous", 1)
model.Set_Material("Left_Ficticous",   1)   # if generated
model.Set_Material("Right_Ficticous",  1)   # if generated
```

The order of `Set_Material` calls matters: later calls overwrite earlier ones. In the example above, the `"Soil"` call overwrites the `"All"` assignment for soil nodes, which is fine. But if you called `Set_Material("All", 1)` after `Set_Material("Soil", 3)`, the soil nodes would be reassigned to material 1.

---

## Stable time step considerations

The explicit time integrator uses a stability criterion based on the wave speed:

```
Δt_stable ≈ C_CFL × δx / c_p
```

where `c_p = √(M / ρ)` is the P-wave speed, `M` is the constrained modulus, and `C_CFL` is a safety factor (≈ 0.25–0.5 in peridynamics). Higher Young's modulus or lower density → smaller stable time step → more steps needed for the same simulated time.

**Practical tips:**
- If the simulation diverges (displacements explode), reduce the time step by increasing `num_steps` in `Run_Analysis`.
- For quasi-static analyses, you can increase density artificially (mass scaling) to allow larger time steps, but be careful that kinetic energy remains small compared to strain energy.
- For very stiff materials (E > 1 GPa), the stable time step becomes very small. Consider running fewer output steps (`output_step_freq > 0`) to keep file sizes manageable.
