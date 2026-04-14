# Đánh Giá Output Của Kịch Bản Tích Hợp 3000 m

## 1. Phạm vi đánh giá

Tài liệu này đánh giá các output hiện đang có trong:

- `phase1_pipeline/output_unified/`

Các output được đánh giá là kết quả của kịch bản:

- `scenario.type = unified_3000m`
- 5 gNB `TX1..TX5`
- trajectory RX liên tục toàn tuyến

Lưu ý rất quan trọng:

- trong lần chạy hiện tại, backend ghi trong `trace_manifest.json` là `fallback` cho cả 5 TX
- vì vậy phần đánh giá này là đánh giá tính hợp lý của pipeline và xu hướng kênh truyền
- chưa phải là đánh giá cuối cùng ở mức ray tracing vật lý đầy đủ như khi chạy Sionna RT thành công

## 2. Tập output đã thu được

Các file chính đã có:

- `scene.xml`
- `scene_metadata.json`
- `trace_manifest.json`
- `mpc_tx1_viaductA.csv`
- `mpc_tx2_ground.csv`
- `mpc_tx3_tunnel.csv`
- `mpc_tx4_viaductF.csv`
- `mpc_tx5_portal.csv`
- plot tổng hợp `doppler_vs_time.png`
- plot tổng hợp `path_count_vs_time.png`
- bộ ảnh per-TX ở các thời điểm `start`, `mid`, `end`

## 3. Kiểm tra tính nhất quán toàn cục

## 3.1. Đồng bộ timestamp

Kết quả kiểm tra:

- cả 5 file CSV đều có `3391` timestamp duy nhất
- timestamp đầu là `0 ns`
- timestamp cuối là `30925518327 ns`

Đánh giá:

- hợp lý
- đây là điều kiện bắt buộc để ns-3/SioLENA có thể đọc đồng bộ nhiều link gNB-UE trên cùng quỹ đạo

## 3.2. Số lượng dòng mỗi file

| File | Tổng số dòng MPC |
|---|---:|
| `mpc_tx1_viaductA.csv` | 17613 |
| `mpc_tx2_ground.csv` | 15736 |
| `mpc_tx3_tunnel.csv` | 17116 |
| `mpc_tx4_viaductF.csv` | 18203 |
| `mpc_tx5_portal.csv` | 15526 |

Đánh giá:

- hợp lý
- số dòng khác nhau giữa các TX là bình thường vì số path khả dụng thay đổi theo vị trí gNB và môi trường
- điều cần giữ giống nhau là chuỗi timestamp, không phải số path tại từng snapshot

## 3.3. Doppler cực đại

Kết quả:

- tất cả các file đều có `max_abs_doppler_hz ≈ 9728.953 Hz`

Đánh giá:

- hợp lý
- với `f = 30 GHz` và `v = 350 km/h = 97.2 m/s`, Doppler cực đại lý thuyết xấp xỉ:

```text
f_d,max = v / lambda ≈ 9720 Hz
```

- kết quả đang thu được bám rất sát giá trị lý thuyết

## 4. Thống kê path theo từng gNB

| File | Min path/snapshot | Max path/snapshot | Trung bình |
|---|---:|---:|---:|
| `mpc_tx1_viaductA.csv` | 4 | 6 | 5.194 |
| `mpc_tx2_ground.csv` | 4 | 6 | 4.641 |
| `mpc_tx3_tunnel.csv` | 4 | 9 | 5.047 |
| `mpc_tx4_viaductF.csv` | 4 | 6 | 5.368 |
| `mpc_tx5_portal.csv` | 4 | 6 | 4.579 |

Đánh giá sơ bộ:

- TX3 trong hầm có `max path = 9`, lớn nhất trong 5 trạm
- điều này phù hợp với kỳ vọng rằng trong hầm sẽ có nhiều đường phản xạ hơn do hiệu ứng waveguide
- TX1 và TX4 ở hai đoạn viaduct có số path trung bình nhỉnh hơn TX2 và TX5, điều này hiện vẫn chấp nhận được trong logic fallback vì ngoài LOS còn có deck reflection, barrier reflection, catenary scatter

## 5. LOS hiện tại có hợp lý không

Tỷ lệ dòng có `los_flag = 1` theo toàn bộ file:

| File | Tỷ lệ LOS rows |
|---|---:|
| `mpc_tx1_viaductA.csv` | 0.0443 |
| `mpc_tx2_ground.csv` | 0.0445 |
| `mpc_tx3_tunnel.csv` | 0.0363 |
| `mpc_tx4_viaductF.csv` | 0.0753 |
| `mpc_tx5_portal.csv` | 0.0316 |

## 5.1. Nhận xét

Kết quả này chỉ hợp lý một phần.

Điểm hợp lý:

- TX3 trong hầm có tỷ lệ LOS thấp là đúng xu hướng
- TX5 ở vùng cửa hầm có tỷ lệ LOS thấp cũng chấp nhận được vì đây là vùng chuyển tiếp dễ bị che khuất

Điểm chưa hợp lý hoàn toàn:

- TX1 và TX4 là hai gNB viaduct, về trực giác phải có một đoạn LOS ngoài trời rõ rệt hơn hiện tại
- tỷ lệ LOS của TX1 chỉ khoảng `4.43%` và TX4 khoảng `7.53%` là hơi thấp nếu so với kỳ vọng vật lý của đoạn cầu cạn dài

## 5.2. Nguyên nhân

Nguyên nhân chính không nằm ở ý tưởng kịch bản mà nằm ở backend hiện tại:

1. Kết quả đang dùng `fallback`, không phải Sionna RT đầy đủ.
2. Logic LOS trong fallback được cài bằng các khoảng khả dụng và một tập reflection/scatter heuristic.
3. Ở mỗi snapshot, số path NLOS nhân tạo luôn được thêm vào khá đều.
4. Khi tính theo “tỷ lệ trên toàn bộ số dòng MPC”, LOS có thể bị chìm do số đường NLOS chiếm đa số.

Nói cách khác:

- `los_flag` hiện hữu ích để kiểm tra xu hướng
- nhưng chưa nên dùng để kết luận định lượng cuối cùng về vùng phủ LOS/NLOS của tuyến

## 6. Kiểm tra các mốc đặc trưng trên tuyến

Để nhìn nhanh sự hợp lý, có thể xét các vùng:

- `start`: đầu tuyến
- `portal_in`: gần cửa hầm vào
- `tunnel_mid`: giữa hầm
- `portal_out`: gần cửa hầm ra
- `end`: cuối tuyến

## 6.1. TX1

- `start`: 6 path
- `portal_in`: 5 path, LOS không còn
- `tunnel_mid`: 6 path, LOS không còn
- `end`: 5 path, LOS không còn

Đánh giá:

- hợp lý về xu hướng tổng thể: TX1 chỉ nên mạnh ở đầu tuyến
- chưa đẹp về mặt LOS labeling, vì đầu tuyến viaduct đáng ra nên thể hiện vùng LOS rõ hơn trong file

## 6.2. TX2

- `start`: 4 path
- `portal_in`: 6 path
- `tunnel_mid`: 6 path, LOS mất
- `end`: 4 path

Đánh giá:

- hợp lý ở chỗ TX2 mạnh lên ở vùng đất và cửa hầm
- yếu dần khi tàu vào sâu trong hầm hoặc đi quá xa

## 6.3. TX3

- `start`: 4 path
- `portal_in`: 6 path
- `tunnel_mid`: 9 path, cao nhất
- `end`: 4 path

Đánh giá:

- đây là kết quả hợp lý nhất trong 5 TX
- số path tăng rõ ở giữa hầm là đúng với trực giác waveguide
- rất phù hợp với vai trò của TX3 là gNB trong hầm

## 6.4. TX4

- `start`: 5 path
- `portal_in`: 5 path
- `portal_out`: 6 path
- `end`: 6 path

Đánh giá:

- hợp lý
- TX4 mạnh dần ở nửa sau của tuyến, nhất là sau khi ra hầm và tiến vào viaduct F

## 6.5. TX5

- `start`: 4 path
- `portal_in`: 6 path
- `tunnel_mid`: 6 path nhưng LOS mất
- `end`: 4 path

Đánh giá:

- hợp lý ở vai trò gNB biên
- TX5 nổi bật quanh cửa hầm và chuyển tiếp vào hầm
- giảm vai trò khi tàu đã đi quá sâu vào hầm hoặc đã ra xa khỏi vùng portal

## 7. Đánh giá ảnh và plot

## 7.1. `scene.xml` và `scene_metadata.json`

Hợp lý ở mức pipeline:

- `scene_metadata.json` phản ánh đúng 6 module
- có đủ 5 gNB
- có trajectory RX chi tiết

Điểm tốt:

- metadata đủ để truy dấu cấu hình đang chạy
- rất hữu ích cho việc hậu kiểm và đồng bộ với ns-3

## 7.2. `doppler_vs_time.png`

Hợp lý:

- đạt đỉnh gần giá trị lý thuyết khoảng `9720 Hz`
- phù hợp với tốc độ tàu và tần số 30 GHz

## 7.3. `path_count_vs_time.png`

Hợp lý tương đối:

- thể hiện số path dao động theo vị trí trên tuyến
- TX3 trong hầm có xu hướng path count cao hơn tại vùng giữa hầm

Nhưng cần lưu ý:

- path count hiện vẫn chịu ảnh hưởng của cách sinh path heuristic trong fallback
- nên dùng để kiểm tra xu hướng, không nên xem là ground truth

## 7.4. Ảnh `rays_3d_*`, `rays_scene_*`, `coverage_*`

Các ảnh này hợp lý cho mục tiêu minh họa:

- cho thấy TX, RX và các đường phản xạ
- nhìn được sự thay đổi giữa đầu tuyến, giữa tuyến và cuối tuyến
- tiện để kiểm tra nhanh pipeline có chạy đúng hay không

Giới hạn:

- đây chưa phải visualization của một nghiệm full-wave hay ray tracing fidelity cao
- chủ yếu là ảnh xác minh logic scene và path generation hiện tại

## 8. Những điểm đang chưa phù hợp hoàn toàn

## 8.1. `.blend` chưa được sinh cho unified scene

Đây là điểm chưa phù hợp giữa tài liệu thiết kế và pipeline cuối:

- `config.yaml` có `paths.blend_file`
- nhưng `run_pipeline.py` hiện bỏ qua Blender cho `unified_3000m`

Nguyên nhân:

- phần dựng Blender chưa được đồng bộ với scene tích hợp 3000 m
- procedural exporter đã được dùng làm nhánh chuẩn để đảm bảo pipeline chạy được ngay

Mức độ ảnh hưởng:

- không ảnh hưởng đến việc sinh CSV và output phân tích
- có ảnh hưởng nếu bạn cần `.blend` làm artifact trình bày hoặc hậu kỳ hình học

## 8.2. LOS trên viaduct còn thấp

Đây là điểm chưa phù hợp nhất trong kết quả hiện tại.

Nguyên nhân khả dĩ:

1. Backend hiện là fallback.
2. LOS không được giải bằng Sionna RT thực sự.
3. Các path NLOS heuristic đang khá “giàu”, làm loãng tỷ lệ LOS trong thống kê tổng.
4. Logic `unified_los_available()` trong code còn đơn giản, mang tính cắt đoạn hơn là giải hình học đầy đủ.

Hướng cải thiện:

- chạy lại với Sionna RT thật
- hoặc tinh chỉnh logic fallback để giảm số path NLOS nhân tạo ở viaduct
- hoặc chuyển metric đánh giá từ “LOS row ratio” sang “LOS availability theo snapshot”

## 8.3. Kết quả hiện chưa phải chuẩn cuối cho đánh giá path loss

Tài liệu thiết kế ban đầu kỳ vọng có thể kiểm tra:

- LOS ngoài trời
- NLOS trong hầm
- suy giảm mạnh ở vùng cửa hầm

Với backend fallback hiện tại:

- có thể thấy xu hướng
- nhưng chưa nên dùng để khẳng định tuyệt đối giá trị path loss, delay spread hay SINR cuối cùng

Nguyên nhân:

- chưa dùng full Sionna RT end-to-end trong lần chạy này
- hình học hiện còn đơn giản hóa

## 9. Kết luận tổng thể

## 9.1. Điều đã đạt

Kết quả hiện tại là hợp lý và thành công ở các điểm cốt lõi sau:

1. Đã chuyển thành công từ 2 scene rời sang 1 scene tích hợp duy nhất.
2. Đã sinh được 5 CSV tương ứng 5 gNB trên cùng chuỗi timestamp.
3. Đã phản ánh được logic chuyển tiếp môi trường dọc tuyến.
4. Doppler cực đại phù hợp với lý thuyết.
5. TX3 thể hiện đúng xu hướng nhiều path hơn ở giữa hầm.

## 9.2. Điều chưa nên coi là hoàn tất

Chưa nên xem kết quả hiện tại là bản cuối cùng để kết luận vật lý kênh truyền, vì:

1. Backend đang là `fallback`.
2. `.blend` cho unified scene chưa có.
3. LOS labeling ở viaduct còn hơi yếu.
4. Hình học và path generation vẫn còn mức đơn giản hóa đáng kể.

## 9.3. Đánh giá cuối

Nếu mục tiêu hiện tại là:

- kiểm tra pipeline
- chứng minh mô hình 1 scene + 5 TX + trajectory liên tục
- chuẩn bị input cho bước tích hợp ns-3

thì output hiện tại là **đủ tốt và hợp lý**.

Nếu mục tiêu là:

- công bố số liệu kênh truyền chi tiết
- so khớp chặt với bài báo hoặc thực nghiệm
- đánh giá SINR/handover ở mức fidelity cao

thì output hiện tại mới là **bản trung gian**, cần thêm bước:

- hoàn thiện Blender unified scene
- chạy Sionna RT đầy đủ
- tinh chỉnh logic LOS/NLOS và reflection trong tunnel/portal
