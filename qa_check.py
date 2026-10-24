"""
Check an annotated scene and write the per-scene QA note.

Usage:
    python qa_check.py out/scene_annotated.usda [-o out/scene_qa_note.md]
Exit code 1 if a check fails.
"""
import argparse
import math
import sys
from collections import Counter

from pxr import Usd, UsdGeom, UsdPhysics

from annotate import DEFAULT_CATEGORIES


def label(prim, taxonomy):
    for attr in (f"semantics:labels:{taxonomy}",
                 f"semantic:Semantics_{taxonomy}:params:semanticData"):
        a = prim.GetAttribute(attr)
        if a and a.HasAuthoredValue():
            v = a.Get()
            if isinstance(v, str):
                return v
            return v[0] if len(v) else None
    return None


def inherited_class(prim, cache):
    """Class label on the prim or its nearest labeled ancestor."""
    path = prim.GetPath()
    if path not in cache:
        own = label(prim, "class")
        parent = prim.GetParent()
        cache[path] = own or (inherited_class(parent, cache) if parent and not parent.IsPseudoRoot() else None)
    return cache[path]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args()

    stage = Usd.Stage.Open(args.scene)
    info = stage.GetRootLayer().customLayerData
    categories = list(info.get("annotation_categories", DEFAULT_CATEGORIES))

    geom = with_api = enabled = 0
    missing = []
    rooms = Counter()
    classes = Counter()
    class_cache, unclassified = {}, []
    cats = Counter()
    measures, bad_measures = [], []
    surfaces = Counter()
    moving, moving_errors = [], []

    for prim in stage.Traverse():
        path = str(prim.GetPath())
        room = label(prim, "room")
        if room:
            rooms[room] += 1
        cls = label(prim, "class")
        if cls:
            classes[cls] += 1
        a = prim.GetAttribute("annotation:category")
        if a and a.HasAuthoredValue():
            cats[a.Get()] += 1
            for m in ("height_m", "clearance_m", "gap_width_m"):
                v = prim.GetAttribute(f"annotation:{m}")
                if v and v.HasAuthoredValue():
                    measures.append(f"{path}: {m} = {v.Get():.3f}")
                    if not (math.isfinite(v.Get()) and abs(v.Get()) < 1000):
                        bad_measures.append(f"Invalid measurement: {path}: {m} = {v.Get()}")
        s = prim.GetAttribute("annotation:surface")
        if s and s.HasAuthoredValue():
            surfaces[s.Get()] += 1
        # read the attribute, not GetAppliedSchemas(): without the PhysX
        # plugin loaded, USD drops the unknown schema name from that list
        sv = prim.GetAttribute("physxSurfaceVelocity:surfaceVelocity")
        if sv and sv.HasAuthoredValue():
            v = sv.Get()
            moving.append(f"{path}: {tuple(round(x, 3) for x in v)} (local, stage units/s)")
            body = UsdPhysics.RigidBodyAPI(prim)
            if not (prim.HasAPI(UsdPhysics.RigidBodyAPI) and body.GetKinematicEnabledAttr().Get()):
                moving_errors.append(f"{path}: not a kinematic rigid body")
        if prim.IsA(UsdGeom.Gprim) and not path.startswith("/Annotations"):
            geom += 1
            if not inherited_class(prim, class_cache):
                unclassified.append(path)
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                with_api += 1
                if UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get():
                    enabled += 1
            else:
                missing.append(path)

    ok = (with_api == geom and geom > 0 and len(rooms) > 0
          and not moving_errors and not bad_measures)
    lines = [
        f"# QA note: {args.scene}",
        "",
        "## Core layer",
        f"- Geometry prims: {geom}",
        f"- Collision attribute set: {with_api}/{geom} "
        f"({enabled} collidable, {with_api - enabled} not collidable)",
    ]
    if "annotation_collision_kept" in info:
        lines.append(f"- Colliders: {info['annotation_collision_kept']} kept from the scene, "
                     f"{info['annotation_collision_added']} added, "
                     f"{info['annotation_collision_disabled']} set not collidable")
    lines += [
        f"- Room/zone labels: {', '.join(f'{r} ({n})' for r, n in sorted(rooms.items())) or 'NONE'}",
        f"- Object classes: {', '.join(f'{c} ({n})' for c, n in sorted(classes.items())) or 'none labeled'}",
        f"- Floor surfaces: {', '.join(f'{s} ({n})' for s, n in surfaces.items()) or 'none labeled'}",
        f"- Moving surfaces: {len(moving) or 'none'}",
        "",
        "## Failure-case categories",
    ]
    for i, c in enumerate(categories, 1):
        lines.append(f"{i}. {c}: {'present (' + str(cats[c]) + ')' if cats[c] else 'absent'}")
    if measures:
        lines += ["", "## Measurements (read from geometry)"] + [f"- {m}" for m in measures]
    if moving:
        lines += ["", "## Surface velocity"] + [f"- {m}" for m in moving]
    if classes:
        lines += ["", "## Geometry without a class label",
                  f"- {len(unclassified)} of {geom} geometry prims"]
        lines += [f"- {p}" for p in unclassified[:20]]
        if len(unclassified) > 20:
            lines.append(f"- ... and {len(unclassified) - 20} more")
    lines += [
        "",
        "## Isaac Sim check (manual)",
        "- [ ] Annotated USD opens in Isaac Sim",
        "- [ ] Room/zone labels visible in the semantics editor",
        "- [ ] Class labels correct in a semantic segmentation render",
        "- [ ] Colliders visible with physics debug visualization",
    ]
    if moving:
        lines.append("- [ ] A box dropped on each conveyor moves along it after Play")
    lines += ["", f"Automated checks: {'PASS' if ok else 'FAIL'}"]
    if missing:
        lines.append(f"Geometry without collision attribute: {missing[:10]}")
    lines += moving_errors + bad_measures

    note = "\n".join(lines)
    print(note)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(note + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
