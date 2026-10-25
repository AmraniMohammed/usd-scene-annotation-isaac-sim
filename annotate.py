"""
Annotate a USD scene for NVIDIA Isaac Sim: room or zone labels, object
classes, collidable attributes, floor surface types, failure-case labels and
conveyor surface velocity, driven by a JSON config.

The original scene is never modified. Annotations are written to a separate
layer that sublayers the original, and can also be flattened into one file.

Usage:
    python annotate.py scene.usd config.json -o out/scene_annotated.usda --flatten
"""
import argparse
import fnmatch
import json
import os

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, Vt

try:
    from pxr import UsdSemantics  # OpenUSD 24.08+ / Isaac Sim 4.5+
except ImportError:
    UsdSemantics = None

# Residential robot failure cases. A config can replace this list with
# "categories" (e.g. an industrial taxonomy).
DEFAULT_CATEGORIES = [
    "thresholds",
    "stairs_cliffs",
    "low_clearance",
    "small_obstacles",
    "rugs_carpets",
    "floor_bumps",
    "reflective_transparent",
    "narrow_passages",
]


# ---------------------------------------------------------------- labels ----

def add_label(prim, taxonomy, value, schema):
    """Semantic label readable by Isaac Sim.

    schema = "labels": UsdSemantics.LabelsAPI (recent Isaac Sim)
    schema = "legacy": old Semantics.SemanticsAPI attributes
    """
    if schema == "labels":
        if UsdSemantics is not None:
            api = UsdSemantics.LabelsAPI.Apply(prim, taxonomy)
            api.CreateLabelsAttr([value])
        else:  # same result, written by hand
            prim.AddAppliedSchema(f"SemanticsLabelsAPI:{taxonomy}")
            prim.CreateAttribute(f"semantics:labels:{taxonomy}",
                                 Sdf.ValueTypeNames.TokenArray).Set([value])
    else:
        inst = f"Semantics_{taxonomy}"
        prim.AddAppliedSchema(f"SemanticsAPI:{inst}")
        prim.CreateAttribute(f"semantic:{inst}:params:semanticType",
                             Sdf.ValueTypeNames.Token).Set(taxonomy)
        prim.CreateAttribute(f"semantic:{inst}:params:semanticData",
                             Sdf.ValueTypeNames.String).Set(value)


def class_labels(prim):
    """Every class label on the prim, in either format, as (attribute, values).
    A scene can carry its own labels, under any instance name."""
    found = []
    for attr in prim.GetAttributes():
        name = attr.GetName()
        if name == "semantics:labels:class":
            found.append((attr, list(attr.Get() or [])))
        elif (name.startswith("semantic:") and name.endswith(":params:semanticType")
              and attr.Get() == "class"):
            data = prim.GetAttribute(name.replace(":semanticType", ":semanticData"))
            if data and data.Get():
                found.append((data, [data.Get()]))
    return found


def copy_timeline(src, dst):
    """Timeline range of the source root layer, or an open-ended default.

    Only the root layer's range counts, so a layer that sublayers or
    references a scene would otherwise leave Isaac Sim with no usable
    range (the timeline loops over one frame)."""
    usable = src.HasStartTimeCode() and src.HasEndTimeCode() and src.endTimeCode > src.startTimeCode
    dst.startTimeCode = src.startTimeCode if usable else 0
    dst.endTimeCode = src.endTimeCode if usable else 1000000
    dst.timeCodesPerSecond = src.timeCodesPerSecond if src.HasTimeCodesPerSecond() else 60


def set_annotation(prim, name, value):
    """Custom attribute in the annotation: namespace."""
    if isinstance(value, bool):
        t = Sdf.ValueTypeNames.Bool
    elif isinstance(value, (int, float)):
        t, value = Sdf.ValueTypeNames.Double, float(value)
    else:
        t, value = Sdf.ValueTypeNames.String, str(value)
    prim.CreateAttribute(f"annotation:{name}", t).Set(value)


# ----------------------------------------------------------- measurement ----

class Measurer:
    """Reads sizes from geometry bounding boxes, in meters."""

    def __init__(self, stage, floor_level_m=0.0):
        self.mpu = UsdGeom.GetStageMetersPerUnit(stage) or 1.0
        up = UsdGeom.GetStageUpAxis(stage)
        self.up = 2 if up == UsdGeom.Tokens.z else 1
        self.horiz = [a for a in range(3) if a != self.up]
        self.floor = floor_level_m
        self.cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render])
        # for prims that only hold stand-in geometry (e.g. collision shapes
        # tagged purpose "proxy")
        self.all_cache = UsdGeom.BBoxCache(
            Usd.TimeCode.Default(),
            [UsdGeom.Tokens.default_, UsdGeom.Tokens.render,
             UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide])
        self.stage = stage

    def box(self, path):
        prim = self.stage.GetPrimAtPath(path)
        if not prim.IsValid():
            raise ValueError(f"prim not found: {path}")
        r = self.cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if r.IsEmpty():
            r = self.all_cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if r.IsEmpty():
            raise ValueError(f"no geometry to measure: {path}")
        return r.GetMin() * self.mpu, r.GetMax() * self.mpu

    def bottom(self, path):
        return self.box(path)[0][self.up] - self.floor

    def height(self, path):
        lo, hi = self.box(path)
        return hi[self.up] - lo[self.up]

    def gap(self, a, b):
        """Shortest horizontal distance between two bounding boxes."""
        (alo, ahi), (blo, bhi) = self.box(a), self.box(b)
        d = [max(0.0, blo[i] - ahi[i], alo[i] - bhi[i]) for i in self.horiz]
        return (d[0] ** 2 + d[1] ** 2) ** 0.5

    def footprint_center(self, path):
        """Horizontal center of the bounding box, or None for empty prims."""
        r = self.cache.ComputeWorldBound(self.stage.GetPrimAtPath(path)).ComputeAlignedRange()
        if r.IsEmpty():
            return None
        c = r.GetMidpoint() * self.mpu
        return c[self.horiz[0]], c[self.horiz[1]]


# ---------------------------------------------------------------- passes ----

def matches(path, pattern):
    """True if path is pattern or below it. Patterns may use * and ?."""
    pattern = pattern.rstrip("/")
    if any(ch in pattern for ch in "*?["):
        return fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(path, pattern + "/*")
    return path == pattern or path.startswith(pattern + "/")


def find(stage, root, pattern):
    """Prims matching a path or a pattern (topmost matches only)."""
    if not any(ch in pattern for ch in "*?["):
        prim = stage.GetPrimAtPath(pattern)
        if not prim.IsValid():
            raise ValueError(f"prim not found: {pattern}")
        return [prim]
    found = []
    it = iter(Usd.PrimRange(stage.GetPrimAtPath(root)))
    for prim in it:
        if fnmatch.fnmatchcase(str(prim.GetPath()), pattern):
            found.append(prim)
            it.PruneChildren()
    if not found:
        raise ValueError(f"no prim matches: {pattern}")
    return found


def uninstance(stage, root):
    """Instanced geometry can't take per-prim attributes: make it editable."""
    while True:
        inst = [p for p in Usd.PrimRange(stage.GetPrimAtPath(root)) if p.IsInstance()]
        if not inst:
            return
        for p in inst:
            p.SetInstanceable(False)


def label_zones(stage, root, rooms, meas, schema):
    """Room/zone labels. Each entry is a prim path or pattern, or a floor
    rectangle {"box": [[xmin, ymin], [xmax, ymax]]} in meters: every child of
    the root whose footprint center lies inside gets the label."""
    counts = {}
    children = None
    for room, entries in rooms.items():
        targets = []
        for e in entries:
            if isinstance(e, str):
                targets += find(stage, root, e)
                continue
            (x0, y0), (x1, y1) = e["box"]
            if children is None:
                children = [(c, meas.footprint_center(str(c.GetPath())))
                            for c in stage.GetPrimAtPath(root).GetChildren()
                            if not str(c.GetPath()).startswith("/Annotations")]
            targets += [c for c, xy in children
                        if xy and x0 <= xy[0] <= x1 and y0 <= xy[1] <= y1]
        for prim in targets:
            add_label(prim, "room", room, schema)
            set_annotation(prim, "room", room)
        counts[room] = len(targets)
    return counts


def label_classes(stage, root, classes, schema):
    """Object class labels (pallet, box, chair...) for perception data.
    Each key is a prim path or pattern; the label covers everything below it.
    Rules apply in config order, so a later rule can override an earlier one."""
    counts, labeled = {}, {}
    for pattern, cls in classes.items():
        prims = find(stage, root, pattern)
        for prim in prims:
            add_label(prim, "class", cls, schema)
            labeled[str(prim.GetPath())] = cls
        counts[cls] = counts.get(cls, 0) + len(prims)
    return counts, labeled


def align_scene_classes(stage, labeled):
    """Class labels the scene already has below a labeled prim are set to the
    same value. Isaac Sim merges every class label on a prim and its
    ancestors, so NVIDIA's "barel" next to our "barrel" would become a
    class "barel,barrel". Returns {"old -> new": number of labels}."""
    changes = {}
    for path, cls in labeled.items():
        it = iter(Usd.PrimRange(stage.GetPrimAtPath(path)))
        for prim in it:
            p = str(prim.GetPath())
            if p != path and p in labeled:  # its own rule covers it
                it.PruneChildren()
                continue
            for attr, values in class_labels(prim):
                if values != [cls]:
                    key = f"{','.join(values)} -> {cls}"
                    changes[key] = changes.get(key, 0) + 1
                    attr.Set([cls] if attr.GetTypeName().isArray else cls)
    return changes


def apply_collision(stage, root, non_collidable):
    """Every geometry prim gets an explicit collision decision.

    Colliders the scene already has are kept as authored (shape and
    approximation). Geometry without one gets an exact triangle-mesh collider.
    Prims matching non_collidable get collisionEnabled = false: things a robot
    should drive over or ignore (a loose cable), or visual meshes whose
    collision comes from simpler proxy shapes."""
    n = {"kept": 0, "added": 0, "disabled": 0}
    for prim in Usd.PrimRange(stage.GetPrimAtPath(root)):
        if not prim.IsA(UsdGeom.Gprim):
            continue
        path = str(prim.GetPath())
        if path.startswith("/Annotations"):
            continue
        if any(matches(path, p) for p in non_collidable):
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(False)
            n["disabled"] += 1
        elif prim.HasAPI(UsdPhysics.CollisionAPI):
            n["kept"] += 1
        else:
            UsdPhysics.CollisionAPI.Apply(prim).CreateCollisionEnabledAttr(True)
            if prim.IsA(UsdGeom.Mesh):
                # static scene: exact triangle mesh collision
                UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr("none")
            n["added"] += 1
    return n


def apply_surface_velocity(stage, root, entries, mpu):
    """Conveyor belts and roller beds: a kinematic body whose surface moves.

    Each key is a prim path or pattern, each value a velocity in m/s in that
    prim's local frame. PhysX can't use triangle meshes on a moving body, so
    the colliders below it switch to convex hulls."""
    prims = []
    for pattern, vel in entries.items():
        for prim in find(stage, root, pattern):
            UsdPhysics.RigidBodyAPI.Apply(prim).CreateKinematicEnabledAttr(True)
            # PhysxSchema.PhysxSurfaceVelocityAPI, written by hand so plain
            # usd-core works too
            prim.AddAppliedSchema("PhysxSurfaceVelocityAPI")
            prim.CreateAttribute("physxSurfaceVelocity:surfaceVelocity",
                                 Sdf.ValueTypeNames.Vector3f).Set(Gf.Vec3f(*[v / mpu for v in vel]))
            prim.CreateAttribute("physxSurfaceVelocity:surfaceVelocityEnabled",
                                 Sdf.ValueTypeNames.Bool).Set(True)
            prim.CreateAttribute("physxSurfaceVelocity:surfaceVelocityLocalSpace",
                                 Sdf.ValueTypeNames.Bool).Set(True)
            for p in Usd.PrimRange(prim):
                if p.IsA(UsdGeom.Mesh) and p.HasAPI(UsdPhysics.CollisionAPI):
                    UsdPhysics.MeshCollisionAPI.Apply(p).CreateApproximationAttr("convexHull")
            set_annotation(prim, "surface_speed_mps", round(Gf.Vec3d(*vel).GetLength(), 4))
            prims.append(prim)
    return prims


def add_cameras(stage, cameras, mpu):
    """Fixed review viewpoints, so anyone opening the scene can return to the
    same views (viewport camera menu). Positions in meters, angles in degrees,
    lens values as Isaac Sim's viewport camera reports them."""
    for name, c in cameras.items():
        cam = UsdGeom.Camera.Define(stage, f"/Cameras/{name}")
        xf = UsdGeom.XformCommonAPI(cam)
        xf.SetTranslate(Gf.Vec3d(*[v / mpu for v in c["translate"]]))
        xf.SetRotate(Gf.Vec3f(*c["rotate_xyz"]), UsdGeom.XformCommonAPI.RotationOrderXYZ)
        cam.CreateFocalLengthAttr(c.get("focal_length", 18.147562))
        cam.CreateHorizontalApertureAttr(c.get("horizontal_aperture", 20.955))
        # USD's default near clip is 1 unit, which would hide nearby objects
        cam.CreateClippingRangeAttr(Gf.Vec2f(0.01 / mpu, 10000 / mpu))
    return list(cameras)


def add_marker(stage, name, center, size_m, mpu):
    """Invisible guide box for features that are not their own prim
    (a threshold strip, a cliff edge, a keep-out zone)."""
    path = f"/Annotations/{name}"
    cube = UsdGeom.Cube.Define(stage, path)
    cube.CreateSizeAttr(1.0)
    cube.CreatePurposeAttr(UsdGeom.Tokens.guide)
    xf = UsdGeom.XformCommonAPI(cube)
    xf.SetTranslate(Gf.Vec3d(*[c / mpu for c in center]))
    xf.SetScale(Gf.Vec3f(*[s / mpu for s in size_m]))
    return cube.GetPrim()


def apply_features(stage, cfg, root, categories, meas, schema):
    found = set()
    for i, f in enumerate(cfg.get("features", [])):
        cat = f["category"]
        if cat not in categories:
            raise ValueError(f"unknown category '{cat}', expected one of {categories}")

        if "marker" in f:
            m = f["marker"]
            prims = [add_marker(stage, m.get("name", f"{cat}_{i}"),
                                m["center"], m["size"], meas.mpu)]
        else:
            # paths or patterns: each match gets its own labels and measurements
            patterns = f["prim"] if isinstance(f["prim"], list) else [f["prim"]]
            prims = [p for pat in patterns for p in find(stage, root, pat)]

        for prim in prims:
            set_annotation(prim, "category", cat)
            set_annotation(prim, "type", f.get("type", cat))
            # own taxonomy, so the object's "class" label is left as it is
            add_label(prim, "failure_case", f.get("type", cat), schema)
            for k, v in f.get("attributes", {}).items():
                set_annotation(prim, k, v)

            # measurements read from geometry, never typed by hand
            path = str(prim.GetPath())
            for what in f.get("measure", []):
                if what == "height":
                    set_annotation(prim, "height_m", round(meas.height(path), 4))
                elif what == "clearance":
                    src = f.get("underside", path)  # e.g. the bed frame, not its legs
                    set_annotation(prim, "clearance_m", round(meas.bottom(src), 4))
                elif what == "gap":
                    a, b = f["between"]
                    set_annotation(prim, "gap_width_m", round(meas.gap(a, b), 4))
                    set_annotation(prim, "gap_between", f"{a} | {b}")
        found.add(cat)
    return found


# ------------------------------------------------------------------ main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("config")
    ap.add_argument("-o", "--out", required=True, help="annotation layer (.usda)")
    ap.add_argument("--flatten", action="store_true",
                    help="also write <out>_flat.usda, a single self-contained file")
    ap.add_argument("--schema", choices=["labels", "legacy"], default="labels",
                    help="semantic label format (match the client's worked example)")
    args = ap.parse_args()

    with open(args.config) as fh:
        cfg = json.load(fh)
    categories = cfg.get("categories", DEFAULT_CATEGORIES)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    stage = Usd.Stage.CreateNew(args.out)
    base = os.path.relpath(os.path.abspath(args.scene),
                           os.path.dirname(os.path.abspath(args.out)))
    stage.GetRootLayer().subLayerPaths.append(base.replace(os.sep, "/"))

    base_stage = Usd.Stage.Open(args.scene)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.GetStageUpAxis(base_stage))
    UsdGeom.SetStageMetersPerUnit(stage, UsdGeom.GetStageMetersPerUnit(base_stage))
    copy_timeline(base_stage.GetRootLayer(), stage.GetRootLayer())
    root = cfg.get("root") or str(base_stage.GetDefaultPrim().GetPath())
    if base_stage.GetDefaultPrim():
        stage.SetDefaultPrim(stage.GetPrimAtPath(root))

    uninstance(stage, root)
    meas = Measurer(stage, cfg.get("floor_level_m", 0.0))

    # 1. room / zone labels
    zones = label_zones(stage, root, cfg.get("rooms", {}), meas, args.schema)

    # 2. object classes
    classes, labeled = label_classes(stage, root, cfg.get("classes", {}), args.schema)
    relabeled = align_scene_classes(stage, labeled)

    # 3. floor surfaces (hard / carpet / rug)
    for p, surface in cfg.get("surfaces", {}).items():
        for prim in find(stage, root, p):
            set_annotation(prim, "surface", surface)

    # 4. failure cases (before collision, so markers exist and are skipped)
    found = apply_features(stage, cfg, root, categories, meas, args.schema)

    # 5. collidable attribute on every geometry prim
    col = apply_collision(stage, root, cfg.get("non_collidable", []))

    # 6. moving surfaces (after collision, so it can set their approximation)
    moving = apply_surface_velocity(stage, root, cfg.get("surface_velocity", {}), meas.mpu)

    # 7. review cameras
    cameras = add_cameras(stage, cfg.get("cameras", {}), meas.mpu)

    stage.GetRootLayer().customLayerData = {
        "annotation_categories": Vt.StringArray(categories),
        "annotation_categories_present": Vt.StringArray(sorted(found)),
        "annotation_categories_absent": Vt.StringArray(
            [c for c in categories if c not in found]),
        "annotation_collision_kept": col["kept"],
        "annotation_collision_added": col["added"],
        "annotation_collision_disabled": col["disabled"],
        "annotation_class_relabeled": Vt.StringArray(
            [f"{k} ({n})" for k, n in sorted(relabeled.items())]),
    }
    stage.Save()
    print(f"annotation layer : {args.out}")
    print(f"zones            : {zones or 'none'}")
    print(f"classes          : {classes or 'none'}")
    print(f"scene labels set : {relabeled or 'none'}")
    print(f"collision        : {col['kept']} kept, {col['added']} added, "
          f"{col['disabled']} not collidable")
    print(f"moving surfaces  : {len(moving)}")
    print(f"cameras          : {cameras or 'none'}")
    print(f"categories       : {sorted(found) or 'none'}")

    if args.flatten:
        flat = os.path.splitext(args.out)[0] + "_flat.usda"
        layer = stage.Flatten()
        layer.documentation = f"Flattened from {os.path.basename(args.out)}"  # not the local path
        layer.Export(flat)
        print(f"flattened        : {flat}")


if __name__ == "__main__":
    main()
