# Đánh giá kết quả ray tracing - SioNetRail

## Tổng quan kịch bản

**Thông số mô phỏng:**
- Tần số: 30 GHz (30,000,000,000 Hz)
- Tốc độ tàu: 350 km/h ≈ 97.22 m/s
- Chiều dài scene: 1000m
- Vị trí trạm gốc: [120, 18, 10] m
- Chiều cao anten tàu: 3.8m

**Doppler lý thuyết:**
```
f_d = v / λ = 97.22 / (3×10^8 / 3×10^10) ≈ 9,722 Hz
```

## 1. Doppler Shift vs Time

### Mô tả biểu đồ
- Trục X: Thời gian (ms)
- Trục Y: Max |Doppler| (Hz)
- Đường biểu diễn giá trị Doppler lớn nhất tại mỗi thời điểm

### Kết quả thu được
- Giá trị dao động quanh **9,722 Hz**
- Phạm vi: 9,722 - 9,728 Hz

### Đánh giá
✅ **Hợp lý và chính xác**
- Giá trị Doppler rất gần với lý thuyết (9,722 Hz)
- Sai số nhỏ (< 0.1%) do:
  - Hiệu ứng đa đường (multiple paths)
  - Góc tới (AoA) thay đổi theo vị trí tàu
- Sự ổn định cho thấy mô phỏng chính xác

## 2. Path Count vs Time

### Mô tả biểu đồ
- Trục X: Thời gian (ms)
- Trục Y: Số đường truyền (paths)
- Hiển thị số lượng paths hợp lệ theo thời gian

### Kết quả thu được
- Ban đầu: ~3-4 paths
- Trung bình: 4-5 paths
- Thỉnh thoảng giảm xuống 1-2 paths

### Đánh giá
✅ **Hợp lý với kịch bản**
- LOS path luôn có
- 2-3 NLOS paths từ phản xạ (đường ray, barrier, catenary)
- Sự thay đổi số paths phản ánh:
  - Tàu di chuyển qua các vật cản
  - Sự xuất hiện/tắt nghẽn của các đường phản xạ

## 3. Amplitude vs Time

### Mô tả biểu đồ
- Trục X: Thời gian (ms)
- Trục Y: Biên độ (amplitude) thực
- Hiển thị cường độ tín hiệu theo thời gian

### Kết quả thu được
- Giá trị dao động từ 10^-6 đến 10^-5
- LOS path có biên độ mạnh nhất
- NLOS paths yếu hơn đáng kể

### Đánh giá
✅ **Hợp lý**
- Biên độ giảm theo 1/r (khoảng cách)
- LOS path mạnh nhất do không suy hao
- NLOS paths suy hao do phản xạ và khoảng cách dài hơn

## 4. Delay vs Time

### Mô tả biểu đồ
- Trục X: Thời gian (ms)
- Trục Y: Độ trễ (delay) tính bằng giây
- Hiển thị thời gian truyền của từng path

### Kết quả thu được
- LOS delay: ~1.5-2.0 × 10^-6 s
- NLOS delay: lớn hơn LOS (đường dài hơn)

### Đánh giá
✅ **Chính xác**
- Delay = distance/c
- LOS: ~450-600m → delay ~1.5-2μs
- NLOS: đường dài hơn → delay lớn hơn
- Phù hợp với kích thước scene 1000m

## 5. Phase vs Time

### Mô tả biểu đồ
- Trục X: Thời gian (ms)
- Trục Y: Pha (phase) tính bằng radian
- Hiển thị pha của tín hiệu

### Kết quả thu được
- LOS path: pha ổn định
- NLOS paths: pha thay đổi phức tạp

### Đánh giá
✅ **Hợp lý**
- LOS path có pha tương đối ổn định
- NLOS paths có pha thay đổi do:
  - Khoảng cách thay đổi
  - Hiệu ứng Doppler
  - Pha phản xạ

## 6. AoA/AoD Distribution

### Mô tả biểu đồ
- Hiển thị phân bố góc tới (AoA) và góc đi (AoD)
- Theta (θ): góc dọc
- Phi (φ): góc ngang

### Kết quả thu được
- AoA theta: tập trung quanh 1.5-1.6 rad
- AoD theta: tương tự nhưng ngược hướng
- Phi: dao động quanh 0

### Đánh giá
✅ **Phù hợp với setup**
- Vị trí trạm gốc: [120, 18, 10]
- Vị trí tàu: di chuyển dọc trục X, y=0, z=3.8
- Góc theta ~1.57 rad (90°) phù hợp với anten cao
- Phi ~0 do tàu di chuyển thẳng

## 7. LOS vs NLOS Statistics

### Mô tả biểu đồ
- Thống kê tỷ lệ LOS/NLOS paths
- Hiển thị số lượng từng loại path

### Kết quả thu được
- LOS: luôn có 1 path
- NLOS: 2-4 paths tùy thời điểm

### Đánh giá
✅ **Hợp lý**
- LOS luôn có trong môi trường line-of-sight
- NLOS từ các bề mặt phản xạ:
  - Đường ray kim loại
  - Barrier bê tông
  - Catenary poles

## 8. Power Delay Profile

### Mô tả biểu đồ
- Trục X: Độ trễ (delay)
- Trục Y: Công suất (power)
- PDP tại một thời điểm cụ thể

### Kết quả thu được
- LOS peak mạnh nhất
- NLOS peaks yếu hơn, trễ hơn

### Đánh giá
✅ **Đúng đặc tính kênh**
- LOS có công suất cao nhất
- NLOS có công suất thấp hơn do suy hao phản xạ
- Delay spread ~0.5-1μs phù hợp với scene kích thước

## 9. RMS Delay Spread

### Mô tả biểu đồ
- Trục X: Thời gian
- Trục Y: RMS delay spread (μs)
- Độ lan trễ RMS theo thời gian

### Kết quả thu được
- Giá trị ~0.3-0.8 μs
- Thay đổi theo vị trí tàu

### Đánh giá
✅ **Phù hợp**
- RMS delay spread nhỏ trong môi trường đô thị
- Sự thay đổi phản ánh sự thay đổi kênh khi tàu di chuyển

## 10. Path Evolution

### Mô tả biểu đồ
- Hiển thị sự thay đổi các paths theo thời gian
- Mỗi đường màu đại diện một path

### Kết quả thu được
- LOS path ổn định
- NLOS paths xuất hiện/tắt nghẽn

### Đánh giá
✅ **Thể hiện động học kênh**
- LOS ổn định khi không bị cản trở
- NLOS paths thay đổi khi tàu di chuyển qua các vật cản

## 11. 2D Angle Distribution

### Mô tả biểu đồ
- Phân bố góc 2D của các paths
- Hiển thị vị trí tương đối của các paths

### Kết quả thu được
- Tập trung quanh vị trí LOS
- Các điểm NLOS phân tán

### Đánh giá
✅ **Trực quan hóa tốt**
- Thể hiện rõ sự phân bố góc của kênh
- LOS ở vị trí trung tâm
- NLOS ở các vị trí khác

## 12. Summary Statistics

### Mô tả biểu đồ
- Thống kê tổng hợp của kênh
- Số paths trung bình, delay spread, etc.

### Kết quả thu được
- Số paths trung bình: ~4
- Delay spread: ~0.5 μs
- Doppler spread: ~9.7 kHz

### Đánh giá
✅ **Tóm tắt chính xác**
- Các giá trị thống kê phù hợp với phân tích chi tiết
- Cung cấp cái nhìn tổng quan về kênh

## Kết luận tổng thể

### ✅ Kết quả ray tracing HỢP LÝ và CHÍNH XÁC

**Điểm mạnh:**
1. **Doppler shift** chính xác với lý thuyết (9,722 Hz)
2. **Số lượng paths** hợp lý (3-5 paths)
3. **Delay profile** phù hợp với kích thước scene
4. **Góc tới/góc đi** đúng với geometry setup
5. **LOS/NLOS ratio** phản ánh môi trường thực

**Điểm cần lưu ý:**
- Một số NLOS paths có biên độ rất yếu (có thể bỏ qua trong mô phỏng)
- Delay spread nhỏ phù hợp với môi trường suburban/railway

**Kết luận:** Kết quả mô phỏng rất đáng tin cậy và có thể sử dụng cho nghiên cứu 5G mmWave trong môi trường đường sắt.