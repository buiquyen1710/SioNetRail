# SioNetRail

Mô phỏng kênh truyền 5G mmWave 30 GHz cho đường sắt tốc độ cao bằng pipeline:

1. Khai báo kịch bản trong `phase1_pipeline/config/config.yaml`
2. Sinh scene hình học
3. Xuất scene Mitsuba `scene.xml` + `meshes/*.obj`
4. Ray tracing cho từng gNB
5. Xuất trace CSV theo schema dùng cho ns-3/SioLENA
6. Xuất biểu đồ và ảnh kiểm tra

Hiện tại repository đã được chỉnh sang kịch bản tích hợp `unified_3000m`: một scene 3000 m duy nhất, 5 gNB, một quỹ đạo RX xuyên suốt toàn tuyến.

## Trạng thái hiện tại của source

- Kịch bản mặc định: `unified_3000m`
- File cấu hình chính: `phase1_pipeline/config/config.yaml`
- Output chính của kịch bản tích hợp: `phase1_pipeline/output_unified/`
- Pipeline chạy được theo cả 2 nhánh:
  - Blender -> `.blend` -> Mitsuba XML
  - procedural exporter fallback nếu máy không có Blender
- Với kịch bản tích hợp hiện tại, nếu máy có Blender thì pipeline có thể sinh `.blend` trực tiếp

Lý do: `run_pipeline.py` chủ động bỏ qua nhánh Blender khi `scenario.type = unified_3000m`, vì phần dựng scene tích hợp hiện được hiện thực trực tiếp trong exporter procedural.

## Yêu cầu môi trường

### Bắt buộc

- Python 3.10+ khuyến nghị
- `pyyaml`
- `numpy`
- `matplotlib`

Cài nhanh:

```bash
pip install pyyaml numpy matplotlib
```

### Tùy chọn nhưng nên có

- `mitsuba`
- `sionna-rt`
- LLVM cho Mitsuba/Sionna RT trên Windows
- Blender 4.x nếu muốn dùng nhánh Blender cho các scene cũ

Ví dụ:

```bash
pip install mitsuba sionna-rt
```

## Cách chạy nhanh

Chạy full pipeline cho kịch bản tích hợp:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```

Nếu muốn ép dùng fallback solver:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml --force-fallback
```

Pipeline trên sẽ:

1. Đọc `config.yaml`
2. Sinh scene tích hợp 3000 m ra `output_unified/scene.xml` và `output_unified/meshes/`
3. Chạy ray tracing riêng cho từng gNB `TX1..TX5`
4. Xuất 5 file CSV MPC theo cùng chuỗi timestamp
5. Xuất biểu đồ Doppler, số path và ảnh trực quan hóa

## Chạy từng bước

### 1. Sinh scene Mitsuba

Kịch bản tích hợp hiện tại dùng procedural export:

```bash
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
```

Output:

- `phase1_pipeline/output_unified/scene.xml`
- `phase1_pipeline/output_unified/meshes/*.obj`
- `phase1_pipeline/output_unified/scene_metadata.json`

### 2. Chạy ray tracing

```bash
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
```

Hoặc:

```bash
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml --force-fallback
```

### 3. Chạy toàn bộ pipeline

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```

## Cách xuất file `.blend`

### Trạng thái hỗ trợ hiện tại

Với `scenario.type = unified_3000m`, source hiện đã hỗ trợ sinh `.blend` qua Blender.

Lệnh:

```bash
blender --background --python phase1_pipeline/blender/generate_scene.py -- --config phase1_pipeline/config/config.yaml
```

Output mặc định:

```text
phase1_pipeline/output_unified/railway_scene_unified.blend
```

Sau khi có `.blend`, có thể xuất Mitsuba XML bằng:

```bash
blender phase1_pipeline/output_unified/railway_scene_unified.blend --background --python phase1_pipeline/export/export_mitsuba.py -- --config phase1_pipeline/config/config.yaml
```

### Khi nào vẫn dùng procedural fallback

Nếu máy không có Blender hoặc Blender không nằm trong `PATH`, `run_pipeline.py` sẽ tự rơi về:

```bash
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
```

Khi đó vẫn sinh được:

- `scene.xml`
- `meshes/*.obj`
- `scene_metadata.json`

nhưng sẽ không có `.blend`.

## Các file output của kịch bản tích hợp

Thư mục chính:

`phase1_pipeline/output_unified/`

### Output hình học

- `railway_scene_unified.blend`: file Blender của scene tích hợp, nếu chạy bằng Blender
- `scene.xml`: scene Mitsuba dùng cho ray tracing
- `scene_metadata.json`: metadata của scene, module, gNB, trajectory RX
- `meshes/*.obj`: mesh thành phần của scene

### Output trace chính

- `mpc_tx1_viaductA.csv`
- `mpc_tx2_ground.csv`
- `mpc_tx3_tunnel.csv`
- `mpc_tx4_viaductF.csv`
- `mpc_tx5_portal.csv`

Tất cả các file trên:

- có cùng chuỗi timestamp
- cùng schema:

```text
timestamp_ns,path_id,delay_s,amplitude_real,amplitude_imag,phase_rad,aoa_theta_rad,aoa_phi_rad,aod_theta_rad,aod_phi_rad,doppler_hz,los_flag
```

### Output tổng hợp

- `doppler_vs_time.png`: tổng hợp tất cả TX
- `path_count_vs_time.png`: tổng hợp tất cả TX
- `trace_manifest.json`: manifest các file trace và plot per-TX

### Output per-TX

Mỗi TX có thêm:

- `{station}_doppler_vs_time.png`
- `{station}_path_count_vs_time.png`
- `{station}_rays_3d_start_*.png`
- `{station}_rays_3d_mid_*.png`
- `{station}_rays_3d_end_*.png`
- `{station}_rays_scene_start_*.png`
- `{station}_rays_scene_mid_*.png`
- `{station}_rays_scene_end_*.png`
- `{station}_coverage_start_*.png`
- `{station}_coverage_mid_*.png`
- `{station}_coverage_end_*.png`

## Ý nghĩa file cấu hình

`phase1_pipeline/config/config.yaml` hiện chứa:

- `scenario`: loại kịch bản
- `scene`: kích thước toàn tuyến
- `railway`: tham số ray
- `noise_barriers`: vị trí và kích thước rào
- `catenary`: tham số cột và dây điện
- `base_stations`: danh sách 5 gNB
- `train`: tham số đoàn tàu và vị trí anten RX
- `trajectory`: quỹ đạo RX chi tiết theo từng module
- `simulation`: tần số, tốc độ tàu, timestep
- `ray_tracing`: tham số solver
- `paths`: nơi lưu output

## Tài liệu đi kèm nên đọc

- `SioNetRail_Unified_Scene_3000m.md`: mô tả chi tiết kịch bản tích hợp đã setup trong source
- `SioNetRail_Unified_Output_Assessment.md`: giải thích và đánh giá chi tiết các output hiện tại

## Lưu ý quan trọng khi đọc kết quả

- Kết quả hiện tại có thể đến từ `fallback` backend nếu Sionna RT không khả dụng hoặc khi dùng `--force-fallback`
- Khi đọc kết quả trong `trace_manifest.json`, cần kiểm tra trường `backend`
- Nếu backend là `fallback`, output phù hợp để kiểm tra logic pipeline và xu hướng kênh truyền, nhưng chưa phải mức fidelity cuối cùng như khi chạy Sionna RT đầy đủ

## Troubleshooting

### Không import được Mitsuba hoặc Sionna RT

- kiểm tra môi trường Python đang dùng
- cài lại:

```bash
pip install mitsuba sionna-rt
```

### Lỗi LLVM trên Windows

- cài LLVM qua conda hoặc installer
- set `DRJIT_LIBLLVM_PATH`

### Muốn chạy lại sạch output

- xóa thủ công thư mục `phase1_pipeline/output_unified/`
- chạy lại pipeline

### Muốn sinh `.blend` cho scene tích hợp

- cài Blender và đảm bảo `blender.exe` có trong `PATH`
- sau đó chạy:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```
