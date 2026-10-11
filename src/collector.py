"""
collector.py - Thu thập dữ liệu IoT: MQTT -> validate -> InfluxDB Cloud.
Chạy trên Google Colab hoặc máy cá nhân.
Token đọc từ Colab Secrets (INFLUX_TOKEN) hoặc biến môi trường INFLUX_TOKEN.
KHÔNG ghi token vào mã nguồn.
"""
import os
import json
import time
import logging
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


def get_token():
    try:
        from google.colab import userdata          # chạy trên Colab
        t = userdata.get("INFLUX_TOKEN")
    except Exception:
        t = os.environ.get("INFLUX_TOKEN", "")      # chạy máy cá nhân
    return t.strip().replace("\n", "").replace(" ", "")


# ---------------- Cấu hình ----------------
BROKER = os.environ.get("MQTT_BROKER", "broker.hivemq.com")
TOPIC = os.environ.get("MQTT_TOPIC", "iot/B23DCCN608/+/telemetry")
INFLUX_URL = os.environ.get("INFLUX_URL", "https://us-east-1-1.aws.cloud2.influxdata.com")
ORG = os.environ.get("INFLUX_ORG", "3d6d0572b2dc7ed7")
BUCKET = os.environ.get("INFLUX_BUCKET_RAW", "iot_raw")
RUN_SECONDS = int(os.environ.get("RUN_SECONDS", 5 * 60))   # thời gian thu thập

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Miền giá trị hợp lệ (dùng để validate)
LIMITS = {"temperature": (-40, 80), "humidity": (0, 100), "distance_cm": (2, 400)}
last_seq = {}   # device_id -> seq gần nhất (phát hiện mất gói)
stats = {"ok": 0, "invalid": 0, "lost": 0, "dup": 0, "restart": 0}

influx = InfluxDBClient(url=INFLUX_URL, token=get_token(), org=ORG)
write_api = influx.write_api(write_options=SYNCHRONOUS)


def validate(d):
    """Trả về None nếu hợp lệ, ngược lại trả về lý do."""
    for k in ("device_id", "ts", "seq"):
        if k not in d:
            return f"thiếu {k}"
    if abs(time.time() * 1000 - d["ts"]) > 24 * 3600 * 1000:
        return "timestamp bất thường"
    for k, (lo, hi) in LIMITS.items():
        if k in d and not (lo <= d[k] <= hi):
            return f"{k}={d[k]} ngoài miền [{lo},{hi}]"
    return None


def on_connect(client, userdata, flags, reason_code, properties):
    logging.info("Connected (%s), subscribe %s", reason_code, TOPIC)
    client.subscribe(TOPIC, qos=1)


def on_message(client, userdata, msg):
    recv_ms = time.time() * 1000
    try:
        d = json.loads(msg.payload)
    except json.JSONDecodeError:
        stats["invalid"] += 1
        return
    err = validate(d)
    if err:
        stats["invalid"] += 1
        logging.warning("Bỏ bản tin: %s", err)
        return

    dev, prev = d["device_id"], last_seq.get(d["device_id"])
    if prev is not None:
        if d["seq"] == prev:
            stats["dup"] += 1                      # trùng (InfluxDB sẽ ghi đè)
        elif d["seq"] < prev:
            stats["restart"] += 1                  # thiết bị khởi động lại
        elif d["seq"] > prev + 1:
            stats["lost"] += d["seq"] - prev - 1   # mất gói
    last_seq[dev] = d["seq"]

    point = (Point("sensor_data")
             .tag("device_id", dev)
             .tag("site", msg.topic.split("/")[1])
             .field("seq", int(d["seq"]))
             .field("latency_ms", float(recv_ms - d["ts"]))
             .time(int(d["ts"]), WritePrecision.MS))
    for k in ("temperature", "humidity", "distance_cm", "rssi", "uptime_s"):
        if k in d:
            point.field(k, float(d[k]))
    try:
        write_api.write(bucket=BUCKET, record=point)
        stats["ok"] += 1
    except Exception as e:
        logging.error("Ghi DB lỗi: %s", e)


if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect, client.on_message = on_connect, on_message
    client.reconnect_delay_set(1, 30)              # tự reconnect
    client.connect(BROKER, 1883)
    client.loop_start()
    time.sleep(RUN_SECONDS)                        # thu thập trong RUN_SECONDS giây
    client.loop_stop()
    print("KẾT QUẢ:", stats)
