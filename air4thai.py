"""ดึงข้อมูลสถานีตรวจวัดจาก Air4Thai (กรมควบคุมมลพิษ)"""
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"


def fetch_stations() -> pd.DataFrame:
    """คืน DataFrame: station_id, name, area, lat, lon, pm25, obs_time"""
    try:
        resp = requests.get(API_URL, timeout=20)
    except requests.exceptions.SSLError:
        # เซิร์ฟเวอร์ Air4Thai ตั้งค่าใบรับรอง SSL ไม่ครบ
        # ข้อมูลเป็นสาธารณะแบบอ่านอย่างเดียว จึงยอมข้ามการตรวจสอบได้
        resp = requests.get(API_URL, timeout=20, verify=False)
    try:
        stations = resp.json()["stations"]
    except ValueError:
        raise RuntimeError(
            f"API ไม่ได้ตอบเป็น JSON (HTTP {resp.status_code}): {resp.text[:150]!r}"
        )

    rows = []
    for s in stations:
        try:
            pm25 = float(s["AQILast"]["PM25"]["value"])
            if pm25 < 0:
                continue
            rows.append({
                "station_id": str(s.get("stationID", s["nameTH"])),
                "name": s["nameTH"],
                "area": s["areaTH"],
                "lat": float(s["lat"]),
                "lon": float(s["long"]),
                "pm25": pm25,
                "obs_time": f'{s["AQILast"]["date"]} {s["AQILast"]["time"]}',
            })
        except (KeyError, ValueError, TypeError):
            continue  # สถานีที่ไม่มีข้อมูล PM2.5
    return pd.DataFrame(rows)
