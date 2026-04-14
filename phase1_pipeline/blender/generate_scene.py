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
from phase1_pipeline.scenarios import active_base_station, all_base_stations, is_tunnel_scenario


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = argv[1:]
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


def facing_offset(facing: str, distance: float) -> tuple[float, float, float]:
    mapping = {
        "x+": (distance, 0.0, 0.0),
        "x-": (-distance, 0.0, 0.0),
        "y+": (0.0, distance, 0.0),
        "y-": (0.0, -distance, 0.0),
    }
    return mapping.get(facing, (0.0, -distance, 0.0))


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


def build_tunnel(config, collections, materials) -> None:
    tunnel_cfg = config["tunnel"]
    tunnel_length = float(tunnel_cfg["length_m"])
    tunnel_width = float(tunnel_cfg["inner_width_m"])
    tunnel_height = float(tunnel_cfg["inner_height_m"])
    wall_thickness = float(tunnel_cfg.get("wall_thickness_m", 0.35))
    tunnel_center_x = float(tunnel_cfg.get("center_x_m", 0.0))

    floor = add_box("tunnel_floor", (tunnel_length + wall_thickness * 2.0, tunnel_width + wall_thickness * 2.0, wall_thickness), (tunnel_center_x, 0.0, -wall_thickness / 2.0))
    assign_material(floor, materials["concrete"])
    link_to_collection(floor, collections["Tunnel"])

    for suffix, y in (("north", tunnel_width / 2.0 + wall_thickness / 2.0), ("south", -tunnel_width / 2.0 - wall_thickness / 2.0)):
        wall = add_box(
            f"tunnel_wall_{suffix}",
            (tunnel_length, wall_thickness, tunnel_height),
            (tunnel_center_x, y, tunnel_height / 2.0),
        )
        assign_material(wall, materials["concrete"])
        link_to_collection(wall, collections["Tunnel"])

    roof = add_box(
        "tunnel_roof",
        (tunnel_length, tunnel_width + wall_thickness * 2.0, wall_thickness),
        (tunnel_center_x, 0.0, tunnel_height + wall_thickness / 2.0),
    )
    assign_material(roof, materials["concrete"])
    link_to_collection(roof, collections["Tunnel"])

    for suffix, x in (("west", tunnel_center_x - tunnel_length / 2.0), ("east", tunnel_center_x + tunnel_length / 2.0)):
        frame = add_box(
            f"portal_frame_{suffix}",
            (wall_thickness, tunnel_width + wall_thickness * 2.0, tunnel_height + wall_thickness),
            (x, 0.0, tunnel_height / 2.0),
        )
        assign_material(frame, materials["concrete"])
        link_to_collection(frame, collections["Tunnel"])


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


def build_base_stations(config, collections, materials):
    stations = []
    for idx, gnb_cfg in enumerate(all_base_stations(config)):
        x, y, z = map(float, gnb_cfg["position_m"])
        mast_height = float(gnb_cfg["height_m"])
        mast_radius = float(gnb_cfg["mast_radius_m"])
        antenna_size = tuple(float(v) for v in gnb_cfg["antenna_size_m"])
        facing = str(gnb_cfg.get("facing", "y-"))
        label = str(gnb_cfg.get("name", f"gnb_{idx}"))

        bpy.ops.mesh.primitive_cylinder_add(radius=mast_radius, depth=mast_height, location=(x, y, mast_height / 2.0))
        mast = bpy.context.active_object
        mast.name = f"{label}_mast"
        assign_material(mast, materials["metal"])
        link_to_collection(mast, collections["BaseStation"])

        dx, dy, dz = facing_offset(facing, antenna_size[1] / 2.0)
        antenna = add_box(f"{label}_antenna", antenna_size, (x + dx, y + dy, z + dz))
        if facing == "y+":
            antenna.rotation_euler = (0.0, 0.0, 0.0)
        elif facing == "x+":
            antenna.rotation_euler = (0.0, 0.0, -math.pi / 2.0)
        elif facing == "x-":
            antenna.rotation_euler = (0.0, 0.0, math.pi / 2.0)
        else:
            antenna.rotation_euler = (0.0, 0.0, math.pi)
        assign_material(antenna, materials["metal"])
        link_to_collection(antenna, collections["BaseStation"])
        stations.append((x, y, z))
    return stations


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


def build_train(config, collections, materials) -> tuple[float, float, float]:
    train_cfg = config.get("train", {})
    length = float(train_cfg.get("length_m", 25.0))
    width = float(train_cfg.get("width_m", 3.2))
    body_height = float(train_cfg.get("body_height_m", 3.6))
    nose_length = float(train_cfg.get("nose_length_m", 4.0))
    bogie_offset = float(train_cfg.get("bogie_offset_m", 7.0))
    wheel_radius = float(train_cfg.get("wheel_radius_m", 0.42))
    wheel_width = float(train_cfg.get("wheel_width_m", 0.12))
    x = -float(config["scene"]["length_m"]) / 2.0 + length / 2.0 + 4.0
    y = float(train_cfg.get("lateral_offset_m", 0.0))
    z = wheel_radius + body_height / 2.0

    body = add_box("train_body", (length - nose_length, width, body_height), (x + nose_length / 2.0, y, z))
    assign_material(body, materials["train_body"])
    link_to_collection(body, collections["Train"])

    nose = add_box("train_nose", (nose_length, width * 0.92, body_height * 0.86), (x - (length - nose_length) / 2.0, y, z + 0.08))
    assign_material(nose, materials["train_body"])
    link_to_collection(nose, collections["Train"])

    roof = add_box("train_roof", (length * 0.74, width * 0.7, 0.28), (x + 0.8, y, z + body_height / 2.0 + 0.12))
    assign_material(roof, materials["train_window"])
    link_to_collection(roof, collections["Train"])

    for idx, bogie_x in enumerate((x - bogie_offset, x + bogie_offset)):
        bogie = add_box(f"train_bogie_{idx:02d}", (2.1, 2.4, 0.45), (bogie_x, y, wheel_radius + 0.25))
        assign_material(bogie, materials["metal"])
        link_to_collection(bogie, collections["Train"])
        for side in (-1, 1):
            for wheel_shift in (-0.7, 0.7):
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=wheel_radius,
                    depth=wheel_width,
                    rotation=(math.pi / 2.0, 0.0, 0.0),
                    location=(bogie_x + wheel_shift, y + side * 1.05, wheel_radius),
                )
                wheel = bpy.context.active_object
                wheel.name = f"train_wheel_{idx}_{'l' if side < 0 else 'r'}_{0 if wheel_shift < 0 else 1}"
                assign_material(wheel, materials["metal"])
                link_to_collection(wheel, collections["Train"])

    pantograph = add_box("train_pantograph", (1.0, 0.3, 1.0), (x + 2.5, y, z + body_height / 2.0 + 0.75))
    assign_material(pantograph, materials["metal"])
    link_to_collection(pantograph, collections["Train"])
    return (x, y, z + body_height * 0.2)


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
        "Train": ensure_collection("Train"),
        "Tunnel": ensure_collection("Tunnel"),
    }
    materials = {
        "metal": create_principled_material("Metal", (0.55, 0.57, 0.6, 1.0), 0.95, 0.18, "conductor"),
        "concrete": create_principled_material("Concrete", (0.62, 0.62, 0.6, 1.0), 0.0, 0.75, "diffuse"),
        "ground": create_principled_material("Ground", (0.35, 0.4, 0.27, 1.0), 0.0, 0.95, "diffuse"),
        "train_body": create_principled_material("TrainBody", (0.92, 0.94, 0.97, 1.0), 0.15, 0.32, "diffuse"),
        "train_window": create_principled_material("TrainWindow", (0.16, 0.32, 0.52, 1.0), 0.35, 0.08, "diffuse"),
    }

    if not is_tunnel_scenario(config):
        build_ground(config, collections, materials)
    build_track(config, collections, materials)
    if is_tunnel_scenario(config):
        build_tunnel(config, collections, materials)
    else:
        build_barriers(config, collections, materials)
        build_catenary(config, collections, materials)
    gnb_positions = build_base_stations(config, collections, materials)
    train_reference = build_train(config, collections, materials)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_paths["blend_file"]))
    metadata = {
        "track_centerline_start_m": [-config["scene"]["length_m"] / 2.0, 0.0, config["train"]["receiver_height_m"]],
        "track_centerline_end_m": [config["scene"]["length_m"] / 2.0, 0.0, config["train"]["receiver_height_m"]],
        "gnb_position_m": list(active_base_station(config)["position_m"]),
        "all_gnb_positions_m": [list(pos) for pos in gnb_positions],
        "train_reference_position_m": list(train_reference),
        "train_dimensions_m": {
            "length_m": config.get("train", {}).get("length_m", 25.0),
            "width_m": config.get("train", {}).get("width_m", 3.2),
            "body_height_m": config.get("train", {}).get("body_height_m", 3.6),
        },
    }
    if is_tunnel_scenario(config):
        metadata["tunnel_inner_planes_y_m"] = [
            config["noise_barriers"]["center_offset_m"] - config["noise_barriers"]["thickness_m"] / 2.0,
            -config["noise_barriers"]["center_offset_m"] + config["noise_barriers"]["thickness_m"] / 2.0,
        ]
        metadata["tunnel_height_m"] = config["tunnel"]["inner_height_m"]
    else:
        metadata["barrier_inner_planes_y_m"] = [
            config["noise_barriers"]["center_offset_m"] - config["noise_barriers"]["thickness_m"] / 2.0,
            -config["noise_barriers"]["center_offset_m"] + config["noise_barriers"]["thickness_m"] / 2.0,
        ]
    dump_json(output_paths["scene_metadata"], metadata)
    print(f"Saved Blender scene to {output_paths['blend_file']}")
    print(f"Saved scene metadata to {output_paths['scene_metadata']}")


if __name__ == "__main__":
    main()
