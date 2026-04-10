# SioNetRail

Cross-layer 5G mmWave simulation for high-speed railways with procedural scene generation, Mitsuba export, trace generation for ns-3, and visualization outputs.

## Pipeline

The repository supports two scene-generation modes:

1. Blender mode
   - Generates the railway scene in Blender
   - Saves `.blend`
   - Exports Mitsuba XML + OBJ meshes from Blender
2. Direct fallback mode
   - Used automatically when Blender is not installed or not on `PATH`
   - Builds Mitsuba XML + OBJ meshes directly from `config.yaml`
   - Still supports ray tracing, CSV export, and visualization generation

## Main commands

Run the full pipeline:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```

Force the propagation fallback solver:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml --force-fallback
```

Run only the ray-tracing stage:

```bash
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
```

## Outputs

Main generated files:

- `phase1_pipeline/output/ns3_trace.csv`
- `phase1_pipeline/output/doppler_vs_time.png`
- `phase1_pipeline/output/path_count_vs_time.png`
- `phase1_pipeline/output/coverage_rays_start_t*.png`
- `phase1_pipeline/output/coverage_rays_mid_t*.png`
- `phase1_pipeline/output/coverage_rays_end_t*.png`
- `phase1_pipeline/output/rays_3d_start_t*.png`
- `phase1_pipeline/output/rays_3d_mid_t*.png`
- `phase1_pipeline/output/rays_3d_end_t*.png`

The sample-style coverage images contain:

- a received-power heatmap
- white ray overlays
- gNB marker
- train marker and train body drawing
- track and barriers

## Dependencies

Core:

```bash
pip install pyyaml matplotlib numpy
```

Optional:

```bash
pip install mitsuba
pip install sionna-rt
```

Optional for full Blender mode:

- Blender 4.x with `blender` or `blender.exe` available

## Notes

- If Mitsuba or Sionna RT is unavailable, the code falls back gracefully where possible.
- If Blender is unavailable, the runner now exports a consistent Mitsuba scene directly, so `scene.xml` and mesh files are still regenerated together.
- Train geometry is included in both Blender-generated scenes and fallback-exported scenes.
