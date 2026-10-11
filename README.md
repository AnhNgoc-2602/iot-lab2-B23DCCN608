# Bài thực hành 2: Thu thập, lưu trữ và tiền xử lý dữ liệu IoT

- Sinh viên: Nguyễn Thị Anh Ngọc | Mã SV: B23DCCN608 
- Học phần: IoT và Ứng dụng (INT14149)

## 1. Tổng quan
Pipeline: ESP32 (Wokwi: DHT22 + HC-SR04) → MQTT (broker.hivemq.com) → Collector Python → InfluxDB Cloud (`iot_raw`) → Tiền xử lý (pandas) → InfluxDB Cloud (`iot_processed`) → Grafana Cloud.

## 2. Cấu trúc thư mục
| Thư mục / file | Nội dung |
|---|---|
| `firmware/` | Mã ESP32 chạy trên Wokwi: `sketch.ino`, `diagram.json`, `libraries.txt` |
| `src/collector.py` | Subscribe MQTT, validate, ghi InfluxDB, đo độ trễ |
| `src/preprocess.py` | Làm sạch (IQR), resample, nội suy, rolling mean, delta, chuẩn hóa |
| `src/latency_report.py` | Thống kê độ trễ (mean, median, P95, P99) và vẽ biểu đồ |
| `config/config.example.env` | Mẫu cấu hình (không chứa token) |
| `requirements.txt` | Thư viện Python |

## 3. Yêu cầu
Tài khoản miễn phí: Wokwi, Google Colab, InfluxDB Cloud (gói Free), Grafana Cloud. Không cần cài phần mềm nào. Thư viện Python: xem `requirements.txt`.

## 4. Cấu hình InfluxDB Cloud
1. Tạo bucket `iot_raw` (retention 7 ngày) và `iot_processed` (retention 30 ngày).
2. Tạo API token (All Access). Lưu vào Colab Secrets tên `INFLUX_TOKEN` (hoặc biến môi trường `INFLUX_TOKEN`). **Không ghi token vào mã nguồn.**
3. Sửa `INFLUX_URL`, `INFLUX_ORG` nếu dùng tài khoản khác (xem `config/config.example.env`).

## 5. Cách chạy
1. Mở dự án Wokwi:(https://wokwi.com/projects/477547492335922177). Kiểm tra `SITE = "B23DCCN608"` trong sketch, bấm ▶.
2. Mở Google Colab, tạo notebook mới, thêm secret `INFLUX_TOKEN`.
3. Ô 1: `!pip -q install paho-mqtt influxdb-client`
4. Ô 2: dán nội dung `src/collector.py` và chạy (mặc định thu thập 5 phút). Trong lúc chạy, đổi giá trị cảm biến trên Wokwi, thỉnh thoảng cho một giá trị bất thường.
5. Ô 3: dán `src/preprocess.py` và chạy để tạo dữ liệu sạch trong `iot_processed`.
6. Ô 4: dán `src/latency_report.py` và chạy để xem thống kê độ trễ.
7. Dashboard Grafana: kết nối data source InfluxDB (Flux), tạo panel từ bucket `iot_raw` và `iot_processed`.

## 6. Quy ước dữ liệu
- Topic: `iot/B23DCCN608/esp32-01/telemetry`
- JSON: `{"device_id","seq","ts","temperature","humidity","distance_cm","rssi","uptime_s"}`
- InfluxDB: measurement `sensor_data` (thô) và `sensor_clean` (đã xử lý); tags `device_id`, `site`.

## 7. Lưu ý
- Không đẩy token hoặc mật khẩu lên GitHub.
- Broker HiveMQ công cộng không mã hóa, chỉ dùng cho thực hành.
- Độ trễ đo từ Wokwi bị ảnh hưởng bởi lệch đồng hồ mô phỏng (xem báo cáo).

## Liên kết
- Dự án Wokwi: https://wokwi.com/projects/477547492335922177
- Dashboard Grafana: [<dán link>](https://blueoak2346.grafana.net/d/antzgg7/bai2-iot-monitoring-b23dccn608?from=2026-10-11T01:30:00.000Z&to=2026-10-11T02:30:59.000Z&timezone=browser&var-filter0=&refresh=5s)

