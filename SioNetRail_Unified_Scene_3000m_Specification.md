# ĐẶC TẢ KỸ THUẬT CHI TIẾT
# Tuyến mô phỏng thống nhất 3000 m — SioNetRail
## Mô hình kênh truyền 5G mmWave 30 GHz cho đường sắt tốc độ cao Việt Nam

---

## 1. TỔNG QUAN THIẾT KẾ

### 1.1. Triết lý thiết kế: 1 Scene, N lần chạy TX

Theo phương pháp của Ke Guan et al. (IEEE ITS Magazine, 2021), toàn bộ tuyến đường
sắt được xây dựng trong **1 scene 3D duy nhất** gồm nhiều module địa hình nối tiếp.
Tàu (RX) chạy xuyên suốt từ đầu đến cuối mà không gián đoạn. Ray-tracing được
chạy **N lần riêng biệt** (N = số gNB), mỗi lần với 1 TX ở vị trí khác nhau nhưng cùng
scene và cùng quỹ đạo RX.

Lý do:
- Bảo toàn hiệu ứng chuyển đổi môi trường (environment transition) — hiện tượng
  quan trọng nhất ở mmWave khi tàu đi từ ngoài trời vào hầm
- Tạo ra chuỗi MPCs timestamp liên tục, khớp với yêu cầu SioLENA TracesChannelModel
- Cho phép ns-3 tính SINR chính xác (tín hiệu serving cell + nhiễu từ tất cả cell khác)
  tại mọi vị trí trên tuyến

### 1.2. Tham số tổng thể

| Tham số | Giá trị |
|---------|---------|
| Tổng chiều dài tuyến | 3000 m |
| Số module địa hình | 5 (nối tiếp liên tục) |
| Tỷ lệ địa hình | Cầu 60% (1800 m), Hầm 10% (300 m), Nền đất 30% (900 m) |
| Số gNB (TX) | 5 trạm |
| Khoảng cách inter-site | 400–700 m |
| Số lần chạy RT | 5 (1 lần/gNB) |
| Tần số | 30 GHz |
| Bandwidth | 400 MHz |
| Vận tốc tàu | 350 km/h = 97.2 m/s |
| Tổng số snapshot ước tính | ~2800 điểm |
| Dung lượng CSV ước tính | ~300–800 MB / file × 5 file |
| Hệ tọa độ | X = dọc đường ray, Y = ngang, Z = lên trên |
| Gốc tọa độ (0,0,0) | Mặt ray, giữa 2 đường ray, đầu tuyến |

### 1.3. Bản đồ tổng thể tuyến 3000 m

```
X(m): 0                700     1100  1300  1600  1900          3000
      |                 |        |     |     |     |             |
      |    MODULE A     | MOD B  |  C  | MOD |  E  |  MODULE F  |
      |                 |        |     |  D  |     |            |
      |   CẦU CẠN       | NỀN    |CHUYỂN| HẦM |CHUYỂN| CẦU CẠN  |
      |   (viaduct)     | ĐẤT   |ĐỔI  |XUYÊN|ĐỔI  | (viaduct) |
      |                 |NGOÀI  |VÀO  |NÚI  |RA   |            |
      |                 |TRỜI   |HẦM  |     |HẦM  |            |
      |_________________|________|_____|_____|_____|____________|
      |     700 m       | 400 m  |200m |300m |300m |  1100 m    |
      |     (23%)       | (13%)  |(7%) |(10%)|(10%)|  (37%)     |
      |     CẦU         | ĐẤT   | ĐẤT | HẦM | ĐẤT|  CẦU      |
      |                 |        |     |     |     |            |

Tổng cầu:  700 + 1100 = 1800 m (60%)
Tổng hầm:  300 m (10%)
Tổng đất:  400 + 200 + 300 = 900 m (30%)
```

### 1.4. Bố trí gNB (TX)

```
X(m): 0    350      700    850  1100 1300  1450  1600 1900   2450    3000
      |     |        |      |    |    |     |     |    |      |       |
      |   [TX1]      |    [TX2]  |    |   [TX3]   |    |    [TX4]    |
      |              |           |    |           |    |             |
      | MODULE A     | MOD B    | C  | MOD D     | E  |  MODULE F  |
      |   CẦU        | ĐẤT     |    |  HẦM      |    |   CẦU      |

      Lưu ý: TX5 đặt bên trong hầm
```

| gNB | X (m) | Y (m) | Z (m) | Vị trí mô tả | Module |
|-----|-------|-------|-------|---------------|--------|
| TX1 | 350 | -8.0 | 22.0 | Trên trụ riêng bên cạnh cầu cạn, giữa Module A | A |
| TX2 | 850 | -8.0 | 10.0 | Ngoài rào chắn, đoạn nền đất, giữa Module B | B |
| TX3 | 1450 | -4.0 | 5.5 | Treo trên vách hầm, giữa Module D | D |
| TX4 | 2450 | -8.0 | 22.0 | Trên trụ riêng bên cạnh cầu cạn, giữa Module F | F |
| TX5 | 1100 | -8.0 | 10.0 | Ngoài rào chắn, ngay trước cửa hầm — gNB biên | C/D |

**Sự kiện Handover dự kiến dọc tuyến**:
- HO #1: TX1 → TX2 (cầu → nền đất) tại khoảng X ≈ 600–700 m
- HO #2: TX2 → TX5 (nền đất → biên hầm) tại khoảng X ≈ 950–1050 m
- HO #3: TX5 → TX3 (biên hầm → trong hầm) tại khoảng X ≈ 1200–1350 m
- HO #4: TX3 → TX4 (trong hầm → cầu) tại khoảng X ≈ 1700–1900 m

HO #2 và HO #3 là **quan trọng nhất** — xảy ra tại vùng chuyển đổi ngoài trời/hầm,
nơi SINR sụt giảm đột ngột và Adaptive Handover cần phản ứng.

---

## 2. ĐẶC TẢ CHI TIẾT TỪNG MODULE

---

### 2.1. MODULE A — Cầu cạn (Viaduct) | X: 0 → 700 m | Dài 700 m

#### Mục đích
Mô hình môi trường cầu cạn — chiếm tỷ lệ lớn nhất trên tuyến Bắc–Nam. Kênh truyền
LOS sạch, ít scatterer, Doppler rõ nhất. Dùng làm baseline reference cho SINR ổn định.

#### Vật thể và kích thước

**A1. Thân cầu (Viaduct Deck)**
- Object name: `VIADUCT_A_Deck`
- Hình dạng: Box
- Kích thước: 700 m (X) × 12.0 m (Y) × 2.0 m (Z)
- Vị trí tâm: (350, 0, 11.0)
- Mặt trên (mặt chạy tàu) tại Z = 12.0 m
- Vật liệu: Concrete (εr = 5.31, σ = 0.0326 S/m)

**A2. Trụ cầu × 14** (mỗi 50 m)
- Object name: `PIER_A_01` đến `PIER_A_14`
- Hình dạng: Box
- Kích thước mỗi trụ: 3.0 m (X) × 6.0 m (Y) × 10.0 m (Z)
- Vị trí trụ thứ i: (50×i, 0, 5.0), i = 1, 2, ..., 14
- Chân trụ tại Z = 0 (mặt đất), đỉnh trụ tại Z = 10.0 (chạm đáy deck)
- Vật liệu: Concrete

**A3. Thành chắn cầu (Parapet) × 2**
- Object name: `PARAPET_A_Left`, `PARAPET_A_Right`
- Hình dạng: Box mỏng
- Kích thước: 700 × 0.25 × 1.2 m
- Vị trí trái: (350, -5.875, 12.6)
- Vị trí phải: (350, +5.875, 12.6)
- Vật liệu: Concrete

**A4. Rào chắn cách âm trên cầu × 2**
- Object name: `BARRIER_A_Left`, `BARRIER_A_Right`
- Hình dạng: Box
- Kích thước: 700 × 0.20 × 3.5 m
- Vị trí trái: (350, -3.6, 13.75) — chân rào tại Z = 12.0
- Vị trí phải: (350, +3.6, 13.75)
- Vật liệu: Concrete

**A5. Đường ray trên cầu × 2**
- Object name: `RAIL_A_Left`, `RAIL_A_Right`
- Hình dạng: Box dài
- Kích thước: 700 × 0.07 × 0.172 m
- Vị trí trái: (350, -0.7175, 12.086)
- Vị trí phải: (350, +0.7175, 12.086)
- Vật liệu: Steel (εr = 1.0, σ = 1×10⁷ S/m)

**A6. Track bed trên cầu**
- Object name: `TRACKBED_A`
- Hình dạng: Box
- Kích thước: 700 × 3.2 × 0.3 m
- Vị trí: (350, 0, 11.85)
- Vật liệu: Concrete

**A7. Cột điện tiếp xúc × 12** (mỗi 60 m, bắt đầu từ X = 30)
- Object name: `POLE_A_01` đến `POLE_A_12`
- Hình dạng: Cylinder (bán kính 0.15 m, cao 7.0 m, 12 vertices)
- Vị trí: (30 + 60×i, -2.5, 12.0 + 3.5) — chân cột tại mặt cầu
- Vật liệu: Steel

**A8. Dây catenary**
- Object name: `WIRE_A_Catenary`
- Hình dạng: Cylinder (bán kính 0.01 m, dài 700 m, 8 vertices)
- Vị trí: (350, -0.2, 17.5)
- Vật liệu: Copper (εr = 1.0, σ = 5.8×10⁷ S/m)

**A9. Mặt đất dưới cầu**
- Object name: `GROUND_A_Below`
- Hình dạng: Plane
- Kích thước: 700 × 200 m
- Vị trí: (350, 0, 0)
- Vật liệu: Dry soil (εr = 3.0, σ = 0.001 S/m)

#### Mặt cắt ngang Module A

```
                    Z (m)
                    |
          22.0 ─────+── [TX1] ← gNB trên trụ riêng
                    |
          17.5 ─────+── ~~~wire~~~ dây catenary
          16.2 ─────+──────── [RX] anten tàu (nóc toa)
          15.8 ─────+── ┌─────────────┐ nóc tàu
                    |   │  ĐOÀN TÀU   │
          13.75─────+─┌─┤             ├─┐ đỉnh rào chắn
                    |  │R│             │R│
          12.6 ─────+─┤P│             │P├ đỉnh parapet
          12.0 =====+═╧╧═══╤═════╤═══╧╧══ mặt cầu (deck top)
          10.0 ─────+  ║   │PIER │   ║    đáy deck
                    |  ║   │     │   ║
           5.0 ─────+  ║   │     │   ║    trụ cầu
                    |  ║   │     │   ║
           0.0 =====+══════╧═════╧══════  mặt đất
                    |
         ──────────+───────────────────── Y (m)
              -8.0  -5.9 -3.6 -0.72  0  +0.72 +3.6  +5.9
              (TX)       (rào) (ray)     (ray) (rào)
```

---

### 2.2. MODULE B — Nền đất ngoài trời có rào chắn | X: 700 → 1100 m | Dài 400 m

#### Mục đích
Mô hình đoạn tuyến trên mặt đất — kênh truyền phản xạ nhiều hơn cầu cạn do mặt đất
gần hơn và rào chắn hai bên tạo waveguide nhẹ. Cũng là đoạn chứa gNB TX2.

#### Chuyển đổi từ Module A sang Module B (X: 690–710 m)
Tại X = 700 m, cầu cạn kết thúc. Trong thực tế, cầu "hạ dần" về mặt đất qua một đoạn
dốc. Để đơn giản hóa cho RT, xử lý như sau:
- Module A kết thúc rõ ràng tại X = 700 m
- Module B bắt đầu tại X = 700 m
- **Đường ray liên tục** — trong Blender, tạo rail xuyên suốt 3000 m (không cắt
  tại điểm chuyển module). Rail luôn ở Z phù hợp với module đó.
- Tại vùng chuyển đổi, Z đường ray giảm từ 12.0 → 0.0 m. Xử lý bằng cách: tàu
  trên cầu Z_RX = 16.2, tàu trên đất Z_RX = 4.2. Quỹ đạo RX nội suy Z trong
  đoạn 20 m chuyển tiếp.

#### Vật thể và kích thước

**B1. Track bed**
- Object name: `TRACKBED_B`
- Kích thước: 400 × 3.2 × 0.3 m
- Vị trí: (900, 0, -0.15) — mặt trên tại Z = 0
- Vật liệu: Concrete

**B2. Đường ray × 2**
- `RAIL_B_Left`: (900, -0.7175, 0.086)
- `RAIL_B_Right`: (900, +0.7175, 0.086)
- Kích thước, vật liệu: giống Module A nhưng dài 400 m, Z trên mặt đất

**B3. Rào chắn cách âm × 2**
- `BARRIER_B_Left`: (900, -3.6, 1.75)
- `BARRIER_B_Right`: (900, +3.6, 1.75)
- Kích thước: 400 × 0.20 × 3.5 m, chân rào tại Z = 0
- Vật liệu: Concrete

**B4. Cột điện × 7** (mỗi 60 m)
- `POLE_B_01` đến `POLE_B_07`
- Vị trí: (700 + 60×i, -2.5, 3.5), i = 0, 1, ..., 6
- Kích thước, vật liệu: giống Module A nhưng chân cột tại Z = 0

**B5. Dây catenary**
- `WIRE_B_Catenary`
- Vị trí: (900, -0.2, 5.5) — Z = 5.5 m trên mặt ray
- Dài 400 m

**B6. Mặt đất**
- `GROUND_B`
- Plane: 400 × 200 m tại Z = -0.3
- Vật liệu: Dry soil

#### Mặt cắt ngang Module B

```
                    Z (m)
                    |
          10.0 ─────+── [TX2] ← gNB ngoài rào
                    |
           5.5 ─────+── ~~~wire~~~ dây catenary
           4.2 ─────+──────── [RX] anten tàu
           3.8 ─────+── ┌─────────────┐ nóc tàu
           3.5 ─────+─┌─┤             ├─┐ đỉnh rào chắn
                    |  │R│  ĐOÀN TÀU   │R│
                    |  │À│             │À│
                    |  │O│             │O│
           0.0 =====+═╧═╧═╤═════════╤═╧═╧═ mặt ray
          -0.3 ─────+─────┴─────────┴───── mặt đất
                    |
         ──────────+──────────────────── Y (m)
              -8.0  -3.6 -2.5  -0.72  0  +0.72  +3.6
              (TX)  (rào) (cột) (ray)     (ray)  (rào)
```

---

### 2.3. MODULE C — Vùng chuyển đổi vào hầm | X: 1100 → 1300 m | Dài 200 m

#### Mục đích
**Module quan trọng nhất của toàn tuyến.** Đây là nơi kênh truyền chuyển đổi đột ngột
từ LOS ngoài trời sang NLOS trong hầm. SINR sụt giảm > 15 dB trong vòng < 50 ms.
Đoạn này cần **lấy mẫu mật độ cao** (mỗi 0.5 m) để capture chính xác hiệu ứng
blockage. Thuật toán Adaptive Handover sẽ được kiểm chứng chủ yếu tại đoạn này.

#### Cấu trúc vật lý (theo thứ tự tàu đi qua)

**Giai đoạn 1 (X: 1100 → 1200 m)**: Đoạn tiếp cận cửa hầm — vẫn ngoài trời
- Rào chắn vẫn có nhưng **kết thúc** tại X = 1200 m
- Vách núi bắt đầu nhô lên hai bên từ X ≈ 1150 m, cao dần
- gNB TX5 đặt tại (1100, -8.0, 10.0) — gNB biên ngoài hầm
- Vẫn LOS đến TX5 và TX2

**Giai đoạn 2 (X: 1200 → 1300 m)**: Đoạn "cổ phễu" dẫn vào hầm
- Rào chắn đã hết
- Vách núi hai bên cao dần, thu hẹp không gian
- Tại X = 1300 m: **CỬA HẦM** — vách núi khép kín thành vỏ hầm
- LOS đến TX5 (ngoài) mất dần, phản xạ từ vách núi tăng dần

#### Vật thể

**C1. Track bed, Rails, Mặt đất**: Tiếp tục từ Module B, không thay đổi.

**C2. Rào chắn (chỉ nửa đầu)**
- `BARRIER_C_Left`: kéo dài từ X = 1100 → 1200 m (100 m)
- `BARRIER_C_Right`: tương tự
- Kích thước: 100 × 0.20 × 3.5 m

**C3. Cột điện (chỉ 2 cột)**
- `POLE_C_01`: (1120, -2.5, 3.5)
- `POLE_C_02`: (1180, -2.5, 3.5)

**C4. Vách núi hai bên (steep walls dẫn vào hầm)**
- `STEEPWALL_C_Left`, `STEEPWALL_C_Right`
- Hình dạng: Box nghiêng hoặc Box thẳng đứng (đơn giản hóa)
- Phiên bản đơn giản: 2 tấm phẳng đứng, cao tăng dần
  - Tại X = 1150: cao 2 m
  - Tại X = 1300: cao 7.5 m (bằng chiều cao hầm)
- Kích thước mỗi tấm: 150 m (X) × 0.5 m (Y) × 7.5 m (Z)
  (chiều cao trung bình)
- Vị trí trái: (1225, -5.25, 3.75)
- Vị trí phải: (1225, +5.25, 3.75)
- Vật liệu: Granite (εr = 7.0, σ = 0.01 S/m) hoặc Concrete

**Cách xử lý đơn giản hơn cho steep wall**:
Thay vì mô hình cao dần, dùng 2–3 bậc:
- Bậc 1 (X: 1150→1200): Box 50 × 0.5 × 3.0 m, tâm Z = 1.5
- Bậc 2 (X: 1200→1250): Box 50 × 0.5 × 5.0 m, tâm Z = 2.5
- Bậc 3 (X: 1250→1300): Box 50 × 0.5 × 7.5 m, tâm Z = 3.75

#### Mặt cắt dọc Module C

```
Z (m)
  |
 10 ── [TX5]
  |     ↓
  |   gNB biên          vách núi cao dần
  |                    ╱╱╱╱╱╱╱╱╱╗
 7.5──                ╱╱╱╱╱╱╱╱╱╱║ ← cửa hầm
  |               ╱╱╱╱╱╱╱╱╱╱╱╱╱║
 4.2── ──[RX]→→→→→→→→→→→→→→→→→→[RX]→→
  |    rào  │rào│ vách bậc1│bậc2│bậc3║
 0.0═══════╧════╧══════════╧════╧════╝
  |
  +──────────────────────────────────── X (m)
  1100     1150  1200  1250  1300
  TX5           rào hết     cửa hầm
         │←── 0.5 m/sample ──→│
```

---

### 2.4. MODULE D — Hầm xuyên núi thẳng | X: 1300 → 1600 m | Dài 300 m

#### Mục đích
Hầm thẳng 300 m — đủ dài để quan sát waveguide effect ổn định. Kênh truyền NLOS
thuần túy với phản xạ bậc cao. Theo Ke Guan et al., trong hầm ở 30 GHz:
- LOS mất tại khoảng cách > 50–100 m từ cửa hầm (phụ thuộc độ cong/thẳng)
- Phản xạ lên đến bậc 10 đóng vai trò quan trọng
- Diffraction và scattering không đáng kể — có thể tắt để tiết kiệm tính toán
- SNR giảm đều theo khoảng cách do waveguide loss

#### Cấu trúc hầm

Sử dụng **hầm 5 mặt phẳng** (box approach) — đơn giản, chính xác, dễ implement:

**D1. Sàn hầm**
- Object name: `TUNNEL_D_Floor`
- Box: 300 × 10.0 × 0.5 m
- Vị trí: (1450, 0, -0.25)
- Vật liệu: Concrete (εr = 5.31, σ = 0.0326)

**D2. Trần hầm**
- Object name: `TUNNEL_D_Ceiling`
- Box: 300 × 10.0 × 0.5 m
- Vị trí: (1450, 0, 7.75)
- Vật liệu: Concrete

**D3. Vách hầm trái**
- Object name: `TUNNEL_D_WallLeft`
- Box: 300 × 0.5 × 7.5 m
- Vị trí: (1450, -5.25, 3.75)
- Vật liệu: Concrete

**D4. Vách hầm phải**
- Object name: `TUNNEL_D_WallRight`
- Box: 300 × 0.5 × 7.5 m
- Vị trí: (1450, +5.25, 3.75)
- Vật liệu: Concrete

**D5. Đường ray trong hầm**
- Tiếp tục từ Module C, giống thông số Module B (Z = 0)

**KHÔNG có**: rào chắn, cột điện, dây catenary (theo nguyên tắc Concise: bỏ
vật thể < 7 m² trong hầm)

**Mặt chặn cửa hầm**: KHÔNG CẦN nếu vách núi Module C đã kín. Nếu muốn
chắc chắn sóng không lọt, thêm 2 tấm chặn tại X = 1300 và X = 1600 (dạng
"vành khuyên": kín quanh ngoài hầm, hở ở tiết diện hầm).

#### Cấu hình RT đặc biệt cho hầm
```
Khi chạy RT cho Module D:
- max_reflection_order = 8 đến 10 (thay vì 4 cho ngoài trời)
- diffraction = OFF (theo Ke Guan: không đáng kể trong hầm thẳng)
- scattering = OFF (không đáng kể trong hầm trơn nhẵn)

Nếu Sionna RT không cho phép thay đổi reflection order theo vùng trong
cùng 1 lần chạy → dùng max_reflection_order = 6 cho toàn scene
(compromise giữa chính xác trong hầm và tốc độ ngoài trời)
```

#### Mặt cắt ngang Module D (trong hầm)

```
                    Z (m)
                    |
           7.5 ─────+── ╔══════════════════════╗ trần hầm
                    |   ║                      ║
           5.5 ─────+── ║  [TX3] ← gNB trong hầm║
                    |   ║    treo trên vách    ║
           4.2 ─────+── ║      [RX] anten tàu  ║
           3.8 ─────+── ║  ┌─────────────┐     ║
                    |   ║  │  ĐOÀN TÀU   │     ║ vách hầm
                    |   ║  │             │     ║
                    |   ║  └─────────────┘     ║
           0.0 =====+══╚══╤═══════════╤═══════╝ sàn hầm
                    |
         ──────────+──────────────────────── Y (m)
                  -5.0  -1.7   0    +1.7   +5.0
                 (vách)       (tâm)        (vách)
```

---

### 2.5. MODULE E — Vùng chuyển đổi ra hầm | X: 1600 → 1900 m | Dài 300 m

#### Mục đích
Đối xứng với Module C nhưng theo chiều ngược lại: tàu ra khỏi hầm, kênh truyền
chuyển từ NLOS → LOS. Module này dài hơn Module C (300 m thay vì 200 m) để bao
gồm cả đoạn ổn định sau khi ra hầm.

#### Cấu trúc (theo thứ tự tàu đi qua)

**Giai đoạn 1 (X: 1600 → 1700 m)**: Cửa hầm ra + vách núi giảm dần
- Tại X = 1600: **CỬA HẦM RA** — tương tự cửa hầm vào
- Vách núi hai bên hạ dần (đối xứng Module C)
- LOS đến TX4 (ngoài) bắt đầu xuất hiện từ cửa hầm

**Giai đoạn 2 (X: 1700 → 1900 m)**: Đoạn ngoài trời sau hầm
- Vách núi hết tại X ≈ 1750 m
- Rào chắn bắt đầu lại từ X = 1750 m
- Cột điện, dây catenary trở lại
- Nền đất phẳng

#### Vật thể
Đối xứng với Module C, cộng thêm phần ngoài trời:

**E1. Vách núi (đối xứng C4)**
- Steep walls giảm chiều cao từ 7.5 m → 0 m
- Bậc 3→2→1 (ngược Module C)

**E2. Rào chắn (X: 1750 → 1900 m)**: 150 m, tương tự Module B

**E3. Cột điện × 3**: tại X = 1770, 1830, 1890

**E4. Track bed, Rails, Mặt đất**: tiếp tục từ Module D

#### Lấy mẫu mật độ cao
Vùng X: 1550 → 1700 m lấy mẫu mỗi 0.5 m (tương tự Module C)

---

### 2.6. MODULE F — Cầu cạn (Viaduct) | X: 1900 → 3000 m | Dài 1100 m

#### Mục đích
Tương tự Module A nhưng dài hơn (1100 m). Đại diện cho phần cầu cạn dài nhất của
tuyến. Kênh truyền quay lại LOS ổn định sau khi ra hầm.

#### Vật thể
**Giống hệt Module A** về cấu trúc, chỉ khác:
- Tất cả object đổi prefix `_A_` → `_F_`
- X offset: tâm tại (2450, ...) thay vì (350, ...)
- Dài 1100 m thay vì 700 m
- Trụ cầu × 22 (mỗi 50 m)
- Cột điện × 18 (mỗi 60 m)

**Chuyển đổi Module E → Module F (X: 1890–1910 m)**: tương tự chuyển đổi B→A
nhưng ngược lại (đất → cầu). Z đường ray tăng từ 0 → 12.0 m.

---

## 3. ĐOÀN TÀU (CHUNG CHO TOÀN TUYẾN)

**Object name: `TRAIN_Body`**

Trong Sionna RT, đoàn tàu được mô hình là 1 box kim loại di chuyển theo quỹ đạo RX.
Tại mỗi snapshot, vị trí tàu được cập nhật.

| Tham số | Giá trị |
|---------|---------|
| Hình dạng | Box |
| Kích thước | 25.0 × 3.4 × 3.8 m (dài × rộng × cao) |
| Vật liệu | Aluminum (εr = 1.0, σ = 3.8×10⁷) |
| Vị trí | Cập nhật mỗi snapshot: tâm tàu tại (X_rx - 12.5, 0, Z_rx - 2.1) |
| Anten RX | Trên nóc toa đầu: (X_rx, 0, Z_rx) với Z_rx phụ thuộc module |

---

## 4. QUỸ ĐẠO RX CHI TIẾT

```python
rx_positions = []

# MODULE A: Cầu cạn (0–700 m), mỗi 1.0 m, Z = 16.2
for x in range(0, 690):
    rx_positions.append([float(x), 0.0, 16.2])

# Chuyển đổi Cầu → Đất (690–710 m), mỗi 0.5 m, Z giảm dần
for i in range(40):
    x = 690.0 + i * 0.5
    z = 16.2 - (16.2 - 4.2) * (i / 40.0)
    rx_positions.append([x, 0.0, round(z, 2)])

# MODULE B: Nền đất (710–1100 m), mỗi 1.0 m, Z = 4.2
for x in range(710, 1100):
    rx_positions.append([float(x), 0.0, 4.2])

# MODULE C: Chuyển đổi vào hầm (1100–1300 m), mỗi 0.5 m, Z = 4.2
for i in range(400):
    rx_positions.append([1100.0 + i * 0.5, 0.0, 4.2])

# MODULE D: Hầm (1300–1600 m), mỗi 1.0 m, Z = 4.2
for x in range(1300, 1600):
    rx_positions.append([float(x), 0.0, 4.2])

# MODULE E: Chuyển đổi ra hầm (1600–1900 m)
# Vùng cửa hầm (1600–1750 m), mỗi 0.5 m
for i in range(300):
    rx_positions.append([1600.0 + i * 0.5, 0.0, 4.2])
# Vùng ổn định (1750–1900 m), mỗi 1.0 m
for x in range(1750, 1900):
    rx_positions.append([float(x), 0.0, 4.2])

# Chuyển đổi Đất → Cầu (1890–1910 m), mỗi 0.5 m, Z tăng dần
for i in range(40):
    x = 1890.0 + i * 0.5
    z = 4.2 + (16.2 - 4.2) * (i / 40.0)
    rx_positions.append([x, 0.0, round(z, 2)])

# MODULE F: Cầu cạn (1910–3000 m), mỗi 1.0 m, Z = 16.2
for x in range(1910, 3001):
    rx_positions.append([float(x), 0.0, 16.2])

print(f"Tổng số snapshot: {len(rx_positions)}")
# Ước tính: 690 + 40 + 390 + 400 + 300 + 300 + 150 + 40 + 1091 ≈ 3401
```

---

## 5. BẢNG VẬT LIỆU ĐIỆN TỪ TỔNG HỢP

Tất cả giá trị theo ITU-R P.2040 tại 30 GHz.

| ID | Tên trong Sionna RT | εr | σ (S/m) | Dùng cho |
|----|---------------------|-----|---------|----------|
| M01 | `concrete` | 5.31 | 0.0326 | Track bed, rào chắn, vách hầm, sàn hầm, thân cầu, parapet, vách núi |
| M02 | `metal_steel` | 1.0 | 1×10⁷ | Đường ray, cột điện |
| M03 | `metal_copper` | 1.0 | 5.8×10⁷ | Dây catenary |
| M04 | `metal_aluminum` | 1.0 | 3.8×10⁷ | Thân tàu |
| M05 | `dry_soil` | 3.0 | 0.001 | Mặt đất ngoài trời |
| M06 | `granite` | 7.0 | 0.01 | Vách núi (vùng chuyển đổi) |

Lưu ý từ Ke Guan et al.: Ở bài báo gốc, họ dùng giá trị vật liệu:
- Metal: εr = 1.00, loss tangent = 10⁷ (cho billboard, barrier, pylon, ...)
- Concrete: εr = 1.06, loss tangent = 0.65 (cho track, tunnel, ...)
- Aluminium alloy: εr = 1.29, loss tangent = 10⁷ (cho tàu)

Các giá trị này ở 60 GHz. Đề tài bạn ở 30 GHz nên dùng giá trị ITU-R P.2040
cho 30 GHz (đã liệt kê ở bảng trên). Sự khác biệt không lớn nhưng cần nhất
quán.

---

## 6. CẤU HÌNH SIONNA RT

### 6.1. Tham số Ray-Tracing

| Tham số | Giá trị ngoài trời | Giá trị trong hầm | Ghi chú |
|---------|--------------------|--------------------|---------|
| Tần số | 30 GHz | 30 GHz | |
| Bandwidth | 400 MHz | 400 MHz | |
| Max reflection order | 4 | 8–10 | Hầm cần bậc cao do waveguide |
| Diffraction | ON | OFF | Ke Guan: diffraction không đáng kể trong hầm thẳng |
| Scattering | ON | OFF | Ke Guan: scattering không đáng kể trong hầm |
| Max paths | 25 | 50 | Hầm nhiều đường phản xạ hơn |

**Nếu Sionna RT chỉ cho phép 1 bộ tham số cho cả scene**:
Dùng compromise: reflection order = 6, diffraction = ON, scattering = ON.
Thời gian chạy sẽ lâu hơn nhưng kết quả bao phủ cả hai loại môi trường.

### 6.2. Anten TX (gNB)

| Tham số | Giá trị |
|---------|---------|
| Loại mảng | UPA (Uniform Planar Array) 4×4 |
| Phân cực | Dual-polarized (±45°) |
| Tổng phần tử | 32 (4×4×2) |
| Khoảng cách | λ/2 = 5 mm |
| Boresight | Hướng về phía đường ray |
| Trong Sionna RT | Có thể dùng omni-directive 0 dBi (giống Ke Guan) rồi thêm antenna pattern ở post-processing |

### 6.3. Anten RX (tàu)

| Tham số | Giá trị |
|---------|---------|
| Loại mảng | ULA 1×2 |
| Phân cực | Dual-polarized (±45°) |
| Tổng phần tử | 4 (1×2×2) |
| Khoảng cách | λ/2 = 5 mm |
| Vị trí | Nóc toa đầu |

---

## 7. FORMAT OUTPUT — CSV THEO SCHEMA SioLENA

Mỗi file CSV (1 file / TX) chứa toàn bộ MPCs cho tất cả snapshot:

```
timestamp_ns,path_id,delay_s,amplitude_real,amplitude_imag,phase_rad,aoa_theta_rad,aoa_phi_rad,aod_theta_rad,aod_phi_rad,doppler_hz,los_flag
```

**5 file output**:
- `mpc_tx1_viaductA.csv` (TX1 tại X=350, cầu cạn)
- `mpc_tx2_ground.csv` (TX2 tại X=850, nền đất)
- `mpc_tx3_tunnel.csv` (TX3 tại X=1450, trong hầm)
- `mpc_tx4_viaductF.csv` (TX4 tại X=2450, cầu cạn)
- `mpc_tx5_portal.csv` (TX5 tại X=1100, biên hầm)

Tất cả 5 file có **cùng chuỗi timestamp** (vì cùng quỹ đạo RX).
ns-3 TracesChannelModel sẽ đọc cả 5 file, mỗi file cho 1 liên kết gNB–UE.

---

## 8. CHECKLIST KIỂM TRA TRƯỚC KHI CHẠY

### 8.1. Hình học
- [ ] Tất cả mesh triangulated
- [ ] Tất cả transform applied
- [ ] Normal hướng ra ngoài
- [ ] Không có khe hở tại điểm chuyển module (đặc biệt cửa hầm X=1300, X=1600)
- [ ] Đường ray liên tục xuyên suốt 3000 m
- [ ] Kích thước đúng mét

### 8.2. Vật liệu
- [ ] Mỗi object gán đúng 1 material
- [ ] Giá trị εr và σ khớp bảng ITU-R P.2040 tại 30 GHz

### 8.3. TX/RX
- [ ] 5 TX đặt đúng tọa độ, KHÔNG nằm bên trong vật thể nào
- [ ] Quỹ đạo RX không xuyên qua vật thể
- [ ] Z quỹ đạo RX đúng: 16.2 trên cầu, 4.2 trên đất/hầm, nội suy tại vùng chuyển đổi

### 8.4. Output
- [ ] Chạy thử 10 snapshot đầu — có output MPCs
- [ ] Path loss snapshot ngoài trời LOS ≈ 80–100 dB
- [ ] LOS flag: ngoài trời/cầu = 1, trong hầm sâu = 0
- [ ] Doppler max ≈ ±9720 Hz
- [ ] Vùng cửa hầm: SINR sụt > 10 dB so với ngoài trời

## 7. Luồng chạy hiện tại trong source

## 7.1. Pipeline chuẩn

Lệnh:

```bash
python -m phase1_pipeline.run_pipeline --config phase1_pipeline/config/config.yaml
```

Luồng xử lý:

1. Nhận diện `scenario.type = unified_3000m`
2. Bỏ qua nhánh Blender
3. Sinh scene procedural qua `export_mitsuba_fallback.py`
4. Gọi `run_sionna_rt.py`
5. Chạy riêng cho từng gNB
6. Ghi CSV và plot tương ứng

## 7.2. Vì sao không dùng `.blend` ở kịch bản này

Kịch bản tích hợp hiện đang được chuẩn hóa theo procedural exporter vì:

- hình học A-F đã được mô tả trực tiếp ở code exporter
- `run_pipeline.py` đang chọn nhánh này để đảm bảo output thống nhất
- `blender/generate_scene.py` chưa được nâng cấp tương ứng cho full tuyến 3000 m

Do đó:

- artifact chuẩn phục vụ ray tracing là `scene.xml` + `meshes/*.obj`
- `.blend` chưa phải artifact được generate tự động cho kịch bản tích hợp

## 8. Output kỳ vọng

Khi chạy xong, thư mục `phase1_pipeline/output_unified/` sẽ có:

- `scene.xml`
- `scene_metadata.json`
- `meshes/*.obj`
- 5 file CSV MPC
- `trace_manifest.json`
- plot tổng hợp `doppler_vs_time.png`
- plot tổng hợp `path_count_vs_time.png`
- plot và ảnh per-TX

Các CSV per-TX dùng chung trục thời gian, phục vụ đúng ý tưởng:

- 1 scene
- N lần chạy TX
- cùng trajectory RX

## 9. Giới hạn hiện tại của mô hình

Kịch bản hiện tại đã đúng về mặt kiến trúc pipeline, nhưng vẫn còn các giới hạn kỹ thuật:

1. Hình học Blender chưa được đồng bộ với kịch bản tích hợp.
2. Scene tích hợp hiện được mô hình hóa bằng các khối hình học đơn giản hóa.
3. Nếu chạy bằng `--force-fallback` hoặc không có Sionna RT, path được sinh theo mô hình fallback heuristic, không phải full physics ray tracing.
4. Tỷ lệ LOS/NLOS hiện phụ thuộc mạnh vào logic fallback hiện thực trong `run_sionna_rt.py`.

## 10. Ý nghĩa thực nghiệm

Dù còn đơn giản hóa, setup hiện tại đã đạt được mục tiêu quan trọng nhất của đề bài:

- thay thế 2 scene độc lập bằng 1 scene tích hợp duy nhất
- cho phép thu 5 trace song song logic cho 5 gNB
- đồng bộ timestamp giữa các trace
- tạo nền tảng đúng để sau này ghép với handover, SINR và ns-3

Tài liệu đánh giá chi tiết các output thực tế được ghi ở:

- `SioNetRail_Unified_Output_Assessment.md`
