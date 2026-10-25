# QA note: out/apartment_annotated_flat.usda

## Core layer
- Geometry prims: 25
- Collision attribute set: 25/25 (24 collidable, 1 not collidable)
- Colliders: 0 kept from the scene, 24 added, 1 set not collidable
- Room/zone labels: bedroom (1), living_room (1)
- Object classes: bed (1), cable (1), chair (2), floor (2), floor_vent (1), mirror (1), rug (1), table (1), threshold (1), wall (1)
- Floor surfaces: hard (1), rug (1), carpet (1)
- Moving surfaces: none

## Failure-case categories
1. thresholds: present (2)
2. stairs_cliffs: absent
3. low_clearance: present (2)
4. small_obstacles: present (1)
5. rugs_carpets: present (1)
6. floor_bumps: present (1)
7. reflective_transparent: present (1)
8. narrow_passages: present (1)

## Measurements (read from geometry)
- /Apartment/LivingRoom/Rug: height_m = 0.012
- /Apartment/LivingRoom/Table: clearance_m = 0.710
- /Apartment/LivingRoom/Chair_A: gap_width_m = 0.175
- /Apartment/LivingRoom/Cable: height_m = 0.008
- /Apartment/LivingRoom/Vent: height_m = 0.020
- /Apartment/Bedroom/Bed: clearance_m = 0.150
- /Apartment/Doorway/Threshold: height_m = 0.020

## Geometry without a class label
- 0 of 25 geometry prims

## Geometry with more than one class (merged by Isaac Sim)
- 0 of 25 geometry prims

## Isaac Sim check (manual)
- [x] Annotated USD opens in Isaac Sim
- [x] Room/zone labels visible in the semantics editor
- [x] Class labels correct in a semantic segmentation render
- [x] Colliders visible with physics debug visualization

Ticked by hand after checking in Isaac Sim 6.2 (2026-10-25); qa_check.py writes them unticked.

Automated checks: PASS
