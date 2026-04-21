# Phân Tích Chi Tiết Kết Quả CSV Sau Lần Chạy Sionna RT Mới Nhất

## 1. Phạm vi phân tích
Tài liệu này phân tích trực tiếp 5 file CSV mới nhất sinh ra từ `backend=sionna` trong thư mục `phase1_pipeline/output_unified`:

- `mpc_tx1_viaductA.csv`
- `mpc_tx2_ground.csv`
- `mpc_tx3_tunnel.csv`
- `mpc_tx4_viaductF.csv`
- `mpc_tx5_portal.csv`

Cấu hình được dùng cho lần chạy này:

- `f = 30 GHz`
- `v = 350 km/h`
- `max_depth = 8`
- `max_num_paths = 6000`
- `samples_per_src = 5000`
- `diffuse_reflection = true`
- `diffraction = true`
- `edge_diffraction = true`
- `antenna TX = 8x4, pattern tr38901, VH`
- `antenna RX = 2x2, pattern tr38901, VH`
- `min_relative_path_gain_db = 40 dB`
- `include_train_in_rt_scene = false`
- `enable_refraction = false`

Ảnh `summary_doppler_los.png` đã được dùng để đối chiếu xu hướng Doppler và trạng thái LOS/NLOS theo thời gian khi viết phần đánh giá này.

## 2. Tổng hợp định lượng từ 5 file CSV

| Trạm | Số dòng | Số timestamp | Trung bình số path/timestamp | Trung vị | Lớn nhất | Tỉ lệ LOS theo dòng | Tỉ lệ LOS theo timestamp | Delay lớn nhất (us) | |Doppler| lớn nhất (Hz) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TX1 viaduct A | 14766 | 3391 | 4.3545 | 3 | 22 | 0.1365 | 0.5945 | 8.8398 | 9728.867 |
| TX2 ground | 13579 | 3391 | 4.0044 | 2 | 20 | 0.1279 | 0.5122 | 7.2056 | 9728.760 |
| TX3 tunnel | 98735 | 3391 | 29.1168 | 4 | 139 | 0.0160 | 0.4671 | 6.2073 | 9728.834 |
| TX4 viaduct F | 18743 | 3391 | 5.5273 | 4 | 20 | 0.1022 | 0.5647 | 8.1726 | 9728.894 |
| TX5 portal | 10995 | 3391 | 3.2424 | 2 | 11 | 0.1471 | 0.4769 | 6.3761 | 9728.920 |

Thời lượng trace của cả 5 trạm đều là `30.925518 s`, ứng với full trajectory `3391` timestamp.

## 3. Kiểm tra tính đúng vật lý cơ bản

### 3.1. Doppler
Tại `30 GHz` và `350 km/h`, Doppler cực đại lý thuyết là:

- `f_D,max = v / lambda = 9728.9528 Hz`

Kết quả CSV cho cả 5 trạm đều rất sát giá trị này:

- TX1: `9728.867 Hz`
- TX2: `9728.760 Hz`
- TX3: `9728.834 Hz`
- TX4: `9728.894 Hz`
- TX5: `9728.920 Hz`

Sai lệch đều rất nhỏ. Điều này cho thấy:

- vector vận tốc tàu
- tần số sóng mang
- cách tính Doppler theo hướng truyền

là nhất quán và đúng về mặt vật lý.

### 3.2. Hành vi Doppler theo thời gian trên `summary_doppler_los.png`
Đồ thị Doppler cho thấy mỗi trạm có các đoạn chuyển dấu từ gần `-f_D,max` sang gần `+f_D,max` khi hình học tương đối giữa TX và RX thay đổi. Đây là hành vi đúng mong đợi khi tàu đi qua vị trí mà vector vận tốc đổi dấu đối với vector tới/đi của đường truyền chính.

Nhận xét từ ảnh tổng hợp:

- TX1 và TX2 đổi dấu sớm hơn, phù hợp vì hai trạm này nằm về nửa đầu tuyến.
- TX3 đổi dấu quanh giữa tuyến, phù hợp vì trạm tunnel đặt gần `x = 1450 m`.
- TX4 đổi dấu muộn hơn, phù hợp vì trạm nằm về nửa cuối tuyến.
- TX5 có hình thái giao thoa và chuyển đoạn phức tạp hơn do nằm gần vùng portal/transition.

Đồ thị này phù hợp với geometry setup và là dấu hiệu tốt về tính nhất quán của mô hình.

## 4. Phân tích chi tiết theo từng trạm

### 4.1. TX1 - Viaduct A
Kết quả:

- `avg_paths = 4.3545`
- `median = 3`
- `max = 22`
- `LOS timestamp ratio = 0.5945`
- `delay max = 8.8398 us`

Đánh giá:

- Đây là kết quả hợp lý cho một trạm viaduct cao, có không gian mở, barrier, deck, pier và các kết cấu kim loại phụ.
- Số path trung bình ở mức vừa phải: cao hơn portal, thấp hơn tunnel. Thứ tự này hợp lý.
- `delay max` lớn nhất trong 5 trạm là điều có thể chấp nhận được, vì viaduct cao cho phép các đường phản xạ dài hơn từ kết cấu xa hơn và từ mặt đất bên dưới.
- `LOS timestamp ratio` gần `59.45%` cho thấy đường nhìn hình học vẫn tồn tại trong một nửa lần thời gian. Điều này không bất thường với viaduct mở.

Điểm cần lưu ý:

- `LOS row ratio` chỉ `13.65%`, trong khi `LOS timestamp ratio` là `59.45%`. Nghĩa là tại nhiều timestamp có LOS, nhưng số path NLOS vẫn chiếm áp đảo. Điều này là hợp lý sau khi đã bật diffuse reflection và diffraction.

### 4.2. TX2 - Ground section
Kết quả:

- `avg_paths = 4.0044`
- `median = 2`
- `max = 20`
- `LOS timestamp ratio = 0.5122`
- `delay max = 7.2056 ?s`

Đánh giá:

- Số path trung bình thấp hơn TX1 và TX4, phù hợp với ground section mở hơn viaduct cao nhưng vẫn có barrier, cột và dây tiếp xúc.
- `LOS timestamp ratio` khoảng `51.22%` là hợp lý cho đoạn ground có nhiều chuyển từ LOS sang NLOS khi tàu đi qua các vật cản hình học trong scene.
- Trung vị chỉ `2` cho thấy phần lớn timestamp không quá giàu path. Đây là xu hướng hợp lý cho ground section.

Điểm cần lưu ý:

- Vì scene không có thân tàu động, các khoảng LOS này vẫn có khả năng hơi lạc quan hơn thực tế.

### 4.3. TX3 - Tunnel
Kết quả:

- `avg_paths = 29.1168`
- `median = 4`
- `max = 139`
- `LOS row ratio = 0.0160`
- `LOS timestamp ratio = 0.4671`
- `delay max = 6.2073 us`

Đây là trạm quan trọng nhất để đánh giá.

Những điểm phù hợp:

- TX3 là trạm giàu path nhất một cách rõ rệt. Đây là xu hướng đúng cho môi trường tunnel vì có nhiều phản xạ lặp lại và hiệu ứng waveguide.
- `LOS row ratio` rất thấp `1.6%` cho thấy phần lớn năng lượng và số path đã chuyển sang dạng NLOS/đa tương tác. Đây là xu hướng hợp lý hơn bản trước.
- Trên đồ thị LOS, TX3 có ít lần chuyển trạng thái hơn các trạm ngoài trời. Điều này đúng với tunnel vì channel mang tính ổn định hơn do hình học bao kín hơn.

Những điểm chưa hoàn toàn hợp lý:

- `avg_paths = 29.1` và đặc biệt `max_paths = 139` là rất cao.
- Trung vị chỉ `4`, nghĩa là phần lớn timestamp không cao đến mức đó; chỉ một số đoạn có hiện tượng "bùng nổ số path".

Diễn giải khoa học:

- Sự kết hợp `max_depth = 8`, `samples_per_src = 5000`, `diffuse_reflection = true`, `diffraction = true`, clutter tunnel bổ sung, và ngưỡng lọc `40 dB` đã làm tăng mạnh số thành phần hợp lý trong hầm.
- Về xu hướng định tính thì điều này đúng: tunnel phải giàu path nhất.
- Tuy nhiên, dưới góc nhìn hệ thống, đây là dấu hiệu cho thấy tunnel hiện vẫn có thể hơi "quá giàu path" so với khả năng phân giải của máy thu thực tế, vì solver vẫn giữ được rất nhiều thành phần yếu nhưng còn trên ngưỡng `40 dB` tương đối.

Kết luận cho TX3:

- Đúng về xu hướng vật lý.
- Chưa chắc đã tối ưu về mức độ "thực địa" của số path. Upper tail `139 path` nên được xem là điểm cần còn tinh chỉnh nếu mục tiêu là mô hình fidelity cao.

### 4.4. TX4 - Viaduct F
Kết quả:

- `avg_paths = 5.5273`
- `median = 4`
- `max = 20`
- `LOS timestamp ratio = 0.5647`
- `delay max = 8.1726 us`

Đánh giá:

- TX4 giàu path hơn TX1 và TX2. Điều này có thể chấp nhận được vì đoạn F dài hơn, có nhiều pier hơn và có lịch sử hình học khác ở nửa sau tuyến.
- `LOS timestamp ratio` gần TX1 và ở mức cao vừa phải là hợp lý cho viaduct mở.
- `delay max` lớn thứ hai sau TX1 cũng phù hợp với một viaduct cao dài.

Điểm cần lưu ý:

- Số lần chuyển LOS/NLOS của TX4 trên đồ thị tổng hợp khá nhiều. Điều này có thể phản ánh đúng hình học thay đổi nhanh theo trajectory, nhưng cũng có thể bị tăng bởi việc thiếu moving train blockage và clutter ngoài trời chưa đầy đủ.

### 4.5. TX5 - Portal / transition
Kết quả:

- `avg_paths = 3.2424`
- `median = 2`
- `max = 11`
- `LOS timestamp ratio = 0.4769`
- `delay max = 6.3761 us`

Đánh giá:

- TX5 có số path thấp hơn viaduct và thấp hơn nhiều so với tunnel. Thứ tự này hợp lý cho vùng transition.
- Số lần chuyển LOS/NLOS trên hình tổng hợp là cao nhất trong 5 trạm. Đây là một dấu hiệu rất phù hợp với portal, nơi channel thay đổi nhanh khi tàu ra/vào vùng chuyển tiếp.
- `LOS timestamp ratio` gần `47.69%` là khá hợp lý: không quá cao như mặt line-of-sight mở, nhưng cũng không quá thấp như hầm sâu.

Điểm cần lưu ý:

- `LOS row ratio` vẫn là `14.71%`, không thấp. Điều này cho thấy khi LOS tồn tại, path LOS và một số path liên quan vẫn được giữ khá rõ. Nếu đưa thân tàu động vào scene, chỉ số này nhiều khả năng sẽ giảm thêm.

## 5. Đối chiếu tổng thể với kịch bản đang setup

### 5.1. Những điểm đã phù hợp tốt
Bộ kết quả hiện tại phù hợp tốt với kịch bản đang setup ở các điểm sau:

1. Thứ tự độ giàu path theo loại môi trường là hợp lý:
   - tunnel > viaduct > ground > portal
   theo ý nghĩa trung bình và upper tail.
2. Doppler đạt mốc lý thuyết, xác nhận phần động học và geometry chạy đúng.
3. Vùng portal có tính chuyển tiếp rõ ràng trên đồ thị LOS và Doppler.
4. Vùng tunnel có tính "rich multipath" rõ ràng và LOS không còn áp đảo về mặt số path.
5. Viaduct cho delay spread cực đại lớn hơn tunnel, hợp lý vì có các tia dài hơn từ kết cấu mở.

### 5.2. Những điểm vẫn chưa hoàn toàn phù hợp

#### A. Chưa có moving train blockage
Cấu hình hiện tại vẫn là:

- `include_train_in_rt_scene = false`

Hệ quả:

- LOS timestamp ratio của TX1, TX2, TX4, TX5 có khả năng vẫn cao hơn thực tế.
- Các khoảng LOS trong portal và ground section vẫn "sạch" hơn môi trường thực địa.

Đây là sai lệch mô hình lớn nhất còn lại.

#### B. Vật liệu ground và hạ tầng vẫn là proxy
Trong source hiện tại, một số mặt ngoài trời và rough surfaces đang dùng các proxy ITU/concrete để đảm bảo tương thích với `sionna.rt` ở `30 GHz`.

Hệ quả:

- hệ số phản xạ, thâm nhập, suy hao chưa thật sự bám sát ballast, đất, bê tông đường sắt, và portal lining thực.
- một số delay tail và phân bố năng lượng path có thể bị sai cục bộ.

#### C. TX3 vẫn có dấu hiệu "path explosion" ở upper tail
`max_paths = 139` là rất cao. Điều này không có nghĩa là sai hoàn toàn, nhưng cho thấy tunnel hiện vẫn có khả năng hơi lạc quan về số thành phần có thể giải được.

Nguyên nhân chính:

- `max_depth = 8` khá sâu
- `samples_per_src = 5000` khá cao
- diffuse và diffraction đều bật
- clutter tunnel bổ sung làm tăng candidate hợp lý
- ngưỡng lọc `40 dB` vẫn còn khá rộng

#### D. Chưa có refraction
Cấu hình hiện tại:

- `enable_refraction = false`

Tác động của mức này không lớn bằng train blockage trong bối cảnh này, nhưng vẫn là một phần thiếu nếu muốn bám sát hơn các đường truyền xuyên qua vật liệu dielectric.

## 6. Giải thích đồ thị `summary_doppler_los.png`

Ảnh tổng hợp phù hợp khá tốt với CSV:

- Đồ thị trên cho thấy Doppler của dominant path ở mỗi trạm đạt sát `±9729 Hz`, trùng với thống kê CSV.
- Đồ thị dưới cho thấy TX3 có ít lần nhảy LOS/NLOS hơn nhiều trạm ngoài trời, phù hợp với `los_transitions = 8`.
- TX5 có nhiều lần chuyển trạng thái nhất, phù hợp với bản chất portal/transition.
- TX1/TX4 có nhiều khoảng LOS dài, đúng với viaduct mở.

Lưu ý quan trọng:

- Ảnh này rất hữu ích để phân tích xu hướng.
- Tuy nhiên, kết luận khoa học cuối cùng vẫn nên dựa chủ yếu trên CSV, vì CSV lưu dữ liệu path đầy đủ hơn.

## 7. Kết luận tổng hợp

Nếu mục tiêu là mô hình hóa:

- xu hướng kênh theo từng module
- sự khác nhau giữa viaduct / ground / tunnel / portal
- bộ trace vật lý hợp lý để đưa vào mô phỏng hệ thống mức đầu

thì bộ kết quả hiện tại là **dùng được và khá hợp lý**.

Nếu mục tiêu là:

- so sánh trực tiếp với measurement
- công bố fidelity cao
- mô hình HSR mmWave thực địa sát hơn nữa

thì bộ kết quả hiện tại **vẫn chưa đủ** và cần các điểm sai lệch mô hình quan trọng đã nêu ở mục 5.2.

## 8. Đề xuất cải thiện

### 8.1. Ưu tiên cao nhất
1. Đưa moving train body vào scene theo từng snapshot để có self-blockage thực sự.
2. Thêm chế độ `resume/by-station/by-segment` để có thể hiệu chỉnh từng đoạn nhanh hơn.
3. Giảm bớt `path explosion` trong tunnel bằng một trong các cách sau:
   - giảm `max_depth` từ `8` xuống `6`
   - giảm `samples_per_src` từ `5000` xuống `3000`
   - siết `min_relative_path_gain_db` từ `40 dB` xuống `30-35 dB`

### 8.2. Ưu tiên trung bình
1. Xây dựng custom `radio-material` cho ballast/ground/portal lining ở `30 GHz`.
2. Hiệu chỉnh `scattering_coefficient` theo benchmark hoặc measurement.
3. Bổ sung clutter ngoài trời chọn lọc cho ground/viaduct nếu muốn LOS transition thực địa hơn.

### 8.3. Ưu tiên bổ sung
1. Cân nhắc bật `refraction` cho các vật liệu dielectric có ý nghĩa.
2. Nếu đánh giá hệ thống, nên trích xuất thêm:
   - PDP
   - RMS delay spread
   - K-factor xấp xỉ
   - lifetime của LOS/NLOS segments

## 9. Kết luận cuối cùng
Bộ 5 file CSV mới nhất đã phản ánh đúng các xu hướng vật lý cốt lõi của kịch bản đang setup:

- Doppler đúng
- tunnel giàu path nhất
- portal có tính chuyển tiếp rõ
- viaduct có delay tail lớn
- ground ở mức trung gian

Tuy nhiên, bộ kết quả này vẫn nên được hiểu là:

`Sionna RT physical channel trace for the configured geometry, with directional arrays, diffraction, diffuse reflection, and simplified static infrastructure assumptions`

Nó đã tốt hơn rõ rệt so với cấu hình cũ, nhưng vẫn chưa phải mô hình HSR thực địa hoàn chỉnh do chưa có moving train blockage và chưa có material calibration đầy đủ.
