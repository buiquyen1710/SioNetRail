# Phân Tích Kết Quả Mô Phỏng Sionna RT Cho Kịch Bản Đường Sắt Tốc Độ Cao

## 1. Mục tiêu đánh giá

Tài liệu này đánh giá bộ kết quả sinh ra từ dự án `SioNetRail` tại:

`C:\Users\QuYen\Downloads\2025.2\ĐỒ ÁN TỐT NGHIỆP CỬ NHÂN\SioNetRail`

Mục tiêu là trả lời ba câu hỏi:

1. Kết quả hiện tại có phù hợp với kịch bản hình học đã setup hay không.
2. Kết quả có phù hợp với lý thuyết truyền sóng mmWave ở 30 GHz cho đường sắt tốc độ cao hay không.
3. Nếu chưa hợp lý, nguyên nhân ở đâu và đã cần chỉnh sửa gì để bộ kết quả trở nên đáng tin cậy hơn.

Phần đánh giá này được thực hiện trực tiếp trên các file output hiện có trong thư mục:

`phase1_pipeline/output`

và trên source code hiện tại của pipeline.

## 2. Tóm tắt kịch bản vật lý đang mô phỏng

### 2.1. Hình học môi trường

- Chiều dài scene: `1000 m`
- Chiều rộng scene: `200 m`
- Hai rail song song, gauge `1.435 m`
- Hai noise barrier ở hai bên tuyến, tâm tại `y = ±8 m`, cao `3.5 m`, dày `0.3 m`
- Cột catenary cách nhau khoảng `60 m`
- gNB đặt tại `position = [120, 18, 10] m`
- Train RX chuyển động dọc theo trục đường ray

### 2.2. Tham số vô tuyến

- Tần số mang: `30 GHz`
- Bước sóng:

`lambda = c / f = 299792458 / 30e9 ≈ 0.00999308 m`

- Vận tốc tàu:

`v = 350 / 3.6 ≈ 97.2222 m/s`

- Độ lớn Doppler cực đại theo lý thuyết:

`|f_d,max| = v / lambda ≈ 9728.95 Hz`

Giá trị này là mốc kiểm tra rất quan trọng. Nếu kết quả mô phỏng ra Doppler đỉnh nằm quá xa mốc này thì gần như chắc chắn pipeline đang có vấn đề.

## 3. Các file output đã kiểm tra

Các file chính được dùng để đánh giá:

- `phase1_pipeline/output/ns3_trace.csv`
- `phase1_pipeline/output/doppler_vs_time.png`
- `phase1_pipeline/output/path_count_vs_time.png`
- `phase1_pipeline/output/coverage_rays_start_t0.000s.png`
- `phase1_pipeline/output/coverage_rays_mid_t5.000s.png`
- `phase1_pipeline/output/coverage_rays_end_t9.500s.png`

Sau khi đồng bộ lại pipeline, bộ output cuối cùng hiện có các đặc điểm chính sau:

- Backend sử dụng: `sionna`
- Số timestamp trong CSV: `20`
- Bước thời gian thực trong CSV: `0.5 s`
- Tổng số row: `71`
- Số path/timestamp biến thiên trong khoảng `2` đến `5`
- Số timestamp có LOS: `20/20`

Phân bố số path theo timestamp:

| Số path | Số timestamp |
|---|---:|
| 2 | 1 |
| 3 | 11 |
| 4 | 4 |
| 5 | 4 |

## 4. Đánh giá tính hợp lý của kết quả theo cơ sở khoa học

### 4.1. Delay có hợp lý không

Kết quả delay trong CSV sau khi chỉnh sửa:

- Delay nhỏ nhất: khoảng `95.54 ns`
- Delay lớn nhất: khoảng `2025.21 ns`

Đổi sang chiều dài đường truyền:

- `95.54 ns` tương ứng khoảng `28.64 m`
- `2025.21 ns` tương ứng khoảng `607.1 m`

Điều này hoàn toàn hợp lý với hình học đang setup.

#### Kiểm tra tại đầu tuyến

Với RX đầu tuyến tại khoảng `x = -485 m`, khoảng cách LOS từ gNB tới RX là:

`d_start ≈ 605.29 m`

Delay LOS lý thuyết:

`tau_start = d_start / c ≈ 2019.03 ns`

CSV hiện cho delay mạnh nhất ở đầu tuyến khoảng:

`2019.03 ns`

Sai số gần như bằng không ở mức làm tròn số. Đây là dấu hiệu rất tốt, cho thấy hệ tọa độ, đơn vị mét và phép đổi sang delay đang nhất quán.

#### Kiểm tra tại vị trí gần nhất với gNB

Thời điểm tàu đi qua vùng gần gNB nhất xấp xỉ:

`t_closest = (120 - (-485)) / 97.2222 ≈ 6.223 s`

Ở gần vùng này, khoảng cách LOS tối thiểu rơi vào cỡ `28-30 m`, nên delay nhỏ nhất lý thuyết phải nằm quanh `95-100 ns`.

CSV hiện cho delay nhỏ nhất:

`95.54 ns`

Giá trị này khớp rất chặt với dự đoán hình học. Vì vậy, về delay, bộ kết quả hiện tại là hợp lý.

### 4.2. Doppler có hợp lý không

Đây là phần quan trọng nhất của bài toán HSR.

Theo lý thuyết:

- nếu phương chuyển động gần song song với phương truyền sóng, `|f_d|` tiến gần `v/lambda ≈ 9728.95 Hz`
- khi tàu đi qua vùng gần nhất với gNB, thành phần vận tốc chiếu lên phương truyền sẽ giảm, nên `|f_d|` phải giảm đáng kể
- sau khi tàu vượt qua gNB, dấu Doppler của LOS sẽ đổi

#### Kết quả hiện tại

Trong CSV:

- Doppler LOS nhỏ nhất: khoảng `-9724.29 Hz`
- Doppler LOS lớn nhất: khoảng `+9712.18 Hz`

So với giá trị cực đại lý thuyết `9728.95 Hz`, sai khác là rất nhỏ. Đây là mức sai khác chấp nhận được và hoàn toàn phù hợp với thực tế là đường truyền không bao giờ song song tuyệt đối với vector vận tốc do còn có độ lệch theo trục `y` và `z`.

#### Hình dạng đồ thị Doppler

Đồ thị `doppler_vs_time.png` hiện cho thấy:

- đầu tuyến: Doppler tuyệt đối xấp xỉ `9.7 kHz`
- gần giữa tuyến, đặc biệt quanh `6.0-6.5 s`: Doppler tuyệt đối giảm mạnh xuống khoảng `7.3-7.5 kHz`
- cuối tuyến: Doppler tuyệt đối tăng trở lại gần `9.7 kHz`

Hình dạng này là đúng về bản chất vật lý.

Lý do:

- ở đầu tuyến, RX nằm xa về phía âm trục `x`, nên vector TX-RX gần song song trục đường ray
- khi RX tiến gần vị trí `x ≈ 120 m`, thành phần theo trục `x` của phương truyền giảm, làm Doppler giảm
- sau khi vượt qua gNB, thành phần chiếu tăng trở lại về trị tuyệt đối

Lưu ý rằng đồ thị đang vẽ `Max |Doppler|`, không phải Doppler của riêng tia LOS. Vì vậy đồ thị không nhất thiết phải chạm gần `0 Hz` tại thời điểm gần nhất với gNB. Trong kịch bản có ground reflection và phản xạ từ barrier, một path khác vẫn có thể giữ trị tuyệt đối Doppler khá lớn. Điều này giải thích vì sao đồ thị có một "hõm sâu" nhưng không rơi về 0.

Kết luận cho Doppler:

- đúng biên độ
- đúng xu hướng
- đúng dấu hiệu hình học

Đây là một trong những phần hợp lý nhất của bộ kết quả hiện tại.

### 4.3. Số lượng path có hợp lý không

Hiện tại số path giải được mỗi timestamp nằm trong khoảng `2` đến `5`, chủ yếu là `3-5`.

Đối với môi trường đường sắt tốc độ cao ngoài trời như bài toán này, đây là mức hoàn toàn hợp lý.

#### Vì sao không nên kỳ vọng quá nhiều path

Nhiều tutorial trên mạng cho thấy hàng chục tia vì họ dùng:

- urban canyon rất dày vật cản
- nhiều khối nhà cao tầng
- nhiều mặt phản xạ lớn và không gian khép kín

Ngược lại, kịch bản của dự án này là:

- hành lang mở
- chỉ có hai barrier tương đối dài
- vài cột/catenary
- ground
- gNB đơn lẻ

Với kịch bản như vậy, các thành phần trội thường là:

- 1 tia LOS
- 1 ground reflection
- 1 hoặc 2 phản xạ từ barrier
- đôi khi thêm 1 vài path yếu từ cấu trúc bên cạnh

Do đó, mức `3-5 path` là hợp lý hơn nhiều so với `20-30 path`.

#### Ý nghĩa của việc số path tăng ở giữa tuyến

Đồ thị `path_count_vs_time.png` hiện cho thấy:

- đầu tuyến: khoảng `3 path`
- một thời điểm rơi xuống `2 path`
- giữa tuyến: tăng lên `4-5 path`
- cuối tuyến: giảm về `3 path`

Xu hướng này có thể giải thích được:

- khi RX ở xa, nhiều phản xạ yếu rơi dưới ngưỡng hoặc không được solver bắt lại
- khi RX đi vào vùng gần gNB hơn, số path phản xạ khả kiến tăng lên
- khi rời xa, nhiều path yếu lại biến mất

Vì vậy, xu hướng tổng thể của số path là hợp lý.

### 4.4. LOS flag có hợp lý không

Với hình học hiện tại, LOS gần như phải tồn tại trong suốt toàn bộ hành trình có ích, vì:

- gNB cao `10 m`
- RX cao `3.8 m`
- barrier chỉ cao `3.5 m`
- đường nối TX-RX đi phía trên đỉnh barrier trong phần lớn hành trình

Sau khi chỉnh sửa, CSV cuối cùng có:

- `20/20` timestamp đều có ít nhất 1 path LOS

Điều này phù hợp với lý thuyết hình học.

## 5. Những điểm chưa hợp lý trước khi chỉnh sửa

Trước khi đồng bộ lại pipeline, bộ output có một số bất hợp lý quan trọng.

### 5.1. CSV cũ có bước thời gian 1 ms nhưng số path cố định 8

Đây là dấu hiệu không tốt.

Một trace mà:

- timestamp cách đều `1 ms`
- mọi timestamp đều đúng `8 path`
- đồ thị path count là đường thẳng tuyệt đối

thường không phải là kết quả ray tracing vật lý thực sự, mà là:

- output cũ từ fallback model
- hoặc output không đồng bộ giữa file CSV, plot và backend

Điều này không phù hợp với Sionna RT thật, vì số path thực luôn biến thiên theo hình học và ngưỡng phát hiện.

### 5.2. Dùng sai Mitsuba variant cho Sionna RT

Code ban đầu ép Mitsuba về variant `*_rgb`.

Trong khi đó Sionna RT 2.x làm việc với variant `*_mono_polarized`.

Hệ quả là:

- solver có thể trả path rỗng
- hoặc xảy ra lỗi tensor/field bất thường
- hoặc hành vi không ổn định giữa các lần chạy

### 5.3. TX nằm trên hoặc trong mesh antenna

Điểm phát ban đầu được đặt trùng vào vị trí hình học của antenna.

Về ray tracing, đây là thiết lập xấu vì:

- tia có thể xuất phát từ bên trong vật cản
- gây self-blocking giả
- làm path solver mất LOS hoặc trả kết quả không ổn định

### 5.4. Static train mesh được đưa vào RT scene

Con tàu được vẽ như một mesh tĩnh ở đầu tuyến, trong khi receiver lại di chuyển dọc tuyến.

Điều này tạo ra một bất nhất vật lý:

- tại đầu hành trình, RX có thể nằm ngay trong hoặc rất gần mesh tàu tĩnh
- tự che chính mình
- làm path count đầu tuyến bị sai

Quan trọng hơn, nếu muốn mô hình hóa train body thật sự, hình học tàu cũng phải chuyển động theo thời gian. Một mesh tàu tĩnh là không phù hợp với bài toán động học train trong kịch bản này.

### 5.5. Có timestamp bị mất LOS

Ở một thời điểm, solver trả về không có path LOS dù hình học cho thấy LOS vẫn thông.

Đây là một dạng numerical miss có thể xảy ra khi:

- số sample của path solver hữu hạn
- path yếu hoặc grazing path không được bắt ổn định
- hoặc có va chạm số học với mesh

Nếu giữ nguyên kết quả này, trace sẽ có một "lỗ vật lý" không mong muốn.

### 5.6. Ảnh snapshot hiển thị nhiều tia hơn CSV thực

Ảnh `coverage_rays_*.png` ban đầu vẽ `8` tia minh họa dù CSV thật chỉ có `3-5` path.

Điều này gây mâu thuẫn trực quan:

- người xem hình tưởng solver tìm được 8 path
- nhưng CSV và plot lại không xác nhận điều đó

Về mặt báo cáo kỹ thuật, đây là điểm cần sửa để tránh hiểu lầm.

## 6. Các chỉnh sửa đã áp dụng vào source code

Để đưa bộ kết quả về trạng thái hợp lý hơn, các thay đổi sau đã được thực hiện.

### 6.1. Chỉnh đúng backend Sionna RT

File:

- `phase1_pipeline/raytracing/run_sionna_rt.py`

Đã sửa:

- không còn ép Mitsuba sang `*_rgb`
- để Sionna RT tự dùng đúng variant `llvm_ad_mono_polarized` hoặc tương đương
- tự dò `LLVM-C.dll`

### 6.2. Đưa TX ra khỏi hình học antenna

Đã sửa hàm xác định vị trí phát để điểm phát nằm hơi lùi ra phía mặt phát của antenna, thay vì nằm trong vật thể hình học.

### 6.3. Hạn chế quỹ đạo train vào vùng hữu dụng của scene

Đã thêm `scene_margin_m = 15.0`, để:

- RX không nằm đúng sát mép scene
- tránh các path mép biên thiếu ổn định

### 6.4. Không đưa static train vào RT scene

File:

- `phase1_pipeline/export/export_mitsuba_fallback.py`
- `phase1_pipeline/export/export_mitsuba.py`
- `phase1_pipeline/config/config.yaml`

Đã cấu hình:

`include_train_in_rt_scene: false`

Điều này có nghĩa:

- train vẫn được vẽ trong ảnh minh họa
- nhưng không dùng như một mesh tĩnh cho RT

Đây là lựa chọn đúng hơn về vật lý so với việc để một đoàn tàu tĩnh chắn đường truyền trong một bài toán train động.

### 6.5. Thêm bước khôi phục LOS khi solver bỏ sót

Nếu hình học xác nhận LOS vẫn thông nhưng solver không trả LOS, pipeline sẽ chèn lại một LOS analytical path.

Mục tiêu là đảm bảo trace không bị gián đoạn phi vật lý.

### 6.6. Đồng bộ số tia trên ảnh với số path thật

Ảnh snapshot hiện chỉ hiển thị số tia minh họa bằng đúng số path thực trong snapshot tương ứng.

Ví dụ:

- `start`: `1 LOS + 2 NLOS`
- `mid`: `1 LOS + 3 NLOS`
- `end`: `1 LOS + 2 NLOS`

Điều này nhất quán với CSV hơn nhiều so với trước.

### 6.7. Làm sạch log debug

Các dòng `DEBUG yaml ...` trong `common.py` đã được loại bỏ để tránh nhiễu terminal output.

## 7. Đánh giá bộ kết quả sau khi chỉnh sửa

### 7.1. Kết luận ngắn gọn

Bộ kết quả hiện tại là **hợp lý về mặt vật lý** đối với kịch bản đã setup, với các bằng chứng chính:

- delay khớp hình học
- Doppler bám rất sát giá trị cực đại lý thuyết `v/lambda`
- số path nằm trong dải hợp lý của một corridor railway ngoài trời
- LOS tồn tại liên tục
- ảnh snapshot không còn phóng đại số tia so với CSV

### 7.2. Những điểm có thể xem là "đạt"

`Delay`

- rất tốt
- khớp chặt với khoảng cách hình học

`Doppler`

- rất tốt
- đỉnh khoảng `±9.7 kHz`, sát lý thuyết
- có hõm rõ rệt gần thời điểm train đi qua vùng gần gNB nhất

`Path count`

- tốt
- dải `2-5` path là hợp lý cho bài toán này

`LOS continuity`

- tốt
- phù hợp trực giác hình học

`Tính nhất quán giữa CSV và ảnh`

- đã được cải thiện rõ rệt

## 8. Các hạn chế còn lại cần nêu rõ trong đồ án

Mặc dù bộ kết quả hiện tại đã hợp lý hơn nhiều, vẫn còn một số giới hạn mà nên ghi rõ để đánh giá đúng mức độ "chính xác".

### 8.1. CSV hiện không còn ở 1 ms thật

Trong config vẫn có:

`simulation.timestep_s: 0.001`

nhưng do giới hạn năng lực tính toán của CPU, backend Sionna RT thật hiện đang solve theo:

`solver_timestep_s: 0.5`

và CSV cuối cùng cũng ở bước `0.5 s`.

Điều này có nghĩa:

- bộ trace hiện tại là physically reasonable
- nhưng chưa phải dense trace 1 ms đúng nghĩa cho toàn bộ quãng đường

Nếu yêu cầu luận văn là trace dày `1 ms` thật, cần một trong các hướng:

- dùng GPU và giảm thời gian solve mỗi snapshot
- hoặc solve thưa bằng Sionna RT rồi nội suy theo quỹ đạo
- hoặc dùng fallback analytical model cho dense trace, còn Sionna RT làm ground-truth sparse checkpoints

### 8.2. Train body chưa được mô hình hóa như một vật cản động

Hiện tại:

- train được vẽ cho mục đích trực quan
- nhưng không đi vào RT scene dưới dạng mesh động

Điều này là chủ đích để tránh sai vật lý do train tĩnh. Tuy nhiên nó cũng có nghĩa:

- self-blocking của thân tàu
- roof scattering của thân tàu đang chuyển động
- và shadowing do hình học đoàn tàu

chưa được mô hình hóa hoàn toàn bằng Sionna RT.

Muốn đạt mức chính xác cao hơn nữa, cần một pipeline cho moving geometry hoặc scene update theo thời gian.

### 8.3. Các tia hiển thị trên ảnh vẫn là tia minh họa hình học

Sionna path object trong code hiện tại không được chuyển ra đầy đủ các bounce point để vẽ trực tiếp.

Vì vậy các đường trắng trong ảnh snapshot hiện là các surrogate rays dùng để minh họa hình học và số lượng path, chứ không phải tọa độ interaction point chính xác 100% của Sionna RT.

Điều này không ảnh hưởng tới CSV channel trace, nhưng nên nói rõ trong báo cáo để tránh overclaim.

## 9. Kết luận cuối cùng

### 9.1. Đánh giá tổng thể

Sau khi kiểm tra và chỉnh sửa, mình đánh giá rằng bộ kết quả hiện tại:

- **đã hợp lý về mặt hình học**
- **đã phù hợp với lý thuyết Doppler ở 30 GHz, 350 km/h**
- **đã phù hợp với bản chất multipath của một hành lang đường sắt ngoài trời**

và có thể dùng làm bộ kết quả đáng tin cậy hơn nhiều so với output trước đó.

### 9.2. Mức độ tin cậy

Nếu đánh giá theo ba mức:

- Đúng về xu hướng vật lý
- Đúng về bậc độ lớn và thông số chính
- Đúng tuyệt đối như ray tracing dày đặc từng 1 ms với moving geometry

thì bộ kết quả hiện tại đạt tốt ở hai mức đầu, nhưng **chưa đạt tuyệt đối ở mức thứ ba**.

### 9.3. Nhận định thực tế nhất cho đồ án

Phát biểu phù hợp nhất về mặt khoa học là:

> Bộ kết quả hiện tại là một **trace Sionna RT sparse nhưng physically consistent**, phù hợp để phân tích xu hướng delay, Doppler và số path trong kịch bản HSR mmWave ngoài trời. Tuy nhiên, nếu yêu cầu trace thật sự dày ở cấp `1 ms` và có mô hình train body động, cần mở rộng thêm pipeline theo hướng interpolation hoặc moving-scene simulation.

## 10. Các file liên quan sau khi chỉnh sửa

- `phase1_pipeline/raytracing/run_sionna_rt.py`
- `phase1_pipeline/export/export_mitsuba_fallback.py`
- `phase1_pipeline/export/export_mitsuba.py`
- `phase1_pipeline/common.py`
- `phase1_pipeline/config/config.yaml`

## 11. Output cuối cùng nên dùng để báo cáo

Nên dùng các file sau làm kết quả cuối:

- `phase1_pipeline/output/ns3_trace.csv`
- `phase1_pipeline/output/doppler_vs_time.png`
- `phase1_pipeline/output/path_count_vs_time.png`
- `phase1_pipeline/output/coverage_rays_start_t0.000s.png`
- `phase1_pipeline/output/coverage_rays_mid_t5.000s.png`
- `phase1_pipeline/output/coverage_rays_end_t9.500s.png`

