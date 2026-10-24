"""
Build a small two-room apartment in USD (Z-up, meters) to test the pipeline
without any downloaded asset.

Usage:
    python make_test_room.py test_scene/apartment.usda
"""
import os
import sys

from pxr import Gf, Usd, UsdGeom


def box(stage, path, center, size):
    """Axis-aligned box mesh. center/size in meters."""
    cx, cy, cz = center
    sx, sy, sz = (s / 2 for s in size)
    pts = [Gf.Vec3f(cx + x * sx, cy + y * sy, cz + z * sz)
           for x, y, z in [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                           (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]]
    m = UsdGeom.Mesh.Define(stage, path)
    m.CreatePointsAttr(pts)
    m.CreateFaceVertexCountsAttr([4] * 6)
    m.CreateFaceVertexIndicesAttr([0, 3, 2, 1, 4, 5, 6, 7, 0, 1, 5, 4,
                                   1, 2, 6, 5, 2, 3, 7, 6, 3, 0, 4, 7])
    m.CreateExtentAttr([pts[0], pts[6]])
    return m


def main(out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    s = Usd.Stage.CreateNew(out)
    UsdGeom.SetStageUpAxis(s, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(s, 1.0)
    root = UsdGeom.Xform.Define(s, "/Apartment")
    s.SetDefaultPrim(root.GetPrim())

    # living room: x in [0, 5], bedroom: x in [5.1, 9], y in [0, 4]
    L, B = "/Apartment/LivingRoom", "/Apartment/Bedroom"
    UsdGeom.Xform.Define(s, L)
    UsdGeom.Xform.Define(s, B)
    box(s, f"{L}/Floor", (2.5, 2, -0.01), (5, 4, 0.02))
    box(s, f"{B}/Floor", (7.05, 2, -0.01), (3.9, 4, 0.02))

    # walls, with a 0.9 m door between the rooms
    box(s, "/Apartment/Walls/Outer_S", (4.5, -0.05, 1.25), (9.2, 0.1, 2.5))
    box(s, "/Apartment/Walls/Outer_N", (4.5, 4.05, 1.25), (9.2, 0.1, 2.5))
    box(s, "/Apartment/Walls/Outer_W", (-0.05, 2, 1.25), (0.1, 4, 2.5))
    box(s, "/Apartment/Walls/Outer_E", (9.05, 2, 1.25), (0.1, 4, 2.5))
    box(s, "/Apartment/Walls/Divider_S", (5.05, 0.8, 1.25), (0.1, 1.6, 2.5))
    box(s, "/Apartment/Walls/Divider_N", (5.05, 3.25, 1.25), (0.1, 1.5, 2.5))

    # door threshold strip, 2 cm high
    box(s, "/Apartment/Doorway/Threshold", (5.05, 2.05, 0.01), (0.1, 0.9, 0.02))

    # living room: rug, table with legs, two chairs, a cable on the floor
    box(s, f"{L}/Rug", (2.0, 2.0, 0.006), (2.0, 1.4, 0.012))
    t = f"{L}/Table"
    UsdGeom.Xform.Define(s, t)
    box(s, f"{t}/Top", (2.0, 2.0, 0.73), (1.2, 0.8, 0.04))
    for i, (x, y) in enumerate([(1.45, 1.65), (2.55, 1.65), (1.45, 2.35), (2.55, 2.35)]):
        box(s, f"{t}/Leg_{i}", (x, y, 0.355), (0.05, 0.05, 0.71))
    box(s, f"{L}/Chair_A", (1.0, 2.0, 0.45), (0.45, 0.45, 0.9))
    box(s, f"{L}/Chair_B", (2.0, 1.15, 0.45), (0.45, 0.45, 0.9))
    box(s, f"{L}/Cable", (3.8, 0.6, 0.004), (1.2, 0.008, 0.008))
    box(s, f"{L}/Vent", (4.6, 3.9, 0.01), (0.3, 0.1, 0.02))

    # bedroom: bed on legs, wall mirror
    b = f"{B}/Bed"
    UsdGeom.Xform.Define(s, b)
    box(s, f"{b}/Frame", (7.5, 2.0, 0.3), (1.6, 2.0, 0.3))
    for i, (x, y) in enumerate([(6.75, 1.05), (8.25, 1.05), (6.75, 2.95), (8.25, 2.95)]):
        box(s, f"{b}/Leg_{i}", (x, y, 0.075), (0.06, 0.06, 0.15))
    box(s, f"{B}/Mirror", (8.97, 0.8, 1.4), (0.02, 0.6, 1.2))

    s.Save()
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "test_scene/apartment.usda")
