from __future__ import annotations

import argparse
import cmath
import json
import math
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase1_pipeline.common import (
    SPEED_OF_LIGHT_M_S,
    add,
    dot,
    load_config,
    normalize,
    resolve_output_paths,
    scale,
    subtract,
    vector_length,
    wavelength_m,
)
from phase1_pipeline.output.export_trace import (
    TraceCsvWriter,
    export_rays_3d_visualization,
    export_rays_3d_with_mitsuba,
    export_sample_style_scene,
    export_validation_plots,
)
from phase1_pipeline.raytracing.compute_doppler import angles_from_vector, compute_doppler_hz, unit_vector_from_angles


def try_import_sionna():
    try:
        ensure_drjit_llvm_path()
        import mitsuba as mi
        from sionna.rt import PathSolver, PlanarArray, Receiver, Transmitter, load_scene
    except ImportError:
        return None
    return {
        "mi": mi,
        "PathSolver": PathSolver,
        "PlanarArray": PlanarArray,
        "Receiver": Receiver,
        "Transmitter": Transmitter,
        "load_scene": load_scene,
    }


def try_import_mitsuba():
    try:
        ensure_drjit_llvm_path()
        import mitsuba as mi

        for variant in ("scalar_rgb", "llvm_ad_rgb", "cuda_ad_rgb"):
            try:
                mi.set_variant(variant)
                break
            except Exception:
                continue
        return mi
    except ImportError:
        return None


def safe_exception_text(exc: Exception) -> str:
    text = str(exc)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")


def safe_path_text(path: Path) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return str(path).encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")


def prepare_ascii_safe_scene(output_paths: Dict) -> Path:
    src_xml = Path(output_paths["mitsuba_xml"])
    src_mesh_dir = Path(output_paths["mesh_dir"])
    ascii_root = Path(tempfile.gettempdir()) / "sionetrail_mitsuba_scene"
    dst_mesh_dir = ascii_root / "meshes"
    dst_mesh_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_xml, ascii_root / "scene.xml")
    if src_mesh_dir.exists():
        for mesh_file in src_mesh_dir.glob("*.obj"):
            shutil.copy2(mesh_file, dst_mesh_dir / mesh_file.name)
    return ascii_root / "scene.xml"


def ensure_drjit_llvm_path() -> None:
    if os.environ.get("DRJIT_LIBLLVM_PATH"):
        return
    candidates = [
        Path("C:/Program Files/LLVM/bin/LLVM-C.dll"),
        Path.home() / "anaconda3" / "envs" / "sionna-rt" / "Library" / "bin" / "LLVM-C.dll",
    ]
    for candidate in candidates:
        if candidate.exists():
            os.environ["DRJIT_LIBLLVM_PATH"] = str(candidate)
            return


@dataclass
class CandidatePath:
    name: str
    points: List[Tuple[float, float, float]]
    coefficient: complex
    delay_s: float
    aoa_theta_rad: float
    aoa_phi_rad: float
    aod_theta_rad: float
    aod_phi_rad: float
    doppler_hz: float
    los_flag: int


def trajectory_bounds(config: Dict) -> Tuple[float, float]:
    length = float(config["scene"]["length_m"])
    margin = float(
        config["simulation"].get(
            "scene_margin_m",
            max(5.0, float(config["train"].get("length_m", 25.0)) / 2.0 + 1.0),
        )
    )
    start_x = -length / 2.0 + margin
    end_x = length / 2.0 - margin
    if end_x <= start_x:
        start_x = -length / 2.0 + 1.0
        end_x = length / 2.0 - 1.0
    return start_x, end_x


def effective_duration_s(config: Dict) -> float:
    explicit = config["simulation"].get("duration_s")
    if explicit not in (None, ""):
        return float(explicit)
    speed_m_s = float(config["simulation"]["train_speed_kmh"]) / 3.6
    start_x, end_x = trajectory_bounds(config)
    return max(0.0, (end_x - start_x) / speed_m_s)


def simulation_times(config: Dict, timestep_s: Optional[float] = None) -> Iterator[Tuple[int, float]]:
    timestep_s = float(timestep_s if timestep_s is not None else config["simulation"]["timestep_s"])
    duration_s = effective_duration_s(config)
    steps = max(1, int(math.floor(duration_s / timestep_s)) + 1)
    for idx in range(steps):
        yield idx, idx * timestep_s


def simulation_step_count(config: Dict, timestep_s: Optional[float] = None) -> int:
    timestep_s = float(timestep_s if timestep_s is not None else config["simulation"]["timestep_s"])
    duration_s = effective_duration_s(config)
    return max(1, int(math.floor(duration_s / timestep_s)) + 1)


def rx_position_for_time(config: Dict, time_s: float) -> Tuple[float, float, float]:
    speed_m_s = float(config["simulation"]["train_speed_kmh"]) / 3.6
    z = float(config["train"]["receiver_height_m"])
    start_x, end_x = trajectory_bounds(config)
    x = start_x + min(end_x - start_x, speed_m_s * time_s)
    y = float(config["train"].get("lateral_offset_m", 0.0))
    return (x, y, z)


def tx_position(config: Dict) -> Tuple[float, float, float]:
    x, y, z = [float(v) for v in config["base_station"]["position_m"]]
    antenna_size = [float(v) for v in config["base_station"].get("antenna_size_m", [0.8, 0.25, 1.2])]
    clearance = float(config["base_station"].get("ray_origin_clearance_m", 0.2))
    # Place the radiating point slightly in front of the antenna face toward the track,
    # instead of on or inside the support geometry.
    face_offset = antenna_size[1] / 2.0 + clearance
    y -= math.copysign(face_offset, y if abs(y) > 1e-9 else 1.0)
    return (x, y, z)


def train_velocity(config: Dict) -> Tuple[float, float, float]:
    return (float(config["simulation"]["train_speed_kmh"]) / 3.6, 0.0, 0.0)


def sionna_solver_timestep_s(config: Dict) -> float:
    sim_timestep = float(config["simulation"]["timestep_s"])
    solver_timestep = float(config["ray_tracing"].get("solver_timestep_s", sim_timestep))
    return max(sim_timestep, solver_timestep)


def complex_array_to_numpy(path_coefficients):
    if hasattr(path_coefficients, "numpy"):
        return path_coefficients.numpy()
    if isinstance(path_coefficients, (tuple, list)) and len(path_coefficients) == 2:
        return path_coefficients[0].numpy() + 1j * path_coefficients[1].numpy()
    raise TypeError(f"Unsupported Sionna path coefficient container: {type(path_coefficients)!r}")


def extract_sionna_paths(paths, config: Dict) -> List[CandidatePath]:
    import numpy as np

    coeffs = np.asarray(complex_array_to_numpy(paths.a))
    delays = np.asarray(paths.tau.numpy())
    theta_t = np.asarray(paths.theta_t.numpy())
    phi_t = np.asarray(paths.phi_t.numpy())
    theta_r = np.asarray(paths.theta_r.numpy())
    phi_r = np.asarray(paths.phi_r.numpy())
    valid = np.asarray(paths.valid.numpy())

    while coeffs.ndim > 1:
        coeffs = coeffs[0]
    while delays.ndim > 1:
        delays = delays[0]
        theta_t = theta_t[0]
        phi_t = phi_t[0]
        theta_r = theta_r[0]
        phi_r = phi_r[0]
        valid = valid[0]

    interactions = np.asarray(paths.interactions.numpy())
    if coeffs.size == 0 or delays.size == 0 or valid.size == 0:
        return []
    if interactions.size == 0 or interactions.shape[-1] == 0:
        interaction_matrix = np.zeros((0, coeffs.shape[-1]), dtype=np.uint32)
    else:
        interaction_depth = interactions.shape[0]
        interaction_matrix = interactions.reshape(interaction_depth, -1, interactions.shape[-1])[:, 0, :]

    velocity = train_velocity(config)
    frequency_hz = float(config["simulation"]["frequency_hz"])
    extracted: List[CandidatePath] = []
    for idx in range(coeffs.shape[-1]):
        if idx >= len(valid) or not bool(valid[idx]):
            continue
        coeff = complex(coeffs[idx])
        aoa_theta = float(theta_r[idx])
        aoa_phi = float(phi_r[idx])
        arrival_from_source = unit_vector_from_angles(aoa_theta, aoa_phi)
        propagation_to_receiver = (-arrival_from_source[0], -arrival_from_source[1], -arrival_from_source[2])
        doppler = compute_doppler_hz(frequency_hz, velocity, propagation_to_receiver)
        los_flag = 1 if interaction_matrix.size == 0 or np.all(interaction_matrix[:, idx] == 0) else 0
        extracted.append(
            CandidatePath(
                name=f"sionna_{idx}",
                points=[],
                coefficient=coeff,
                delay_s=float(delays[idx]),
                aoa_theta_rad=aoa_theta,
                aoa_phi_rad=aoa_phi,
                aod_theta_rad=float(theta_t[idx]),
                aod_phi_rad=float(phi_t[idx]),
                doppler_hz=doppler,
                los_flag=los_flag,
            )
        )
    return extracted


def segment_clear(scene, mi, start: Sequence[float], end: Sequence[float], epsilon: float = 1e-3) -> bool:
    direction = subtract(end, start)
    distance = vector_length(direction)
    if distance <= epsilon:
        return True
    unit_direction = normalize(direction)
    ray = mi.Ray3f(o=mi.Point3f(*start), d=mi.Vector3f(*unit_direction))
    ray.maxt = distance - epsilon
    return not bool(scene.ray_test(ray))


def reflect_point_across_plane(point, plane_point, plane_normal):
    offset = subtract(point, plane_point)
    distance = dot(offset, plane_normal)
    return subtract(point, scale(plane_normal, 2.0 * distance))


def line_plane_intersection(start, end, plane_point, plane_normal) -> Optional[Tuple[float, float, float]]:
    direction = subtract(end, start)
    denom = dot(plane_normal, direction)
    if abs(denom) < 1e-9:
        return None
    t = dot(plane_normal, subtract(plane_point, start)) / denom
    if not 0.0 < t < 1.0:
        return None
    return add(start, scale(direction, t))


def build_candidate_from_points(name: str, points, reflection_gain: complex, config: Dict, los_flag: int) -> CandidatePath:
    total_distance = 0.0
    for start, end in zip(points, points[1:]):
        total_distance += vector_length(subtract(end, start))
    wavelength = wavelength_m(float(config["simulation"]["frequency_hz"]))
    amplitude = (wavelength / (4.0 * math.pi * total_distance)) * reflection_gain
    phase = -2.0 * math.pi * total_distance / wavelength
    coefficient = amplitude * cmath.exp(1j * phase)
    aod_theta, aod_phi = angles_from_vector(subtract(points[1], points[0]))
    aoa_theta, aoa_phi = angles_from_vector(subtract(points[-2], points[-1]))
    doppler = compute_doppler_hz(
        float(config["simulation"]["frequency_hz"]),
        train_velocity(config),
        subtract(points[-1], points[-2]),
    )
    return CandidatePath(
        name=name,
        points=points,
        coefficient=coefficient,
        delay_s=total_distance / SPEED_OF_LIGHT_M_S,
        aoa_theta_rad=aoa_theta,
        aoa_phi_rad=aoa_phi,
        aod_theta_rad=aod_theta,
        aod_phi_rad=aod_phi,
        doppler_hz=doppler,
        los_flag=los_flag,
    )


def polyline_clear(scene, mi, points: Sequence[Tuple[float, float, float]], epsilon: float = 1e-3) -> bool:
    for start, end in zip(points, points[1:]):
        if not segment_clear(scene, mi, start, end, epsilon=epsilon):
            return False
    return True


def nearest_catenary_points(config: Dict, rx: Tuple[float, float, float], count: int = 3) -> List[Tuple[float, float, float]]:
    scene_length = float(config["scene"]["length_m"])
    catenary_cfg = config["catenary"]
    spacing = float(catenary_cfg["pole_spacing_m"])
    pole_offset = float(catenary_cfg["pole_offset_m"])
    wire_height = float(catenary_cfg["wire_height_m"])
    pole_count = int(scene_length / spacing) + 1
    points = []
    for idx in range(pole_count):
        x = -scene_length / 2.0 + idx * spacing
        points.append((x, pole_offset * 0.35, wire_height))
    points.sort(key=lambda point: abs(point[0] - rx[0]))
    return points[:count]


def softened_gain(base_gain: complex, validated: bool, penalty_db: float = 8.0) -> complex:
    if validated:
        return base_gain
    linear_penalty = 10.0 ** (-penalty_db / 20.0)
    return base_gain * linear_penalty


def los_clears_barriers(tx: Tuple[float, float, float], rx: Tuple[float, float, float], barrier_center: float, barrier_thickness: float, barrier_height: float) -> bool:
    barrier_planes_y = [
        barrier_center - barrier_thickness / 2.0,
        -barrier_center + barrier_thickness / 2.0,
    ]
    ty = tx[1]
    ry = rx[1]
    for plane_y in barrier_planes_y:
        if abs(ry - ty) < 1e-9:
            continue
        t = (plane_y - ty) / (ry - ty)
        if 0.0 <= t <= 1.0:
            z_at_plane = tx[2] + t * (rx[2] - tx[2])
            if z_at_plane <= barrier_height + 0.25:
                return False
    return True


def fallback_paths(config: Dict, mitsuba_scene=None, mi=None):
    barrier_cfg = config["noise_barriers"]
    barrier_center = float(barrier_cfg["center_offset_m"])
    barrier_thickness = float(barrier_cfg["thickness_m"])
    barrier_height = float(barrier_cfg["height_m"])
    scene_length = float(config["scene"]["length_m"])
    scene_width = float(config["scene"]["width_m"])
    tx = tx_position(config)

    barrier_planes = [
        {
            "name": "barrier_north",
            "point": (0.0, barrier_center - barrier_thickness / 2.0, barrier_height / 2.0),
            "normal": (0.0, -1.0, 0.0),
            "gain": complex(-0.72, 0.0),
            "bounds": {"x": (-scene_length / 2.0, scene_length / 2.0), "z": (0.0, barrier_height + 8.0)},
        },
        {
            "name": "barrier_south",
            "point": (0.0, -barrier_center + barrier_thickness / 2.0, barrier_height / 2.0),
            "normal": (0.0, 1.0, 0.0),
            "gain": complex(-0.72, 0.0),
            "bounds": {"x": (-scene_length / 2.0, scene_length / 2.0), "z": (0.0, barrier_height + 8.0)},
        },
    ]
    ground_plane = {
        "point": (0.0, 0.0, 0.0),
        "normal": (0.0, 0.0, 1.0),
        "gain": complex(-0.55, 0.0),
        "bounds": {"x": (-scene_length / 2.0, scene_length / 2.0), "y": (-scene_width / 2.0, scene_width / 2.0)},
    }
    strict_los = True

    for _, time_s in simulation_times(config):
        rx = rx_position_for_time(config, time_s)
        candidates = []

        los_points = [tx, rx]
        los_valid = los_clears_barriers(tx, rx, barrier_center, barrier_thickness, barrier_height)
        if mitsuba_scene is not None and strict_los:
            los_valid = los_valid or polyline_clear(mitsuba_scene, mi, los_points)
        if los_valid:
            candidates.append(build_candidate_from_points("los", los_points, complex(1.0, 0.0), config, 1))

        mirrored_tx = reflect_point_across_plane(tx, ground_plane["point"], ground_plane["normal"])
        reflection = line_plane_intersection(mirrored_tx, rx, ground_plane["point"], ground_plane["normal"])
        if reflection is not None:
            within_ground = (
                ground_plane["bounds"]["x"][0] <= reflection[0] <= ground_plane["bounds"]["x"][1]
                and ground_plane["bounds"]["y"][0] <= reflection[1] <= ground_plane["bounds"]["y"][1]
            )
            clear = True
            if mitsuba_scene is not None:
                clear = polyline_clear(mitsuba_scene, mi, [tx, add(reflection, (0.0, 0.0, 1e-3)), rx])
            if within_ground:
                candidates.append(
                    build_candidate_from_points(
                        "ground_reflection",
                        [tx, reflection, rx],
                        softened_gain(ground_plane["gain"], clear, penalty_db=5.0),
                        config,
                        0,
                    )
                )

        for barrier in barrier_planes:
            mirrored_tx = reflect_point_across_plane(tx, barrier["point"], barrier["normal"])
            reflection = line_plane_intersection(mirrored_tx, rx, barrier["point"], barrier["normal"])
            if reflection is None:
                continue
            within_barrier = (
                barrier["bounds"]["x"][0] <= reflection[0] <= barrier["bounds"]["x"][1]
                and barrier["bounds"]["z"][0] <= reflection[2] <= barrier["bounds"]["z"][1]
            )
            clear = True
            if mitsuba_scene is not None:
                clear = polyline_clear(mitsuba_scene, mi, [tx, reflection, rx])
            if within_barrier:
                candidates.append(
                    build_candidate_from_points(
                        barrier["name"],
                        [tx, reflection, rx],
                        softened_gain(barrier["gain"], clear, penalty_db=7.0),
                        config,
                        0,
                    )
                )

            edge_point = (reflection[0], barrier["point"][1], barrier_height + 0.25)
            if mitsuba_scene is not None:
                clear = polyline_clear(mitsuba_scene, mi, [tx, edge_point, rx])
            else:
                clear = True
            candidates.append(
                build_candidate_from_points(
                    f"{barrier['name']}_edge",
                    [tx, edge_point, rx],
                    softened_gain(complex(-0.24, 0.0), clear, penalty_db=9.0),
                    config,
                    0,
                )
            )

        for idx, scatter_point in enumerate(nearest_catenary_points(config, rx, count=3)):
            clear = True
            if mitsuba_scene is not None:
                clear = polyline_clear(mitsuba_scene, mi, [tx, scatter_point, rx])
            candidates.append(
                build_candidate_from_points(
                    f"catenary_scatter_{idx}",
                    [tx, scatter_point, rx],
                    softened_gain(complex(0.11, 0.0), clear, penalty_db=10.0 + idx * 1.5),
                    config,
                    0,
                )
            )

        train_roof_point = (rx[0], rx[1], float(config["train"].get("body_height_m", 3.6)) + 0.8)
        if mitsuba_scene is not None:
            roof_clear = polyline_clear(mitsuba_scene, mi, [tx, train_roof_point, rx])
        else:
            roof_clear = True
        candidates.append(
            build_candidate_from_points(
                "train_roof_scatter",
                [tx, train_roof_point, rx],
                softened_gain(complex(0.09, 0.0), roof_clear, penalty_db=12.0),
                config,
                0,
            )
        )

        unique_candidates = {}
        for candidate in candidates:
            unique_candidates[candidate.name] = candidate
        candidates = list(unique_candidates.values())
        candidates.sort(key=lambda item: abs(item.coefficient), reverse=True)

        if not candidates:
            candidates.append(build_candidate_from_points("los_nominal", [tx, rx], complex(1.0, 0.0), config, 1))
        yield time_s, candidates


def fallback_paths_for_times(config: Dict, times_s: List[float], mitsuba_scene=None, mi=None) -> Dict[float, List[CandidatePath]]:
    targets = {round(time_s, 9) for time_s in times_s}
    results: Dict[float, List[CandidatePath]] = {}
    for time_s, candidates in fallback_paths(config, mitsuba_scene=mitsuba_scene, mi=mi):
        rounded = round(time_s, 9)
        if rounded in targets:
            results[rounded] = candidates
        if len(results) == len(targets):
            break
    return results


def export_snapshot_visualizations(config: Dict, output_paths: Dict, snapshot_data: Dict, mitsuba_scene=None, mi=None) -> None:
    if not snapshot_data:
        return

    tx_pos = tx_position(config)
    output_dir = output_paths["mitsuba_xml"].parent
    scene_render_path = None
    if Path(output_paths["mitsuba_xml"]).exists():
        try:
            scene_render_path = prepare_ascii_safe_scene(output_paths)
        except Exception:
            scene_render_path = Path(output_paths["mitsuba_xml"])
    for pattern in ("rays_3d_*.png", "rays_scene_*.png", "coverage_rays_*.png"):
        for file_path in output_dir.glob(pattern):
            try:
                file_path.unlink()
            except OSError:
                pass
    snapshot_times = [float(item["time_s"]) for item in snapshot_data.values()]
    fallback_visual_paths = fallback_paths_for_times(config, snapshot_times, mitsuba_scene=mitsuba_scene, mi=mi)

    for key, data in snapshot_data.items():
        time_s = float(data["time_s"])
        visual_paths = fallback_visual_paths.get(round(time_s, 9), data["paths"])
        if not visual_paths:
            continue

        export_rays_3d_visualization(
            tx_position=tx_pos,
            rx_position=data["rx_pos"],
            paths=visual_paths,
            output_path=output_paths["mitsuba_xml"].parent / f"rays_3d_{key}_t{time_s:.3f}s.png",
            title=f"3D Ray Paths (t = {time_s:.3f}s) - {key.upper()}",
        )

        if scene_render_path is not None:
            export_rays_3d_with_mitsuba(
                mitsuba_xml_path=scene_render_path,
                tx_position=tx_pos,
                rx_position=data["rx_pos"],
                paths=visual_paths,
                output_path=output_paths["mitsuba_xml"].parent / f"rays_scene_{key}_t{time_s:.3f}s.png",
                title=f"Scene with Ray Paths (t = {time_s:.3f}s) - {key.upper()}",
            )

        export_sample_style_scene(
            tx_position=tx_pos,
            rx_position=data["rx_pos"],
            paths=visual_paths,
            output_path=output_paths["mitsuba_xml"].parent / f"coverage_rays_{key}_t{time_s:.3f}s.png",
            scene_cfg={**config["scene"], "frequency_hz_override": float(config["simulation"]["frequency_hz"])},
            barrier_cfg=config["noise_barriers"],
            train_cfg=config["train"],
            title=f"Coverage and Ray Paths (t = {time_s:.3f}s)",
        )


def _append_rows(writer: TraceCsvWriter, time_s: float, extracted: List[CandidatePath]) -> Dict[str, float]:
    timestamp_ns = int(round(time_s * 1e9))
    rows = []
    for path_id, path in enumerate(extracted):
        rows.append(
            {
                "timestamp_ns": timestamp_ns,
                "path_id": path_id,
                "delay_s": path.delay_s,
                "amplitude_real": path.coefficient.real,
                "amplitude_imag": path.coefficient.imag,
                "phase_rad": cmath.phase(path.coefficient),
                "aoa_theta_rad": path.aoa_theta_rad,
                "aoa_phi_rad": path.aoa_phi_rad,
                "aod_theta_rad": path.aod_theta_rad,
                "aod_phi_rad": path.aod_phi_rad,
                "doppler_hz": path.doppler_hz,
                "los_flag": path.los_flag,
            }
        )
    writer.write_rows(rows)
    return {
        "time_s": time_s,
        "path_count": len(rows),
        "max_abs_doppler_hz": max((abs(row["doppler_hz"]) for row in rows), default=0.0),
    }


def run_sionna_backend(config: Dict, output_paths: Dict) -> List[Dict[str, float]]:
    imports = try_import_sionna()
    if imports is None:
        raise RuntimeError("Sionna RT is not available.")

    mitsuba_scene_path = prepare_ascii_safe_scene(output_paths)
    scene = imports["load_scene"](str(mitsuba_scene_path), merge_shapes=False)
    scene.frequency = float(config["simulation"]["frequency_hz"])
    scene.tx_array = imports["PlanarArray"](
        num_rows=1,
        num_cols=1,
        vertical_spacing=0.5,
        horizontal_spacing=0.5,
        pattern="iso",
        polarization="V",
    )
    scene.rx_array = imports["PlanarArray"](
        num_rows=1,
        num_cols=1,
        vertical_spacing=0.5,
        horizontal_spacing=0.5,
        pattern="iso",
        polarization="V",
    )

    mi = imports["mi"]
    tx = imports["Transmitter"](
        name="tx",
        position=mi.Point3f(*tx_position(config)),
        orientation=mi.Point3f(0.0, 0.0, 0.0),
    )
    rx = imports["Receiver"](
        name="rx",
        position=mi.Point3f(*rx_position_for_time(config, 0.0)),
        orientation=mi.Point3f(0.0, 0.0, 0.0),
    )
    scene.add(tx)
    scene.add(rx)
    solver = imports["PathSolver"]()

    solver_timestep = sionna_solver_timestep_s(config)
    total_steps = simulation_step_count(config, timestep_s=solver_timestep)
    mid_step = total_steps // 2
    summary: List[Dict[str, float]] = []
    snapshot_data: Dict[str, Dict] = {}
    with TraceCsvWriter(output_paths["trace_csv"]) as writer:
        for step_idx, time_s in simulation_times(config, timestep_s=solver_timestep):
            rx.position = mi.Point3f(*rx_position_for_time(config, time_s))
            tx.look_at(rx)
            rx.look_at(tx)
            paths = solver(
                scene=scene,
                max_depth=int(config["ray_tracing"]["max_depth"]),
                max_num_paths_per_src=int(config["ray_tracing"]["max_num_paths"]),
                samples_per_src=int(config["ray_tracing"]["samples_per_src"]),
                synthetic_array=True,
                los=True,
                specular_reflection=True,
                diffuse_reflection=False,
                refraction=bool(config["ray_tracing"]["enable_refraction"]),
                diffraction=False,
            )
            extracted = extract_sionna_paths(paths, config)
            summary_point = _append_rows(writer, time_s, extracted)
            summary.append(summary_point)

            if step_idx == 0:
                snapshot_data["start"] = {"time_s": time_s, "rx_pos": rx_position_for_time(config, time_s), "paths": extracted}
            if step_idx == mid_step:
                snapshot_data["mid"] = {"time_s": time_s, "rx_pos": rx_position_for_time(config, time_s), "paths": extracted}
            snapshot_data["end"] = {"time_s": time_s, "rx_pos": rx_position_for_time(config, time_s), "paths": extracted}

    export_snapshot_visualizations(config, output_paths, snapshot_data)
    return summary


def run_fallback_backend(config: Dict, output_paths: Dict) -> List[Dict[str, float]]:
    mi = try_import_mitsuba()
    mitsuba_scene = None
    if mi is not None and output_paths["mitsuba_xml"].exists():
        try:
            mitsuba_scene_path = prepare_ascii_safe_scene(output_paths)
            mitsuba_scene = mi.load_file(str(mitsuba_scene_path))
            print(f"Loaded Mitsuba scene from {safe_path_text(mitsuba_scene_path)}")
        except Exception as exc:
            print(f"Warning: Could not load Mitsuba scene: {safe_exception_text(exc)}")
            print("Continuing with fallback path generation (no geometry validation)...")
    elif not output_paths["mitsuba_xml"].exists():
        print(f"Warning: Mitsuba XML file not found at {safe_path_text(output_paths['mitsuba_xml'])}")
        print("Continuing with fallback path generation (no geometry validation)...")

    if output_paths["scene_metadata"].exists():
        with output_paths["scene_metadata"].open("r", encoding="utf-8") as handle:
            json.load(handle)

    total_steps = simulation_step_count(config)
    mid_step = total_steps // 2
    summary: List[Dict[str, float]] = []
    snapshot_data: Dict[str, Dict] = {}
    with TraceCsvWriter(output_paths["trace_csv"]) as writer:
        for step_idx, (time_s, extracted) in enumerate(fallback_paths(config, mitsuba_scene=mitsuba_scene, mi=mi)):
            summary_point = _append_rows(writer, time_s, extracted)
            summary.append(summary_point)

            if step_idx == 0:
                snapshot_data["start"] = {"time_s": time_s, "rx_pos": rx_position_for_time(config, time_s), "paths": extracted}
            if step_idx == mid_step:
                snapshot_data["mid"] = {"time_s": time_s, "rx_pos": rx_position_for_time(config, time_s), "paths": extracted}
            snapshot_data["end"] = {"time_s": time_s, "rx_pos": rx_position_for_time(config, time_s), "paths": extracted}

    export_snapshot_visualizations(config, output_paths, snapshot_data, mitsuba_scene=mitsuba_scene, mi=mi)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sionna RT with Mitsuba-assisted fallback.")
    parser.add_argument(
        "--config",
        default=str(ROOT / "phase1_pipeline" / "config" / "config.yaml"),
        help="Path to the pipeline YAML configuration file.",
    )
    parser.add_argument("--force-fallback", action="store_true", help="Skip Sionna RT and use fallback.")
    args = parser.parse_args()

    config = load_config(args.config)
    output_paths = resolve_output_paths(config)
    backend = "sionna"
    try:
        if args.force_fallback:
            raise RuntimeError("Fallback explicitly requested.")
        summary = run_sionna_backend(config, output_paths)
    except Exception as exc:
        backend = "fallback"
        print(f"Sionna RT backend unavailable or failed: {safe_exception_text(exc)}")
        summary = run_fallback_backend(config, output_paths)

    export_validation_plots(summary, output_paths["doppler_plot"], output_paths["path_count_plot"])

    print(f"\n{'=' * 60}")
    print(f"Ray-tracing backend: {backend}")
    print(f"{'=' * 60}")
    print(f"Trace CSV: {safe_path_text(output_paths['trace_csv'])}")
    print(f"Doppler plot: {safe_path_text(output_paths['doppler_plot'])}")
    print(f"Path-count plot: {safe_path_text(output_paths['path_count_plot'])}")

    output_dir = output_paths["mitsuba_xml"].parent
    ray_viz_files = sorted(output_dir.glob("rays_3d_*.png"))
    coverage_files = sorted(output_dir.glob("coverage_rays_*.png"))
    if ray_viz_files:
        print("\n3D Ray Visualizations:")
        for viz_file in ray_viz_files:
            print(f"  - {viz_file.name}")
    else:
        print("\nNote: No 3D ray visualizations generated (no valid paths found)")
    if coverage_files:
        print("\nSample-style coverage visualizations:")
        for viz_file in coverage_files:
            print(f"  - {viz_file.name}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
