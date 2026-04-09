# Setup order

Every GeoPeriX simulation must follow a specific call sequence. This is not an arbitrary convention — it reflects the mathematical dependencies between the quantities being computed. Calling methods out of order produces either a runtime error (if the engine detects the violation) or, worse, silently incorrect results.

---

## The required sequence

```text
1.  Model()                                  — create the model
2.  Add_Node / Add_Node_Group               — define geometry and boundary groups
3.  Set_Node_Spacing                         — particle spacing δx
4.  Set_Horizon                              — nonlocal horizon δ
5.  Generate_Ficticious_Nodes               — generate ghost nodes (BEFORE volumes/neighbours)
6.  Compute_Volume                           — Voronoi / geometric volumes
7.  Compute_Neighbours                       — build the bond list
8.  Create_Material                          — register constitutive models
9.  Set_Material                             — assign materials to node groups
10. Create_Constraint_Timer                  — define time windows for BCs
11. Apply_Fixity / Apply_Force / ...         — apply boundary conditions
12. Run_Analysis                             — execute time stepping
```

---

## Why this order is mandatory

### Step 1-2: Geometry before everything else

The engine pre-allocates internal data structures when `Model()` is created and populates them when nodes are added. `Add_Node` and `Add_Node_Group` must be called before any computation can happen because every subsequent step depends on knowing which nodes exist and where they are.

**What breaks:** Calling `Set_Horizon` before adding any nodes results in a no-op (no nodes to set the horizon on). The horizon will be uninitialised, and `Compute_Neighbours` will find zero neighbours for every node.

---

### Step 3-4: Spacing and horizon before fictitious nodes

`Generate_Ficticious_Nodes` uses the horizon to determine how many fictitious node layers to generate and where to place them. If the horizon has not been set, the generated fictitious nodes will have incorrect positions.

`Set_Node_Spacing` must come before `Compute_Volume` because the spacing is used in the area/volume interpolation formulas.

---

### Step 5: Fictitious nodes MUST precede volume and neighbour computation

This is the most commonly violated constraint. Here is why it matters.

Fictitious (ghost) nodes are mirror images of real boundary nodes reflected to the exterior of the domain. They fill in the truncated neighbourhood of boundary nodes so that the nonlocal integral operator is evaluated with the same completeness as interior nodes.

`Compute_Volume` uses Voronoi tessellation over the complete point cloud — real nodes plus fictitious nodes. If fictitious nodes are added after `Compute_Volume`, the Voronoi cells near the boundary will not reflect the fictitious nodes, and boundary nodes will have inflated volumes.

Similarly, `Compute_Neighbours` builds the bond list using the distance criterion `|x_j - x_i| < δ`. If fictitious nodes are absent when this runs, boundary nodes will have fewer neighbours than they should, the nonlocal integral will be truncated, and boundary forces will be wrong.

**What breaks (concretely):**

| Violation | Symptom |
|-----------|---------|
| `Compute_Volume` before `Generate_Ficticious_Nodes` | Boundary nodes get Voronoi volumes that are too large (no fictitious nodes to share the boundary Voronoi cell). Stress at boundaries is overestimated. |
| `Compute_Neighbours` before `Generate_Ficticious_Nodes` | Fictitious nodes are not in the bond list. Boundary conditions applied via fictitious nodes have no effect. The simulation proceeds as if the boundaries are free surfaces. |
| Both `Compute_*` before `Generate_Ficticious_Nodes` | Both effects combined. Results near boundaries are completely wrong. |

**Correct pattern:**

```python
# Add all real nodes first
model.Add_Node(...)
model.Add_Node_Group("Top", top_ids)
model.Add_Node_Group("Bottom", bottom_ids)

# Set discretization
model.Set_Node_Spacing("All", 0.05)
model.Set_Horizon("All", 0.05 * 4.000015)

# Generate fictitious nodes BEFORE any Compute_* call
model.Generate_Ficticious_Nodes("Top",    [0.5, 1.0], 4, "Soil")
model.Generate_Ficticious_Nodes("Bottom", [0.5, 1.0], 4, "Soil")

# Now safe to compute volumes and neighbours
model.Compute_Volume("All")
model.Compute_Neighbours("All")
```

---

### Steps 6-7: Volume before neighbours

`Compute_Volume` and `Compute_Neighbours` are independent of each other in principle, but the canonical order (volume first, then neighbours) is recommended because some internal state set during volume computation may be used when building the neighbour weights.

---

### Steps 8-9: Materials must exist before assignment

`Set_Material` looks up the material by tag in the engine's material registry. If `Create_Material` has not been called first, the tag does not exist and `Set_Material` will produce an error (or silently assign an invalid material, depending on build configuration).

You can call `Create_Material` and `Set_Material` multiple times in any interleaved order as long as each tag is created before it is assigned.

---

### Steps 10-11: Timers before BCs

Every `Apply_Fixity`, `Apply_Force`, and `Apply_Surface_Load` call takes a `constraint_timer_tag` argument. If the corresponding timer has not been created with `Create_Constraint_Timer`, the tag is invalid and the BC will not be active during the simulation.

---

### Step 12: Run_Analysis is always last

`Run_Analysis` initialises the time integrator, computes the stable time step, and begins the stepping loop. Any `Apply_Fixity` or `Create_Material` call made after `Run_Analysis` has no effect on the running or completed simulation.

---

## Quick reference: dependencies at a glance

```text
Add_Node
    └─ Set_Node_Spacing
    └─ Set_Horizon
         └─ Generate_Ficticious_Nodes ←── MUST be here
              └─ Compute_Volume
              └─ Compute_Neighbours
                   └─ Create_Material
                        └─ Set_Material
                             └─ Create_Constraint_Timer
                                  └─ Apply_Fixity / Apply_Force
                                       └─ Run_Analysis
```

---

## Checklist before calling `Run_Analysis`

Before running the simulation, verify:

- [ ] Every node has a `node_spacing` and `horizon` set
- [ ] `Generate_Ficticious_Nodes` was called for **every** boundary surface that needs fictitious nodes
- [ ] `Compute_Volume("All")` has been called
- [ ] `Compute_Neighbours("All")` has been called
- [ ] Every real-node group has a material assigned
- [ ] Every fictitious-node group has a (typically elastic) material assigned
- [ ] At least one `Create_Constraint_Timer` exists
- [ ] All boundary conditions reference valid timer tags
- [ ] `Run_Analysis` `start_time` matches or exceeds the minimum `start_time` of all active timers

---

## Debugging a mis-ordered setup

If your simulation shows unphysical results near boundaries (e.g., boundary nodes displacing much more than interior nodes, stress concentrations at corners), the most likely cause is that `Generate_Ficticious_Nodes` was not called before `Compute_Volume` or `Compute_Neighbours`.

Use `Print_Node_Group("Top_Ficticous")` immediately after `Generate_Ficticious_Nodes` to confirm that the group exists and has the expected number of nodes. The number of fictitious nodes should be comparable to the number of real boundary nodes multiplied by `m_factor`.

```python
model.Generate_Ficticious_Nodes("Top", [0.5, 1.0], 4, "Soil")
model.Print_Node_Group("Top_Ficticous")   # should list nodes
model.Compute_Volume("All")
```
