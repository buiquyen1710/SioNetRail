from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase1_pipeline.common import load_config, resolve_output_paths


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="Export the current Blender scene to Mitsuba XML.")
    parser.add_argument(
        "--config",
        default=str(ROOT / "phase1_pipeline" / "config" / "config.yaml"),
        help="Path to the pipeline YAML configuration file.",
    )
    return parser.parse_args(argv)


def safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in ("_", "-") else "_" for char in name)


def export_object_to_obj(obj: bpy.types.Object, mesh_path: Path):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()

        mesh.calc_loop_triangles()

        material = obj.active_material
        material_name = material.name if material else "Default"

        with mesh_path.open("w", encoding="utf-8") as handle:
            handle.write(f"o {safe_name(obj.name)}\n")
            handle.write(f"usemtl {safe_name(material_name)}\n")
            for vertex in mesh.vertices:
                world = obj.matrix_world @ vertex.co
                handle.write(f"v {world.x:.9f} {world.y:.9f} {world.z:.9f}\n")
            for vertex in mesh.vertices:
                normal = vertex.normal.normalized()
                handle.write(f"vn {normal.x:.9f} {normal.y:.9f} {normal.z:.9f}\n")
            for face in mesh.loop_triangles:
                indices = [index + 1 for index in face.vertices]
                handle.write("f " + " ".join(f"{idx}//{idx}" for idx in indices) + "\n")
    finally:
        evaluated.to_mesh_clear()
    return material_name


def material_ref_id(material: bpy.types.Material | None) -> str:
    if material is None:
        return "mat-itu_concrete"
    bsdf_type = material.get("mitsuba_bsdf", "diffuse")
    if bsdf_type == "conductor":
        return "mat-itu_metal"
    return "mat-itu_concrete"


def material_bsdf(material: bpy.types.Material | None, bsdf_id: str) -> ET.Element:
    if material is None:
        bsdf_type = "diffuse"
        color = (0.7, 0.7, 0.7)
    else:
        bsdf_type = material.get("mitsuba_bsdf", "diffuse")
        principled = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
        rgba = principled.inputs["Base Color"].default_value if principled else (0.7, 0.7, 0.7, 1.0)
        color = rgba[:3]

    if bsdf_type == "conductor":
        bsdf = ET.Element("bsdf", {"type": "roughconductor", "id": bsdf_id})
        ET.SubElement(bsdf, "string", {"name": "material", "value": "none"})
        ET.SubElement(bsdf, "rgb", {"name": "eta", "value": "0.2,0.92,1.1"})
        ET.SubElement(bsdf, "rgb", {"name": "k", "value": "3.9,2.45,2.14"})
        ET.SubElement(bsdf, "float", {"name": "alpha", "value": "0.15"})
    else:
        bsdf = ET.Element("bsdf", {"type": "diffuse", "id": bsdf_id})
        ET.SubElement(
            bsdf,
            "rgb",
            {"name": "reflectance", "value": f"{color[0]:.4f},{color[1]:.4f},{color[2]:.4f}"},
        )
    return bsdf


def build_scene_xml(output_paths) -> ET.ElementTree:
    mesh_dir = output_paths["mesh_dir"]
    root = ET.Element("scene", {"version": "3.0.0"})

    integrator = ET.SubElement(root, "integrator", {"type": "path"})
    ET.SubElement(integrator, "integer", {"name": "max_depth", "value": "8"})

    sensor = ET.SubElement(root, "sensor", {"type": "perspective"})
    ET.SubElement(sensor, "float", {"name": "fov", "value": "45"})
    film = ET.SubElement(sensor, "film", {"type": "hdrfilm"})
    ET.SubElement(film, "integer", {"name": "width", "value": "800"})
    ET.SubElement(film, "integer", {"name": "height", "value": "450"})
    sampler = ET.SubElement(sensor, "sampler", {"type": "independent"})
    ET.SubElement(sampler, "integer", {"name": "sample_count", "value": "16"})

    emitter = ET.SubElement(root, "emitter", {"type": "constant"})
    ET.SubElement(emitter, "rgb", {"name": "radiance", "value": "0.25,0.25,0.25"})

    declared_bsdfs = set()

    for obj in sorted(bpy.data.objects, key=lambda item: item.name):
        if obj.type not in {"MESH", "CURVE"}:
            continue
        mesh_path = mesh_dir / f"{safe_name(obj.name)}.obj"
        export_object_to_obj(obj, mesh_path)
        bsdf_id = material_ref_id(obj.active_material)
        if bsdf_id not in declared_bsdfs:
            root.append(material_bsdf(obj.active_material, bsdf_id))
            declared_bsdfs.add(bsdf_id)
        shape = ET.SubElement(root, "shape", {"type": "obj", "id": safe_name(obj.name)})
        ET.SubElement(shape, "string", {"name": "filename", "value": str(mesh_path.as_posix())})
        ET.SubElement(shape, "ref", {"id": bsdf_id})

    return ET.ElementTree(root)


def indent(element: ET.Element, level: int = 0) -> None:
    prefix = "\n" + "  " * level
    if len(element):
        if not element.text or not element.text.strip():
            element.text = prefix + "  "
        for child in element:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = prefix
    elif level and (not element.tail or not element.tail.strip()):
        element.tail = prefix


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    output_paths = resolve_output_paths(config)
    tree = build_scene_xml(output_paths)
    indent(tree.getroot())
    tree.write(output_paths["mitsuba_xml"], encoding="utf-8", xml_declaration=True)
    print(f"Exported Mitsuba XML to {output_paths['mitsuba_xml']}")


if __name__ == "__main__":
    main()
