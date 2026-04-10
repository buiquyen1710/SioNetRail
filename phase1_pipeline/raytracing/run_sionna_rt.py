from __future__ import annotations

import argparse
import cmath
import json
import math
import sys
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
    railway_duration_s,
    resolve_output_paths,
    scale,
    subtract,
    vector_length,
    wavelength_m,
)
from phase1_pipeline.output.export_trace import TraceCsvWriter, export_validation_plots
from phase1_pipeline.raytracing.compute_doppler import angles_from_vector, compute_doppler_hz, unit_vector_from_angles


def try_import_sionna():
    try:
        import mitsuba as mi
        for variant in ("cuda_ad_rgb", "llvm_ad_rgb", "scalar_rgb"):
            try:
                mi.set_variant(variant)
                break
            except Exception:
                continue
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


def simulation_times(config: Dict) -> Iterator[Tuple[int, float]]:
    timestep_s = float(config["simulation"]["timestep_s"])
    duration_s = railway_duration_s(config)
    steps = max(1, int(math.floor(duration_s / timestep_s)) + 1)
    for idx in range(steps):
        yield idx, idx * timestep_s


def rx_position_for_time(config: Dict, time_s: float) -> Tuple[float, float, float]:
    length = float(config["scene"]["length_m"])
    speed_m_s = float(config["simulation"]["train_speed_kmh"]) / 3.6
    z = float(config["train"]["receiver_height_m"])
    x = -length / 2.0 + min(length, speed_m_s * time_s)
    y = float(config["train"].get("lateral_offset_m", 0.0))
    return (x, y, z)


def tx_position(config: Dict) -> Tuple[float, float, float]:
    return tuple(float(v) for v in config["base_station"]["position_m"])


def train_velocity(config: Dict) -> Tuple[float, float, float]:
    return (float(config["simulation"]["train_speed_kmh"]) / 3.6, 0.0, 0.0)


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
    interaction_depth = interactions.shape[0]
    interaction_matrix = interactions.reshape(interaction_depth, -1, interactions.shape[-1])[:, 0, :]

    velocity = train_velocity(config)
    frequency_hz = float(config["simulation"]["frequency_hz"])
    extracted = []
    for idx in range(coeffs.shape[-1]):
        if idx >= len(valid) or not bool(valid[idx]):
            continue
        coeff = complex(coeffs[idx])
        aoa_theta = float(theta_r[idx])
        aoa_phi = float(phi_r[idx])
        arrival_from_source = unit_vector_from_angles(aoa_theta, aoa_phi)
        propagation_to_receiver = (-arrival_from_source[0], -arrival_from_source[1], -arrival_from_source[2])
        doppler = compute_doppler_hz(frequency_hz, velocity, propagation_to_receiver)
        los_flag = 1 if np.all(interaction_matrix[:, idx] == 0) else 0
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
            "bounds": {"x": (-scene_length / 2.0, scene_length / 2.0), "z": (0.0, barrier_height)},
        },
        {
            "name": "barrier_south",
            "point": (0.0, -barrier_center + barrier_thickness / 2.0, barrier_height / 2.0),
            "normal": (0.0, 1.0, 0.0),
            "gain": complex(-0.72, 0.0),
            "bounds": {"x": (-scene_length / 2.0, scene_length / 2.0), "z": (0.0, barrier_height)},
        },
    ]
    ground_plane = {
        "point": (0.0, 0.0, 0.0),
        "normal": (0.0, 0.0, 1.0),
        "gain": complex(-0.55, 0.0),
        "bounds": {"x": (-scene_length / 2.0, scene_length / 2.0), "y": (-scene_width / 2.0, scene_width / 2.0)},
    }

    for _, time_s in simulation_times(config):
        rx = rx_position_for_time(config, time_s)
        candidates = []
        if mitsuba_scene is None or segment_clear(mitsuba_scene, mi, tx, rx):
            candidates.append(build_candidate_from_points("los", [tx, rx], complex(1.0, 0.0), config, 1))

        mirrored_tx = reflect_point_across_plane(tx, ground_plane["point"], ground_plane["normal"])
        reflection = line_plane_intersection(mirrored_tx, rx, ground_plane["point"], ground_plane["normal"])
        if reflection is not None:
            within_ground = (
                ground_plane["bounds"]["x"][0] <= reflection[0] <= ground_plane["bounds"]["x"][1]
                and ground_plane["bounds"]["y"][0] <= reflection[1] <= ground_plane["bounds"]["y"][1]
            )
            clear = True
            if mitsuba_scene is not None:
                clear = segment_clear(mitsuba_scene, mi, tx, reflection) and segment_clear(
                    mitsuba_scene, mi, add(reflection, (0.0, 0.0, 1e-3)), rx
                )
            if within_ground and clear:
                candidates.append(
                    build_candidate_from_points("ground_reflection", [tx, reflection, rx], ground_plane["gain"], config, 0)
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
                offset = scale(barrier["normal"], 1e-3)
                clear = segment_clear(mitsuba_scene, mi, tx, subtract(reflection, offset)) and segment_clear(
                    mitsuba_scene, mi, add(reflection, offset), rx
                )
            if within_barrier and clear:
                candidates.append(
                    build_candidate_from_points(barrier["name"], [tx, reflection, rx], barrier["gain"], config, 0)
                )

        # Keep output usable even when geometric visibility tests reject all paths.
        if not candidates:
            candidates.append(build_candidate_from_points("los_nominal", [tx, rx], complex(1.0, 0.0), config, 1))
        yield time_s, candidates


def run_sionna_backend(config: Dict, output_paths: Dict) -> List[Dict[str, float]]:
    imports = try_import_sionna()
    if imports is None:
        raise RuntimeError("Sionna RT is not available.")

    scene = imports["load_scene"](str(output_paths["mitsuba_xml"]), merge_shapes=False)
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

    summary = []
    with TraceCsvWriter(output_paths["trace_csv"]) as writer:
        for _, time_s in simulation_times(config):
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
            summary.append(
                {
                    "time_s": time_s,
                    "path_count": len(rows),
                    "max_abs_doppler_hz": max((abs(row["doppler_hz"]) for row in rows), default=0.0),
                }
            )
    return summary


def run_fallback_backend(config: Dict, output_paths: Dict) -> List[Dict[str, float]]:
    mi = try_import_mitsuba()
    mitsuba_scene = mi.load_file(str(output_paths["mitsuba_xml"])) if mi is not None else None
    if output_paths["scene_metadata"].exists():
        with output_paths["scene_metadata"].open("r", encoding="utf-8") as handle:
            json.load(handle)

    summary = []
    with TraceCsvWriter(output_paths["trace_csv"]) as writer:
        for time_s, extracted in fallback_paths(config, mitsuba_scene=mitsuba_scene, mi=mi):
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
            summary.append(
                {
                    "time_s": time_s,
                    "path_count": len(rows),
                    "max_abs_doppler_hz": max((abs(row["doppler_hz"]) for row in rows), default=0.0),
                }
            )
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
        print(f"Sionna RT backend unavailable or failed: {exc}")
        summary = run_fallback_backend(config, output_paths)

    export_validation_plots(summary, output_paths["doppler_plot"], output_paths["path_count_plot"])
    print(f"Ray-tracing backend: {backend}")
    print(f"Trace CSV: {output_paths['trace_csv']}")
    print(f"Doppler plot: {output_paths['doppler_plot']}")
    print(f"Path-count plot: {output_paths['path_count_plot']}")


if __name__ == "__main__":
    main()
