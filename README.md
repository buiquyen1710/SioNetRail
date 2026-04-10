<<<<<<< HEAD
# High-Speed Railway Propagation Pipeline

This project builds a complete automated pipeline for a 30 GHz outdoor railway scenario:

1. Generate a 1000 m x 200 m railway scene in Blender
2. Export the geometry to Mitsuba 3 XML plus OBJ meshes
3. Run ray tracing with Sionna RT when available
4. Fall back to a Mitsuba-assisted geometric solver when Sionna RT is unavailable
5. Stream an ns-3 compatible CSV trace and validation plots to disk

The output trace columns are:

`timestamp_ns,path_id,delay_s,amplitude_real,amplitude_imag,phase_rad,aoa_theta_rad,aoa_phi_rad,aod_theta_rad,aod_phi_rad,doppler_hz,los_flag`

## Project Layout

```text
phase1_pipeline/
  blender/
    generate_scene.py
  export/
    export_mitsuba.py
  raytracing/
    compute_doppler.py
    run_sionna_rt.py
  output/
    export_trace.py
  config/
    config.yaml
  common.py
  run_pipeline.py
```

## Dependencies

Core Python packages:

```bash
pip install pyyaml matplotlib numpy
```

Optional ray-tracing backends:

```bash
pip install mitsuba
pip install sionna-rt
```

Blender is required for scene generation/export. Mitsuba is required for XML loading and the fallback solver validation. Sionna RT is preferred for full path solving.

## Blender Setup

1. Install Blender 4.x and make sure `blender` or `blender.exe` is available on your `PATH`.
2. No external Blender add-on is required. The exporter is implemented in [export_mitsuba.py](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/export/export_mitsuba.py).
3. The scene generator uses real-world metric units and writes:
   - [railway_scene.blend](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/railway_scene.blend)
   - [scene_metadata.json](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/scene_metadata.json)

Generate only the Blender scene:

```bash
blender --background --python phase1_pipeline/blender/generate_scene.py -- --config phase1_pipeline/config/config.yaml
```

## Mitsuba Setup

Install Mitsuba 3:

```bash
pip install mitsuba
```

Export the current `.blend` file to Mitsuba XML:

```bash
blender phase1_pipeline/output/railway_scene.blend --background --python phase1_pipeline/export/export_mitsuba.py -- --config phase1_pipeline/config/config.yaml
```

The exporter writes:

- [scene.xml](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/scene.xml)
- one OBJ mesh per object in [output/meshes](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/meshes)

## Sionna RT Setup

Install Sionna RT:

```bash
pip install sionna-rt
```

The ray-tracing runner uses:

- `load_scene()` to read Mitsuba XML
- `Transmitter` / `Receiver` for gNB and train positions
- `PathSolver()` for path extraction

If Sionna RT import or execution fails, the pipeline automatically falls back to a Mitsuba-assisted deterministic solver that resolves LOS, ground reflection, and both barrier reflections while still writing the same ns-3 trace schema.

Run ray tracing only:

```bash
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
```

Force the fallback solver:

```bash
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml --force-fallback
```

## Full Pipeline

Run everything end to end:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml --blender-executable blender
```

If the scene already exists and only the propagation stage needs to run:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml --skip-blender
```

## Outputs

Main artifacts:

- [ns3_trace.csv](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/ns3_trace.csv)
- [doppler_vs_time.png](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/doppler_vs_time.png)
- [path_count_vs_time.png](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/output/path_count_vs_time.png)

The CSV is streamed row by row, so the full trace does not need to be buffered in memory.

## Notes

- Default train speed is `350 km/h` (`97.22 m/s`).
- Default carrier frequency is `30 GHz`.
- Default timestep is `1 ms`.
- If `duration_s` in [config.yaml](/C:/Users/QuYen/OneDrive - Hanoi University of Science and Technology/Documents/New project/phase1_pipeline/config/config.yaml) is left empty, the run spans the full 1000 m track.
=======
# SioNetRail
Cross-layer 5G mmWave simulation for high-speed railways with ray tracing, ns-3, adaptive handover, and real-time digital twin visualization.
>>>>>>> 8e80f4c045da0b20fd400da433c66f9434b0815e
