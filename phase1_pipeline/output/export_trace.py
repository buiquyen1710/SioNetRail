from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt

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
