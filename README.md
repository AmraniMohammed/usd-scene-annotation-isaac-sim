# USD scene annotation for Isaac Sim

Python tools that prepare a USD scene for robot simulation in NVIDIA Isaac Sim, driven by one JSON config per scene:

- **Zone and room labels** as semantic labels Isaac Sim reads (`UsdSemantics.LabelsAPI`, or the legacy `SemanticsAPI` format with `--schema legacy`). A zone can be a list of prims or a floor rectangle, for scenes with no room structure such as a warehouse.
- **A collision decision on every geometry prim** (`UsdPhysics.CollisionAPI`). Colliders the scene already has are kept as authored. Geometry without one gets a triangle-mesh collider. Listed prims are set not collidable: a loose cable, or visual meshes whose collision comes from simpler proxy shapes.
- **Moving surfaces**: conveyor belts and roller beds become kinematic bodies with a PhysX surface velocity, so boxes placed on them are carried along.
- **Failure-case labels** for robot navigation, with the category list set per site in the config (industrial: moving surfaces, keep-out zones, low clearance, small floor obstacles, narrow aisles; residential: thresholds, rugs, low furniture, floor vents, mirrors).
- **Measurements read from geometry** (height, clearance under an object, gap width) from bounding boxes, in meters, whatever the scene's units and up axis.
- **A QA note** per scene: collider counts, labels, categories present or absent, conveyor speeds, and pass/fail checks.

The original scene is never modified. Annotations go in a separate layer that sublayers it. `--flatten` also writes a single self-contained file.

## Files

| File | Purpose |
|---|---|
| `inspect_scene.py` | Prints the prim tree with types, sizes and positions, to write the config |
| `annotate.py` | Applies the config: labels, collision, moving surfaces, failure cases, measurements |
| `qa_check.py` | Checks the result and writes the QA note |
| `make_line.py` | Places a straight conveyor line in an environment, as a small file referencing both |
| `make_test_room.py` | Builds a small two-room apartment to test everything without downloads |
| `isaac_python.bat` | Runs a script with Isaac Sim's Python and USD libraries (Windows) |
| `configs/apartment.json` | Config for the test apartment |

## Setup

Tested with Isaac Sim 6.2 on Windows. Isaac Sim's `python.bat` can't import `pxr` outside the app, so `isaac_python.bat` sets the paths to the USD libraries Isaac Sim ships:

```bat
set ISAAC_SIM=C:\path\to\isaac-sim-standalone-6.2.0-windows-x86_64
isaac_python.bat inspect_scene.py some_scene.usd
```

The scripts only need OpenUSD (`pxr`), so another OpenUSD 24.08+ Python install should also work, but that hasn't been tested.

## Example 1: test apartment (residential, no download)

```bat
isaac_python.bat make_test_room.py test_scene/apartment.usda
isaac_python.bat annotate.py test_scene/apartment.usda configs/apartment.json -o out/apartment_annotated.usda --flatten
isaac_python.bat qa_check.py out/apartment_annotated_flat.usda -o out/apartment_qa_note.md
```

The results are in `out/`.

## Example 2: warehouse with a conveyor line (industrial)

The scene files aren't in this repository. They are NVIDIA Isaac Sim assets, licensed under CC BY 4.0:

- Warehouse: `Isaac/Environments/Simple_Warehouse/full_warehouse.usd`
- Conveyor: `Isaac/Props/Conveyors/ConveyorBelt_A04.usd`

Both are on the Isaac Sim 6.2 asset server (`https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.2/`). To get a local copy with all props and textures, open the Content tab in Isaac Sim, right-click each file, and use **Collect As…** with every option unchecked.

```bat
isaac_python.bat make_line.py scenes/full_warehouse/full_warehouse.usd scenes/conveyor_A04/ConveyorBelt_A04.usd -o scenes/warehouse_line.usda --start -11 -12 --yaw 90 --count 3
isaac_python.bat inspect_scene.py scenes/warehouse_line.usda --depth 2
```

The warehouse config is still being written.

## Check in Isaac Sim

1. Open the annotated file.
2. Select a labeled prim: the Property panel shows `semantics:labels:room`. Isaac Sim's Semantics Schema Editor lists the labels too.
3. Turn on collider visualization (viewport eye menu, Show By Type, Physics, Colliders). Prims set not collidable show no collider.
4. Press Play and drop a rigid cube on the floor, or on a conveyor, to see collisions and surface velocity work.

Menu names can differ slightly between Isaac Sim versions.

## Config format

```json
{
  "root": "/Root",
  "categories": ["moving_surfaces", "keep_out_zones", "low_clearance", "small_obstacles", "narrow_aisles"],
  "rooms": {
    "living_room":   ["/Apartment/LivingRoom"],
    "conveyor_cell": [{"box": [[-14, -14], [-8, -4]]}]
  },
  "non_collidable":   ["/Apartment/LivingRoom/Cable", "/Root/ConveyorLine/*/Conveyor/Rubberbands"],
  "surface_velocity": {"/Root/ConveyorLine/*/Conveyor/Rollers": [0.3, 0.0, 0.0]},
  "surfaces":         {"/Apartment/LivingRoom/Rug": "rug"},
  "features": [
    {"category": "low_clearance", "prim": "/Apartment/Bedroom/Bed",
     "underside": "/Apartment/Bedroom/Bed/Frame", "type": "bed", "measure": ["clearance"]},
    {"category": "keep_out_zones", "type": "conveyor_keep_out",
     "marker": {"name": "ConveyorKeepOut", "center": [-11.0, -9.0, 0.0], "size": [2.2, 7.0, 0.01]}}
  ]
}
```

- `categories`: the failure-case list for this site. If it's left out, the residential list is used.
- `rooms`: each entry is a prim path, or a floor rectangle `{"box": [[xmin, ymin], [xmax, ymax]]}` in meters. A rectangle labels every direct child of `root` whose footprint center lies inside it.
- `non_collidable`, `surface_velocity`, `surfaces`: prim paths or patterns with `*`. A path also covers everything below it.
- `surface_velocity`: velocity in m/s, in the prim's local frame.
- `measure`: `height`, `clearance` (bottom of `underside` above `floor_level_m`, so legs don't count), `gap` (needs `between: [a, b]`).
- `marker`: for a feature that isn't its own prim (a floor transition line, a keep-out area). Creates an invisible guide box under `/Annotations`, in meters.
- `attributes`: any extra labels from the taxonomy, e.g. `{"material": "wood"}`. Written as `annotation:<name>`.

## Limits

- Colliders that already exist are kept, not validated: their shapes are the scene author's choice.
- The surface velocity attributes (`PhysxSurfaceVelocityAPI`) are written by hand, so the scripts don't need the PhysX schema package.
- Custom USD attributes don't survive a plain glTF export. For a glTF deliverable, the `annotation:*` values would need to be copied into each node's glTF `extras`. That isn't implemented here.

## Credits

Warehouse and conveyor assets: NVIDIA Isaac Sim, CC BY 4.0. Everything in this repository was written for this project.
