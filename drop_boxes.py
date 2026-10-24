"""
Drop demo for the warehouse conveyor: places cardboard boxes above the
rollers so they fall, land and ride the line when the simulation plays.

Run it inside Isaac Sim (Window > Script Editor) with the annotated
warehouse open, then press Play. Running it again replaces the boxes.

The boxes are written to the open file's own layer: in Isaac Sim 6.2,
boxes in the session layer were simulated (their velocity matched the
rollers) but the viewport didn't show them moving. Don't save the stage
afterwards, or the boxes end up in the annotation layer (re-running
annotate.py regenerates it clean).

The box models are NVIDIA's (from the collected warehouse's Props folder),
found through the warehouse layer the stage already loads.
"""
import os

import omni.usd
from pxr import Gf, Usd, UsdGeom, UsdPhysics

ROOT = "/Root/DemoBoxes"
MODELS = ["SM_CardBoxD_03", "SM_CardBoxC_01", "SM_CardBoxD_01",
          "SM_CardBoxB_01", "SM_CardBoxC_02", "SM_CardBoxD_02"]
LINE_X = -11.0       # center of the rollers (m)
FIRST_Y = -11.5      # above Section_01 (m)
SPACING_Y = 0.8      # along the line, so each box lands on free rollers
# Box bottoms (the models' origin). They must start in the gap between the
# rollers (top at about 0.77 m) and the upper belt (underside at about
# 1.59 m): the tallest box (0.50 m) tops out at 1.51 m.
FIRST_Z = 0.95
STEP_Z = 0.02
YAWS = [0, 8, -6, 12, -10, 4]
MASS_KG = 5.0

stage = omni.usd.get_context().get_stage()
warehouse = next(l for l in stage.GetUsedLayers() if l.identifier.endswith("full_warehouse.usd"))
props = os.path.join(os.path.dirname(warehouse.realPath), "Props")

# remove boxes from earlier runs, including older ones in the session layer
for layer in (stage.GetSessionLayer(), stage.GetRootLayer()):
    if layer.GetPrimAtPath(ROOT):
        with Usd.EditContext(stage, layer):
            stage.RemovePrim(ROOT)

with Usd.EditContext(stage, stage.GetRootLayer()):
    UsdGeom.Xform.Define(stage, ROOT)
    for i, model in enumerate(MODELS):
        box = UsdGeom.Xform.Define(stage, f"{ROOT}/Box_{i + 1:02d}")
        box.GetPrim().GetReferences().AddReference(os.path.join(props, model + ".usd").replace("\\", "/"))
        xf = UsdGeom.XformCommonAPI(box)
        xf.SetTranslate(Gf.Vec3d(LINE_X, FIRST_Y + i * SPACING_Y, FIRST_Z + i * STEP_Z))
        xf.SetRotate(Gf.Vec3f(0, 0, YAWS[i]))

        prim = box.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(MASS_KG)
        for p in Usd.PrimRange(prim):
            if p.IsA(UsdGeom.Mesh) and p.HasAPI(UsdPhysics.CollisionAPI):
                # a moving body needs a convex shape, not the triangle mesh
                UsdPhysics.MeshCollisionAPI.Apply(p).CreateApproximationAttr("convexHull")

print(f"{len(MODELS)} boxes under {ROOT}, models from {props}")
print("Don't save the stage: the boxes are in the annotation layer.")
