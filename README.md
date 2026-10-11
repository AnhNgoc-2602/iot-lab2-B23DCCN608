# Bài thực hành 2: Thu thập, lưu trữ và tiền xử lý dữ liệu IoT

Sinh viên: <Họ tên> | MSSV: B23DCCN608 | Học phần: IoT và Ứng dụng (INT14149)

## Mô tả
Pipeline IoT chạy hoàn toàn trên nền tảng web: ESP32 mô phỏng (Wokwi) đo nhiệt độ,
độ ẩm, khoảng cách và gửi JSON qua MQTT. Collector Python (Google Colab) nhận, kiểm tra
hợp lệ rồi ghi vào InfluxDB Cloud. Dữ liệu thô được tiền xử lý rồi hiển thị trên Grafana.

Luồng dữ liệu:
Wokwi (ESP32) -> broker.hivemq.com -> Colab collector -> InfluxDB (iot_raw)
-> Colab tiền xử lý -> InfluxDB (iot_processed) -> Grafana Cloud

## Cấu trúc thư mục
- `firmware/`: mã ESP32 (sketch.ino, diagram.json, libraries.txt)
- `src/collector.py`: subscribe MQTT, validate, ghi InfluxDB
- `src/preprocess.py`: làm sạch, phát hiện outlier, resample, chuẩn hóa
- `src/latency_report.py`: đo độ trễ end-to-end
- `config/config.example.env`: mẫu cấu hình (không chứa token)

## Tài khoản cần có
Wokwi, Google (Colab), InfluxDB Cloud (gói Free), Grafana Cloud (gói Free).
Broker công cộng HiveMQ không cần tài khoản.

## Cách chạy
1. InfluxDB Cloud: tạo bucket `iot_raw` (retention 7 ngày) và `iot_processed`
   (retention 30 ngày), tạo API token.
2. Colab: mở khóa Secrets, thêm secret `INFLUX_TOKEN` và bật Notebook access.
3. Wokwi: mở dự án (link bên dưới), kiểm tra `SITE = "B23DCCN608"`, bấm Run.
4. Colab: cài thư viện `pip install paho-mqtt influxdb-client`, sửa `INFLUX_URL`,
   `ORG` trong `src/collector.py`, chạy file này (thu thập 15 phút).
5. Trong lúc đó đổi giá trị cảm biến trên Wokwi để có dữ liệu thay đổi và vài giá trị bất thường.
6. Chạy `src/preprocess.py` rồi `src/latency_report.py`.
7. Grafana: thêm data source InfluxDB (Flux) và dựng dashboard.

## Bảo mật
Token chỉ lưu trong Colab Secrets, không có trong mã nguồn.

## Liên kết
- Dự án Wokwi: https://wokwi.com/projects/477547492335922177
- Dashboard Grafana: [<dán link>](https://blueoak2346.grafana.net/d/antzgg7/bai2-iot-monitoring-b23dccn608?from=2026-10-11T01:30:00.000Z&to=2026-10-11T02:30:59.000Z&timezone=browser&var-filter0=&refresh=5s)
- Báo cáo:  https://docs.google.com/document/d/1dbgEJqVQAJxA2S2J3FrV7PXS0qo7ccIakitiMm9AGvM/edit?tab=t.0
