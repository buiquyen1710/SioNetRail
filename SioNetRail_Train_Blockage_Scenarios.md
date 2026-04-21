# SioNetRail - Hai scenario CSV có và không có moving train blockage

Tài liệu này mô tả phần bổ sung `moving train blockage model` vào pipeline hiện tại. Mục tiêu là giữ nguyên bộ CSV Sionna RT gốc và tạo thêm một bộ CSV độc lập để áp dụng suy hao do thân tàu chuyển động, để có thể so sánh hai trường hợp khi đưa vào ns-3 hoặc khi thiết kế thuật toán handover.

## 1. Hai scenario độc lập

### Scenario A - Không có train blockage

Đây là bộ CSV gốc được xuất trực tiếp từ Sionna RT sau khi ray tracing và lọc path.

Thư mục output:

`	ext
phase1_pipeline/output_unified
`

Các file chính:

`	ext
mpc_tx1_viaductA.csv
mpc_tx2_ground.csv
mpc_tx3_tunnel.csv
mpc_tx4_viaductF.csv
mpc_tx5_portal.csv
`

Ý nghĩa vật lý:

- Biểu diễn kênh truyền theo ray tracing hình học và điện từ đang setup.
- Đã có các cơ chế như phản xạ, diffraction/diffuse nếu được bật trong cấu hình Sionna RT.
- Chưa áp dụng che chắn động bởi thân tàu đối với các tia truyền.

### Scenario B - Có moving train blockage

Đây là bộ CSV mới được tạo bằng bước hậu xử lý từ bộ CSV gốc. Bộ CSV gốc không bị ghi đè.

Thư mục output:

`	ext
phase1_pipeline/output_unified_train_blockage
`

Các file chính:

`	ext
mpc_tx1_viaductA.csv
mpc_tx2_ground.csv
mpc_tx3_tunnel.csv
mpc_tx4_viaductF.csv
mpc_tx5_portal.csv
trace_manifest_train_blockage.json
train_blockage_summary.json
`

Ý nghĩa vật lý:

- Mỗi timestamp được gắn với vị trí RX/tàu trên quỹ đạo.
- Thân tàu được mô hình hóa như một khối hộp chuyển động theo phương tuyến đường.
- Nếu đoạn tia truyền bị cắt bởi thể tích thân tàu, biên độ phức của path sẽ bị suy hao.
- Path bị ảnh hưởng được đánh dấu bằng các cột bổ sung để tiện phân tích và so sánh.

## 2. Cơ sở khoa học của moving train blockage

Trong kênh truyền vô tuyến đường sắt cao tốc, thân tàu là một vật cản điện từ lớn, có kích thước dài theo phương chuyển động, rộng theo phương ngang và cao theo phương đứng. Khi anten đặt trên mái tàu, thân tàu ít khi che trực tiếp đường LOS từ trạm tới anten nếu anten đặt cao, nhưng thân tàu vẫn có thể che hoặc làm suy hao các thành phần phản xạ/NLOS đi tới từ góc thấp, từ hai bên, hoặc từ phía sau.

Vì vậy, mô hình được bổ sung ở đây không thay thế Sionna RT, mà là một lớp hậu xử lý vật lý để đưa hiệu ứng che chắn động vào trace. Cách làm này phù hợp với mục tiêu tạo CSV cho ns-3 vì:

- Giữ được kết quả ray tracing gốc làm baseline.
- Tạo được scenario so sánh có/không có blockage mà không cần chạy lại toàn bộ ray tracing nặng.
- Có thể kiểm soát riêng tham số suy hao do blockage.
- Có thể đưa trực tiếp các cột mới vào phân tích handover, ví dụ timestamp nào bị blockage, station nào nhạy với blockage, mức suy hao công suất theo thời gian.

Mô hình hiện tại là mô hình hình học đơn giản hóa, không phải mô phỏng điện từ toàn phần của thân tàu. Nó phù hợp ở mức trace engineering cho mô phỏng mạng, nhưng nếu mục tiêu là so sánh tuyệt đối với đo kiểm thực địa thì cần hiệu chỉnh bằng measurement.

## 3. Tham số cấu hình đã bổ sung

Các tham số nằm trong \phase1_pipeline/config/config.yaml\:

`yaml
train_blockage:
  enabled: true
  input_trace_csv_pattern: output_unified/{station}.csv
  output_trace_csv_pattern: output_unified_train_blockage/{station}.csv
  output_manifest: output_unified_train_blockage/trace_manifest_train_blockage.json
  summary_json: output_unified_train_blockage/train_blockage_summary.json
  rx_offset_from_train_front_m: 4.0
  roof_clearance_m: 0.35
  lateral_margin_m: 0.10
  vertical_margin_m: 0.05
  lookback_distance_m: 80.0
  los_blockage_loss_db: 22.0
  nlos_blockage_loss_db: 12.0
  set_blocked_los_to_nlos: true
`

Giải thích:

- x_offset_from_train_front_m\: khoảng cách từ anten RX tới mũi tàu. Giá trị nhỏ thể hiện anten đặt gần đầu tàu.
- oof_clearance_m\: anten đặt cao hơn mái tàu bao nhiêu mét. Giá trị này giúp phân biệt anten rooftop với anten đặt bên hông.
- \lateral_margin_m\, \ertical_margin_m\: biên an toàn hình học để tránh mô hình quá lý tưởng.
- \lookback_distance_m\: chiều dài đoạn tia tới gần RX dùng để kiểm tra NLOS blockage theo hướng đến của path.
- \los_blockage_loss_db\: suy hao áp dụng cho path LOS nếu LOS bị thân tàu cắt.
- los_blockage_loss_db\: suy hao áp dụng cho path NLOS nếu thành phần tới RX bị thân tàu cắt.
- \set_blocked_los_to_nlos\: nếu LOS bị chắn thì đặt lại \los_flag = 0\ trong CSV blockage.

## 4. Quy trình chạy lại để xuất cả hai bộ CSV

Chạy từ thư mục dự án:

`powershell
cd C:\Users\asela\OneDrive\Members\K67.BuiVanQuyen\SioNetRail
`

Bước 1: chạy pipeline Sionna RT để tạo bộ CSV không blockage.

`powershell
python -m phase1_pipeline.export.export_mitsuba_fallback --config phase1_pipeline/config/config.yaml
python -m phase1_pipeline.raytracing.run_sionna_rt --config phase1_pipeline/config/config.yaml
`

Kết quả bước 1 nằm trong:

`	ext
phase1_pipeline/output_unified
`

Bước 2: chạy hậu xử lý moving train blockage để tạo bộ CSV thứ hai.

`powershell
python -m phase1_pipeline.postprocess.apply_train_blockage --config phase1_pipeline/config/config.yaml
`

Kết quả bước 2 nằm trong:

`	ext
phase1_pipeline/output_unified_train_blockage
`

Như vậy, sau một lần chạy đầy đủ, dự án có hai scenario độc lập:

`	ext
Scenario A: phase1_pipeline/output_unified
Scenario B: phase1_pipeline/output_unified_train_blockage
`

## 5. Các cột được bổ sung trong CSV có blockage

Bộ CSV có blockage giữ nguyên các cột gốc và bổ sung:

`	ext
original_los_flag
train_blocked
blockage_loss_db
`

Ý nghĩa:

- \original_los_flag\: trạng thái LOS ban đầu trước khi áp dụng blockage.
- \	rain_blocked\: bằng 1 nếu path bị thân tàu che chắn, bằng 0 nếu không bị che chắn.
- \lockage_loss_db\: mức suy hao đã áp dụng cho path đó.

Các cột \mplitude_real\ và \mplitude_imag\ đã được scale theo suy hao blockage. Vì vậy nếu ns-3 dùng công suất/path gain từ amplitude thì scenario B sẽ phản ánh công suất nhỏ hơn ở các path bị che chắn.

## 6. Kết quả lần chạy hiện tại

Bước hậu xử lý đã tạo đủ 5 CSV có blockage.

| TX | Số dòng CSV | Dòng bị blockage | Tỷ lệ dòng bị blockage | Timestamp bị blockage | Tỷ lệ timestamp bị blockage | Suy hao trung bình trên path bị blockage |
|---|---:|---:|---:|---:|---:|---:|
| TX1 viaductA | 6236 | 1899 | 30.45% | 1480/3391 | 43.64% | 12.0 dB |
| TX2 ground | 8460 | 2826 | 33.40% | 2449/3391 | 72.22% | 12.0 dB |
| TX3 tunnel | 36504 | 10630 | 29.12% | 2699/3391 | 79.59% | 12.0 dB |
| TX4 viaductF | 8103 | 1134 | 13.99% | 722/3391 | 21.29% | 12.0 dB |
| TX5 portal | 8990 | 2701 | 30.04% | 2275/3391 | 67.09% | 12.0 dB |

Nhận xét chính:

- TX3 tunnel có nhiều timestamp bị blockage nhất vì môi trường tunnel giàu path NLOS và nhiều path tới RX theo hướng thấp hoặc sau/phía bên.
- TX2 ground và TX5 portal cũng nhạy với blockage vì hình học mở và vùng chuyển tiếp tạo nhiều path có hướng tới RX dễ bị thân tàu cắt.
- TX4 viaductF bị blockage thấp nhất trong lần chạy này, cho thấy hình học path tại khu vực này ít giao với thể tích thân tàu hơn.
- Tỷ lệ LOS theo timestamp gần như không đổi trong lần chạy này. Nguyên nhân là anten RX đang đặt trên mái tàu, cao hơn thân tàu, nên LOS trực tiếp thường không bị thân tàu tự che chắn. Hiệu ứng blockage chủ yếu tác động vào NLOS/reflected paths.

## 7. Đánh giá mức độ phù hợp với kịch bản

Bổ sung moving train blockage là phù hợp với mục tiêu tạo trace cho ns-3 để nghiên cứu handover vì nó tạo thêm một scenario có suy hao động theo vị trí tàu. Khi tàu di chuyển, các paths tới RX không chỉ phụ thuộc vào hình học môi trường cố định mà còn phụ thuộc vào chính thân tàu. Đây là yếu tố có ý nghĩa đối với handover vì nó có thể làm công suất nhận, độ ổn định liên kết, hoặc chất lượng candidate cell thay đổi theo timestamp.

Điểm hợp lý của kết quả hiện tại:

- Bộ CSV gốc được giữ nguyên, không làm mất baseline.
- Bộ CSV blockage có cùng số dòng với baseline, thuận tiện so sánh một-một theo timestamp/path.
- Các path bị ảnh hưởng được đánh dấu rõ bằng \	rain_blocked\ và \lockage_loss_db\.
- Tunnel và portal có tỷ lệ timestamp bị blockage cao hơn, phù hợp trực giác vì các vùng này có nhiều multipath và thành phần tới từ nhiều hướng.
- LOS không bị thay đổi mạnh là hợp lý với giả thiết anten rooftop cao hơn mái tàu.

Điểm cần lưu ý:

- Mô hình blockage hiện tại là hậu xử lý hình học, không phải ray tracing lại với thân tàu là mesh điện từ trong scene.
- Hệ số 12 dB cho NLOS và 22 dB cho LOS là tham số kỹ thuật cần hiệu chỉnh nếu có measurement.
- Nếu muốn mô phỏng anten đặt bên hông tàu hoặc anten thấp hơn mái, cần giảm oof_clearance_m\ hoặc thay đổi vị trí RX trong cấu hình chính.
- Nếu muốn blockage tác động mạnh hơn tới LOS, cần mô hình hóa rooftop equipment, pantograph, mép mái, hoặc khối che chắn cục bộ quanh anten.

## 8. Khuyến nghị khi dùng cho ns-3 và handover

Khi đưa vào ns-3, nên giữ cả hai scenario:

- Scenario A dùng làm baseline ray tracing không blockage.
- Scenario B dùng làm scenario có self-blockage động bởi thân tàu.

Khi đánh giá thuật toán handover, nên so sánh ít nhất các đại lượng:

- RSRP/SINR hoặc received power suy ra từ amplitude.
- Tỷ lệ timestamp bị mất hoặc suy giảm path mạnh.
- Sự thay đổi best serving station theo thời gian.
- Số lần handover và ping-pong handover giữa hai scenario.
- Vùng tunnel/portal, vì đây là nơi blockage và multipath có thể làm chất lượng kênh biến động mạnh.

Nếu sau này có dữ liệu đo thực địa, nên hiệu chỉnh \los_blockage_loss_db\, los_blockage_loss_db\, oof_clearance_m\ và x_offset_from_train_front_m\ để trace bám sát measurement hơn.
