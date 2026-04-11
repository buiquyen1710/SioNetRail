# SioNetRail

Cross-layer 5G mmWave simulation for high-speed railways with procedural scene generation, Mitsuba export, trace generation for ns-3, and visualization outputs.

## Yêu cầu hệ thống

### Phần mềm bắt buộc
- **Python 3.8+** (khuyến nghị 3.9-3.11)
- **Windows 10/11** (hoặc Linux/MacOS)
- **Git** (để clone repository)

### Phần mềm tùy chọn
- **Blender 4.x** (để tạo scene 3D đầy đủ)
- **LLVM 14.x+** (cho visualization Mitsuba)
- **CUDA** (tùy chọn cho GPU acceleration)

## Cài đặt

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd SioNetRail
```

### Bước 2: Cài đặt Python environment

#### Sử dụng Anaconda/Miniconda (khuyến nghị)

```bash
# Tạo environment mới
conda create -n sionna-rt python=3.10 -y
conda activate sionna-rt

# Cài đặt dependencies cơ bản
pip install pyyaml matplotlib numpy
```

#### Hoặc sử dụng venv

```bash
# Tạo virtual environment
python -m venv sionna_env
sionna_env\Scripts\activate  # Windows
# source sionna_env/bin/activate  # Linux/Mac

# Cài đặt dependencies cơ bản
pip install pyyaml matplotlib numpy
```

### Bước 3: Cài đặt Sionna RT (cho ray tracing)

```bash
pip install sionna-rt
```

### Bước 4: Cài đặt Mitsuba (cho visualization)

```bash
pip install mitsuba
```

### Bước 5: Cài đặt LLVM (cho Windows - bắt buộc)

#### Phương pháp 1: Từ conda (khuyến nghị)

```bash
conda install -c conda-forge llvm=14 -y
```

#### Phương pháp 2: Từ website (nếu conda lỗi)

1. Tải LLVM từ: https://llvm.org/releases/download.html
2. Chọn LLVM 14.x hoặc 15.x cho Windows
3. Cài đặt vào `C:\Program Files\LLVM`
4. Set biến môi trường:

```bash
setx DRJIT_LIBLLVM_PATH "C:\Program Files\LLVM\bin\LLVM-C.dll"
```

### Bước 6: Cài đặt Blender (tùy chọn - cho scene 3D đầy đủ)

1. Tải Blender 4.x từ: https://www.blender.org/download/
2. Cài đặt và đảm bảo `blender.exe` có trong PATH
3. Hoặc thêm vào PATH thủ công

### Bước 7: Kiểm tra cài đặt

```bash
# Kiểm tra Python
python --version

# Kiểm tra packages
python -c "import sionna; print('Sionna OK')"
python -c "import mitsuba as mi; print('Mitsuba OK')"

# Kiểm tra LLVM (Windows)
python -c "import pathlib; print('LLVM OK' if pathlib.Path(r'C:\Program Files\LLVM\bin\LLVM-C.dll').exists() or pathlib.Path(r'C:\Users\%USERNAME%\anaconda3\Library\bin\LLVM-C.dll').exists() else 'LLVM missing')"

# Kiểm tra Blender (tùy chọn)
blender --version
```

## Cách chạy

### Chạy full pipeline (khuyến nghị)

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```

Pipeline sẽ:
1. Tạo scene Blender (.blend) nếu Blender có sẵn
2. Xuất scene Mitsuba (scene.xml + meshes)
3. Chạy ray tracing với Sionna
4. Tạo file trace CSV cho ns-3
5. Tạo biểu đồ visualization

### Chạy từng bước riêng lẻ

#### Bước 1: Tạo scene Blender (nếu có Blender)

```bash
# Tạo scene 3D và lưu file .blend
blender --background --python "phase1_pipeline/blender/generate_scene.py" -- --config "phase1_pipeline/config/config.yaml"
```

Output: `phase1_pipeline/output/railway_scene.blend`

#### Bước 2: Xuất scene Mitsuba

##### Nếu có file .blend:

```bash
blender "phase1_pipeline/output/railway_scene.blend" --background --python "phase1_pipeline/export/export_mitsuba.py" -- --config "phase1_pipeline/config/config.yaml"
```

##### Nếu không có Blender (fallback mode):

```bash
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
```

Output:
- `phase1_pipeline/output/scene.xml`
- `phase1_pipeline/output/meshes/*.obj`
- `phase1_pipeline/output/scene_metadata.json`

#### Bước 3: Chạy ray tracing

```bash
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
```

Output:
- `phase1_pipeline/output/ns3_trace.csv` (dữ liệu chính)
- `phase1_pipeline/output/doppler_vs_time.png`
- `phase1_pipeline/output/path_count_vs_time.png`
- Các file hình ảnh visualization

### Tùy chọn chạy

#### Force fallback solver (không dùng Sionna RT)

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml --force-fallback
```

#### Skip Blender (nếu đã có scene)

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml --skip-blender
```

## Outputs

### File chính
- `phase1_pipeline/output/ns3_trace.csv` - Dữ liệu ray tracing cho ns-3
- `phase1_pipeline/output/scene.xml` - Scene Mitsuba
- `phase1_pipeline/output/scene_metadata.json` - Metadata scene

### Biểu đồ
- `phase1_pipeline/output/doppler_vs_time.png` - Biểu đồ Doppler shift
- `phase1_pipeline/output/path_count_vs_time.png` - Số đường truyền theo thời gian

### Hình ảnh visualization
- `phase1_pipeline/output/rays_3d_*.png` - Ray paths 3D
- `phase1_pipeline/output/coverage_rays_*.png` - Coverage maps với ray overlays

## Troubleshooting

### Lỗi "Blender executable not found"
- Cài đặt Blender và thêm vào PATH
- Hoặc dùng fallback mode (tự động)

### Lỗi "LLVM shared library not found"
- Cài đặt LLVM như hướng dẫn ở Bước 5
- Set biến `DRJIT_LIBLLVM_PATH`

### Lỗi conda dependency
- Update conda: `conda update -n base -c defaults conda -y`
- Hoặc cài LLVM từ website

### Pipeline chạy chậm
- Giảm `max_num_paths` trong `config.yaml`
- Sử dụng GPU nếu có CUDA

### Hình ảnh visualization không render
- Kiểm tra LLVM đã cài đúng chưa
- Restart terminal sau khi set `DRJIT_LIBLLVM_PATH`

## Cấu hình

File `phase1_pipeline/config/config.yaml` chứa tất cả tham số:

- **scene**: Kích thước scene (length, width)
- **railway**: Thông số đường ray
- **train**: Thông số tàu (tốc độ, kích thước)
- **base_station**: Vị trí trạm gốc
- **simulation**: Tham số mô phỏng (tần số, timestep)
- **ray_tracing**: Tham số ray tracing

## Ghi chú

- Nếu Mitsuba/Sionna không khả dụng, code sẽ fallback gracefully
- Blender mode tạo scene 3D đầy đủ hơn fallback mode
- Train geometry luôn được include trong cả hai mode
- Pipeline hỗ trợ cả LOS và NLOS paths
