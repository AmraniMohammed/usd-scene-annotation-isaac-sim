# Warehouse config: values that depend on the use case

Values in `warehouse.json` that were chosen for this demo and would be confirmed with the client on a real project. Each row says what was chosen, why, and what would change it.

| Value | Chosen | Why | Would change if |
|---|---|---|---|
| Zone borders | `storage` from y = 8 (red markings at the rack row ends); `conveyor_cell` = the line plus about 2 m | Follows lines already painted on the floor | The site defines its zones differently (e.g. a separate loading area) |
| Class detail | 27 classes; cardboard and plastic boxes both `box`; `crate` separate | Enough for a demo without hand-checking every asset | The perception task needs finer classes (box material, pallet type) |
| Rack location labels | Own class `rack_label`, not `sign` | A system that reads rack locations must tell them apart from other signs | Nobody reads rack labels: merge into `sign` |
| Conveyor collision | Frame, stickers and drive bands not collidable; NVIDIA's simplified shapes kept | Avoids double colliders and boxes catching on bolts | A test needs exact contact with the frame |
| Conveyor direction | Section_01 to Section_05 (toward the racks) | Arbitrary for the demo | The real line's flow direction |
| Conveyor speed | 0.3 m/s | A typical real line speed | The site's line runs at another speed |
| Upper belt (1.74 m) | Not moving | Above the area the demo focuses on | It's a return line or part of the process |
| Forklift area | Keep-out zone: forklift footprint plus 1 m | Forklifts are the main danger for a robot (heavy, forks sticking out, driver may not see it). Parked here, but treated as if it moved | The site separates robot and forklift traffic in time or space, or the forklift is only a static prop |
| Painted red markings | All 16 (14 around rack-end guards, 1 striped area and 1 "KEEP CLEAR" by the west wall) are keep-out zones | Real warehouses paint these to keep spots clear; robots shouldn't stop or drive on them | The site uses red paint for something else, or robots may cross them |
| Robot height (low clearance) | Not set: free heights are measured, not judged | A spot is only dangerous for robots taller than its free height | The client's robot height is known: compare it with the measured `clearance_m` values |
| Free height under the conveyor | Measured to the bottom of NVIDIA's collision side wall (about 0.59 m), not to the rollers (0.71 m) | The side rails hang below the rollers; the collision wall is what a robot hits in simulation | - |
| Lowest rack shelves | The 28 bottom shelves (4 per row) | Empty rack bays look free to a 2D lidar; a taller robot hits the shelf beam | Robots never enter rack bays (then it's a keep-out case instead) |
| Wall-mounted items | 7 fire extinguishers and 1 emergency board, labeled as protrusions | They stick out about 0.18 m above lidar height; a robot following the wall can hit them | - |
| Lidar scan height (small obstacles) | Not set: obstacle heights are measured, not judged | Which obstacles a 2D lidar misses depends on its mounting height (often 0.2-0.4 m) | The client's sensor setup is known: compare it with the measured `height_m` values |
| Floor clutter | 35 loose objects in the cluttered aisle (cones, signs, flat bottles, boxes, crates, barrels, pushcart, papers) | Loose floor objects are a common cause of robot failures | - |
| Objects on the pushcart | Not labeled separately (one box, one plastic bin) | They move with the cart | Items on carts are tested on their own |
| Papers on the floor | Labeled as `flat_debris`: a camera case (false stops), not a collision case | Robots drive over them; vision systems may stop for them | The robot has no camera-based obstacle detection |
| Wet-floor area | Marker over the aisle area bounded by the wet-floor signs and cones (3.4 x 6.4 m) | The signs and cones say the floor is wet there | The client defines spill areas differently |
| Known limit: wet floor not simulated | The marker is a label only: no puddle is rendered and floor grip is unchanged | Changing grip would need a physics material on that area, not built here | A test needs the robot to actually slip or brake longer |
| Floor surface | All floor tiles recorded as `hard_glossy` (a surface type, not a failure case) | The floor reflects ceiling lights everywhere, which affects cameras; marking the whole floor as a failure case would tell a test nothing | The site's floor is matte |
| Robot and forklift width (aisles) | Not set: aisle widths are measured, not judged | Whether a robot can enter, or pass a forklift, depends on their widths plus safety gaps | The client's vehicle widths are known: compare them with the measured `gap_width_m` values |
| Aisle clear width | The narrowest gap between objects facing each other from the two rack rows, counting objects below 2 m (3.59-3.79 m), not the rack frame spacing (3.95 m) | Pallets, boxes sticking out and rack-end guards are what limit a robot | Robots are taller than 2 m, or the client wants the width at a specific height |
| Known limit: aisle width is fixed to one pair | Each aisle's width is measured between the pair that was narrowest when the config was written | If pallets or boxes are moved, another spot may become narrowest; the config would need updating | The scene changes (re-run the narrowest-point check) |
| Known limit: conveyor floor bar | The 6.8 cm bar along the floor under the conveyor has no collider (NVIDIA's simplified shapes don't include it, and the detailed frame is not collidable) | Robots shouldn't be under the line: the keep-out zone covers it | A test drives robots under the line: the bar needs its own collider |
| Conveyor keep-out margin | 0.5 m on every side | Covers robot position error, boxes overhanging and stopping distance; about 0.5 m is the clearance common AGV/AMR standards ask for (check exact wording before quoting) | People work at the line (about 1.0 m), or a robot must load or unload it (no keep-out at the loading end) |
