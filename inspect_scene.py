"""
Print a scene's prim tree with types and sizes (meters), to write the config.

Usage:
    python inspect_scene.py scene.usd [--depth 4] [--filter Chair]
"""
import argparse

from pxr import Usd, UsdGeom


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--filter", default="", help="only show paths containing this text")
    args = ap.parse_args()

    stage = Usd.Stage.Open(args.scene)
    mpu = UsdGeom.GetStageMetersPerUnit(stage) or 1.0
    up = UsdGeom.GetStageUpAxis(stage)
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                              [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
    print(f"up axis {up}, metersPerUnit {mpu}, default prim "
          f"{stage.GetDefaultPrim().GetPath() if stage.GetDefaultPrim() else '-'}\n")

    for prim in stage.Traverse(Usd.TraverseInstanceProxies()):
        path = str(prim.GetPath())
        depth = path.count("/")
        if depth > args.depth or args.filter.lower() not in path.lower():
            continue
        size = ""
        if prim.IsA(UsdGeom.Imageable):
            r = cache.ComputeWorldBound(prim).ComputeAlignedRange()
            if not r.IsEmpty():
                s = r.GetSize() * mpu
                lo = r.GetMin() * mpu
                size = (f"  size {s[0]:.2f} x {s[1]:.2f} x {s[2]:.2f} m"
                        f"  min ({lo[0]:.2f}, {lo[1]:.2f}, {lo[2]:.2f})")
        inst = " [instance]" if prim.IsInstance() else ""
        print(f"{'  ' * (depth - 1)}{prim.GetName()}  <{prim.GetTypeName()}>{inst}{size}"
              f"   {path}")


if __name__ == "__main__":
    main()
