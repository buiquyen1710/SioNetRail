# SioNetRail Unified Output Assessment After Channel-Model Refinement

## 1. Mục tiêu của lần chỉnh sửa này
Mục tiêu của đợt chỉnh sửa hiện tại không phải chỉ làm cho `sionna.rt` chạy được, mà là kéo mô hình tiến gần hơn tới ý tưởng kịch bản kênh HSR mmWave đã setup:

- giảm tính quá lý tưởng của anten `1x1 isotropic`
- bổ sung các cơ chế lan truyền còn thiếu trong solver: `diffuse reflection`, `diffraction`, `edge diffraction`
- làm hình học tunnel/portal bớt “sạch quá mức” bằng các phần tử clutter hợp lý
- bổ sung cơ chế lọc các path quá yếu theo dynamic range để kết quả gần hơn với trace đo thực tế
- giữ tất cả trong phạm vi mà bản `sionna.rt` đang cài trên máy thực sự hỗ trợ

## 2. Những thay đổi tôi đã thực hiện trực tiếp trong source code

### 2.1. `phase1_pipeline/config/config.yaml`
Tôi đã nâng cấu hình ray tracing và anten như sau:

- `max_depth: 8` thay cho `6`
- `max_num_paths: 6000` thay cho `4000`
- `samples_per_src: 5000` thay cho `3000`
- bật `enable_diffuse_reflection: true`
- bật `enable_diffraction: true`
- bật `enable_edge_diffraction: true`
- bật `enable_diffraction_lit_region: true`
- thêm `min_relative_path_gain_db: 40.0`
- thêm block `antenna.tx_array` và `antenna.rx_array`

Cấu hình anten mới:

- TX: `8x4`, spacing `0.5 lambda`, pattern `tr38901`, polarization `VH`
- RX: `2x2`, spacing `0.5 lambda`, pattern `tr38901`, polarization `VH`

### 2.2. `phase1_pipeline/raytracing/run_sionna_rt.py`
Tôi đã sửa solver theo ba ý chính:

1. Thêm hàm `build_planar_array()` để đọc cấu hình mảng anten từ `config.yaml` thay vì hard-code `1x1 iso`.
2. Bật các cờ vật lý còn thiếu khi gọi `PathSolver(...)`:
   - `diffuse_reflection`
   - `diffraction`
   - `edge_diffraction`
   - `diffraction_lit_region`
3. Thêm hậu xử lý `min_relative_path_gain_db` trong `extract_sionna_paths()` để loại các path yếu hơn path mạnh nhất quá `40 dB`.

### 2.3. `phase1_pipeline/export/export_mitsuba_fallback.py`
Tôi đã sửa exporter theo bốn ý chính:

1. Mở rộng phần sinh BSDF để hỗ trợ `scattering_coefficient` và `xpd_coefficient` của `itu-radio-material`.
2. Tạo `material_library()` để gom toàn bộ tham số vật liệu vào một nơi.
3. Đổi các mặt tunnel sang `mat-itu_concrete_rough` thay vì concrete lý tưởng hơn.
4. Thêm `append_tunnel_clutter()` để đưa các đối tượng phụ vào tunnel/portal:
   - cable tray hai bên hầm
   - service box dọc hầm
   - portal jamb/lintel ở hai đầu portal

Ngoài ra, tôi đã thử dùng ground kiểu `medium_dry_ground`, nhưng bản `sionna.rt` đang cài chỉ cho phép các ITU ground model đó trong dải `1-10 GHz`, không hợp lệ ở `30 GHz`. Vì vậy tôi đã rút lại thay đổi đó và dùng `mat-itu_concrete_rough` làm proxy hợp lệ ở `30 GHz`. Đây là quyết định đúng về mặt mô phỏng vì tránh extrapolation vượt khỏi miền hiệu lực của mô hình vật liệu ITU.

## 3. Cơ sở khoa học cho các chỉnh sửa

### 3.1. Bật diffuse reflection và dùng rougher material là đúng hướng
Tài liệu chính thức của Sionna RT nêu rõ `RadioMaterial` và `ITURadioMaterial` hỗ trợ `scattering_coefficient` và diffuse reflection như một cách mô hình hóa roughness hiệu dụng của bề mặt. Điều này đặc biệt quan trọng khi scene hình học còn sạch và bề mặt thực tế không phải gương lý tưởng.

Nguồn:
- [Sionna Radio Materials](https://nvlabs.github.io/sionna/rt/api/radio_materials.html)

Hệ quả khoa học:
- tunnel và portal không còn chỉ gồm các phản xạ gương mạnh
- năng lượng được phân tán sang các thành phần yếu hơn và góc đến đa dạng hơn
- channel hợp lý hơn cho môi trường hạ tầng thực có roughness, khe, thiết bị phụ và không đồng nhất bề mặt

### 3.2. Bật diffraction và edge diffraction là cần thiết cho portal/transition
Bản `PathSolver` của Sionna RT đang cài trên máy hỗ trợ trực tiếp:

- `diffraction`
- `edge_diffraction`
- `diffraction_lit_region`

Điều này phù hợp với vùng portal, mép barrier, mép kết cấu hầm, nơi mà thành phần nhiễu xạ đóng vai trò quan trọng khi LOS suy yếu hoặc bị che một phần.

Nguồn:
- [Sionna Radio Materials](https://nvlabs.github.io/sionna/rt/api/radio_materials.html)
- [Sionna RT PathSolver source/docs](https://nvlabs.github.io/sionna/)

Hệ quả khoa học:
- portal không còn thiên lệch quá mạnh về `LOS + specular`
- xuất hiện các path trung gian yếu nhưng bền hơn về mặt hình học
- phù hợp hơn với trực giác đo đạc ở vùng chuyển tiếp ngoài hầm <-> trong hầm

### 3.3. Thay anten isotropic bằng pattern `tr38901` là đúng với bài toán 5G/FR2
3GPP TR 38.901 mô tả phần tử anten định hướng với gain phần tử cực đại `8 dBi`, beamwidth hữu hạn và panel array phân cực chéo. Đây là cơ sở chuẩn để tránh mô hình `1x1 isotropic` quá lạc quan.

Nguồn:
- [ETSI TR 138 901 V17.1.0](https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/17.01.00_60/tr_138901v170100p.pdf)

Hệ quả khoa học:
- không phải mọi path hợp lệ hình học đều được anten “nhìn thấy” mạnh như nhau
- path lệch góc lớn bị suy giảm hợp lý hơn
- số path hữu dụng và delay spread hiệu dụng giảm về hướng thực tế hơn so với isotropic

### 3.4. Thêm clutter tunnel/portal là đúng với bản chất kênh HSR tunnel
Các tổng quan và mô hình tunnel HSR chỉ ra rằng tunnel có waveguide effect, nhiều thành phần phản xạ/scattering, và thống kê kênh bị chi phối mạnh bởi hình học vỏ hầm cộng với scatterer phụ chứ không chỉ bốn mặt phẳng trơn.

Nguồn:
- [Channel measurements and models for high-speed train wireless communication systems in tunnel scenarios: a survey](https://researchportal.hw.ac.uk/en/publications/channel-measurements-and-models-for-high-speed-train-wireless-com)
- [3D non-stationary GBSMs for high-speed train tunnel channels](https://researchportal.hw.ac.uk/en/publications/3d-non-stationary-gbsms-for-high-speed-train-tunnel-channels/)
- [Millimeter Wave Propagation in Long Corridors and Tunnels—Theoretical Model and Experimental Verification](https://www.mdpi.com/2079-9292/9/5/707)

Hệ quả khoa học:
- tunnel vẫn giữ tính “giàu đường truyền” do hiệu ứng dẫn sóng và phản xạ nhiều lần
- nhưng kênh bớt sạch, bớt thuần specular, hợp lý hơn với môi trường có thiết bị phụ

### 3.5. Lọc path theo dynamic range là hợp lý khi dùng trace cho hệ thống
Trong đo đạc thực, channel sounder luôn có noise floor và dynamic range hữu hạn. Việc giữ mọi path rất yếu chỉ vì solver coi là hợp lệ sẽ làm phình trace theo hướng không phản ánh mức path mà hệ thống thực còn khai thác được. Vì vậy ngưỡng `40 dB` tương đối theo path mạnh nhất là một cách chuẩn hóa thực dụng và có cơ sở hệ thống.

## 4. Kết quả xác minh sau khi chỉnh sửa

### 4.1. Kiểm tra scene
Scene sau chỉnh sửa đã nạp thành công bằng `sionna.rt`:

- `scene_load_ok = true`
- `object_count = 162`

Số object tăng do đã thêm clutter tunnel/portal.

### 4.2. Kết quả kiểm tra ngắn 3 snapshot đại diện
Tôi đã chạy kiểm tra ngắn với 3 vị trí đại diện của đoàn tàu: đầu tuyến, giữa tuyến, cuối tuyến. Đây không phải full run toàn 3391 timestamp, nhưng đủ để đánh giá xu hướng vật lý sau khi chỉnh mô hình.

| Station | Avg paths | Max paths | LOS ratio theo row | Max |Doppler| (Hz) |
|---|---:|---:|---:|---:|
| TX1 | 4.667 | 11 | 0.071 | 9728.665 |
| TX2 | 2.000 | 3 | 0.167 | 9727.810 |
| TX3 | 11.333 | 26 | 0.029 | 9728.482 |
| TX4 | 4.000 | 8 | 0.083 | 9728.894 |
| TX5 | 1.667 | 2 | 0.000 | 9719.985 |

### 4.3. Diễn giải kết quả mới

#### TX3 tunnel
Đây là thay đổi quan trọng nhất.

Trước khi chỉnh, tunnel có xu hướng rất giàu path specular mạnh do hình học quá sạch và anten isotropic. Sau chỉnh sửa:

- tunnel vẫn là station giàu path nhất, điều này vẫn đúng với bản chất waveguide-like của tunnel
- nhưng path count đại diện giảm về mức hợp lý hơn trong short-run: `avg 11.333`, `max 26`
- LOS ratio rất thấp `0.029`, phù hợp hơn với trực giác vật lý của môi trường tunnel nhiều phản xạ và nhiều chướng ngại phụ

Đây là hướng cải thiện đúng. Tunnel vẫn “rich”, nhưng không còn quá “gương lý tưởng”.

#### TX5 portal
Portal sau khi bật diffraction và thêm portal edges cho kết quả sạch hơn về mặt vật lý:

- `avg_paths = 1.667`
- `LOS ratio = 0.000` trên 3 snapshot đại diện

Điều này cho thấy vùng chuyển tiếp đã bớt lệ thuộc vào LOS hình học đơn thuần. Với bài toán portal, đây là xu hướng đúng hơn so với phiên bản cũ vốn giữ LOS khá cao do thiếu diffraction và hình học portal quá sạch.

#### TX1 / TX4 viaduct
Viaduct vẫn giữ tính mở và ít path hơn tunnel, nhưng directional antenna + ngưỡng dynamic range đã cắt bớt các path lạc quan do isotropic trước đây.

- TX1: `avg_paths = 4.667`
- TX4: `avg_paths = 4.000`

Điều này hợp lý hơn cho kênh ngoài trời có ít tường bao hơn tunnel nhưng vẫn có phản xạ từ deck, barrier, mast, wire, pier.

#### TX2 ground
Ground section hiện cho số path thấp và gọn hơn:

- `avg_paths = 2.000`
- `max_paths = 3`

Điều này hợp lý với môi trường mở hơn, ít hiệu ứng dẫn sóng hơn tunnel.

#### Doppler
Các giá trị `max |doppler|` vẫn rất gần mốc lý thuyết khoảng `9728.95 Hz` tại `30 GHz`, `350 km/h`. Như vậy phần động học chính của mô hình vẫn đúng sau khi chỉnh source.

## 5. Đánh giá khoa học: mô hình mới đã cải thiện gì

### 5.1. Những điểm đã được khắc phục tốt

1. Đã loại bỏ giả thiết anten quá lý tưởng `1x1 isotropic`.
2. Đã bổ sung diffuse reflection có điều khiển thông qua rough material.
3. Đã bổ sung diffraction và edge diffraction cho vùng portal/transition.
4. Đã làm tunnel/portal bớt sạch bằng clutter hình học phụ.
5. Đã thêm dynamic-range pruning để trace hữu dụng hơn cho mô phỏng hệ thống.

### 5.2. Vì sao bộ kết quả mới hợp lý hơn
Bộ kết quả mới hợp lý hơn vì nó cùng lúc thay đổi ba lớp vật lý quan trọng:

- lớp anten: giảm thiên lệch isotropic
- lớp solver: bổ sung cơ chế lan truyền trước đây bị tắt
- lớp scene/material: bề mặt và hình học đã gần hạ tầng thực hơn

Nếu chỉ bật solver mà không đổi anten, path count vẫn có thể bị phình. Nếu chỉ đổi anten mà không thêm diffraction/diffuse, portal vẫn quá sạch. Nếu chỉ thêm clutter mà không có scattering, clutter cũng không phát huy hết ý nghĩa vật lý. Lần sửa này xử lý đồng thời cả ba lớp nên kết quả cân bằng hơn.

## 6. Điểm nào vẫn chưa được khắc phục hoàn toàn

### 6.1. Chưa có moving train blockage đúng nghĩa
`include_train_in_rt_scene` trong exporter hiện chỉ phù hợp với object tĩnh. Để mô phỏng self-blockage của thân tàu đúng nghĩa cho toàn trajectory, cần scene động theo từng snapshot hoặc cơ chế cập nhật hình học của đoàn tàu đồng bộ với vị trí RX. Tôi chưa bật tính năng này vì cách exporter hiện tại chỉ chèn được một train mesh tĩnh, nếu ép bật sẽ tạo sai lệch hình học còn lớn hơn.

### 6.2. Ground/outdoor material vẫn là proxy
Do bộ vật liệu ITU ground của Sionna hiện chỉ có hiệu lực tới `10 GHz`, còn bài toán này ở `30 GHz`, nên phần ground hiện dùng proxy concrete rough hợp lệ về mặt solver thay vì ground ITU thật. Đây là một hạn chế còn lại.

### 6.3. Chưa có calibration theo measurement
Mô hình hiện hợp lý hơn về mặt cơ chế vật lý, nhưng vẫn chưa phải mô hình “validated by measurement”. Muốn chốt fidelity cao hơn nữa cần:

- benchmark với dữ liệu đo HSR thực
- hiệu chỉnh roughness/scattering coefficient theo measurement
- hiệu chỉnh clutter density theo loại hầm thực tế

## 7. Kết luận thực dụng
Sau đợt chỉnh sửa này, mô hình hiện tại nên được gọi là:

`Sionna RT physical channel model with directional 3GPP-like arrays, diffuse reflection, diffraction, and tunnel/portal clutter proxies`

Tên gọi này chính xác hơn đáng kể so với phiên bản trước.

Nếu mục tiêu là:

- kiểm tra pipeline: tốt
- tạo trace vật lý hợp lý cho mô phỏng hệ thống: tốt hơn rõ rệt so với trước
- công bố fidelity cao hoặc bám sát measurement: vẫn chưa đủ, nhưng đã đi đúng hướng về mặt vật lý

## 8. Lệnh chạy lại full output sau chỉnh sửa
Chạy lại toàn bộ scene và trace:

```powershell
cd C:\Users\asela\OneDrive\Members\K67.BuiVanQuyen\SioNetRail
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
```

## 9. Khuyến nghị bước tiếp theo
Nếu muốn tăng thêm fidelity, thứ tự ưu tiên đúng nhất là:

1. thêm moving train blockage theo từng snapshot
2. đưa ground sang custom `radio-material` có tham số điện môi riêng ở `30 GHz`
3. hiệu chỉnh `scattering_coefficient` bằng benchmark đo thực hoặc sensitivity analysis
4. chạy lại full 3391 timestamp và cập nhật thống kê toàn tuyến
