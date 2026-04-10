from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from phase1_pipeline.common import load_config, repo_root, resolve_output_paths


def run_command(command, cwd: Path) -> None:
    print("Running:", " ".join(str(part) for part in command))
    subprocess.run(command, cwd=str(cwd), check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full Blender -> Mitsuba -> ray-tracing pipeline.")
    parser.add_argument(
        "--config",
        default=str(repo_root() / "phase1_pipeline" / "config" / "config.yaml"),
        help="Path to the pipeline YAML configuration file.",
    )
    parser.add_argument(
        "--blender-executable",
        default=os.environ.get("BLENDER_BIN", "blender"),
        help="Blender executable path. Defaults to BLENDER_BIN or `blender`.",
    )
    parser.add_argument("--force-fallback", action="store_true", help="Skip Sionna RT and run the fallback solver.")
    parser.add_argument("--skip-blender", action="store_true", help="Assume the scene and XML already exist.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    repo = repo_root()
    config = load_config(config_path)
    output_paths = resolve_output_paths(config)

    if not args.skip_blender:
        run_command(
            [
                args.blender_executable,
                "--background",
                "--python",
                str(repo / "phase1_pipeline" / "blender" / "generate_scene.py"),
                "--",
                "--config",
                str(config_path),
            ],
            cwd=repo,
        )
        run_command(
            [
                args.blender_executable,
                str(output_paths["blend_file"]),
                "--background",
                "--python",
                str(repo / "phase1_pipeline" / "export" / "export_mitsuba.py"),
                "--",
                "--config",
                str(config_path),
            ],
            cwd=repo,
        )

    command = [sys.executable, "-m", "phase1_pipeline.raytracing.run_sionna_rt", "--config", str(config_path)]
    if args.force_fallback:
        command.append("--force-fallback")
    run_command(command, cwd=repo)


if __name__ == "__main__":
    main()
