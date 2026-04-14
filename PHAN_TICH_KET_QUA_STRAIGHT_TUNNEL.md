# Phân Tích Kết Quả Kịch Bản 2: Straight Tunnel

## 1. Mục tiêu của phân tích

Tài liệu này phân tích bộ output của kịch bản 2 `Straight Tunnel` trong thư mục:

`phase1_pipeline/output_tunnel`

Mục tiêu là đánh giá:

1. kết quả hiện tại có phù hợp với hình học hầm thẳng đã setup hay không
2. kết quả có phù hợp với lý thuyết truyền sóng trong tunnel ở 30 GHz hay không
3. tại sao vẫn còn LOS trong hầm
4. tại sao trực giác "vào hầm sẽ có nhiều tia hơn" là đúng một phần, nhưng không nhất thiết phải xuất hiện thành hàng chục path trong trace hiện tại

## 2. Tóm tắt kịch bản vật lý

### 2.1. Hình học

- hầm thẳng
- chiều dài lòng hầm: `800 m`
- chiều rộng lòng hầm: `10 m`
- chiều cao lòng hầm: `7.5 m`
- vật liệu chính: bê tông
- một gNB active đặt ngoài cửa hầm phía tây, hướng phát vào lòng hầm
- một gNB phía đông cũng được dựng trong scene nhưng chưa dùng làm cell active trong trace hiện tại

### 2.2. Tham số vô tuyến

- tần số: `30 GHz`
- bước sóng:

`lambda ≈ 0.00999308 m`

- tốc độ tàu:

`v ≈ 97.2222 m/s`

- Doppler cực đại lý thuyết:

`|f_d,max| = v/lambda ≈ 9728.95 Hz`

Đây là mốc chuẩn để kiểm tra tính hợp lý của các path trội.

## 3. Thống kê thực tế từ CSV tunnel

File dùng để phân tích:

[ns3_trace.csv](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\ns3_trace.csv)

### 3.1. Kích thước dữ liệu

- số timestamp: `20`
- bước thời gian thực trong trace: `0.5 s`
- tổng số row: `80`
- số path mỗi timestamp: `4`
- số LOS row: `20`

Điều này có nghĩa:

- mỗi thời điểm hiện đang giữ đúng `4` path
- trong đó có `1 LOS` và `3 NLOS`

### 3.2. Delay

CSV cho:

- delay nhỏ nhất: khoảng `19.03 ns`
- delay lớn nhất: khoảng `2929.77 ns`

Đổi sang khoảng cách truyền:

- `19.03 ns` tương ứng khoảng `5.71 m`
- `2929.77 ns` tương ứng khoảng `878.3 m`

Các giá trị này phù hợp với hình học tunnel:

- khi train ở gần portal active, LOS rất ngắn
- khi train đi sâu về phía cuối scene, khoảng cách LOS tăng dần
- các path phản xạ dài hơn LOS nên delay lớn hơn

### 3.3. Doppler

CSV cho:

- Doppler nhỏ nhất: khoảng `-9677.18 Hz`
- Doppler lớn nhất: khoảng `+9728.81 Hz`

So với `9728.95 Hz` lý thuyết, đây là mức rất sát.

Điều này cho thấy:

- path mạnh nhất phần lớn vẫn gần song song với trục hầm
- tunnel đang cư xử như một corridor mạnh theo phương chuyển động

## 4. Đánh giá tính hợp lý của kết quả

## 4.1. Vẫn còn LOS trong hầm có đúng không

Đây là điểm khiến bạn dễ bị "confused", nhưng về vật lý thì điều này hoàn toàn có thể đúng.

### Kết luận ngắn

Với **hầm thẳng**, **không có khúc cua**, **không có vật chắn trong lòng hầm**, và gNB **nhìn dọc theo trục hầm**, thì:

- LOS hoàn toàn có thể tồn tại suốt quá trình

### Giải thích hình học

Ở kịch bản hiện tại:

- gNB phía tây hướng vào trong hầm theo trục `x+`
- tàu chạy dọc cùng trục hầm
- giữa TX và RX không có vật thể đặc chặn trục

Vì vậy, luôn tồn tại một đoạn thẳng nối trực tiếp từ TX đến RX bên trong hành lang hầm.

Điều này khác với các tình huống sau, nơi LOS dễ mất hơn:

- hầm cong
- có khúc cua hoặc thay đổi hướng
- có vật cản lớn trong lòng hầm
- gNB đặt lệch và không chiếu trực tiếp dọc trục
- hoặc bài toán xét cell ngoài trời khi tàu đã đi sâu vào hầm

Tức là:

> "Vào hầm thì mất LOS" là một trực giác đúng trong nhiều tình huống thực tế, nhưng **không đúng cho hầm thẳng lý tưởng**.

## 4.2. Tunnel có nhiều tia hơn mà sao trace hiện chỉ có 4 path

Đây là câu hỏi rất quan trọng.

### Về mặt vật lý

Đúng là tunnel thường có nhiều thành phần phản xạ khả dĩ hơn ngoài trời, vì:

- hai vách
- trần
- sàn

đều là các mặt phản xạ lớn và liên tục.

Ở 30 GHz, tunnel có thể thể hiện hành vi gần như waveguide, nghĩa là năng lượng bị "giữ" trong hành lang nhiều hơn môi trường mở.

### Nhưng trong trace hiện tại

Trace chỉ giữ `4 path` tại mỗi timestamp. Điều này **không có nghĩa tunnel chỉ có 4 tia vật lý tồn tại**, mà có nghĩa:

- pipeline hiện giữ các path trội nhất
- và bổ sung thêm các path hình học cơ bản để đảm bảo một mô hình tunnel hợp lý

Cụ thể, 4 path hiện tại tương ứng gần đúng với:

- 1 LOS
- 1 phản xạ sàn
- 1 phản xạ vách bắc
- 1 phản xạ vách nam

Tùy thời điểm, Sionna có thể tự tìm được ít hơn số này; pipeline sẽ bù các path chi phối để trace không bị quá nghèo và phù hợp hơn với corridor tunnel.

### Ý nghĩa khoa học

Do đó:

- "Tunnel có nhiều tia hơn" là đúng ở mức vật lý tổng quát
- nhưng "CSV phải hiện rất nhiều path" thì chưa chắc đúng, vì còn phụ thuộc thuật toán solver và tiêu chí chọn path

## 4.3. Path count phẳng ở mức 4 có hợp lý không

Đây là điểm cần nói thật rõ:

- **về xu hướng vật lý thuần túy**, path count trong tunnel không nhất thiết phải phẳng tuyệt đối
- **về trace hiện tại**, đường phẳng ở mức 4 xuất phát một phần từ cách pipeline đang giữ bộ path chi phối nhất một cách ổn định

Nói cách khác:

- đây là output hợp lý cho một mô hình "dominant path tunnel"
- nhưng chưa phải là kết quả đầy đủ nhất nếu mục tiêu là thấy toàn bộ richness của waveguide propagation

Nếu muốn path count biến thiên giàu hơn, cần tăng:

- `max_depth`
- `samples_per_src`
- số bậc phản xạ
- hoặc thêm scattering/diffraction

## 4.4. Doppler gần như bám sát cực đại trong phần lớn hành trình có hợp lý không

Có.

Lý do:

- trong tunnel thẳng, các path trội chủ yếu chạy dọc trục hầm
- vận tốc tàu cũng dọc theo trục này
- nên thành phần chiếu của vận tốc lên phương truyền luôn lớn

Vì vậy `|f_d|` thường gần `v/lambda`.

Đồ thị:

[doppler_vs_time.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\doppler_vs_time.png)

cho thấy:

- phần lớn thời gian Doppler nằm rất gần `9.7 kHz`
- có một điểm tụt mạnh hơn ở đầu hành trình

Điều này là hợp lý vì ở thời điểm gần portal, hình học giữa TX và RX thay đổi nhanh hơn, và path trội có thể tạm thời không song song hoàn toàn với trục tunnel.

## 4.5. Delay có phản ánh đúng logic tunnel không

Có.

Logic đúng trong tunnel là:

- gần portal active, delay ngắn
- đi sâu trong hầm, LOS và các path phản xạ đều dài dần
- path phản xạ luôn có delay lớn hơn LOS

Các giá trị `19 ns` đến `~2930 ns` trong CSV phù hợp với cơ chế này.

## 5. Điều gì trong kết quả hiện tại là hợp lý

Các điểm có thể xem là **đúng và hợp lý**:

### 5.1. LOS tồn tại liên tục

Điều này đúng với hầm thẳng lý tưởng.

### 5.2. Có thêm các phản xạ chính của tunnel

Ít nhất về mặt dominant path, trace hiện đã phản ánh:

- sàn
- vách trái/phải
- và LOS

### 5.3. Doppler đạt đúng bậc độ lớn

Kết quả xấp xỉ `±9.7 kHz` là rất sát lý thuyết.

### 5.4. Delay tăng mạnh khi train đi sâu hơn

Phù hợp với hình học portal-to-deep-tunnel.

## 6. Điều gì còn chưa thật sự "đẹp" hoặc chưa phải mức chính xác cao nhất

Phần này rất quan trọng để bạn giải thích trung thực trong báo cáo.

### 6.1. Path count hiện đang quá đều

Đường `Resolved Paths vs Time` hiện gần như là hằng số `4`.

Điều này phù hợp với mô hình dominant-path đơn giản, nhưng chưa thể hiện hết:

- richness của tunnel multipath
- thay đổi cường độ theo mode
- xuất hiện / biến mất của các path yếu hơn

### 6.2. Chưa phải mô hình waveguide modal đầy đủ

Kết quả hiện tại nên hiểu là:

- **mô hình dominant geometric paths trong tunnel**

chứ chưa phải:

- **phân tích mode điện từ đầy đủ của một waveguide hình chữ nhật**

Nếu muốn nghiên cứu sâu hiệu ứng waveguide, cần một mức mô hình khác, hoặc ít nhất phải mở rộng solver path richness đáng kể.

### 6.3. Hai gNB đã dựng nhưng trace chưa là dual-cell handover thật

Scene đã có:

- gNB phía tây
- gNB phía đông

Nhưng CSV hiện chỉ dùng `west_portal_gnb` làm nguồn phát active.

Do đó:

- kịch bản đã sẵn sàng cho handover
- nhưng chưa phải output handover hai cell đầy đủ

## 7. Trả lời trực tiếp câu hỏi của bạn

### 7.1. "Vào hầm thì sẽ nhiều tia hơn đúng không?"

Đúng về bản chất vật lý tổng quát.

Vì tunnel có:

- sàn
- trần
- hai vách

nên có nhiều cơ hội phản xạ hơn ngoài trời mở.

Nhưng:

- output hiện tại chỉ giữ các path chi phối nhất
- nên bạn không thấy số path tăng lên quá nhiều trong CSV

### 7.2. "Vào hầm thì sẽ mất LOS chứ?"

Không nhất thiết.

Với hầm thẳng như kịch bản này, LOS hoàn toàn có thể còn tồn tại.

LOS chỉ thường mất khi:

- hầm cong
- có vật chắn trong lòng hầm
- hoặc xét liên kết từ cell ngoài trời không còn nhìn xuyên vào sâu trong hầm nữa

### 7.3. "Vậy kết quả hiện tại có sai không?"

Không sai theo hướng "LOS còn tồn tại".

Điểm cần hiểu đúng là:

- kết quả hiện tại là hợp lý cho **straight tunnel**
- nhưng vẫn còn đơn giản ở mức số lượng path được giữ lại

## 8. Kết luận đánh giá

### 8.1. Kết luận chính

Đối với kịch bản tunnel hiện tại, kết quả sau khi chỉnh sửa là:

- **hợp lý về hình học**
- **đúng về bậc độ lớn Doppler**
- **đúng về sự tồn tại của LOS trong hầm thẳng**
- **hợp lý ở mức dominant multipath**

### 8.2. Điều cần ghi rõ trong đồ án

Phát biểu chuẩn xác nhất nên là:

> Kịch bản 2 hiện mô phỏng một hầm thẳng với LOS còn tồn tại và một tập các phản xạ chi phối từ sàn và vách hầm. Kết quả phù hợp với trực giác truyền sóng trong hành lang hẹp và với lý thuyết Doppler ở 30 GHz, nhưng chưa nhằm mô hình hóa đầy đủ toàn bộ mode waveguide bậc cao trong tunnel.

### 8.3. Nếu muốn tunnel "giống trực giác hơn nữa"

Có ba hướng nâng cấp:

1. tăng richness của path solver để lấy thêm phản xạ bậc cao
2. dùng tunnel cong hoặc vùng chuyển tiếp ngoài-trong hầm để tạo mất LOS tự nhiên
3. mở rộng sang mô hình hai gNB active để nghiên cứu handover thực sự

## 9. Các file nên dùng khi báo cáo kịch bản 2

- [config_straight_tunnel.yaml](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\config\config_straight_tunnel.yaml)
- [ns3_trace.csv](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\ns3_trace.csv)
- [doppler_vs_time.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\doppler_vs_time.png)
- [path_count_vs_time.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\path_count_vs_time.png)
- [coverage_rays_mid_t5.000s.png](C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail\phase1_pipeline\output_tunnel\coverage_rays_mid_t5.000s.png)

