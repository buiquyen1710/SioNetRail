from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

try:
    import yaml
    print("DEBUG yaml object:", yaml)
    print("DEBUG yaml file:", getattr(yaml, "__file__", "no file"))
    print("DEBUG yaml has safe_load:", hasattr(yaml, "safe_load"))
except ImportError as exc:  # pragma: no cover
    yaml = None
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None


SPEED_OF_LIGHT_M_S = 299_792_458.0


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_config(config_path: str | os.PathLike[str]) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to load config files. Install it with `pip install pyyaml`."
        ) from YAML_IMPORT_ERROR

    path = Path(config_path).resolve()
    with path.open("r", encoding="utf-8") as handle:
        print("DEBUG before safe_load, yaml:", yaml)
        print("DEBUG before safe_load, type(yaml):", type(yaml))
        print("DEBUG before safe_load, has safe_load:", hasattr(yaml, "safe_load"))
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config at {path} did not parse as a mapping.")
    data["_config_path"] = str(path)
    data["_repo_root"] = str(repo_root())
    return data


def dump_json(path: str | os.PathLike[str], payload: Dict[str, Any]) -> None:
    target = ensure_parent(Path(path).resolve())
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def resolve_output_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    cfg_path = Path(config["_config_path"])
    base = cfg_path.parent.parent
    out_cfg = config["paths"]
    resolved = {}
    for key, rel in out_cfg.items():
        resolved[key] = (base / rel).resolve()
    for key in ("blend_file", "mitsuba_xml", "trace_csv", "doppler_plot", "path_count_plot", "scene_metadata"):
        ensure_parent(resolved[key])
    resolved["mesh_dir"].mkdir(parents=True, exist_ok=True)
    return resolved


def railway_duration_s(config: Dict[str, Any]) -> float:
    sim = config["simulation"]
    duration = sim.get("duration_s")
    if duration is not None:
        return float(duration)
    scene_length = float(config["scene"]["length_m"])
    speed = float(sim["train_speed_kmh"]) / 3.6
    return scene_length / speed


def wavelength_m(frequency_hz: float) -> float:
    return SPEED_OF_LIGHT_M_S / frequency_hz


def parse_cli(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--config",
        default=str(repo_root() / "phase1_pipeline" / "config" / "config.yaml"),
        help="Path to the YAML configuration file.",
    )
    return parser


def vector_length(vector: Iterable[float]) -> float:
    x, y, z = vector
    return math.sqrt(x * x + y * y + z * z)


def normalize(vector: Iterable[float]) -> Tuple[float, float, float]:
    x, y, z = vector
    length = vector_length((x, y, z))
    if length == 0:
        raise ValueError("Cannot normalize a zero vector.")
    return (x / length, y / length, z / length)


def dot(a: Iterable[float], b: Iterable[float]) -> float:
    ax, ay, az = a
    bx, by, bz = b
    return ax * bx + ay * by + az * bz


def subtract(a: Iterable[float], b: Iterable[float]) -> Tuple[float, float, float]:
    ax, ay, az = a
    bx, by, bz = b
    return (ax - bx, ay - by, az - bz)


def add(a: Iterable[float], b: Iterable[float]) -> Tuple[float, float, float]:
    ax, ay, az = a
    bx, by, bz = b
    return (ax + bx, ay + by, az + bz)


def scale(vector: Iterable[float], factor: float) -> Tuple[float, float, float]:
    x, y, z = vector
    return (x * factor, y * factor, z * factor)
