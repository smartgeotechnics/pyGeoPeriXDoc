# Material

The `Material` class is a read-only interface to a constitutive model registered with the engine. You obtain a `Material` instance by calling `PyGeoPeriX.Get_Material(tag)`. The class lets you inspect material properties and invoke the constitutive update directly from Python — useful for verification and calibration scripts.

```python
import PyGeoPeriX

# After Create_Material has been called on the model:
mat = PyGeoPeriX.Get_Material(1)
print(mat.Get_Name())
print(mat.Get_Density())
```

---

## Identification

### `Get_Tag()` → `int`

Return the integer tag assigned to this material when it was created with `Create_Material`.

```python
tag = mat.Get_Tag()   # e.g. 1
```

---

### `Get_Name()` → `str`

Return the material model name string.

| Return value | Model |
|-------------|-------|
| `"LinearElasticMaterial"` | Isotropic linear elasticity |
| `"KinematicHardeningMaterial"` | Von Mises plasticity with kinematic hardening |
| `"DruckerPragerMaterial"` | Pressure-dependent Drucker-Prager plasticity |

```python
name = mat.Get_Name()
print(f"Material model: {name}")
```

---

## Properties

### `Get_Density()` → `float`

Return the material mass density (kg/m³).

```python
rho = mat.Get_Density()   # e.g. 2000.0
```

---

## Constitutive evaluation

### `Compute_Stress(strain, strain_inc)` → `list[float]`

Evaluate the constitutive model for the given total strain and strain increment. Returns the updated Cauchy stress tensor as a flat 9-component vector.

| Parameter | Type | Description |
|-----------|------|-------------|
| `strain` | `list[float]` | Current total strain tensor (flat 9-component, row-major) |
| `strain_inc` | `list[float]` | Strain increment for this step (flat 9-component, row-major) |

Returns a `list[float]` of length 9: the updated stress tensor `[σ_xx, σ_xy, σ_xz, σ_yx, σ_yy, σ_yz, σ_zx, σ_zy, σ_zz]`.

```python
import PyGeoPeriX

mat = PyGeoPeriX.Get_Material(1)

# Uniaxial strain increment of 1e-4 in the y-direction
strain     = [0.0] * 9
strain_inc = [0.0] * 9
strain_inc[4] = 1e-4   # ε_yy increment

stress = mat.Compute_Stress(strain, strain_inc)
print(f"σ_yy = {stress[4]:.2f} Pa")
```

This method is particularly useful for:

- **Verification**: checking that a material reproduces expected analytical results (e.g., Young's modulus from a uniaxial strain test)
- **Calibration**: sweeping material parameters and comparing stress paths to laboratory data without running a full simulation
- **Custom post-processing**: re-computing stress from stored strain histories

---

## Example: verify elastic stiffness

```python
import PyGeoPeriX

# Create and verify a linear elastic material
model = PyGeoPeriX.Model(dim=3, num_nodes=1, model_name="MatTest")
model.Create_Material(1, "LinearElasticMaterial", {
    "density":        2000.0,
    "youngs_modulus": 100e6,
    "poissons_ratio": 0.25,
})

mat = PyGeoPeriX.Get_Material(1)
print(f"Material: {mat.Get_Name()}, tag={mat.Get_Tag()}, rho={mat.Get_Density()} kg/m³")

# Apply a small uniaxial strain increment and check Young's modulus
E = 100e6
nu = 0.25
eps_yy = 1e-5

strain_inc = [0.0] * 9
strain_inc[4] = eps_yy   # ε_yy

stress = mat.Compute_Stress([0.0]*9, strain_inc)
sigma_yy = stress[4]

# For uniaxial strain: σ_yy = E*(1-ν)/((1+ν)*(1-2ν)) * ε_yy (constrained modulus)
M = E * (1 - nu) / ((1 + nu) * (1 - 2*nu))
print(f"Computed σ_yy = {sigma_yy:.2f} Pa")
print(f"Expected σ_yy = {M * eps_yy:.2f} Pa (constrained modulus = {M:.2f} Pa)")
```
