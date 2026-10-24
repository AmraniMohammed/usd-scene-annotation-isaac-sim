"""
Print a scene's prim tree with types and sizes (meters), to write the config.

Usage:
    python inspect_scene.py scene.usd [--depth 4] [--filter Chair]
    python inspect_scene.py scene.usd --summary [--root /Root]

--summary groups the children of the root by name, trailing numbers removed
(Box_12, Box_340 -> Box), with count, size range, bottom height range and how
many stand on the floor: an overview of what a large flat scene contains.
"""
import argparse
import re
from collections import defaultdict

from pxr import Usd, UsdGeom


def summary(stage, root, cache, mpu, up):
    groups = defaultdict(list)
    for c in stage.GetPrimAtPath(root).GetChildren():
        r = cache.ComputeWorldBound(c).ComputeAlignedRange()
        groups[re.sub(r"(_?\d+)+$", "", c.GetName())].append((c, None if r.IsEmpty() else r))

    print(f"{len(groups)} name groups, {sum(len(v) for v in groups.values())} prims under {root}\n")
    print(f"{'name':32s} {'count':>5s}  {'type':12s} {'size min .. max (m)':34s} "
          f"{'bottom (m)':14s} {'on floor':>8s}  example")
    for name, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        t, example = items[0][0].GetTypeName(), items[0][0].GetPath()
        rs = [r for _, r in items if r]
        if not rs:
            print(f"{name:32s} {len(items):5d}  {t:12s} {'(no geometry)':34s} {'':14s} {'':8s}  {example}")
            continue
        sizes = [r.GetSize() * mpu for r in rs]
        bottoms = [r.GetMin()[up] * mpu for r in rs]
        lo = "x".join(f"{min(s[i] for s in sizes):.2f}" for i in range(3))
        hi = "x".join(f"{max(s[i] for s in sizes):.2f}" for i in range(3))
        on_floor = sum(b < 0.05 for b in bottoms)
        print(f"{name:32s} {len(items):5d}  {t:12s} {lo + ' .. ' + hi:34s} "
              f"{min(bottoms):5.2f} .. {max(bottoms):5.2f} {on_floor:8d}  {example}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--filter", default="", help="only show paths containing this text")
    ap.add_argument("--summary", action="store_true", help="group the root's children by name")
    ap.add_argument("--root", default=None, help="for --summary (default: the default prim)")
    args = ap.parse_args()

    stage = Usd.Stage.Open(args.scene)
    mpu = UsdGeom.GetStageMetersPerUnit(stage) or 1.0
    up = UsdGeom.GetStageUpAxis(stage)
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(),
                              [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
    print(f"up axis {up}, metersPerUnit {mpu}, default prim "
          f"{stage.GetDefaultPrim().GetPath() if stage.GetDefaultPrim() else '-'}\n")

    if args.summary:
        root = args.root or str(stage.GetDefaultPrim().GetPath())
        summary(stage, root, cache, mpu, 2 if up == UsdGeom.Tokens.z else 1)
        return

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
