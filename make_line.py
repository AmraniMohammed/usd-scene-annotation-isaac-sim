"""
Place a straight conveyor line in an environment, as a small USD file that
references both. Neither source file is modified or copied.

Sections are laid end to end along the conveyor's own X axis, starting at
--start (meters, floor plane) and turned by --yaw degrees around the up axis.

Usage:
    python make_line.py warehouse.usd conveyor.usd -o scenes/warehouse_line.usda \
        --start 2.0 -4.0 --yaw 90 --count 3
"""
import argparse
import os

from pxr import Gf, Usd, UsdGeom


def rel(path, out):
    return os.path.relpath(os.path.abspath(path),
                           os.path.dirname(os.path.abspath(out))).replace(os.sep, "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("environment")
    ap.add_argument("conveyor")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--start", type=float, nargs=2, default=[0.0, 0.0], metavar=("X", "Y"))
    ap.add_argument("--yaw", type=float, default=0.0, help="degrees")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--name", default="ConveyorLine")
    args = ap.parse_args()

    env = Usd.Stage.Open(args.environment)
    conv = Usd.Stage.Open(args.conveyor)
    mpu = UsdGeom.GetStageMetersPerUnit(env) or 1.0
    up = UsdGeom.GetStageUpAxis(env)
    if UsdGeom.GetStageUpAxis(conv) != up:
        raise SystemExit(f"up axis differs: environment {up}, conveyor {UsdGeom.GetStageUpAxis(conv)}")
    scale = (UsdGeom.GetStageMetersPerUnit(conv) or 1.0) / mpu

    # section length along the conveyor's X axis, in environment units
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    size = cache.ComputeWorldBound(conv.GetDefaultPrim()).ComputeAlignedRange().GetSize()
    length = size[0] * scale

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    stage = Usd.Stage.CreateNew(args.out)
    stage.GetRootLayer().subLayerPaths.append(rel(args.environment, args.out))
    UsdGeom.SetStageUpAxis(stage, up)
    UsdGeom.SetStageMetersPerUnit(stage, mpu)
    root = env.GetDefaultPrim().GetPath()
    stage.SetDefaultPrim(stage.GetPrimAtPath(root))

    line = UsdGeom.Xform.Define(stage, root.AppendChild(args.name))
    x, y = (v / mpu for v in args.start)
    line.AddTranslateOp().Set(Gf.Vec3d(x, y, 0) if up == UsdGeom.Tokens.z else Gf.Vec3d(x, 0, y))
    if up == UsdGeom.Tokens.z:
        line.AddRotateZOp().Set(args.yaw)
    else:
        line.AddRotateYOp().Set(args.yaw)

    for i in range(args.count):
        sec = UsdGeom.Xform.Define(stage, line.GetPath().AppendChild(f"Section_{i + 1:02d}"))
        sec.AddTranslateOp().Set(Gf.Vec3d(i * length, 0, 0))
        if scale != 1.0:
            sec.AddScaleOp().Set(Gf.Vec3f(scale, scale, scale))
        # the asset keeps its own transform, so it goes one level down
        asset = UsdGeom.Xform.Define(stage, sec.GetPath().AppendChild("Conveyor"))
        asset.GetPrim().GetReferences().AddReference(rel(args.conveyor, args.out))

    stage.Save()
    print(f"wrote {args.out}: {args.count} x {length * mpu:.2f} m sections under {line.GetPath()}"
          f"/Section_NN/Conveyor")


if __name__ == "__main__":
    main()
