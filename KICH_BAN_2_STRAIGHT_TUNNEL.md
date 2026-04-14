# Kịch Bản 2: Straight Tunnel

## 1. Mục đích của kịch bản

Kịch bản `Straight Tunnel` được thêm vào để mô phỏng môi trường hầm xuyên núi thẳng, nơi sự thay đổi điều kiện truyền sóng có thể xảy ra rất mạnh khi đoàn tàu tiến vào hoặc ra khỏi hầm. Đây là một trong những môi trường quan trọng nhất để nghiên cứu:

- suy hao đột ngột tại vùng cửa hầm
- sự thay đổi cấu trúc multipath
- hiệu ứng dẫn sóng (`waveguide effect`)
- và tính ổn định của handover/handover prediction

Trong một hầm thẳng, kênh truyền không giống môi trường ngoài trời:

- không gian truyền bị giới hạn bởi các mặt bê tông
- các tia phản xạ từ vách, trần, sàn có thể tồn tại lâu hơn
- kênh có xu hướng mang tính "corridor / guide" hơn là tán xạ tự do như ngoài trời

## 2. File cấu hình của kịch bản

Kịch bản này dùng file:

[config_straight_tunnel.yaml](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\config\config_straight_tunnel.yaml)

Các tham số chính:

- loại kịch bản: `straight_tunnel`
- chiều dài scene: `1000 m`
- chiều dài hầm: `800 m`
- bề rộng lòng hầm: `10 m`
- chiều cao lòng hầm: `7.5 m`
- độ dày vách/trần/sàn: `0.35 m`
- vật liệu bê tông theo ITU: `epsilon_r = 5.31`, `sigma = 0.02 S/m`
- tần số: `30 GHz`
- tốc độ tàu: `350 km/h`
- hai gNB đặt tại hai portal

## 3. Hình học đang dùng trong mô phỏng

### 3.1. Hầm

Hiện tại hầm được dựng dưới dạng hình chữ nhật kín:

- một sàn hầm
- hai vách bên
- một trần hầm

Điều này phù hợp với bài toán ray tracing cơ bản và đủ để sinh ra:

- tia LOS dọc trục hầm
- phản xạ từ tường trái/phải
- phản xạ từ sàn
- phản xạ từ trần

Nếu cần, về sau có thể mở rộng lên tiết diện vòm ellipse. Tuy nhiên với mục tiêu mô phỏng cơ bản về propagation và handover, hình chữ nhật là đủ tốt để nắm cơ chế vật lý chính.

### 3.2. Hai trạm gốc tại hai cửa hầm

Kịch bản hiện có:

- `west_portal_gnb` tại phía tây
- `east_portal_gnb` tại phía đông

Tuy nhiên để giữ nguyên format output và tránh làm vỡ pipeline hiện có, trace CSV hiện tại vẫn đang chạy với:

- một `active base station`

tức là một gNB được dùng làm nguồn phát chính trong mỗi lần chạy.

Trong config hiện tại:

- `base_station` là `west_portal_gnb`
- `portal_base_stations` chứa `east_portal_gnb`

Nghĩa là:

- cả hai gNB đều được dựng trong scene
- nhưng trace hiện chỉ được tính theo gNB phía tây

Đây là thiết kế có chủ đích để:

- giữ format output giống kịch bản 1
- nhưng vẫn sẵn sàng mở rộng sang `dual-gNB / handover` ở bước tiếp theo

## 4. Các file output của kịch bản 2

Toàn bộ output của hầm được ghi vào thư mục riêng:

`phase1_pipeline/output_tunnel`

Các file chính:

- [ns3_trace.csv](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\ns3_trace.csv)
- [doppler_vs_time.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\doppler_vs_time.png)
- [path_count_vs_time.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\path_count_vs_time.png)
- [coverage_rays_start_t0.000s.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\coverage_rays_start_t0.000s.png)
- [coverage_rays_mid_t5.000s.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\coverage_rays_mid_t5.000s.png)
- [coverage_rays_end_t9.500s.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\coverage_rays_end_t9.500s.png)
- [scene.xml](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\scene.xml)
- [scene_metadata.json](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\scene_metadata.json)

## 5. Cách chạy kịch bản 2

### 5.1. Export scene tunnel

```powershell
C:\Users\QuYen\anaconda3\envs\sionna-rt\python.exe -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config_straight_tunnel.yaml
```

### 5.2. Chạy ray tracing

```powershell
C:\Users\QuYen\anaconda3\envs\sionna-rt\python.exe -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config_straight_tunnel.yaml
```

### 5.3. Chạy full pipeline

```powershell
C:\Users\QuYen\anaconda3\envs\sionna-rt\python.exe -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config_straight_tunnel.yaml --skip-blender
```

Nếu máy có Blender và muốn generate `.blend`, có thể bỏ `--skip-blender`.

## 6. Ý nghĩa vật lý của từng output

### 6.1. `ns3_trace.csv`

Đây là file dữ liệu quan trọng nhất.

Mỗi dòng tương ứng với một `path` tại một `timestamp`, gồm:

- `timestamp_ns`: thời điểm
- `path_id`: số thứ tự path tại thời điểm đó
- `delay_s`: độ trễ đường truyền
- `amplitude_real`, `amplitude_imag`: hệ số kênh phức
- `phase_rad`: pha
- `aoa_*`, `aod_*`: góc đến/góc đi
- `doppler_hz`: Doppler của path
- `los_flag`: cờ LOS

Trong ngữ cảnh tunnel, file này cho biết:

- path trực tiếp dọc trục hầm còn mạnh đến đâu
- phản xạ từ tường/trần/sàn tạo thành bao nhiêu tia trội
- Doppler biến thiên thế nào khi tàu tiến vào sâu trong hầm

### 6.2. `doppler_vs_time.png`

Biểu đồ này cho biết trị tuyệt đối lớn nhất của Doppler theo thời gian.

Trong tunnel thẳng:

- nếu path mạnh nhất gần song song hướng chuyển động, Doppler sẽ gần `v/lambda`
- khi tàu đi qua vùng hình học đặc biệt, Doppler có thể giảm nếu path trội đổi sang một hướng khác

Nói cách khác, đồ thị này phản ánh:

- path nào đang chi phối tại mỗi thời điểm
- hướng chiếu của vận tốc lên phương truyền sóng

### 6.3. `path_count_vs_time.png`

Biểu đồ này cho biết số path trội được giữ lại theo thời gian.

Trong hầm, nếu mô hình bắt được mạnh hiệu ứng guide/reflection, số path có thể:

- ổn định trong một khoảng
- hoặc tăng ở vùng hình học thuận lợi hơn cho phản xạ

Nếu đồ thị gần như phẳng, điều đó thường có nghĩa:

- hoặc môi trường tunnel đang rất đối xứng và đều
- hoặc pipeline đang chỉ giữ các path chi phối nhất

### 6.4. `coverage_rays_*.png`

Các hình này dùng để minh họa:

- tương quan hình học giữa TX, RX và các path
- vùng cường độ thu tương đối
- số tia minh họa tại các snapshot đầu, giữa, cuối

Lưu ý:

- các đường trắng là ray visualization phục vụ diễn giải trực quan
- chúng được làm nhất quán với số path trong snapshot
- nhưng không nên xem chúng như bản đồ interaction point chính xác tuyệt đối của mọi bounce từ Sionna RT

### 6.5. `rays_3d_*.png`

Đây là ảnh 3D để nhìn trực tiếp cấu trúc truyền sóng trong scene.

Trong tunnel, các ảnh này đặc biệt hữu ích để thấy:

- path LOS chạy dọc trục hầm
- path phản xạ lên trần / xuống sàn / sang hai vách

## 7. Giải thích câu hỏi thường gặp: vào hầm có mất LOS không

Không phải lúc nào vào hầm cũng mất LOS.

Điều này phụ thuộc mạnh vào hình học của hầm.

### 7.1. Khi nào LOS vẫn tồn tại

Nếu hầm:

- thẳng
- không cong
- không có vật cản lớn chặn giữa trục
- TX và RX cùng nhìn dọc hành lang hầm

thì vẫn có một đường thẳng nối trực tiếp giữa TX và RX trong lòng hầm. Khi đó:

- LOS vẫn tồn tại
- nhưng đồng thời các path phản xạ từ tường/trần/sàn cũng mạnh hơn ngoài trời

Đó chính là lý do một hầm thẳng có thể vừa:

- còn LOS
- vừa có multipath kiểu waveguide

### 7.2. Khi nào LOS dễ mất

LOS dễ mất hơn nếu:

- hầm cong
- có khúc cua
- có tàu khác / vật cản lớn trong lòng hầm
- gNB đặt lệch ngoài portal hoặc không nhìn trực diện vào lòng hầm
- xét handover với cell ngoài trời khi train đi sâu vào trong hầm

Vì vậy, câu "vào hầm thì phải mất LOS" là đúng cho nhiều tình huống thực tế, nhưng **không đúng cho mọi hầm**. Với `Straight Tunnel` lý tưởng, LOS còn là điều hoàn toàn bình thường.

## 8. Vì sao tunnel thường có nhiều tia hơn ngoài trời

Trong ngoài trời mở, năng lượng nhiều khi tản đi vào không gian tự do.

Trong hầm, trường điện từ bị giam giữa:

- hai vách
- trần
- sàn

nên các phản xạ hữu ích có xu hướng được "giữ lại" trong corridor. Đây là lý do người ta thường nói hầm có hiệu ứng gần waveguide.

Tuy nhiên, "nhiều tia hơn" có thể được hiểu theo hai mức:

### 8.1. Nhiều tia vật lý thực sự tồn tại

Điều này gần như đúng.

### 8.2. Nhiều tia được giữ lại trong trace output

Điều này còn phụ thuộc vào:

- `max_depth`
- `samples_per_src`
- cách lọc path yếu
- việc có bật scattering/diffraction hay không
- việc pipeline có chỉ giữ path trội hay không

Vì vậy, một tunnel có thể có nhiều path vật lý hơn ngoài trời, nhưng file output cuối cùng vẫn chỉ hiện vài path mạnh nhất.

## 9. Hạn chế hiện tại của kịch bản 2

Đây là điểm rất quan trọng để đọc kết quả cho đúng.

Kịch bản tunnel hiện tại đã hợp lý để mô phỏng:

- LOS dọc hầm
- phản xạ bậc một từ trần, sàn, tường

Nhưng chưa phải là mô hình waveguide đầy đủ theo nghĩa điện từ học chặt nhất.

Hiện tại pipeline:

- chạy `Sionna RT` thật
- nhưng khi Sionna trả quá ít path trong tunnel, pipeline bổ sung các phản xạ hình học chi phối nhất
- vì vậy trace cuối cùng phản ánh các path chính, chứ chưa phải đầy đủ mode propagation trong hầm

Nói ngắn gọn:

- phù hợp để nghiên cứu xu hướng handover và đặc trưng path trội
- chưa phải mô hình modal waveguide đầy đủ

## 10. Nếu muốn nghiên cứu handover trong tunnel sâu hơn

Có ba hướng mở rộng hợp lý:

1. chạy riêng hai lần với `west_portal_gnb` và `east_portal_gnb`, sau đó so sánh RSRP/path dominance giữa hai phía
2. mở rộng runner sang `dual-gNB` thật sự để cùng lúc xuất trace của hai cell portal
3. tăng độ phong phú tunnel propagation bằng:
   - bật phản xạ bậc cao hơn
   - tăng sampling
   - thêm diffraction/scattering
   - hoặc mô hình hóa tunnel cong / vùng chuyển tiếp ngoài-trong hầm

## 11. Kết luận

Kịch bản `Straight Tunnel` hiện tại đã được tích hợp độc lập vào dự án và có thể chạy từ đầu đến cuối với output riêng.

Nó phù hợp cho:

- mô phỏng cơ bản propagation trong hầm thẳng
- quan sát LOS trong tunnel
- quan sát phản xạ tường/trần/sàn
- làm nền để phát triển tiếp bài toán handover giữa hai portal gNB

File phân tích chi tiết kết quả của kịch bản 2 được ghi riêng tại:

[PHAN_TICH_KET_QUA_STRAIGHT_TUNNEL.md](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\PHAN_TICH_KET_QUA_STRAIGHT_TUNNEL.md)

