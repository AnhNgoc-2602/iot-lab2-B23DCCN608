"""
preprocess.py - Tiền xử lý dữ liệu IoT.
Đọc iot_raw -> outlier (IQR) -> resample 10s -> nội suy -> rolling mean, delta
-> chuẩn hóa -> ghi vào iot_processed (measurement sensor_clean).
"""
import os
import warnings
import numpy as np
import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.warnings import MissingPivotFunction
from sklearn.preprocessing import MinMaxScaler, StandardScaler

warnings.simplefilter("ignore", MissingPivotFunction)


def get_token():
    try:
        from google.colab import userdata
        t = userdata.get("INFLUX_TOKEN")
    except Exception:
        t = os.environ.get("INFLUX_TOKEN", "")
    return t.strip().replace("\n", "").replace(" ", "")


INFLUX_URL = os.environ.get("INFLUX_URL", "https://us-east-1-1.aws.cloud2.influxdata.com")
ORG = os.environ.get("INFLUX_ORG", "3d6d0572b2dc7ed7")
BUCKET_RAW = os.environ.get("INFLUX_BUCKET_RAW", "iot_raw")
BUCKET_OUT = os.environ.get("INFLUX_BUCKET_PROCESSED", "iot_processed")
FIELDS = ["temperature", "humidity", "distance_cm"]

client = InfluxDBClient(url=INFLUX_URL, token=get_token(), org=ORG)

# 1. Đọc dữ liệu theo khoảng thời gian (pivot field thành cột)
flux = f'''
from(bucket: "{BUCKET_RAW}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "sensor_data")
  |> filter(fn: (r) => r._field == "temperature" or r._field == "humidity" or r._field == "distance_cm")
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
'''
df = client.query_api().query_data_frame(flux)
if isinstance(df, list):
    df = pd.concat(df)
dev = df["device_id"].iloc[0]
df = df.set_index("_time").sort_index()[FIELDS]

before = df.describe().T[["count", "min", "max", "mean"]]
print("Số bản ghi thô:", len(df))
print("Missing:\n", df.isna().sum())


# 2. Phát hiện outlier bằng IQR -> đánh dấu NaN
def iqr_mask(s, k=1.5):
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:                                   # dữ liệu phẳng: bỏ qua
        return pd.Series(False, index=s.index)
    return (s < q1 - k * iqr) | (s > q3 + k * iqr)


for col in FIELDS:
    m = iqr_mask(df[col])
    print(f"{col}: {m.sum()} outlier")
    df.loc[m, col] = np.nan

# 3. Resample 10 giây (lưới thời gian đều)
rs = df.resample("10s").mean()

# 4. Xử lý missing: nội suy theo thời gian, tối đa 6 điểm liên tiếp
rs = rs.interpolate(method="time", limit=6).dropna()

# 5. Tạo đặc trưng: rolling mean, delta
for col in FIELDS:
    rs[f"{col}_roll_mean"] = rs[col].rolling(window=6, min_periods=1).mean()
    rs[f"{col}_delta"] = rs[col].diff().fillna(0)

# 6. Chuẩn hóa Min-Max và Z-score
rs[[f"{c}_minmax" for c in FIELDS]] = MinMaxScaler().fit_transform(rs[FIELDS])
rs[[f"{c}_zscore" for c in FIELDS]] = StandardScaler().fit_transform(rs[FIELDS])

print("Số bản ghi sau xử lý:", len(rs))
print(before)
print(rs[FIELDS].describe().T[["count", "min", "max", "mean"]])   # bảng trước/sau

# 7. Ghi vào bucket mới (measurement mới)
rs["device_id"] = dev
client.write_api(write_options=SYNCHRONOUS).write(
    bucket=BUCKET_OUT, record=rs,
    data_frame_measurement_name="sensor_clean",
    data_frame_tag_columns=["device_id"])
print(f"Đã ghi vào {BUCKET_OUT}/sensor_clean")
