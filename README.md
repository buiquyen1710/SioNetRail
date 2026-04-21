# SioNetRail

Mo phong kenh truyen 5G mmWave 30 GHz cho duong sat toc do cao bang scene 3D + Sionna RT.

Repository hien tai da duoc canh chinh cho kich ban `unified_3000m`:

- 1 scene dai 3000 m
- 5 tram gNB `TX1..TX5`
- 1 quy dao RX chay xuyen suot toan tuyen
- output MPC CSV phuc vu ns-3/SioLENA

README nay tap trung vao muc tieu: chay du an bang backend `sionna` thuc su, khong phai `fallback`.

## 1. Trang thai da xac minh

Da kiem tra tren may hien tai:

- project path: `C:\Users\asela\OneDrive\Members\K67.BuiVanQuyen\SioNetRail`
- Python dang dung: `C:\Users\asela\anaconda3\python.exe`
- `mitsuba`, `sionna`, `drjit`: import duoc
- scene `output_unified/scene.xml` da load duoc bang `sionna.rt.load_scene()`
- da xac minh chay tuan tu backend `sionna` cho ca 5 tram `TX1..TX5` voi tap mau ngan

Luu y:

- Full run 5 tram bang Sionna RT co the rat lau.
- Neu log co `backend=fallback` thi ban chua chay ray tracing vat ly that.

## 2. Cau truc pipeline

Pipeline tong quat:

1. Doc `phase1_pipeline/config/config.yaml`
2. Sinh scene Mitsuba `scene.xml` va `meshes/*.obj`
3. Nap scene vao `sionna.rt`
4. Ray tracing rieng cho tung gNB
5. Xuat MPC CSV, bieu do Doppler, so luong path, anh 3D ray

Entrypoint chinh:

- Full pipeline: `python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml`
- Export scene procedural: `python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml`
- Ray tracing: `python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml`

## 3. Moi truong khuyen nghi

### 3.1. Neu may da co moi truong dang chay duoc

Uu tien dung dung interpreter dang hoat dong va da import duoc:

```powershell
python --version
python -c "import mitsuba, sionna, drjit; print('OK')"
```

### 3.2. Neu ban muon tao moi moi truong

Khuyen nghi Python `3.10` hoac `3.11` de de tuong thich hon voi ecosystem Sionna/Mitsuba.

Vi du voi conda:

```powershell
conda create -n sionetrail python=3.11 -y
conda activate sionetrail
pip install pyyaml numpy matplotlib mitsuba sionna-rt
```

Neu can Blender:

- cai Blender 4.x
- dam bao `blender.exe` co trong `PATH`

### 3.3. Kiem tra nhanh dependency

```powershell
@'
mods = ["mitsuba", "sionna", "drjit"]
for m in mods:
    try:
        __import__(m)
        print(f"{m}: OK")
    except Exception as e:
        print(f"{m}: FAIL -> {type(e).__name__}: {e}")
'@ | python -
```

## 4. Luu y quan trong de chay duoc Sionna RT that

Project nay da duoc sua de phu hop voi version `sionna.rt` dang co tren may:

- Scene exporter procedural da chuyen BSDF sang schema ma `sionna.rt` chap nhan.
- Cac material khong hop le o `30 GHz` da duoc map sang material ITU hop le:
  - ground -> concrete
  - granite -> marble
  - copper -> metal
- Visualization bang plain Mitsuba cho `itu-radio-material` da duoc tach khoi luong solver, tranh lam hong variant/plugin state cua Sionna.

He qua:

- anh `*_rays_scene_*.png` khong con la output chinh trong luong ray tracing
- anh `*_rays_3d_*.png` va `*_coverage_*.png` van duoc xuat binh thuong

## 5. Quy trinh chay chi tiet

Tat ca lenh ben duoi duoc chay trong thu muc goc project:

```powershell
cd C:\Users\asela\OneDrive\Members\K67.BuiVanQuyen\SioNetRail
```

### Buoc 1. Kiem tra config dang su dung

Config mac dinh:

`phase1_pipeline/config/config.yaml`

Kiem tra nhanh:

```powershell
Get-Content phase1_pipeline\config\config.yaml
```

Nhung tham so quan trong hien tai:

- `scenario.type: unified_3000m`
- `simulation.frequency_hz: 30000000000.0`
- `ray_tracing.max_depth: 6`
- `ray_tracing.max_num_paths: 4000`
- `ray_tracing.samples_per_src: 3000`

### Buoc 2. Sinh lai scene Mitsuba

Lenh:

```powershell
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
```

Ban phai thay file:

- `phase1_pipeline/output_unified/scene.xml`
- `phase1_pipeline/output_unified/meshes/*.obj`
- `phase1_pipeline/output_unified/scene_metadata.json`

### Buoc 3. Kiem tra scene co nap duoc vao Sionna RT khong

Buoc nay rat quan trong. Neu khong qua buoc nay, full run se roi ve `fallback`.

```powershell
@'
import os, sys
from pathlib import Path

candidates = [
    Path("C:/Program Files/LLVM/bin/LLVM-C.dll"),
    Path("C:/Program Files (x86)/LLVM/bin/LLVM-C.dll"),
    Path(sys.executable).resolve().parent / "Library" / "bin" / "LLVM-C.dll",
    Path(sys.executable).resolve().parent / "lib" / "LLVM-C.dll",
]

conda_prefix = os.environ.get("CONDA_PREFIX")
if conda_prefix:
    candidates.append(Path(conda_prefix) / "Library" / "bin" / "LLVM-C.dll")

for p in candidates:
    if p.exists():
        os.environ["DRJIT_LIBLLVM_PATH"] = str(p)
        break

from sionna.rt import load_scene
scene = load_scene(r"phase1_pipeline/output_unified/scene.xml", merge_shapes=False)
print("load_scene: OK")
print("num objects:", len(scene.objects))
'@ | python -
```

Neu thanh cong, ban se thay:

```text
load_scene: OK
```

### Buoc 4. Kiem tra backend `sionna` bang bai test ngan

Day la bai test khuyen nghi truoc khi full run, vi full run rat lau.

```powershell
@'
from phase1_pipeline.common import load_config, resolve_output_paths
from phase1_pipeline.raytracing.run_sionna_rt import fallback_trajectory_samples, run_sionna_backend
from phase1_pipeline.scenarios import all_base_stations, station_label

config = load_config("phase1_pipeline/config/config.yaml")
output_paths = resolve_output_paths(config)
samples = fallback_trajectory_samples(config)
test_samples = [samples[0], samples[len(samples)//2], samples[-1]]

for index, station in enumerate(all_base_stations(config)):
    label = station_label(station, index)
    summary = run_sionna_backend(config, output_paths, station, index, test_samples)
    print(label, "backend=sionna", "samples=", len(summary))
'@ | python -
```

Ket qua mong doi:

```text
TX1 backend=sionna
TX2 backend=sionna
TX3 backend=sionna
TX4 backend=sionna
TX5 backend=sionna
```

Neu buoc nay qua, kha nang cao la full run cung se dung backend that.

### Buoc 5. Chay ray tracing day du bang Sionna RT

Lenh chinh:

```powershell
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
```

Ban khong duoc thay `--force-fallback`.

Trong log, moi tram phai co dang:

```text
[TX1] backend=sionna ...
[TX2] backend=sionna ...
[TX3] backend=sionna ...
[TX4] backend=sionna ...
[TX5] backend=sionna ...
```

Neu log ghi `backend=fallback` thi ray tracing vat ly that da that bai tai tram do.

### Buoc 6. Chay full pipeline neu muon ca scene export + RT trong 1 lenh

```powershell
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```

Lenh nay:

1. Sinh scene
2. Xuat Mitsuba XML
3. Chay Sionna RT
4. Xuat CSV va hinh

### Buoc 7. Chay fallback co chu dich de doi chieu

Chi dung khi ban muon so sanh backend:

```powershell
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml --force-fallback
```
### Tong hop cac lenh chay full cac kich ban so sanh
cd C:\Users\asela\OneDrive\Members\K67.BuiVanQuyen\SioNetRail
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
python -m phase1_pipeline.postprocess.apply_train_blockage --config phase1_pipeline/config/config.yaml


## 6. Output sau khi chay

Thu muc chinh:

`phase1_pipeline/output_unified/`

### 6.1. Output hinh hoc

- `scene.xml`
- `scene_metadata.json`
- `meshes/*.obj`
- `railway_scene_unified.blend` neu chay bang Blender

### 6.2. Output trace

- `mpc_tx1_viaductA.csv`
- `mpc_tx2_ground.csv`
- `mpc_tx3_tunnel.csv`
- `mpc_tx4_viaductF.csv`
- `mpc_tx5_portal.csv`

Schema CSV:

```text
timestamp_ns,path_id,delay_s,amplitude_real,amplitude_imag,phase_rad,aoa_theta_rad,aoa_phi_rad,aod_theta_rad,aod_phi_rad,doppler_hz,los_flag
```

### 6.3. Output tong hop

- `doppler_vs_time.png`
- `path_count_vs_time.png`
- `trace_manifest.json`

### 6.4. Output theo tung tram

- `{station}_doppler_vs_time.png`
- `{station}_path_count_vs_time.png`
- `{station}_rays_3d_start_*.png`
- `{station}_rays_3d_mid_*.png`
- `{station}_rays_3d_end_*.png`
- `{station}_coverage_start_*.png`
- `{station}_coverage_mid_*.png`
- `{station}_coverage_end_*.png`

## 7. Cach xac nhan ban dang chay vat ly that

Khong du vao viec co CSV hay khong. Phai kiem tra:

1. `load_scene()` qua duoc
2. Log ghi `backend=sionna`
3. `trace_manifest.json` co truong `backend` bang `sionna`

Kiem tra nhanh manifest:

```powershell
Get-Content phase1_pipeline\output_unified\trace_manifest.json
```

Neu dung, trong moi entry phai co:

```text
"backend": "sionna"
```

## 8. Full run mat bao lau

Khong co con so co dinh, phu thuoc vao:

- GPU/CUDA hay chi LLVM
- `samples_per_src`
- `max_num_paths`
- so luong mau tren trajectory

Voi config hien tai:

- `samples_per_src: 3000`
- `max_num_paths: 4000`
- trajectory rat dai

nen full run co the rat lau.

Neu can test nhanh truoc, hay dung bai test ngan o Buoc 4.

## 9. Blender branch

Neu muon xuat `.blend`:

```powershell
blender --background --python phase1_pipeline/blender/generate_scene.py -- --config phase1_pipeline/config/config.yaml
```

Sau do co the export XML tu `.blend`:

```powershell
blender phase1_pipeline/output_unified/railway_scene_unified.blend --background --python phase1_pipeline/export/export_mitsuba.py -- --config phase1_pipeline/config/config.yaml
```

Tuy nhien, voi kich ban `unified_3000m`, procedural exporter da du de chay Sionna RT that, khong bat buoc phai qua Blender.

## 10. Troubleshooting

### 10.1. `backend=fallback`

Nguyen nhan thuong gap:

- import `sionna` hoac `mitsuba` loi
- `scene.xml` khong load duoc vao `sionna.rt`
- variant/plugin cua Mitsuba bi doi sai

Cach xu ly:

1. Chay lai Buoc 2
2. Chay lai Buoc 3
3. Chay bai test ngan Buoc 4

### 10.2. Loi LLVM tren Windows

Neu can, set bien moi truong:

```powershell
$env:DRJIT_LIBLLVM_PATH="C:\Program Files\LLVM\bin\LLVM-C.dll"
```

Hoac dung ban LLVM trong `conda`.

### 10.3. Muon xoa output cu

Xoa thu cong:

`phase1_pipeline/output_unified/`

roi chay lai tu Buoc 2.

### 10.4. Plain Mitsuba khong render duoc `itu-radio-material`

Day la hanh vi binh thuong trong setup hien tai.

- khong anh huong toi solver `sionna`
- chi anh huong toi viec render scene bang plain Mitsuba
- project van xuat `rays_3d` va `coverage` binh thuong

## 11. Lenh nen dung hang ngay

Neu chi can workflow an toan:

```powershell
cd C:\Users\asela\OneDrive\Members\K67.BuiVanQuyen\SioNetRail
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
Get-Content phase1_pipeline\output_unified\trace_manifest.json
```

Muc tieu cuoi cung:

- scene export thanh cong
- log hien `backend=sionna`
- manifest xac nhan `"backend": "sionna"`
