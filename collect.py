"""เก็บข้อมูล PM2.5 ทุกสถานีต่อท้าย data/history.csv (รันซ้ำได้ ไม่เก็บซ้ำ)

ใช้: python collect.py
"""
from pathlib import Path

import pandas as pd

from air4thai import fetch_stations

DATA = Path("data")
KEEP_DAYS = 90  # เก็บย้อนหลังไม่เกินกี่วัน ไม่ให้ไฟล์โตเกินไป


def main():
    DATA.mkdir(exist_ok=True)
    df = fetch_stations()
    df["obs_time"] = pd.to_datetime(df["obs_time"], errors="coerce")
    df = df.dropna(subset=["obs_time"])

    # รายชื่อสถานี (เขียนทับทุกครั้ง)
    df[["station_id", "name", "area", "lat", "lon"]].drop_duplicates("station_id") \
        .to_csv(DATA / "stations.csv", index=False)

    # ประวัติค่าฝุ่น (ต่อท้าย + ตัดซ้ำ + ตัดข้อมูลเก่า)
    new = df[["obs_time", "station_id", "pm25"]]
    path = DATA / "history.csv"
    if path.exists():
        old = pd.read_csv(path, dtype={"station_id": str}, parse_dates=["obs_time"])
        new = pd.concat([old, new])
    new = new.drop_duplicates(["obs_time", "station_id"])
    new = new[new["obs_time"] >= new["obs_time"].max() - pd.Timedelta(days=KEEP_DAYS)]
    new = new.sort_values(["obs_time", "station_id"])
    new.to_csv(path, index=False)
    print(f"บันทึกแล้ว: {len(df)} สถานี | ประวัติรวม {len(new)} แถว")


if __name__ == "__main__":
    main()
