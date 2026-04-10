from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase1_pipeline.common import dump_json, load_config, resolve_output_paths


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="Generate the railway scene in Blender.")
    parser.add_argument(
        "--config",
        default=str(ROOT / "phase1_pipeline" / "config" / "config.yaml"),
        help="Path to the pipeline YAML configuration file.",
    )
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for data_block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.collections):
        for block in list(data_block):
            if block.users == 0:
                data_block.remove(block)


def ensure_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def link_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)


def create_principled_material(name, base_color, metallic, roughness, mitsuba_bsdf):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    material["mitsuba_bsdf"] = mitsuba_bsdf
    return material


def assign_material(obj: bpy.types.Object, material: bpy.types.Material) -> None:
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def add_box(name: str, size, location) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] / 2.0, size[1] / 2.0, size[2] / 2.0)
    return obj


def build_track(config, collections, materials) -> None:
    scene_cfg = config["scene"]
    track_cfg = config["railway"]
    length = float(scene_cfg["length_m"])
    rail_height = float(track_cfg["rail_height_m"])
    rail_width = float(track_cfg["rail_width_m"])
    gauge = float(track_cfg["gauge_m"])
    sleeper_spacing = float(track_cfg["sleeper_spacing_m"])
    sleeper_dims = track_cfg["sleeper_dimensions_m"]

    half_gauge = gauge / 2.0
    rail_z = rail_height / 2.0

    for suffix, y in (("left", half_gauge), ("right", -half_gauge)):
        rail = add_box(f"rail_{suffix}", (length, rail_width, rail_height), (0.0, y, rail_z))
        assign_material(rail, materials["metal"])
        link_to_collection(rail, collections["Track"])

    sleeper_count = int(length / sleeper_spacing) + 1
    sleeper_width, sleeper_depth, sleeper_height = sleeper_dims
    for idx in range(sleeper_count):
        x = -length / 2.0 + idx * sleeper_spacing
        sleeper = add_box(
            f"sleeper_{idx:03d}",
            (sleeper_width, sleeper_depth, sleeper_height),
            (x, 0.0, sleeper_height / 2.0 - 0.02),
        )
        assign_material(sleeper, materials["concrete"])
        link_to_collection(sleeper, collections["Track"])


def build_barriers(config, collections, materials) -> None:
    scene_cfg = config["scene"]
    barrier_cfg = config["noise_barriers"]
    length = float(scene_cfg["length_m"])
    height = float(barrier_cfg["height_m"])
    thickness = float(barrier_cfg["thickness_m"])
    offset = float(barrier_cfg["center_offset_m"])

    for suffix, y in (("north", offset), ("south", -offset)):
        barrier = add_box(f"barrier_{suffix}", (length, thickness, height), (0.0, y, height / 2.0))
        assign_material(barrier, materials["concrete"])
        link_to_collection(barrier, collections["Barriers"])


def build_catenary(config, collections, materials) -> None:
    scene_cfg = config["scene"]
    catenary_cfg = config["catenary"]
    length = float(scene_cfg["length_m"])
    pole_spacing = float(catenary_cfg["pole_spacing_m"])
    pole_height = float(catenary_cfg["pole_height_m"])
    pole_offset = float(catenary_cfg["pole_offset_m"])
    wire_height = float(catenary_cfg["wire_height_m"])
    pole_radius = float(catenary_cfg["pole_radius_m"])

    pole_count = int(length / pole_spacing) + 1
    pole_positions = []
    for idx in range(pole_count):
        x = -length / 2.0 + idx * pole_spacing
        pole_positions.append(x)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=pole_radius,
            depth=pole_height,
            location=(x, pole_offset, pole_height / 2.0),
        )
        pole = bpy.context.active_object
        pole.name = f"catenary_pole_{idx:03d}"
        assign_material(pole, materials["metal"])
        link_to_collection(pole, collections["Catenary"])

        arm = add_box(f"catenary_arm_{idx:03d}", (0.3, pole_offset, 0.12), (x, pole_offset / 2.0, wire_height))
        assign_material(arm, materials["metal"])
        link_to_collection(arm, collections["Catenary"])

    curve_data = bpy.data.curves.new("contact_wire_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 12
    curve_data.bevel_depth = float(catenary_cfg["wire_radius_m"])
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(pole_positions) - 1)
    for idx, x in enumerate(pole_positions):
        sag = 0.08 * math.sin((idx / max(1, len(pole_positions) - 1)) * math.pi)
        spline.points[idx].co = (x, 0.0, wire_height - sag, 1.0)
    wire = bpy.data.objects.new("contact_wire", curve_data)
    assign_material(wire, materials["metal"])
    link_to_collection(wire, collections["Catenary"])

    messenger_curve = bpy.data.curves.new("messenger_wire_curve", type="CURVE")
    messenger_curve.dimensions = "3D"
    messenger_curve.resolution_u = 12
    messenger_curve.bevel_depth = float(catenary_cfg["wire_radius_m"]) * 1.2
    messenger_spline = messenger_curve.splines.new("POLY")
    messenger_spline.points.add(len(pole_positions) - 1)
    for idx, x in enumerate(pole_positions):
        sag = 0.14 * math.sin((idx / max(1, len(pole_positions) - 1)) * math.pi)
        messenger_spline.points[idx].co = (x, 0.0, wire_height + 0.45 - sag, 1.0)
    messenger = bpy.data.objects.new("messenger_wire", messenger_curve)
    assign_material(messenger, materials["metal"])
    link_to_collection(messenger, collections["Catenary"])


def build_base_station(config, collections, materials):
    gnb_cfg = config["base_station"]
    x, y, z = map(float, gnb_cfg["position_m"])
    mast_height = float(gnb_cfg["height_m"])
    mast_radius = float(gnb_cfg["mast_radius_m"])
    antenna_size = tuple(float(v) for v in gnb_cfg["antenna_size_m"])

    bpy.ops.mesh.primitive_cylinder_add(radius=mast_radius, depth=mast_height, location=(x, y, mast_height / 2.0))
    mast = bpy.context.active_object
    mast.name = "gnb_mast"
    assign_material(mast, materials["metal"])
    link_to_collection(mast, collections["BaseStation"])

    antenna = add_box("gnb_antenna", antenna_size, (x, y - antenna_size[1] / 2.0, z))
    antenna.rotation_euler = (0.0, 0.0, math.pi)
    assign_material(antenna, materials["metal"])
    link_to_collection(antenna, collections["BaseStation"])
    return (x, y, z)


def build_ground(config, collections, materials) -> None:
    scene_cfg = config["scene"]
    length = float(scene_cfg["length_m"])
    width = float(scene_cfg["width_m"])
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "ground"
    ground.scale = (length / 2.0, width / 2.0, 1.0)
    assign_material(ground, materials["ground"])
    link_to_collection(ground, collections["Ground"])


def configure_scene_units() -> None:
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    output_paths = resolve_output_paths(config)

    clear_scene()
    configure_scene_units()

    collections = {
        "Ground": ensure_collection("Ground"),
        "Track": ensure_collection("Track"),
        "Barriers": ensure_collection("Barriers"),
        "Catenary": ensure_collection("Catenary"),
        "BaseStation": ensure_collection("BaseStation"),
    }
    materials = {
        "metal": create_principled_material("Metal", (0.55, 0.57, 0.6, 1.0), 0.95, 0.18, "conductor"),
        "concrete": create_principled_material("Concrete", (0.62, 0.62, 0.6, 1.0), 0.0, 0.75, "diffuse"),
        "ground": create_principled_material("Ground", (0.35, 0.4, 0.27, 1.0), 0.0, 0.95, "diffuse"),
    }

    build_ground(config, collections, materials)
    build_track(config, collections, materials)
    build_barriers(config, collections, materials)
    build_catenary(config, collections, materials)
    gnb_position = build_base_station(config, collections, materials)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_paths["blend_file"]))
    metadata = {
        "track_centerline_start_m": [-config["scene"]["length_m"] / 2.0, 0.0, config["train"]["receiver_height_m"]],
        "track_centerline_end_m": [config["scene"]["length_m"] / 2.0, 0.0, config["train"]["receiver_height_m"]],
        "gnb_position_m": list(gnb_position),
        "barrier_inner_planes_y_m": [
            config["noise_barriers"]["center_offset_m"] - config["noise_barriers"]["thickness_m"] / 2.0,
            -config["noise_barriers"]["center_offset_m"] + config["noise_barriers"]["thickness_m"] / 2.0,
        ],
    }
    dump_json(output_paths["scene_metadata"], metadata)
    print(f"Saved Blender scene to {output_paths['blend_file']}")
    print(f"Saved scene metadata to {output_paths['scene_metadata']}")


if __name__ == "__main__":
    main()
