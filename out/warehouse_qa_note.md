# QA note: out/warehouse_annotated.usda

## Core layer
- Geometry prims: 3809
- Collision attribute set: 3809/3809 (3604 collidable, 205 not collidable)
- Colliders: 3658 kept from the scene, 1 added, 150 set not collidable
- Room/zone labels: conveyor_cell (11), open_floor (193), storage (2914)
- Object classes: barrel (37), beam (99), bottle (120), box (1841), bucket (1), cable (17), ceiling (72), conveyor (1), crate (51), electrical_box (2), fire_extinguisher (7), floor (55), floor_marking (72), forklift (2), label (20), lamp (30), pallet (158), paper (13), pillar (36), pushcart (1), rack (174), rack_label (195), rack_parts (7), sign (31), traffic_cone (6), wall (91), wet_floor_sign (2)
- Floor surfaces: hard_glossy (54)
- Moving surfaces: 5

## Failure-case categories
1. moving_surfaces: present (5)
2. keep_out_zones: present (18)
3. low_clearance: present (37)
4. small_obstacles: present (35)
5. reflective_transparent: present (1)
6. aisles: present (6)
7. ramps_dock_plates: absent

## Measurements (read from geometry)
- /Root/SM_RackShelf_135: clearance_m = 0.955
- /Root/SM_RackShelf_138: clearance_m = 0.955
- /Root/SM_RackShelf_141: clearance_m = 0.955
- /Root/SM_RackShelf_144: clearance_m = 0.955
- /Root/SM_EmergencyBoardFull_5: clearance_m = 0.915
- /Root/SM_RackShelf_156: clearance_m = 0.955
- /Root/SM_RackShelf_159: clearance_m = 0.955
- /Root/SM_RackShelf_162: clearance_m = 0.955
- /Root/SM_RackShelf_165: clearance_m = 0.955
- /Root/SM_FireExtinguisher_18: clearance_m = 0.938
- /Root/SM_CardBoxA_02_2: height_m = 0.636
- /Root/SM_CardBoxA_3: height_m = 0.503
- /Root/SM_CardBoxD_04_6: height_m = 0.149
- /Root/SM_CardBoxD_03_9: height_m = 0.266
- /Root/SM_CardBoxD_4: height_m = 0.266
- /Root/SM_CratePlasticNote_B_03_18: height_m = 0.136
- /Root/SM_CratePlasticNote_B_5: height_m = 0.136
- /Root/SM_PushcartA_02_22: height_m = 0.377
- /Root/SM_BarelPlastic_C_01_25: height_m = 0.421
- /Root/SM_BarelPlastic_C_2: height_m = 0.421
- /Root/SM_CardBoxB_02_32: height_m = 0.500
- /Root/SM_BottlePlasticD_01_35: height_m = 0.061
- /Root/SM_BottlePlasticD_2: height_m = 0.061
- /Root/SM_BottlePlasticD_3: height_m = 0.061
- /Root/SM_BottlePlasticD_4: height_m = 0.061
- /Root/SM_CratePlastic_E_03_44: height_m = 0.080
- /Root/SM_CratePlastic_D_01_47: height_m = 0.263
- /Root/SM_PaperNote_Small_15: height_m = 0.019
- /Root/SM_PaperNote_Small_06_54: height_m = 0.023
- /Root/SM_PaperNote_Small_20: height_m = 0.017
- /Root/SM_PaperNote_Small_16: height_m = 0.019
- /Root/SM_PaperNote_Small_13: height_m = 0.019
- /Root/SM_PaperNote_Small_17: height_m = 0.019
- /Root/SM_PaperNote_Small_18: height_m = 0.019
- /Root/SM_PaperNote_Small_09_72: height_m = 0.000
- /Root/SM_PaperNote_Small_08_75: height_m = 0.000
- /Root/SM_CardBoxB_3: height_m = 0.500
- /Root/S_TrafficCone_2: height_m = 0.463
- /Root/S_TrafficCone2: height_m = 0.463
- /Root/S_TrafficCone3: height_m = 0.463
- /Root/S_TrafficCone4: height_m = 0.463
- /Root/S_TrafficCone5: height_m = 0.463
- /Root/S_TrafficCone6: height_m = 0.463
- /Root/S_WetFloorSign_2: height_m = 0.644
- /Root/S_WetFloorSign2: height_m = 0.644
- /Root/SM_RackShelf_1061: clearance_m = 0.955
- /Root/SM_RackShelf_1066: clearance_m = 0.955
- /Root/SM_RackShelf_1071: clearance_m = 0.955
- /Root/SM_RackShelf_179: clearance_m = 0.955
- /Root/SM_FireExtinguisher_20: clearance_m = 1.125
- /Root/SM_FireExtinguisher_1925: clearance_m = 0.938
- /Root/SM_FireExtinguisher_1929: clearance_m = 0.938
- /Root/SM_FireExtinguisher_1931: clearance_m = 1.125
- /Root/SM_FireExtinguisher_24: clearance_m = 1.125
- /Root/SM_RackShelf_2966: clearance_m = 0.955
- /Root/SM_RackShelf_2970: clearance_m = 0.955
- /Root/SM_RackShelf_2975: clearance_m = 0.955
- /Root/SM_RackShelf_2980: clearance_m = 0.955
- /Root/SM_RackShelf_3822: clearance_m = 0.955
- /Root/SM_RackShelf_3827: clearance_m = 0.955
- /Root/SM_RackShelf_3832: clearance_m = 0.955
- /Root/SM_RackShelf_3837: clearance_m = 0.955
- /Root/SM_RackShelf_4470: clearance_m = 0.955
- /Root/SM_RackShelf_4475: clearance_m = 0.955
- /Root/SM_RackShelf_4480: clearance_m = 0.955
- /Root/SM_RackShelf_4485: clearance_m = 0.955
- /Root/SM_RackShelf_221: clearance_m = 0.955
- /Root/SM_RackShelf_224: clearance_m = 0.955
- /Root/SM_RackShelf_227: clearance_m = 0.955
- /Root/SM_RackShelf_230: clearance_m = 0.955
- /Root/SM_FireExtinguisher_330: clearance_m = 0.938
- /Root/ConveyorLine: clearance_m = 0.589
- /Annotations/Aisle_1: gap_width_m = 3.688
- /Annotations/Aisle_2: gap_width_m = 3.732
- /Annotations/Aisle_3: gap_width_m = 3.791
- /Annotations/Aisle_4: gap_width_m = 3.594
- /Annotations/Aisle_5: gap_width_m = 3.745
- /Annotations/Aisle_6: gap_width_m = 3.710

## Surface velocity
- /Root/ConveyorLine/Section_01/Conveyor/Rollers: (0.3, 0.0, 0.0) (local, stage units/s)
- /Root/ConveyorLine/Section_02/Conveyor/Rollers: (0.3, 0.0, 0.0) (local, stage units/s)
- /Root/ConveyorLine/Section_03/Conveyor/Rollers: (0.3, 0.0, 0.0) (local, stage units/s)
- /Root/ConveyorLine/Section_04/Conveyor/Rollers: (0.3, 0.0, 0.0) (local, stage units/s)
- /Root/ConveyorLine/Section_05/Conveyor/Rollers: (0.3, 0.0, 0.0) (local, stage units/s)

## Geometry without a class label
- 0 of 3809 geometry prims

## Geometry with more than one class (merged by Isaac Sim)
- 0 of 3809 geometry prims

## Scene's own class labels set to the config's class
- barcode -> label (20)
- barel -> barrel (37)
- bracket -> beam (59)
- cart -> pushcart (1)
- cone -> traffic_cone (6)
- emergency_board -> sign (3)
- floor_decal -> floor_marking (72)
- fuse_box -> electrical_box (2)
- paper_note -> paper (12)
- paper_shortcut -> paper (1)
- rack -> rack_parts (8)
- sign -> rack_label (195)
- sign -> wet_floor_sign (4)
- wire -> cable (17)

## Isaac Sim check (manual)
- [x] Annotated USD opens in Isaac Sim
- [x] Room/zone labels visible in the semantics editor
- [x] Class labels correct in a semantic segmentation render
- [x] Colliders visible with physics debug visualization
- [x] A box dropped on each conveyor moves along it after Play

Ticked by hand after checking in Isaac Sim 6.2 (2026-10-25); qa_check.py writes them unticked.

Automated checks: PASS
