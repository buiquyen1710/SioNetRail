# Đánh Giá Chi Tiết Output Của Kịch Bản `unified_3000m` Sau Khi Chạy Sionna RT Vật Lý Thực

## 1. Phạm vi đánh giá

Tài liệu này đánh giá trực tiếp các output hiện có trong:

- `phase1_pipeline/output_unified/`

với cấu hình mô phỏng đang dùng:

- `scenario.type = unified_3000m`
- `frequency_hz = 30 GHz`
- `train_speed_kmh = 350`
- `ray_tracing.max_depth = 6`
- `ray_tracing.max_num_paths = 4000`
- `ray_tracing.samples_per_src = 3000`
- `include_train_in_rt_scene = false`
- `enable_refraction = false`

Kết luận quan trọng nhất trước khi đi vào chi tiết:

- `trace_manifest.json` hiện tại cho thấy cả 5 liên kết `TX1..TX5` đều chạy bằng backend `sionna`
- nghĩa là bộ CSV hiện đang đánh giá là kết quả ray tracing vật lý thật của Sionna RT, không phải fallback
- tuy nhiên không phải mọi artifact trong thư mục output đều có cùng giá trị khoa học; một số file chỉ có giá trị minh họa hoặc là sản phẩm còn sót từ luồng cũ

## 2. Xác nhận bộ output nào là “đầu ra vật lý thực” cần dùng để phân tích

### 2.1. Bộ output có giá trị khoa học trực tiếp

- `mpc_tx1_viaductA.csv`
- `mpc_tx2_ground.csv`
- `mpc_tx3_tunnel.csv`
- `mpc_tx4_viaductF.csv`
- `mpc_tx5_portal.csv`
- `doppler_vs_time.png`
- `path_count_vs_time.png`
- `*_doppler_vs_time.png`
- `*_path_count_vs_time.png`
- `*_rays_3d_*.png`
- `*_coverage_*.png`
- `trace_manifest.json`
- `scene.xml`
- `scene_metadata.json`

### 2.2. Artifact không nên dùng để kết luận về tính đúng sai vật lý

- `*_rays_scene_*.png`
- `ns3_trace.csv`

Lý do:

- `*_rays_scene_*.png` là ảnh render Mitsuba kiểu minh họa; chúng không phải output của path solver
- các file `*_rays_scene_*.png` hiện có timestamp cũ hơn lần chạy Sionna RT hiện tại, nên không còn đồng bộ với manifest mới
- `ns3_trace.csv` là output legacy đơn lẻ, không phản ánh bộ 5 trạm của unified scenario

## 3. Kiểm tra tính nhất quán toàn cục của bộ CSV

### 3.1. Đồng bộ thời gian

Cả 5 file CSV đều có:

- `3391` timestamp
- timestamp đầu `0 ns`
- timestamp cuối `30925518327 ns`

Đánh giá:

- đây là điểm tốt và rất quan trọng
- nó cho thấy toàn bộ 5 liên kết được lấy mẫu trên cùng một timeline hình học
- điều này phù hợp với yêu cầu hậu xử lý cho hệ thống nhiều gNB, đặc biệt nếu sau này đưa vào ns-3/SioLENA

### 3.2. Tốc độ, bước sóng và Doppler cực đại lý thuyết

Từ cấu hình:

- vận tốc tàu: `350 km/h = 97.2222 m/s`
- bước sóng tại `30 GHz`: `0.009993 m`
- Doppler cực đại lý thuyết:

```text
f_D,max = v / lambda ≈ 9728.95 Hz
```

Đây là mốc kiểm tra vật lý quan trọng nhất vì nó gần như độc lập với hình học chi tiết: nếu output sai mốc này thì mô phỏng động học là sai gốc.

### 3.3. Thống kê định lượng toàn bộ 5 liên kết

| File | Tổng dòng | Timestamps | Path TB/timestamp | Min path | Median path | Max path | LOS theo dòng | LOS theo timestamp | Delay min (µs) | Delay max (µs) | |Doppler|max (Hz) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `mpc_tx1_viaductA.csv` | 6789 | 3391 | 2.00 | 1 | 1 | 6 | 31.54% | 63.14% | 0.03196 | 8.83971 | 9728.87 |
| `mpc_tx2_ground.csv` | 9228 | 3391 | 2.72 | 1 | 2 | 6 | 22.29% | 60.66% | 0.03196 | 7.25759 | 9728.95 |
| `mpc_tx3_tunnel.csv` | 65372 | 3391 | 19.28 | 1 | 4 | 84 | 3.08% | 59.36% | 0.01300 | 5.25620 | 9728.83 |
| `mpc_tx4_viaductF.csv` | 11014 | 3391 | 3.25 | 1 | 3 | 6 | 19.90% | 64.64% | 0.03196 | 8.17238 | 9728.95 |
| `mpc_tx5_portal.csv` | 9844 | 3391 | 2.90 | 1 | 3 | 6 | 17.43% | 50.60% | 0.03196 | 6.42369 | 9728.73 |

Nhận xét tổng quát:

- mốc Doppler cực đại của cả 5 TX đều bám sát gần như tuyệt đối với lý thuyết `9728.95 Hz`
- điều đó xác nhận phần mô hình chuyển động, hướng truyền và quy đổi Doppler là đúng về vật lý
- sự khác biệt lớn nhất giữa các TX nằm ở số path, LOS ratio và delay spread, đúng với kỳ vọng vì 5 trạm nằm trong 5 môi trường truyền khác nhau

## 4. Giải thích vật lý của từng nhóm output

## 4.1. `trace_manifest.json`

Ý nghĩa:

- file này là bằng chứng quan trọng nhất để biết backend nào đã được dùng
- với lần chạy hiện tại, cả 5 entry đều có `"backend": "sionna"`

Đánh giá khoa học:

- nếu không có file này, chỉ nhìn thấy CSV là chưa đủ để khẳng định đó là ray tracing vật lý thật
- hiện tại file manifest xác nhận bộ CSV là hợp lệ để đánh giá theo góc nhìn vật lý của Sionna RT

## 4.2. Các file `mpc_*.csv`

Mỗi dòng là một multipath component tại một timestamp:

- `delay_s`: trễ lan truyền
- `amplitude_real`, `amplitude_imag`: hệ số kênh phức
- `phase_rad`: pha
- `aoa_*`, `aod_*`: góc đến/góc đi
- `doppler_hz`: Doppler của từng path
- `los_flag`: path LOS hay không

Về mặt mô hình kênh, đây là output có giá trị nhất vì chúng mô tả trực tiếp:

- số lượng thành phần đa đường
- cường độ tương đối
- độ phân tán trễ
- độ phân tán Doppler
- mức độ tồn tại của LOS

## 4.3. `doppler_vs_time.png` và `*_doppler_vs_time.png`

Ý nghĩa vật lý:

- các đồ thị này biểu diễn biên độ Doppler cực đại theo thời gian
- với tàu chạy tốc độ cao, Doppler là một chỉ số cốt lõi của tính động kênh

Đánh giá:

- cực trị Doppler khớp gần như tuyệt đối với lý thuyết
- đây là một bằng chứng mạnh cho thấy phần động học của mô hình đang đúng
- nói cách khác, nếu chỉ xét “độ đúng về tốc độ/động học”, bộ kết quả hiện tại là rất tốt

## 4.4. `path_count_vs_time.png` và `*_path_count_vs_time.png`

Ý nghĩa vật lý:

- mô tả số path được giải tại từng thời điểm
- đây là chỉ số phản ánh mức độ “giàu đa đường” của môi trường

Đánh giá:

- tunnel có path count rất lớn so với viaduct/ground/portal
- sự phân tầng này phù hợp với trực giác vật lý:
  - tunnel: nhiều phản xạ bậc cao từ tường, trần, sàn
  - viaduct: môi trường hở hơn, ít bề mặt kẹp hơn
  - portal/ground: trung gian

## 4.5. `*_rays_3d_*.png`

Ý nghĩa:

- đây là ảnh minh họa topology không gian của các ray
- chúng hữu ích để kiểm tra định tính:
  - ray có đi theo các bề mặt hợp lý không
  - ở tunnel có nhiều ray phản xạ hơn không
  - ở viaduct LOS có hiện diện ở những thời điểm phù hợp không

Đánh giá:

- chúng có giá trị debug và kiểm tra hình học rất tốt
- nhưng không nên dùng một mình để rút kết luận định lượng

## 4.6. `*_coverage_*.png`

Ý nghĩa:

- đây là hình minh họa trực quan vùng phủ tương đối quanh hình học tuyến
- chúng giúp nhìn xu hướng cường độ và đường đi ray

Đánh giá:

- có ích để kiểm tra trực quan
- nhưng đây không phải coverage map điện từ đầy đủ theo nghĩa chuẩn hệ thống
- chúng là sản phẩm hậu xử lý phục vụ phân tích nhanh hơn là một metric độc lập có thể dùng công bố

## 5. Đánh giá chi tiết từng trạm

## 5.1. TX1 – viaduct đầu tuyến

Số liệu chính:

- average path count: `2.00`
- median path count: `1`
- max path count: `6`
- LOS theo dòng: `31.54%`
- LOS theo timestamp: `63.14%`
- delay max: `8.84 µs`

Giải thích:

- TX1 ở cao độ `22 m`, RX ở module A ở cao độ `16.2 m`, môi trường đầu tuyến là viaduct khá mở
- vì thế LOS thường tồn tại theo thời gian là hợp lý
- median path count chỉ bằng `1` cho thấy trong phần lớn thời gian chỉ có vài ray mạnh tồn tại; điều này cũng phù hợp với môi trường viaduct mở, ít mặt phản xạ kẹp

Đánh giá khoa học:

- kết quả của TX1 là hợp lý về mặt vật lý
- viaduct thường có cụm path nghèo hơn tunnel, và kết quả này phản ánh đúng xu hướng đó

Điểm cần lưu ý:

- delay max `8.84 µs` là khá lớn so với một scene viaduct đầu tuyến
- điều này không phải vô lý, nhưng cho thấy vẫn còn tồn tại một số đường vòng dài qua các cấu trúc như barrier, cột, deck và các bề mặt dọc tuyến

## 5.2. TX2 – ground section

Số liệu chính:

- average path count: `2.72`
- median path count: `2`
- max path count: `6`
- LOS theo dòng: `22.29%`
- LOS theo timestamp: `60.66%`
- delay max: `7.26 µs`

Giải thích:

- TX2 đặt ở `x = 850 m`, cao độ `10 m`, đúng đoạn ground
- so với TX1, TX2 thấp hơn và gần các vật cản bên tuyến hơn, nên LOS theo dòng giảm là hợp lý
- path count tăng nhẹ so với TX1 vì đoạn ground có tương tác rõ hơn với mặt đất và hàng rào

Đánh giá:

- xu hướng kết quả là đúng với trực giác vật lý
- đoạn ground không giàu đa đường như tunnel nhưng không “sạch” như viaduct cao

Điểm cần chú ý:

- môi trường ground trong mô hình đang được vật liệu hóa khá đơn giản
- do đó số path và phân bố công suất có thể vẫn “sạch” hơn so với kênh ground thực địa ngoài đời

## 5.3. TX3 – tunnel section

Số liệu chính:

- average path count: `19.28`
- median path count: `4`
- max path count: `84`
- LOS theo dòng: `3.08%`
- LOS theo timestamp: `59.36%`
- delay min: `0.013 µs`
- delay max: `5.256 µs`

Giải thích đúng về vật lý:

- TX3 là trạm đặc trưng nhất của toàn bộ scene
- tunnel tạo điều kiện waveguide mạnh: tường trái, tường phải, trần và sàn sinh ra nhiều phản xạ bậc cao
- vì vậy path count tăng vọt là điều mong đợi

Điểm hợp lý:

- average path count rất lớn so với các TX còn lại: điều này đúng
- LOS theo dòng cực thấp: điều này cũng đúng vì trong tunnel số ray NLOS thường áp đảo về số lượng

Điểm cần phân tích kỹ hơn:

- LOS theo timestamp vẫn lên đến `59.36%`
- điều này nghĩa là ở hơn một nửa thời điểm vẫn có ít nhất một ray LOS tồn tại

Đánh giá:

- kết quả này không mâu thuẫn hoàn toàn với tunnel hiện đang setup, vì TX3 nằm ngay trong tunnel, RX cũng đi dọc trục hầm, nên dọc trục chính vẫn có thể tồn tại tia trực tiếp
- tuy nhiên tỷ lệ LOS theo timestamp cao như vậy cho thấy mô hình hầm hiện tại đang là “ống dẫn tương đối sạch”, chứ chưa phải môi trường tunnel phức tạp kiểu thực địa có nhiều che chắn cục bộ

Điểm đáng ngờ về mô hình:

- `max path = 84` trong khi median chỉ `4` cho thấy phân bố số path rất lệch
- điều đó nói lên rằng chỉ ở một số vùng không gian nhất định solver tìm được bùng nổ ray phản xạ
- đây có thể là đặc trưng vật lý của vùng cộng hưởng hình học, nhưng cũng có thể phản ánh scene đang quá lý tưởng hóa theo kiểu mặt phẳng phẳng, đối xứng, ít tổn hao ngẫu nhiên

Kết luận cho TX3:

- đây là output đúng xu hướng lớn nhất của tunnel
- nhưng mức độ “giàu path” hiện có nhiều khả năng là giàu theo phản xạ gương lý tưởng, chưa phải giàu theo kênh tunnel thực đo

## 5.4. TX4 – viaduct cuối tuyến

Số liệu chính:

- average path count: `3.25`
- median path count: `3`
- max path count: `6`
- LOS theo dòng: `19.90%`
- LOS theo timestamp: `64.64%`
- delay max: `8.17 µs`

Giải thích:

- TX4 cũng là viaduct nhưng ở cuối tuyến và có đoạn tương tác với portal out phía trước
- average path count cao hơn TX1 là hợp lý vì vùng này nhận ảnh hưởng hỗn hợp từ viaduct + vùng chuyển tiếp

Đánh giá:

- kết quả nhìn chung hợp lý
- LOS theo timestamp cao là phù hợp với đoạn mở
- số path vẫn thấp hơn rất nhiều so với tunnel, đúng logic hình học

Điểm chưa hoàn toàn thỏa đáng:

- delay spread vẫn khá lớn
- điều này cho thấy scene đang cho phép tồn tại các đường vòng xa trong môi trường viaduct; xu hướng này có thể hơi mạnh hơn kỳ vọng nếu so với một kênh HSR ngoài thực tế có beam/hướng anten chặt hơn

## 5.5. TX5 – portal

Số liệu chính:

- average path count: `2.90`
- median path count: `3`
- max path count: `6`
- LOS theo dòng: `17.43%`
- LOS theo timestamp: `50.60%`
- delay max: `6.42 µs`

Giải thích:

- portal là vùng chuyển tiếp giữa ngoài trời và hầm
- ở đây kỳ vọng vật lý là kênh pha trộn:
  - vẫn còn LOS ở một phần thời gian
  - xuất hiện thêm các reflection mạnh từ cửa hầm, mái, tường chuyển tiếp

Đánh giá:

- output hiện tại phản ánh đúng tinh thần đó
- LOS ratio thấp hơn viaduct, path count cao hơn TX1, thấp hơn tunnel là hợp lý

Điểm cần chú ý:

- do mô hình đang tắt diffraction và diffuse reflection, vùng portal hiện chủ yếu được mô tả bằng phản xạ gương
- vì vậy portal trong output có thể “sạch và ít path mềm” hơn thực tế

## 6. Các điểm phù hợp với cơ sở khoa học của mô hình kênh

## 6.1. Doppler cực đại khớp lý thuyết gần như tuyệt đối

Đây là điểm mạnh nhất của bộ kết quả.

Cơ sở khoa học:

- với sóng mang `30 GHz` và tốc độ `350 km/h`, Doppler cực đại hình học phải xấp xỉ `9728.95 Hz`
- output của 5 TX đều rơi đúng vào khoảng này

Ý nghĩa:

- mô hình chuyển động tàu, quy đổi bước sóng và chiếu vận tốc theo phương truyền là đúng
- đây là bằng chứng vật lý rất mạnh cho phần động học của channel solver

## 6.2. Tunnel giàu đa đường hơn rõ rệt so với viaduct/ground

Cơ sở khoa học:

- tunnel là môi trường có nhiều biên phản xạ bao quanh
- với specular reflections, số ray hợp lệ thường tăng mạnh hơn môi trường hở

Output:

- TX3 average path count `19.28`
- các TX khác chỉ quanh `2-3`

Đánh giá:

- hoàn toàn phù hợp với trực giác vật lý và lý thuyết lan truyền trong đường hầm

## 6.3. Delay spread của từng vùng có trật tự hợp lý

Quan sát:

- viaduct có delay max lớn nhất
- tunnel có nhiều path nhưng delay max không phải lớn nhất

Giải thích:

- viaduct có thể sinh các đường vòng dài hình học
- tunnel lại nhiều path hơn nhưng bị giới hạn trong không gian hẹp hơn nên chiều dài đường đi dư không nhất thiết lớn nhất

Điều này hợp lý về mặt vật lý.

## 7. Các điểm chưa phù hợp hoàn toàn với kịch bản mô hình kênh đang setup

Đây là phần quan trọng nhất của đánh giá.

## 7.1. Mô hình “kênh vật lý thật” hiện vẫn chưa tương ứng với kênh HSR thực địa hoàn chỉnh

Nguyên nhân nằm trong chính cấu hình đang setup:

- `include_train_in_rt_scene = false`
- `diffraction = false`
- `diffuse_reflection = false`
- `refraction = false`
- mảng anten TX/RX thực tế trong code là `1x1`, pattern `iso`, polarization `V`

Hệ quả vật lý:

- chưa có che chắn bởi thân tàu, mái tàu, nose tàu và self-blockage
- chưa mô phỏng nhiễu xạ ở mép portal, mép barrier, mép viaduct, mép tunnel
- chưa mô phỏng scattering tán xạ bề mặt thô
- chưa mô phỏng anten định hướng kiểu 5G thực tế

Vì vậy:

- output hiện tại là “ray tracing vật lý thật theo mô hình hình học-specular đang setup”
- nhưng chưa phải “mô hình kênh HSR ngoài đời đầy đủ”

## 7.2. LOS ratio theo timestamp còn cao hơn trực giác ở một số vùng khó

Ví dụ:

- TX3 tunnel có `LOS theo timestamp = 59.36%`
- TX5 portal có `LOS theo timestamp = 50.60%`

Điều này chưa hẳn sai, nhưng cần hiểu đúng:

- LOS ở đây là LOS hình học giữa điểm TX và điểm RX
- vì không có thân tàu trong scene và không có block cục bộ phức tạp, tia trực tiếp vẫn tồn tại nhiều hơn so với môi trường thực đo

Nguyên nhân:

1. train body không được đưa vào RT scene
2. tunnel và portal được mô hình hóa rất sạch, ít chi tiết ngẫu nhiên
3. solver chỉ xét bề mặt lớn và rõ ràng, không có clutter thực địa

## 7.3. Tunnel cho quá nhiều path specular nhưng vẫn thiếu các path “thực tế mềm”

TX3 có:

- average `19.28` path
- max `84` path

Điều này vừa hợp lý vừa chưa hoàn toàn hợp lý.

Hợp lý ở chỗ:

- tunnel đúng là môi trường nhiều phản xạ

Chưa hoàn toàn hợp lý ở chỗ:

- số path cao này đến chủ yếu từ phản xạ gương trên bề mặt lý tưởng
- trong tunnel thực tế, một phần năng lượng sẽ bị:
  - tán xạ
  - hấp thụ
  - suy hao do bề mặt không lý tưởng
  - chia nhỏ thành nhiều thành phần yếu hơn

Nguyên nhân:

- diffuse reflection đang tắt
- vật liệu đang dùng là các thay thế ITU hợp lệ nhưng đơn giản hóa
- geometry còn khá “sạch”, chưa có cáp, giá đỡ, thiết bị dọc hầm, biển báo, khe hở, roughness

Kết quả:

- TX3 hiện có thể đang hơi “quá giàu path specular mạnh” và “chưa đủ giàu scattering yếu”

## 7.4. Vật liệu điện từ chưa hoàn toàn bám đúng vật liệu hạ tầng đường sắt cao tốc

Đây là điểm lệch mô hình quan trọng.

Trong luồng hiện tại, một số vật liệu đã được map để tương thích với version `sionna.rt` đang cài:

- ground -> concrete
- granite -> marble
- copper -> metal

Về mặt chạy mô phỏng, cách làm này là đúng và cần thiết.

Nhưng về mặt vật lý, đây là xấp xỉ.

Hệ quả:

- hằng số điện môi và conductivity của một số bề mặt không còn đúng bản chất vật liệu gốc
- do đó hệ số phản xạ, tổn hao xuyên vật và phân bố năng lượng path có thể sai lệch cục bộ

Ảnh hưởng nhiều nhất ở:

- ground section
- portal transitions
- bề mặt đá/đất dốc ở module C và E

## 7.5. Anten đang quá lý tưởng so với kịch bản 5G HSR thực

Trong code, scene đang dùng:

- TX array: planar array `1x1`
- RX array: planar array `1x1`
- pattern: `iso`
- polarization: `V`

Điều này không phù hợp hoàn toàn với kịch bản 5G mmWave HSR thực tế, nơi thường có:

- beamforming định hướng
- mảng phần tử nhiều hơn
- gain anten hữu hạn theo góc
- sidelobe và steering

Hệ quả:

- path count hiện tại phản ánh khả năng lan truyền hình học nhiều hơn là khả năng path thực sự được anten “nhìn thấy”
- một số path yếu, góc lệch nhiều vẫn được giữ lại theo cách lạc quan hơn thực tế

Đây là một trong những nguyên nhân chính làm delay spread và số path có thể cao hơn cảm nhận thực địa.

## 7.6. Thiếu cơ chế xuyên qua cửa hầm / mép chuyển tiếp bằng diffraction

Ở portal, transition in/out, một phần quan trọng của kênh thực là:

- nhiễu xạ mép
- creeping/edge-like components
- thành phần yếu nhưng bền theo thời gian

Hiện tại:

- diffraction tắt

Hệ quả:

- mô hình portal hiện nghiêng về “LOS + specular”
- thiếu một lớp thành phần lan truyền trung gian rất quan trọng trong vùng chuyển tiếp

Đây là nguyên nhân vì sao:

- path count ở portal có thể còn thấp hơn thực tế
- nhưng LOS/đường gương lại sạch hơn thực tế

## 7.7. File `*_rays_scene_*.png` không còn tương thích với kết quả hiện tại

Đây là điểm dễ gây hiểu sai khi đọc output.

Quan sát:

- các file `*_rays_scene_*.png` có timestamp cũ hơn lần chạy Sionna RT hiện tại
- sau khi sửa luồng solver, các ảnh này không còn là sản phẩm trực tiếp của run hiện tại

Kết luận:

- không nên dùng chúng để kết luận về tính đúng/sai của Sionna RT hiện tại
- nếu giữ lại trong thư mục output thì cần ghi chú rõ là artifact cũ

## 8. Đánh giá mức độ phù hợp của bộ kết quả với mục tiêu mô hình

## 8.1. Nếu mục tiêu là kiểm tra pipeline và xu hướng kênh

Đánh giá: tốt.

Lý do:

- bộ output nhất quán
- manifest xác nhận backend thật
- Doppler đúng lý thuyết
- tunnel/viaduct/ground/portal cho hành vi phân biệt rõ ràng

## 8.2. Nếu mục tiêu là tạo trace vật lý hợp lý cho mô phỏng hệ thống mức đầu

Đánh giá: dùng được, nhưng cần ghi rõ giả thiết.

Nên ghi chú khi dùng:

- đây là trace Sionna RT dựa trên geometry sạch và specular-dominant
- chưa có train blockage
- chưa có beamforming thực
- chưa có diffraction/diffuse scattering

## 8.3. Nếu mục tiêu là bám sát measurement hoặc công bố fidelity cao

Đánh giá: chưa đủ.

Cần bổ sung:

1. train body vào scene RT
2. anten pattern thực tế hơn
3. vật liệu sát hạ tầng đường sắt hơn
4. diffraction cho vùng portal/transition
5. clutter hình học phụ
6. bước hiệu chỉnh theo measurement hoặc benchmark khác

## 9. Kết luận tổng hợp

### 9.1. Những gì bộ output hiện tại làm tốt

- xác nhận được full backend `sionna`
- Doppler đúng gần tuyệt đối với lý thuyết 30 GHz, 350 km/h
- phân biệt đúng bản chất môi trường:
  - tunnel: giàu đa đường
  - viaduct: nghèo đa đường hơn
  - ground/portal: trung gian
- bộ CSV sạch, đồng bộ và đủ tốt cho phân tích tiếp theo

### 9.2. Những gì chưa phù hợp hoàn toàn với kịch bản mô hình kênh truyền đang setup

- chưa có che chắn thân tàu dù scene mô tả tàu
- chưa có diffraction ở vùng chuyển tiếp
- chưa có diffuse scattering
- vật liệu điện từ là xấp xỉ tương thích Sionna chứ chưa phải vật liệu hạ tầng thực
- anten là isotropic 1x1, chưa phải anten mmWave/5G HSR thực
- một số artifact hình ảnh cũ (`*_rays_scene_*.png`) không còn đại diện cho lần chạy hiện tại

### 9.3. Kết luận cuối cùng

Bộ output hiện tại là một bộ kết quả Sionna RT vật lý thật, nhất quán và có cơ sở vật lý tốt ở mức geometry + specular propagation. Nó phù hợp để:

- đánh giá xu hướng kênh
- kiểm tra pipeline
- sinh trace đầu vào mức hệ thống

Tuy nhiên nó chưa phải là mô hình kênh HSR “đầy đủ hiện thực”. Những sai lệch còn lại chủ yếu không phải do solver Sionna RT chạy sai, mà do giả thiết mô hình hiện đang setup còn đơn giản hóa:

- hình học còn sạch
- vật liệu còn xấp xỉ
- anten quá lý tưởng
- chưa có blockage, diffraction và diffuse scattering

Nói ngắn gọn:

- đúng về động học và xu hướng lan truyền lớn
- hợp lý về mặt ray tracing hình học
- nhưng vẫn còn lạc quan và lý tưởng hóa nếu so với kênh đo thực địa đường sắt cao tốc mmWave
