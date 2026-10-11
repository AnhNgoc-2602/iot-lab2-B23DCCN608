"""latency_report.py - Thống kê độ trễ end-to-end từ trường latency_ms."""
import os
import warnings
import pandas as pd
import matplotlib.pyplot as plt
from influxdb_client import InfluxDBClient
from influxdb_client.client.warnings import MissingPivotFunction

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
client = InfluxDBClient(url=INFLUX_URL, token=get_token(), org=ORG)

flux = '''from(bucket:"iot_raw") |> range(start:-2h)
  |> filter(fn:(r)=> r._measurement=="sensor_data" and r._field=="latency_ms")'''
df = client.query_api().query_data_frame(flux)
if isinstance(df, list):
    df = pd.concat(df)
s = df.set_index("_time")["_value"].sort_index()


def report(x, title):
    print(f"{title}: n={len(x)} | Mean={x.mean():.0f} | Median={x.median():.0f} | "
          f"P95={x.quantile(.95):.0f} | P99={x.quantile(.99):.0f} | Max={x.max():.0f} (ms)")


report(s, "Độ trễ đo được")
adj = s - s.min()            # hiệu chỉnh lệch đồng hồ (trừ giá trị nhỏ nhất)
report(adj, "Sau hiệu chỉnh (jitter)")

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
s.plot(ax=ax[0], title="Độ trễ theo thời gian (ms)")
adj.plot.hist(ax=ax[1], bins=30, title="Phân bố độ trễ sau hiệu chỉnh (ms)")
plt.tight_layout()
plt.show()
