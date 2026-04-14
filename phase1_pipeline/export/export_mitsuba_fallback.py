from __future__ import annotations

import argparse
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from phase1_pipeline.common import dump_json, ensure_parent, load_config, resolve_output_paths
from phase1_pipeline.scenarios import active_base_station, all_base_stations, is_tunnel_scenario


def safe_text(value: object) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return str(value).encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")


def safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in ("_", "-") else "_" for char in name)


def box_vertices(center: Tuple[float, float, float], size: Tuple[float, float, float]) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, int, int]]]:
    cx, cy, cz = center
    lx, ly, lz = size
    hx, hy, hz = lx / 2.0, ly / 2.0, lz / 2.0
    vertices = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    faces = [
        (1, 2, 3), (1, 3, 4),
        (5, 6, 7), (5, 7, 8),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 4, 8), (3, 8, 7),
        (4, 1, 5), (4, 5, 8),
    ]
    return vertices, faces


def cylinder_vertices(
    center: Tuple[float, float, float],
    radius: float,
    depth: float,
    segments: int = 16,
    axis: str = "z",
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, int, int]]]:
    cx, cy, cz = center
    half = depth / 2.0
    bottom = []
    top = []
    for idx in range(segments):
        angle = 2.0 * math.pi * idx / segments
        ca = radius * math.cos(angle)
        sa = radius * math.sin(angle)
        if axis == "y":
            bottom.append((cx + ca, cy - half, cz + sa))
            top.append((cx + ca, cy + half, cz + sa))
        elif axis == "x":
            bottom.append((cx - half, cy + ca, cz + sa))
            top.append((cx + half, cy + ca, cz + sa))
        else:
            bottom.append((cx + ca, cy + sa, cz - half))
            top.append((cx + ca, cy + sa, cz + half))
    vertices = bottom + top + [center]
    faces: List[Tuple[int, int, int]] = []
    for idx in range(segments):
        nidx = (idx + 1) % segments
        b0 = idx + 1
        b1 = nidx + 1
        t0 = idx + segments + 1
        t1 = nidx + segments + 1
        faces.extend([(b0, b1, t1), (b0, t1, t0)])
    return vertices, faces


def write_obj(path: Path, vertices: Iterable[Tuple[float, float, float]], faces: Iterable[Tuple[int, int, int]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for vx, vy, vz in vertices:
            handle.write(f"v {vx:.6f} {vy:.6f} {vz:.6f}\n")
        for a, b, c in faces:
            handle.write(f"f {a} {b} {c}\n")


def material_bsdf(bsdf_id: str) -> ET.Element:
    bsdf = ET.Element("bsdf", {"type": "diffuse", "id": bsdf_id})
    return bsdf


def add_shape(root: ET.Element, shape_id: str, filename: Path, bsdf_id: str, xml_dir: Path) -> None:
    shape = ET.SubElement(root, "shape", {"type": "obj", "id": f"mesh-{safe_name(shape_id)}"})
    ET.SubElement(shape, "string", {"name": "filename", "value": filename.relative_to(xml_dir).as_posix()})
    ET.SubElement(shape, "boolean", {"name": "face_normals", "value": "true"})
    ET.SubElement(shape, "ref", {"id": bsdf_id, "name": "bsdf"})


def facing_offset(facing: str, distance: float) -> Tuple[float, float, float]:
    mapping = {
        "x+": (distance, 0.0, 0.0),
        "x-": (-distance, 0.0, 0.0),
        "y+": (0.0, distance, 0.0),
        "y-": (0.0, -distance, 0.0),
    }
    return mapping.get(facing, (0.0, -distance, 0.0))


def append_base_station_objects(config: Dict, mesh_dir: Path, objects: List[Tuple[str, Path, str]]) -> List[Tuple[float, float, float]]:
    stations = []
    for idx, gnb_cfg in enumerate(all_base_stations(config)):
        label = safe_name(str(gnb_cfg.get("name", f"gnb_{idx}")))
        mast_x, mast_y, mast_z = [float(v) for v in gnb_cfg["position_m"]]
        mast_path = mesh_dir / f"{label}_mast.obj"
        verts, faces = cylinder_vertices((mast_x, mast_y, float(gnb_cfg["height_m"]) / 2.0), float(gnb_cfg["mast_radius_m"]), float(gnb_cfg["height_m"]), axis="z")
        write_obj(mast_path, verts, faces)
        objects.append((f"{label}_mast", mast_path, "mat-itu_metal"))

        antenna_path = mesh_dir / f"{label}_antenna.obj"
        antenna_size = tuple(float(v) for v in gnb_cfg["antenna_size_m"])
        dx, dy, dz = facing_offset(str(gnb_cfg.get("facing", "y-")), antenna_size[1] / 2.0)
        verts, faces = box_vertices((mast_x + dx, mast_y + dy, mast_z + dz), antenna_size)
        write_obj(antenna_path, verts, faces)
        objects.append((f"{label}_antenna", antenna_path, "mat-itu_metal"))
        stations.append((mast_x, mast_y, mast_z))
    return stations


def build_scene(config: Dict, output_paths: Dict[str, Path]) -> None:
    mesh_dir = output_paths["mesh_dir"]
    scene_cfg = config["scene"]
    rail_cfg = config["railway"]
    barrier_cfg = config["noise_barriers"]
    train_cfg = config["train"]
    include_train_in_rt_scene = bool(config.get("ray_tracing", {}).get("include_train_in_rt_scene", False))

    length = float(scene_cfg["length_m"])
    width = float(scene_cfg["width_m"])
    rail_height = float(rail_cfg["rail_height_m"])
    rail_width = float(rail_cfg["rail_width_m"])
    gauge = float(rail_cfg["gauge_m"])
    barrier_offset = float(barrier_cfg["center_offset_m"])
    barrier_height = float(barrier_cfg["height_m"])
    barrier_thickness = float(barrier_cfg["thickness_m"])

    objects = []

    if not is_tunnel_scenario(config):
        ground_path = mesh_dir / "ground.obj"
        verts, faces = box_vertices((0.0, 0.0, -0.05), (length, width, 0.1))
        write_obj(ground_path, verts, faces)
        objects.append(("ground", ground_path, "mat-itu_concrete"))

    rail_half = gauge / 2.0
    for suffix, y in (("left", rail_half), ("right", -rail_half)):
        path = mesh_dir / f"rail_{suffix}.obj"
        verts, faces = box_vertices((0.0, y, rail_height / 2.0), (length, rail_width, rail_height))
        write_obj(path, verts, faces)
        objects.append((f"rail_{suffix}", path, "mat-itu_metal"))

    for suffix, y in (("north", barrier_offset), ("south", -barrier_offset)):
        path = mesh_dir / f"barrier_{suffix}.obj"
        verts, faces = box_vertices((0.0, y, barrier_height / 2.0), (length, barrier_thickness, barrier_height))
        write_obj(path, verts, faces)
        objects.append((f"barrier_{suffix}", path, "mat-itu_concrete"))

    if is_tunnel_scenario(config):
        tunnel_cfg = config["tunnel"]
        inner_width = float(tunnel_cfg["inner_width_m"])
        inner_height = float(tunnel_cfg["inner_height_m"])
        wall_thickness = float(tunnel_cfg.get("wall_thickness_m", 0.35))
        tunnel_length = float(tunnel_cfg["length_m"])
        tunnel_center_x = float(tunnel_cfg.get("center_x_m", 0.0))
        floor_path = mesh_dir / "tunnel_floor.obj"
        verts, faces = box_vertices((tunnel_center_x, 0.0, -wall_thickness / 2.0), (tunnel_length + wall_thickness * 2.0, inner_width + wall_thickness * 2.0, wall_thickness))
        write_obj(floor_path, verts, faces)
        objects.append(("tunnel_floor", floor_path, "mat-itu_concrete"))
        for suffix, y in (("north", inner_width / 2.0 + wall_thickness / 2.0), ("south", -inner_width / 2.0 - wall_thickness / 2.0)):
            path = mesh_dir / f"tunnel_wall_{suffix}.obj"
            verts, faces = box_vertices((tunnel_center_x, y, inner_height / 2.0), (tunnel_length, wall_thickness, inner_height))
            write_obj(path, verts, faces)
            objects.append((f"tunnel_wall_{suffix}", path, "mat-itu_concrete"))
        roof_path = mesh_dir / "tunnel_roof.obj"
        verts, faces = box_vertices((tunnel_center_x, 0.0, inner_height + wall_thickness / 2.0), (tunnel_length, inner_width + wall_thickness * 2.0, wall_thickness))
        write_obj(roof_path, verts, faces)
        objects.append(("tunnel_roof", roof_path, "mat-itu_concrete"))
    else:
        catenary_cfg = config["catenary"]
        pole_spacing = float(catenary_cfg["pole_spacing_m"])
        pole_height = float(catenary_cfg["pole_height_m"])
        pole_offset = float(catenary_cfg["pole_offset_m"])
        pole_radius = float(catenary_cfg["pole_radius_m"])
        pole_count = int(length / pole_spacing) + 1
        for idx in range(pole_count):
            x = -length / 2.0 + idx * pole_spacing
            path = mesh_dir / f"catenary_pole_{idx:03d}.obj"
            verts, faces = cylinder_vertices((x, pole_offset, pole_height / 2.0), pole_radius, pole_height, axis="z")
            write_obj(path, verts, faces)
            objects.append((f"catenary_pole_{idx:03d}", path, "mat-itu_metal"))

    gnb_positions = append_base_station_objects(config, mesh_dir, objects)

    train_length = float(train_cfg.get("length_m", 25.0))
    train_width = float(train_cfg.get("width_m", 3.2))
    train_height = float(train_cfg.get("body_height_m", 3.6))
    nose_length = float(train_cfg.get("nose_length_m", 4.0))
    wheel_radius = float(train_cfg.get("wheel_radius_m", 0.42))
    x = -length / 2.0 + train_length / 2.0 + 4.0
    y = float(train_cfg.get("lateral_offset_m", 0.0))
    z = wheel_radius + train_height / 2.0

    body_path = mesh_dir / "train_body.obj"
    verts, faces = box_vertices((x + nose_length / 2.0, y, z), (train_length - nose_length, train_width, train_height))
    write_obj(body_path, verts, faces)

    nose_path = mesh_dir / "train_nose.obj"
    verts, faces = box_vertices((x - (train_length - nose_length) / 2.0, y, z + 0.08), (nose_length, train_width * 0.92, train_height * 0.86))
    write_obj(nose_path, verts, faces)

    roof_path = mesh_dir / "train_roof.obj"
    verts, faces = box_vertices((x + 0.8, y, z + train_height / 2.0 + 0.12), (train_length * 0.74, train_width * 0.7, 0.28))
    write_obj(roof_path, verts, faces)
    if include_train_in_rt_scene:
        objects.append(("train_body", body_path, "mat-itu_metal"))
        objects.append(("train_nose", nose_path, "mat-itu_metal"))
        objects.append(("train_roof", roof_path, "mat-itu_glass"))

    root = ET.Element("scene", {"version": "3.0.0"})
    xml_dir = output_paths["mitsuba_xml"].parent
    integrator = ET.SubElement(root, "integrator", {"type": "path"})
    ET.SubElement(integrator, "integer", {"name": "max_depth", "value": "8"})
    emitter = ET.SubElement(root, "emitter", {"type": "constant"})
    ET.SubElement(emitter, "rgb", {"name": "radiance", "value": "0.25,0.25,0.25"})
    sensor = ET.SubElement(root, "sensor", {"type": "perspective"})
    ET.SubElement(sensor, "float", {"name": "fov", "value": "45"})
    film = ET.SubElement(sensor, "film", {"type": "hdrfilm"})
    ET.SubElement(film, "integer", {"name": "width", "value": "800"})
    ET.SubElement(film, "integer", {"name": "height", "value": "450"})

    for bsdf_id in ("mat-itu_concrete", "mat-itu_metal", "mat-itu_glass"):
        root.append(material_bsdf(bsdf_id))

    for name, path, bsdf_id in objects:
        add_shape(root, name, path, bsdf_id, xml_dir)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_paths["mitsuba_xml"], encoding="utf-8", xml_declaration=True)

    metadata = {
        "track_centerline_start_m": [-config["scene"]["length_m"] / 2.0, 0.0, config["train"]["receiver_height_m"]],
        "track_centerline_end_m": [config["scene"]["length_m"] / 2.0, 0.0, config["train"]["receiver_height_m"]],
        "gnb_position_m": list(active_base_station(config)["position_m"]),
        "all_gnb_positions_m": [list(pos) for pos in gnb_positions],
        "train_reference_position_m": [x, y, z + train_height * 0.2],
        "train_dimensions_m": {
            "length_m": train_length,
            "width_m": train_width,
            "body_height_m": train_height,
        },
    }
    if is_tunnel_scenario(config):
        metadata["tunnel_inner_planes_y_m"] = [
            barrier_offset - barrier_thickness / 2.0,
            -barrier_offset + barrier_thickness / 2.0,
        ]
        metadata["tunnel_height_m"] = config["tunnel"]["inner_height_m"]
    else:
        metadata["barrier_inner_planes_y_m"] = [
            barrier_offset - barrier_thickness / 2.0,
            -barrier_offset + barrier_thickness / 2.0,
        ]
    dump_json(output_paths["scene_metadata"], metadata)


# def parse_args() -> argparse.Namespace:
#     parser = argparse.ArgumentParser(description="Export a Mitsuba scene directly from config without Blender.")
#     parser.add_argument(
#         "--config",
#         default=str(Path(__file__).resolve().parents[2] / "phase1_pipeline" / "config" / "config.yaml"),
#         help="Path to the pipeline YAML configuration file.",
#     )
#     return parser.parse_args()
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a Mitsuba scene directly from config without Blender.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[2] / "phase1_pipeline" / "config" / "config.yaml"),
        help="Path to the pipeline YAML configuration file.",
    )

    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]

    return parser.parse_args(argv)

def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    output_paths = resolve_output_paths(config)
    build_scene(config, output_paths)
    print(f"Exported fallback Mitsuba XML to {safe_text(output_paths['mitsuba_xml'])}")


if __name__ == "__main__":
    main()
