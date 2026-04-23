# SioNetRail - Báo cáo đánh giá chi tiết output hiện tại

Tài liệu này là báo cáo tổng hợp chính cho bộ output hiện tại của pipeline SioNetRail. Báo cáo tập trung vào ba nhóm kết quả:

- Biểu đồ tổng hợp Doppler và số path theo thời gian của bộ CSV Sionna RT gốc.
- Các thông số kênh truyền suy ra từ bộ CSV mới nhất trong hai scenario: không blockage và có moving train blockage.
- Đánh giá khoa học về mức độ phù hợp của kết quả với kịch bản mô hình kênh truyền đang setup.

Các báo cáo đánh giá cũ dư thừa đã được loại bỏ để tránh trùng lặp và mâu thuẫn. Bộ tài liệu còn lại ở root dự án hiện được giữ tập trung vào:

- `SioNetRail_Unified_Scene_3000m_Specification.md`
- `SioNetRail_Channel_Characterization_Assessment.md`
- `SioNetRail_Train_Blockage_Scenarios.md`
- báo cáo này

---

## 1. Nguồn dữ liệu được dùng để đánh giá

### 1.1. Bộ CSV gốc không blockage

Thư mục:

```text
phase1_pipeline/output_unified
```

File chính:

```text
mpc_tx1_viaductA.csv
mpc_tx2_ground.csv
mpc_tx3_tunnel.csv
mpc_tx4_viaductF.csv
mpc_tx5_portal.csv
```

### 1.2. Bộ CSV có moving train blockage

Thư mục:

```text
phase1_pipeline/output_unified_train_blockage
```

File chính:

```text
mpc_tx1_viaductA.csv
mpc_tx2_ground.csv
mpc_tx3_tunnel.csv
mpc_tx4_viaductF.csv
mpc_tx5_portal.csv
train_blockage_summary.json
trace_manifest_train_blockage.json
```

### 1.3. Bộ chỉ tiêu kênh truyền đã tính từ CSV

Thư mục:

```text
phase1_pipeline/channel_characterization
```

File quan trọng:

```text
channel_characterization_summary.csv
channel_characterization_summary.json
channel_metrics_all_scenarios.csv
```

### 1.4. Các hình tổng hợp chính đang được dùng để đọc kết quả

```text
phase1_pipeline/output_unified/doppler_vs_time.png
phase1_pipeline/output_unified/path_count_vs_time.png
phase1_pipeline/channel_characterization/paper_style_path_loss_distance_no_blockage.png
phase1_pipeline/channel_characterization/paper_style_path_loss_distance_with_train_blockage.png
phase1_pipeline/channel_characterization/paper_style_delay_spread_distance_no_blockage.png
phase1_pipeline/channel_characterization/paper_style_delay_spread_distance_with_train_blockage.png
phase1_pipeline/channel_characterization/paper_style_k_factor_distance_no_blockage.png
phase1_pipeline/channel_characterization/paper_style_k_factor_distance_with_train_blockage.png
phase1_pipeline/channel_characterization/paper_style_angular_spreads_distance_no_blockage.png
phase1_pipeline/channel_characterization/paper_style_angular_spreads_distance_with_train_blockage.png
```

---

## 2. Tóm tắt cấu hình vật lý và RT đang chi phối output hiện tại

Bộ output hiện tại được sinh với các giả thiết chính sau:

```text
Tần số sóng mang: 30 GHz
Tốc độ tàu: 350 km/h
Scenario: unified_3000m
TX array: 8 x 4, pattern TR38901, polarization VH
RX array: 2 x 2, pattern TR38901, polarization VH
max_depth = 6
max_num_paths = 4000
samples_per_src = 3000
diffuse_reflection = true
diffraction = true
edge_diffraction = true
refraction = false
min_relative_path_gain_db = 35 dB
max_paths_after_filter = 32
include_train_in_rt_scene = false
moving train blockage = post-processing độc lập
```

Điều này dẫn đến ba hệ quả quan trọng khi đọc output:

1. Bộ CSV không blockage là trace Sionna RT vật lý theo scene hình học, có reflection, diffuse reflection và diffraction.
2. Bộ CSV có blockage không chạy lại Sionna RT từ đầu mà lấy bộ CSV gốc rồi áp suy hao blockage lên các path bị thân tàu che chắn gần RX.
3. Số path trong CSV là số path sau lọc. Vì vậy biểu đồ path count luôn phản ánh `resolved paths after filtering`, không phản ánh toàn bộ raw path trong object `Paths` mà Sionna RT có thể trả về trước lọc.

---

## 3. Giải thích chi tiết biểu đồ Doppler tổng hợp

Hình đang xét:

```text
phase1_pipeline/output_unified/doppler_vs_time.png
```

Biểu đồ này vẽ `max |doppler_hz|` theo thời gian cho từng TX. Nó không vẽ Doppler của mỗi path riêng lẻ, mà tại mỗi timestamp chỉ lấy giá trị lớn nhất theo trị tuyệt đối trong tập các path đã được giữ lại của từng TX.

### 3.1. Ý nghĩa vật lý của Doppler trong bài toán này

Doppler sinh ra do RX di chuyển với vận tốc cao dọc tuyến đường sắt. Công thức bậc một:

```text
f_D = (v / lambda) cos(theta_rel)
```

Trong đó:

- `v` là tốc độ tương đối của tàu.
- `lambda` là bước sóng tại 30 GHz.
- `theta_rel` là góc tương đối giữa hướng chuyển động của tàu và hướng lan truyền thành phần sóng tại RX.

Với cấu hình hiện tại:

```text
v = 350 km/h ≈ 97.22 m/s
lambda = c / 30 GHz ≈ 0.00999 m
v / lambda ≈ 9728 Hz
```

Do đó, Doppler cực đại lý thuyết cỡ khoảng `9.7 kHz`. Đây chính là mức xuất hiện trong output hiện tại.

### 3.2. Số liệu Doppler tổng hợp theo TX

| TX | Mean max |Doppler| (Hz) | Median max |Doppler| (Hz) | P95 max |Doppler| (Hz) | Peak max |Doppler| (Hz) |
|---|---:|---:|---:|---:|
| TX1 | 9653.33 | 9726.87 | 9728.85 | 9728.87 |
| TX2 | 9671.64 | 9727.24 | 9728.71 | 9728.95 |
| TX3 | 9705.71 | 9727.95 | 9728.74 | 9728.83 |
| TX4 | 9645.32 | 9726.60 | 9728.92 | 9728.95 |
| TX5 | 9642.90 | 9727.12 | 9728.62 | 9728.95 |

### 3.3. Đánh giá và giải thích chi tiết

#### 3.3.1. Vì sao các đường Doppler của 5 TX gần nhau?

Đây là kết quả hợp lý. Tốc độ tàu là chung cho mọi TX và tần số 30 GHz là chung cho cả hệ, nên biên trần của Doppler gần như cố định quanh `9.73 kHz`. Điều khác nhau giữa các TX chỉ là góc tới của path mạnh nhất tại từng timestamp. Vì vậy đồ thị các TX có thể khác nhau nhỏ, nhưng đều nằm cùng một bậc độ lớn.

#### 3.3.2. Vì sao median và P95 của tất cả TX đều gần 9728 Hz?

Điều này cho thấy trong phần lớn thời gian, ít nhất một path mạnh của mỗi TX có hướng truyền gần song song hoặc ngược song song với hướng chạy của tàu, khiến `cos(theta_rel)` gần `±1`. Đây là hành vi rất dễ gặp trong kịch bản railway chạy dọc tuyến, nơi TX và RX nằm dọc theo trục đường ray.

#### 3.3.3. Vì sao mean nhỏ hơn median?

Do ở một số khoảng thời gian, đặc biệt gần vùng chuyển tiếp hoặc khi chỉ còn các path tới từ góc lệch lớn, Doppler cực đại trong tập path còn lại giảm xuống. Những đoạn thấp này kéo giá trị trung bình xuống, trong khi median vẫn gần mức cực đại.

#### 3.3.4. Vì sao TX3 có mean max |Doppler| cao nhất?

TX3 là tunnel. Trong tunnel, có rất nhiều path với góc đến khác nhau, nhưng cũng thường tồn tại các thành phần tới gần trục đường ray. Vì số path phong phú hơn, xác suất xuất hiện ít nhất một path có Doppler rất gần cực đại tại mỗi timestamp cao hơn. Do đó mean của `max |Doppler|` ở TX3 cao hơn các TX khác một chút.

### 3.4. Kết luận về Doppler

Biểu đồ Doppler hiện tại là hợp lý về mặt vật lý và nhất quán với cấu hình 30 GHz, 350 km/h. Nó là một dấu hiệu mạnh cho thấy pipeline đang không bị sai đơn vị tần số, sai tốc độ tàu hoặc sai công thức Doppler. Nếu Doppler cực đại không nằm quanh `9.7 kHz` thì khi đó mới có nghi ngờ lớn về cấu hình hoặc code.

---

## 4. Giải thích chi tiết biểu đồ path count tổng hợp

Hình đang xét:

```text
phase1_pipeline/output_unified/path_count_vs_time.png
```

Biểu đồ này vẽ số `resolved paths` theo thời gian cho từng TX. Đây là số path sau khi:

- Sionna RT đã trả về raw paths.
- pipeline lọc theo `min_relative_path_gain_db = 35 dB`.
- pipeline giới hạn `max_paths_after_filter = 32`.

### 4.1. Số liệu path count theo TX

| TX | Mean path count | Median | P95 | Max |
|---|---:|---:|---:|---:|
| TX1 | 1.84 | 1 | 5 | 6 |
| TX2 | 2.49 | 2 | 4 | 6 |
| TX3 | 10.76 | 4 | 32 | 32 |
| TX4 | 2.39 | 2 | 6 | 6 |
| TX5 | 2.65 | 3 | 5 | 6 |

### 4.2. Đánh giá và giải thích chi tiết theo từng TX

#### TX1 - Viaduct A

TX1 chủ yếu nằm trong vùng viaduct thoáng. Môi trường này ít vật phản xạ mạnh ở gần hơn so với tunnel hoặc portal. Vì vậy số path được giữ lại thường thấp, nhiều thời điểm chỉ còn 1 đến 3 path mạnh. Đây là hành vi hợp lý.

#### TX2 - Ground

TX2 có path count trung bình cao hơn TX1 một chút. Điều này cũng hợp lý, vì khu ground có barrier, mặt đất và một số bề mặt lân cận có thể tạo thêm reflection/diffuse thành path phụ. Tuy nhiên môi trường vẫn chưa giàu multipath như tunnel, nên số path thường chỉ ở mức vài path.

#### TX3 - Tunnel

Đây là đường màu quan trọng nhất. TX3 tăng mạnh lên vùng 20-32 path trong khoảng tunnel trung tâm. Kết quả này có ý nghĩa khoa học rõ ràng:

- tunnel là môi trường dẫn sóng gần đúng;
- vách hầm, nền và trần tạo nhiều path phản xạ;
- khi diffraction và diffuse reflection được bật, tập path có thể rất phong phú;
- sau lọc, số path vẫn còn đủ nhiều để chạm ngưỡng `32`.

Đoạn plateau ở `32` không có nghĩa tunnel chỉ có đúng 32 path vật lý. Nó nghĩa là sau lọc vẫn còn ít nhất 32 path đủ mạnh, và pipeline đã chạm giới hạn `max_paths_after_filter = 32`. Nếu nâng giới hạn này lên, đoạn plateau có thể còn tăng cao hơn.

Đây là một trong những bằng chứng mạnh nhất cho thấy tunnel đang được mô hình hóa như một môi trường multipath-rich đúng trực giác vật lý.

#### TX4 - Viaduct F

TX4 là viaduct thứ hai ở cuối tuyến. Hành vi gần giống TX1 nhưng không hoàn toàn trùng. Có những đoạn TX4 tăng lên 5-6 path, phản ánh những vùng hình học mà barrier/deck hoặc tương tác với các phần chuyển tiếp cần gộp thêm path phụ. Mức này vẫn thấp hơn nhiều so với tunnel, phù hợp vật lý.

#### TX5 - Portal / Transition

TX5 thường nằm trong vùng 2-5 path, cao hơn TX1 và gần TX2/TX4. Điều này phù hợp với portal: đây là vùng chuyển tiếp trong/ngoài hầm, thường có reflection từ mặt đất, mép portal, vách và các thành phần diffraction ở cạnh cửa hầm. Tuy nhiên nó không giàu path bền vững như tunnel sâu, nên path count không duy trì cao như TX3.

### 4.3. Ý nghĩa của việc TX3 đạt ngưỡng 32

Đây là chi tiết rất quan trọng khi đánh giá output:

- Nó cho thấy tunnel đang là vùng có mật độ multipath mạnh nhất.
- Nó cũng cho thấy cấu hình lọc path hiện tại đã trở thành giới hạn nhân tạo ở một số đoạn tunnel.
- Nếu mục tiêu tương lai là nghiên cứu thật sâu về intra-tunnel richness, có thể cân nhắc tăng `max_paths_after_filter` lên 48 hoặc 64 cho riêng bộ trace tunnel để xem còn thêm được bao nhiêu path đáng kể.

Tuy nhiên, với mục tiêu đưa vào ns-3 và tránh trace quá nặng, mức `32` hiện tại là một trade-off hợp lý giữa fidelity và chi phí mô phỏng.

### 4.4. Kết luận về path count

Biểu đồ path count hiện tại có logic vật lý tốt:

- viaduct ít path,
- ground/portal mức trung gian,
- tunnel giàu path rõ rệt,
- plateau 32 là do giới hạn hậu lọc chứ không phải do Sionna RT không thể tìm thêm path.

Đây là kết quả đáng tin cậy và phù hợp với mục tiêu mô phỏng kênh truyền cho railway mmWave/FR2.

---

## 5. Đánh giá chi tiết bộ CSV mới nhất trong scenario không blockage

### 5.1. Bảng tổng hợp chính

| TX | Môi trường | Mean path loss (dB) | Mean RMS delay spread (ns) | Mean ASA (deg) | Mean ASD (deg) | Mean ESA (deg) | Mean ESD (deg) | Mean K-factor (dB) | LOS timestamp ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TX1 | Viaduct A | 106.67 | 0.63 | 3.37 | 0.60 | 2.14 | 0.29 | 3.12 | 59.45% |
| TX2 | Ground | 108.43 | 3.68 | 12.44 | 0.59 | 8.09 | 0.29 | 4.29 | 51.22% |
| TX3 | Tunnel | 105.51 | 5.07 | 15.83 | 2.07 | 9.60 | 0.93 | -6.87 | 46.71% |
| TX4 | Viaduct F | 111.06 | 2.90 | 3.88 | 0.67 | 3.43 | 0.31 | 3.69 | 58.21% |
| TX5 | Portal | 107.44 | 3.51 | 12.94 | 0.80 | 8.28 | 0.31 | 4.26 | 47.69% |

### 5.2. Path loss

#### TX3 tunnel có path loss trung bình thấp nhất

Điều này thoạt nhìn có thể gây ngạc nhiên vì tunnel thường được xem là môi trường khó. Tuy nhiên ở mmWave, tunnel có thể tạo hiệu ứng dẫn sóng gần đúng: vách, trần và nền hầm giữ lại và tái phân bố năng lượng phản xạ sao cho tổng công suất nhận hữu ích không giảm nhanh như môi trường mở ở cùng cự ly. Vì vậy `mean path loss = 105.51 dB` của TX3 là hợp lý.

#### TX4 viaduct F có path loss cao nhất

TX4 nằm trong môi trường thoáng hơn, ít vật phản xạ hỗ trợ, vì vậy tổng công suất path sau lọc thấp hơn, dẫn đến path loss hiệu dụng cao hơn. `111.06 dB` là dấu hiệu cho thấy đây là vùng tương đối nghèo hỗ trợ multipath.

### 5.3. Delay spread

#### TX1 rất nhỏ

`0.63 ns` cho TX1 cho thấy năng lượng rất tập trung vào vài path đến sớm, phù hợp vùng viaduct mở.

#### TX3 cao nhất

`5.07 ns` ở TX3 phản ánh đúng tính chất tunnel nhiều reflection. Kết quả này nhất quán với path count cao của TX3. Khi có nhiều path tới với trễ khác nhau, RMS delay spread phải tăng.

#### TX2 và TX5 ở mức trung gian cao

Ground và portal có delay spread cỡ `3.5-3.7 ns`, hợp lý vì cả hai môi trường đều phong phú hơn viaduct nhưng chưa bị nhốt năng lượng như tunnel.

### 5.4. Angular spread

#### ASA lớn nhất ở TX3, tiếp theo TX5 và TX2

Đây là chỉ tiêu rất quan trọng. `ASA` cho thấy tín hiệu tại RX đến từ nhiều hướng phương vị khác nhau. TX3 `15.83°`, TX5 `12.94°`, TX2 `12.44°` là thứ tự rất hợp lý:

- tunnel sinh nhiều hướng tới do phản xạ hai bên vách;
- portal là vùng chuyển tiếp giàu interaction;
- ground có barrier và mặt phản xạ ngang.

#### ASD nhỏ hơn ASA rõ rệt

Điều này cũng hợp lý. TX là trạm cố định, còn RX đang di chuyển và nhận tín hiệu từ nhiều vật thể xung quanh. Do đó phân tán góc ở phía đến thường lớn hơn ở phía phát.

### 5.5. K-factor

#### TX3 có K-factor âm

Đây là kết quả rất có giá trị khoa học. `K = -6.87 dB` nghĩa là tổng công suất NLOS đang mạnh hơn LOS. Đây là đặc trưng điển hình của tunnel multipath-rich. Nó phù hợp với trực giác và rất quan trọng cho mô phỏng handover: tunnel không phải là môi trường có LOS áp đảo ổn định.

#### TX1, TX2, TX4, TX5 có K dương

Các TX ngoài tunnel có LOS vẫn giữ vai trò đáng kể. Điều này tạo ra K-factor dương khoảng `3-4 dB`, tức LOS mạnh hơn NLOS nhưng không áp đảo tuyệt đối. Đây là vùng có thể xem là Ricean moderate.

### 5.6. Nhận xét tổng quát cho scenario không blockage

Scenario không blockage đang cho một cấu trúc kênh rất hợp lý:

- TX3 tunnel mạnh về multipath, delay spread, angular spread, K âm.
- TX1/TX4 viaduct nghèo path hơn, delay spread thấp hơn.
- TX2/TX5 là các vùng trung gian có nhiều tương tác hơn viaduct nhưng chưa giàu path như tunnel.

Đây là một dấu hiệu tốt cho thấy geometry và cơ chế lan truyền đang tạo ra sự khác biệt đúng giữa các module cảnh quan.

---

## 6. Đánh giá chi tiết bộ CSV mới nhất trong scenario có moving train blockage

### 6.1. Bảng tổng hợp chính

| TX | Môi trường | Mean path loss (dB) | Mean RMS delay spread (ns) | Mean ASA (deg) | Mean ASD (deg) | Mean ESA (deg) | Mean ESD (deg) | Mean K-factor (dB) | LOS timestamp ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TX1 | Viaduct A | 108.90 | 0.41 | 3.69 | 0.39 | 2.11 | 0.13 | 11.56 | 59.45% |
| TX2 | Ground | 110.33 | 1.16 | 9.34 | 0.39 | 7.31 | 0.10 | 14.82 | 51.22% |
| TX3 | Tunnel | 107.02 | 2.41 | 12.79 | 2.10 | 9.02 | 0.72 | -5.89 | 46.71% |
| TX4 | Viaduct F | 111.68 | 2.66 | 3.50 | 0.48 | 3.07 | 0.18 | 10.77 | 58.21% |
| TX5 | Portal | 109.36 | 1.19 | 10.42 | 0.58 | 7.66 | 0.13 | 9.95 | 47.69% |

### 6.2. Tỷ lệ blockage theo timestamp và thay đổi công suất

| TX | Blocked timestamp ratio | Delta mean total power (dB) |
|---|---:|---:|
| TX1 | 43.64% | -0.165 dB |
| TX2 | 72.22% | -0.156 dB |
| TX3 | 79.59% | -0.220 dB |
| TX4 | 21.29% | -0.151 dB |
| TX5 | 67.09% | -0.117 dB |

### 6.3. Điều gì thay đổi và điều gì không thay đổi?

#### Không thay đổi

- Số dòng CSV theo timestamp/path vẫn giữ nguyên so với scenario không blockage.
- Path count plot không đổi.
- Doppler plot không đổi.
- LOS timestamp ratio không đổi trong output hiện tại.

Lý do là bước blockage hiện tại là hậu xử lý trên biên độ path, không gọi lại PathSolver và không xóa path ra khỏi tập trace.

#### Có thay đổi

- Biên độ phức của các path bị blockage bị suy hao.
- Tổng công suất nhận giảm.
- Path loss tăng.
- Delay spread giảm.
- Angular spread giảm ở nhiều TX.
- K-factor tăng ở phần lớn TX.

### 6.4. Giải thích vật lý của các thay đổi

#### Path loss tăng

Đây là hiệu ứng trực tiếp nhất và phù hợp nhất. Khi train blockage áp suy hao lên các path bị thân tàu che các bề mặt gần RX, tổng công suất nhận giảm, nên path loss hiệu dụng tăng.

#### Delay spread giảm

Blockage hiện tại chủ yếu làm yếu các path NLOS/góc thấp/đi đường dài hơn. Khi các path trễ lớn bị suy giảm, phân bố công suất theo delay co lại quanh các path đến sớm hơn. Kết quả là RMS delay spread giảm. Điều này thấy rất rõ ở TX2, TX3, TX5.

#### Angular spread giảm

Tương tự, khi các path đến từ nhiều hướng phụ bị suy yếu, năng lượng góc tập trung hơn vào một số hướng mạnh còn lại, thường là gần hướng LOS hoặc vài hướng phản xạ chủ đạo. Vì vậy `ASA` giảm đáng kể ở TX2, TX3, TX5.

#### K-factor tăng

Đây là điểm dễ gây hiểu sai nếu không giải thích kỹ. K-factor tăng không có nghĩa chất lượng kênh tốt hơn. Nó chỉ có nghĩa tỷ lệ `P_LOS / P_NLOS` lớn hơn. Vì blockage hiện tại chủ yếu làm yếu NLOS, còn LOS rooftop ít bị chắn, nên K-factor tăng là điều tự nhiên.

### 6.5. Tại sao LOS ratio không đổi?

Đây là chi tiết rất quan trọng. Trong cấu hình hiện tại, RX đặt trên mái tàu, cao hơn thân tàu một khoảng `roof_clearance_m = 0.35`. Vì vậy thân tàu hiếm khi chắn trực tiếp LOS từ gNB đến anten RX. Blockage chủ yếu cắt các thành phần tới theo góc thấp hoặc từ bên hông/phía sau. Do đó LOS timestamp ratio của scenario blockage gần như giữ nguyên so với scenario gốc.

Điều này không phải là lỗi. Nó là hệ quả trực tiếp của giả thiết anten rooftop. Nếu sau này muốn blockage ảnh hưởng mạnh hơn tới LOS, cần thay đổi mô hình anten thấp hơn, đặt bên hông, hoặc đưa thêm rooftop equipment/pantograph vào mô hình hình học.

---

## 7. So sánh chi tiết hai scenario

### 7.1. Chênh lệch trung bình do blockage

| TX | Delta path loss mean (dB) | Delta delay spread mean (ns) | Delta ASA mean (deg) | Delta K-factor mean (dB) |
|---|---:|---:|---:|---:|
| TX1 | +2.24 | -0.22 | +0.32 | +8.44 |
| TX2 | +1.90 | -2.51 | -3.11 | +10.53 |
| TX3 | +1.51 | -2.66 | -3.05 | +0.98 |
| TX4 | +0.62 | -0.25 | -0.38 | +7.09 |
| TX5 | +1.92 | -2.31 | -2.52 | +5.69 |

### 7.2. Diễn giải theo từng TX

#### TX1

Viaduct A ít bị blockage hơn tunnel/portal. Delay spread vốn đã rất thấp nên sau blockage chỉ giảm nhẹ. K-factor lại tăng mạnh vì NLOS vốn ít, chỉ cần giảm thêm một phần nhỏ là tỷ số LOS/NLOS tăng đáng kể.

#### TX2

Ground bị ảnh hưởng blockage rất mạnh theo timestamp. Delay spread và ASA giảm rõ, chứng tỏ nhiều path từ bên hông/góc thấp đã bị thân tàu cắt. Đây là hiệu ứng vật lý hợp lý.

#### TX3

Tunnel có blocked timestamp ratio cao nhất, nhưng K-factor chỉ tăng nhẹ và vẫn âm. Điều này rất quan trọng: ngay cả khi blockage làm yếu nhiều path NLOS, tunnel vẫn còn là môi trường NLOS-dominant. Kết quả này rất có giá trị cho nghiên cứu handover trong tunnel.

#### TX4

Viaduct F ít blockage nhất. Hầu hết các chỉ số thay đổi ít, phản ánh đây là vùng mở hơn và ít path bị tàu tự che.

#### TX5

Portal bị blockage mạnh. Delay spread giảm nhiều, K tăng khá rõ. Điều này phản ánh vùng portal rất nhạy với việc các path trung gian/phản xạ bị cắt gần RX.

---

## 8. Đánh giá mức độ phù hợp khoa học của output hiện tại

### 8.1. Những điểm rất hợp lý

1. **Doppler đúng bậc độ lớn lý thuyết** tại 30 GHz, 350 km/h.
2. **Tunnel có số path, delay spread, angular spread cao nhất** và K-factor âm, đúng trực giác vật lý.
3. **Viaduct path count thấp hơn tunnel** và delay spread nhỏ hơn.
4. **Portal/ground có hành vi trung gian** giữa viaduct và tunnel.
5. **Blockage không đổi Doppler và path count**, vì đó là bước hậu xử lý amplitude-only. Điều này logic với kiến trúc pipeline hiện tại.
6. **Blockage làm path loss tăng, delay spread giảm, angular spread giảm và K-factor tăng**. Đây là bộ xu hướng rất hợp lý nếu blockage chủ yếu làm suy yếu NLOS gần RX.

### 8.2. Những điểm cần hiểu đúng để tránh kết luận sai

1. Số path trong biểu đồ không phải raw path của Sionna RT. Nó là số path sau lọc và bị chặn trần `32` bởi `max_paths_after_filter`.
2. K-factor tăng sau blockage không có nghĩa chất lượng liên kết tốt hơn. Path loss vẫn tăng, chỉ là NLOS bị yếu đi nhanh hơn LOS.
3. Blockage không làm LOS ratio giảm trong cấu hình hiện tại không phải vì model sai, mà vì anten đặt trên mái tàu.
4. Bộ CSV blockage hiện chưa phải mô hình điện từ đầy đủ của thân tàu trong RT scene. Nó là hậu xử lý hình học có cơ sở nhưng vẫn là xấp xỉ.

### 8.3. Những điểm chưa hoàn toàn lý tưởng

1. `include_train_in_rt_scene = false`, nên thân tàu chưa tham gia trực tiếp vào ray tracing.
2. Refraction đang tắt, điều này chấp nhận được cho bài toán hiện tại nhưng vẫn là một giả thiết đơn giản hóa.
3. Một số vùng tunnel đang chạm ngưỡng `32` path, nên richness thực tế có thể còn cao hơn những gì CSV đang giữ lại.
4. Chưa có bước measurement validation thực địa. Vì vậy bộ output hiện tại là physically plausible và internally consistent, nhưng chưa thể gọi là experimentally validated.

---

## 9. Kết luận cuối cùng

Bộ output hiện tại của SioNetRail là một bộ kết quả tốt, nhất quán và có cơ sở khoa học để tiếp tục dùng cho ns-3 và nghiên cứu handover.

Điểm mạnh nhất của bộ output là nó thể hiện được rất rõ sự khác biệt giữa các môi trường:

- viaduct mở và ít multipath,
- ground/portal ở mức trung gian,
- tunnel giàu multipath và NLOS-dominant.

Bổ sung moving train blockage cũng đã tạo ra một scenario so sánh có ý nghĩa:

- không làm sai lệch cấu trúc path count/Doppler vốn có,
- nhưng làm thay đổi công suất và hình dáng phân bố năng lượng theo delay/góc theo hướng hợp lý về vật lý.

Nếu mục tiêu của bạn là tạo trace thực dụng nhưng giàu tính vật lý để đưa vào ns-3 thay cho channel model chuẩn, thì bộ output hiện tại là dùng được. Nếu mục tiêu tăng fidelity thêm một bậc cho nghiên cứu sâu hơn hoặc hướng công bố, bước tiếp theo nên là:

1. đưa thân tàu vào RT scene cho một số case benchmark;
2. cân nhắc tăng `max_paths_after_filter` cho tunnel;
3. bổ sung validation với measurement hoặc benchmark literature;
4. liên kết các chỉ tiêu path loss, K-factor, delay spread, angular spread với chỉ tiêu mạng như RSRP, SINR, HO count và ping-pong rate trong ns-3.