from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from phase1_pipeline.common import ensure_parent


TRACE_HEADER = [
    "timestamp_ns",
    "path_id",
    "delay_s",
    "amplitude_real",
    "amplitude_imag",
    "phase_rad",
    "aoa_theta_rad",
    "aoa_phi_rad",
    "aod_theta_rad",
    "aod_phi_rad",
    "doppler_hz",
    "los_flag",
]


def _safe_exception_text(exc: Exception) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return str(exc).encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")


def _safe_path_text(path: str | Path) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return str(path).encode(encoding, errors="backslashreplace").decode(encoding, errors="replace")


class TraceCsvWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = ensure_parent(Path(path).resolve())
        self.handle = self.path.open("w", encoding="utf-8", newline="")
        self.writer = csv.DictWriter(self.handle, fieldnames=TRACE_HEADER)
        self.writer.writeheader()

    def write_rows(self, rows: Iterable[Dict[str, float | int]]) -> None:
        for row in rows:
            self.writer.writerow(row)

    def close(self) -> None:
        self.handle.close()

    def __enter__(self) -> "TraceCsvWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def export_validation_plots(
    summary: List[Dict[str, float]],
    doppler_plot_path: str | Path,
    path_count_plot_path: str | Path,
) -> None:
    doppler_plot_path = ensure_parent(Path(doppler_plot_path).resolve())
    path_count_plot_path = ensure_parent(Path(path_count_plot_path).resolve())

    time_ms = [point["time_s"] * 1e3 for point in summary]
    max_abs_doppler = [point["max_abs_doppler_hz"] for point in summary]
    path_count = [point["path_count"] for point in summary]

    plt.figure(figsize=(10, 4.5))
    plt.plot(time_ms, max_abs_doppler, linewidth=1.2)
    plt.xlabel("Time (ms)")
    plt.ylabel("Max |Doppler| (Hz)")
    plt.title("Doppler Shift vs Time")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(doppler_plot_path, dpi=180)
    plt.close()

    plt.figure(figsize=(10, 4.5))
    plt.plot(time_ms, path_count, linewidth=1.2)
    plt.xlabel("Time (ms)")
    plt.ylabel("Number of Paths")
    plt.title("Resolved Paths vs Time")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path_count_plot_path, dpi=180)
    plt.close()


def _box_faces(center: Tuple[float, float, float], size: Tuple[float, float, float]) -> List[List[Tuple[float, float, float]]]:
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
    return [
        [vertices[i] for i in (0, 1, 2, 3)],
        [vertices[i] for i in (4, 5, 6, 7)],
        [vertices[i] for i in (0, 1, 5, 4)],
        [vertices[i] for i in (1, 2, 6, 5)],
        [vertices[i] for i in (2, 3, 7, 6)],
        [vertices[i] for i in (3, 0, 4, 7)],
    ]


def _add_box(ax, center, size, facecolor, edgecolor=None, alpha: float = 1.0, linewidth: float = 0.5) -> None:
    collection = Poly3DCollection(
        _box_faces(center, size),
        facecolors=facecolor,
        edgecolors=edgecolor or facecolor,
        linewidths=linewidth,
        alpha=alpha,
    )
    ax.add_collection3d(collection)


def _path_points(path, tx_position, rx_position):
    if hasattr(path, "points") and path.points and len(path.points) >= 2:
        return list(path.points)
    return [tx_position, rx_position]


def _mirror_point_across_ground(point: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (point[0], point[1], -point[2])


def _mirror_point_across_y_plane(point: Tuple[float, float, float], plane_y: float) -> Tuple[float, float, float]:
    return (point[0], 2.0 * plane_y - point[1], point[2])


def _complex_field_from_sources(
    points_xyz: np.ndarray,
    tx_position: Tuple[float, float, float],
    frequency_hz: float,
    barrier_y: Tuple[float, float],
) -> np.ndarray:
    wavelength = 299_792_458.0 / frequency_hz
    k = 2.0 * math.pi / wavelength
    tx = np.array(tx_position, dtype=float)
    ground_img = np.array(_mirror_point_across_ground(tx_position), dtype=float)
    barrier_imgs = [np.array(_mirror_point_across_y_plane(tx_position, barrier_y[0]), dtype=float), np.array(_mirror_point_across_y_plane(tx_position, barrier_y[1]), dtype=float)]

    contributions = [
        (tx, 1.0 + 0.0j),
        (ground_img, -0.55 + 0.0j),
        (barrier_imgs[0], -0.72 + 0.0j),
        (barrier_imgs[1], -0.72 + 0.0j),
    ]

    field = np.zeros(points_xyz.shape[0], dtype=np.complex128)
    for source, gain in contributions:
        distances = np.linalg.norm(points_xyz - source[None, :], axis=1)
        distances = np.maximum(distances, 1.0)
        field += gain * (wavelength / (4.0 * math.pi * distances)) * np.exp(-1j * k * distances)
    return field


def _power_map_db(
    tx_position: Tuple[float, float, float],
    scene_cfg: Dict,
    barrier_cfg: Dict,
    train_cfg: Dict,
    grid_resolution: int = 140,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.linspace(-float(scene_cfg["length_m"]) / 2.0, float(scene_cfg["length_m"]) / 2.0, grid_resolution)
    y = np.linspace(-float(scene_cfg["width_m"]) / 2.0, float(scene_cfg["width_m"]) / 2.0, max(40, grid_resolution // 3))
    xx, yy = np.meshgrid(x, y)
    rx_height = float(train_cfg.get("receiver_height_m", 3.8))
    points = np.stack([xx.ravel(), yy.ravel(), np.full(xx.size, rx_height)], axis=1)
    barrier_y = (
        float(barrier_cfg["center_offset_m"]) - float(barrier_cfg["thickness_m"]) / 2.0,
        -float(barrier_cfg["center_offset_m"]) + float(barrier_cfg["thickness_m"]) / 2.0,
    )
    field = _complex_field_from_sources(points, tx_position, float(scene_cfg.get("frequency_hz_override", 30e9)), barrier_y)
    power_db = 20.0 * np.log10(np.maximum(np.abs(field), 1e-12))
    power_db -= np.max(power_db)
    power_db = np.clip(power_db, -130.0, 0.0)
    return xx, yy, power_db.reshape(xx.shape)


def export_rays_3d_visualization(
    tx_position: Tuple[float, float, float],
    rx_position: Tuple[float, float, float],
    paths: List,
    output_path: str | Path,
    title: str = "Ray Tracing Visualization",
) -> None:
    output_path = ensure_parent(Path(output_path).resolve())

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(*tx_position, color="red", s=300, marker="*", label="TX (Base Station)", zorder=10)
    ax.scatter(*rx_position, color="blue", s=200, marker="o", label="RX (Train)", zorder=10)

    los_count = 0
    nlos_count = 0
    for path in paths:
        points = _path_points(path, tx_position, rx_position)
        is_los = getattr(path, "los_flag", 0) == 1
        color = "green" if is_los else "orange"
        linestyle = "-" if is_los else "--"
        linewidth = 2.5 if is_los else 1.8
        los_count += int(is_los)
        nlos_count += int(not is_los)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        ax.plot(xs, ys, zs, color=color, linestyle=linestyle, linewidth=linewidth, alpha=0.85)
        if not is_los:
            for point in points[1:-1]:
                ax.scatter(point[0], point[1], point[2], color="darkred", s=25, alpha=0.65, zorder=5)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.view_init(elev=20, azim=45)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"3D Ray visualization saved: {_safe_path_text(output_path)} ({los_count} LOS + {nlos_count} NLOS paths)")


def export_rays_3d_with_mitsuba(
    mitsuba_xml_path: str | Path,
    tx_position: Tuple[float, float, float],
    rx_position: Tuple[float, float, float],
    paths: List,
    output_path: str | Path,
    title: str = "Ray Tracing with Scene",
) -> None:
    try:
        import mitsuba as mi

        for variant in ("scalar_rgb", "llvm_ad_rgb", "cuda_ad_rgb"):
            try:
                mi.set_variant(variant)
                break
            except Exception:
                continue
    except ImportError:
        print("Warning: Mitsuba not available, using simple 3D visualization instead")
        return None

    try:
        output_path = ensure_parent(Path(output_path).resolve())
        scene = mi.load_file(str(mitsuba_xml_path))
        img = mi.render(scene, spp=8)
        img_array = img[:, :]
        if isinstance(img_array, tuple):
            img_array = img_array[0]
        img_np = np.array(img_array)
        if img_np.dtype != np.uint8:
            img_np = (np.clip(img_np, 0, 1) * 255).astype(np.uint8)
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.imshow(img_np)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.axis("off")
        los_count = sum(1 for p in paths if getattr(p, "los_flag", 0) == 1)
        nlos_count = len(paths) - los_count
        ax.text(
            0.02,
            0.98,
            f"Paths: {los_count} LOS + {nlos_count} NLOS",
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"3D Scene with rays saved: {_safe_path_text(output_path)}")
        return str(output_path)
    except Exception as exc:
        print(f"Warning: Could not render Mitsuba scene: {_safe_exception_text(exc)}")
        return None


def export_sample_style_scene(
    tx_position: Tuple[float, float, float],
    rx_position: Tuple[float, float, float],
    paths: List,
    output_path: str | Path,
    scene_cfg: Dict,
    barrier_cfg: Dict,
    train_cfg: Dict,
    title: str = "Coverage and Ray Paths",
) -> None:
    output_path = ensure_parent(Path(output_path).resolve())
    xx, yy, power_db = _power_map_db(tx_position, scene_cfg, barrier_cfg, train_cfg)
    cmap = cm.get_cmap("viridis")
    norm = mcolors.Normalize(vmin=-130.0, vmax=0.0)
    fig, ax = plt.subplots(figsize=(12.5, 6.8))

    image = ax.imshow(
        power_db,
        extent=[float(xx.min()), float(xx.max()), float(yy.min()), float(yy.max())],
        origin="lower",
        cmap=cmap,
        norm=norm,
        aspect="auto",
        interpolation="bilinear",
    )

    length = float(scene_cfg["length_m"])
    width = float(scene_cfg["width_m"])
    barrier_offset = float(barrier_cfg["center_offset_m"])
    barrier_height = float(barrier_cfg["height_m"])
    barrier_thickness = float(barrier_cfg["thickness_m"])
    for y_center in (barrier_offset, -barrier_offset):
        ax.add_patch(
            Rectangle(
                (-length / 2.0, y_center - barrier_thickness / 2.0),
                length,
                barrier_thickness,
                facecolor=(0.80, 0.79, 0.74, 0.95),
                edgecolor=(0.63, 0.63, 0.60, 1.0),
                linewidth=1.0,
                zorder=4,
            )
        )

    rail_half = float(train_cfg.get("track_visual_offset_m", 0.7175))
    ax.plot([-length / 2.0, length / 2.0], [rail_half, rail_half], color="#676B74", linewidth=2.0, alpha=0.95, zorder=5)
    ax.plot([-length / 2.0, length / 2.0], [-rail_half, -rail_half], color="#676B74", linewidth=2.0, alpha=0.95, zorder=5)

    train_length = float(train_cfg.get("length_m", 25.0))
    train_width = float(train_cfg.get("width_m", 3.2))
    train_body = Rectangle(
        (rx_position[0] - train_length / 2.0, rx_position[1] - train_width / 2.0),
        train_length,
        train_width,
        facecolor=(0.92, 0.96, 0.99, 0.98),
        edgecolor=(0.30, 0.44, 0.54, 1.0),
        linewidth=1.4,
        zorder=8,
    )
    ax.add_patch(train_body)
    ax.add_patch(
        Rectangle(
            (rx_position[0] - train_length * 0.2, rx_position[1] - train_width * 0.26),
            train_length * 0.38,
            train_width * 0.52,
            facecolor=(0.17, 0.35, 0.49, 0.95),
            edgecolor="none",
            zorder=9,
        )
    )

    ax.add_patch(Circle((tx_position[0], tx_position[1]), radius=3.8, facecolor="#7ED4F7", edgecolor="none", zorder=10))
    ax.add_patch(Circle((rx_position[0], rx_position[1]), radius=3.8, facecolor="#88E0B7", edgecolor="none", zorder=10))

    for path in paths:
        points = _path_points(path, tx_position, rx_position)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        ax.plot(xs, ys, color="white", linewidth=1.8, alpha=0.85, zorder=7)
        for point in points[1:-1]:
            ax.add_patch(Circle((point[0], point[1]), radius=1.0, facecolor="white", edgecolor="none", zorder=8))

    cbar = fig.colorbar(image, ax=ax, pad=0.012, fraction=0.03)
    cbar.set_label("Relative received power (dB)")

    focus_margin_x = max(120.0, train_length * 2.0)
    focus_margin_y = max(22.0, barrier_offset + 6.0)
    x_min = max(-length / 2.0, min(tx_position[0], rx_position[0]) - focus_margin_x)
    x_max = min(length / 2.0, max(tx_position[0], rx_position[0]) + focus_margin_x)
    y_min = max(-width / 2.0, min(tx_position[1], rx_position[1], -barrier_offset) - focus_margin_y)
    y_max = min(width / 2.0, max(tx_position[1], rx_position[1], barrier_offset) + focus_margin_y)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Sample-style coverage visualization saved: {_safe_path_text(output_path)}")
