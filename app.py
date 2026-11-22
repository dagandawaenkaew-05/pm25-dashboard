"""PM2.5 Thailand Dashboard - ข้อมูลจาก Air4Thai (กรมควบคุมมลพิษ)"""
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"

# เกณฑ์ PM2.5 เฉลี่ย 24 ชม. (µg/m³) ตามประกาศ คพ. ปี 2566
LEVELS = [
    (15, "ดีมาก", [0, 160, 255], "ทำกิจกรรมกลางแจ้งได้ตามปกติ"),
    (25, "ดี", [0, 190, 90], "ทำกิจกรรมกลางแจ้งได้ตามปกติ"),
    (37.5, "ปานกลาง", [240, 200, 0], "กลุ่มเสี่ยงควรลดกิจกรรมกลางแจ้งที่หนัก"),
    (75, "เริ่มมีผลกระทบต่อสุขภาพ", [255, 140, 0], "ควรใส่หน้ากาก N95 และลดการออกกำลังกายนอกบ้าน"),
    (float("inf"), "มีผลกระทบต่อสุขภาพ", [230, 40, 40], "หลีกเลี่ยงกิจกรรมกลางแจ้ง ใส่หน้ากาก N95"),
]


def classify(v):
    for limit, label, color, advice in LEVELS:
        if v <= limit:
            return label, color, advice


@st.cache_data(ttl=3600)  # ข้อมูลอัปเดตทุกชั่วโมง
def load_data() -> pd.DataFrame:
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
                "สถานี": s["nameTH"],
                "พื้นที่": s["areaTH"],
                "lat": float(s["lat"]),
                "lon": float(s["long"]),
                "PM2.5": pm25,
                "เวลา": f'{s["AQILast"]["date"]} {s["AQILast"]["time"]}',
            })
        except (KeyError, ValueError, TypeError):
            continue  # สถานีที่ไม่มีข้อมูล PM2.5
    df = pd.DataFrame(rows)
    df["ระดับ"], df["color"], df["คำแนะนำ"] = zip(*df["PM2.5"].map(classify))
    return df


st.set_page_config(page_title="PM2.5 Thailand", page_icon="😷", layout="wide")
st.title("😷 คุณภาพอากาศ PM2.5 ทั่วประเทศไทย")

try:
    df = load_data()
except Exception as e:
    st.error(f"ดึงข้อมูลไม่สำเร็จ: {e}")
    st.stop()

# ---- ตัวกรอง ----
areas = sorted(df["พื้นที่"].unique())
picked = st.sidebar.multiselect("เลือกพื้นที่", areas)
view = df[df["พื้นที่"].isin(picked)] if picked else df

# ---- ตัวเลขสรุป ----
c1, c2, c3 = st.columns(3)
c1.metric("ค่าเฉลี่ย PM2.5", f'{view["PM2.5"].mean():.1f} µg/m³')
c2.metric("สถานีที่ตรวจวัด", len(view))
c3.metric("สถานีเกินเกณฑ์ (>37.5)", int((view["PM2.5"] > 37.5).sum()))

avg_label, _, avg_advice = classify(view["PM2.5"].mean())
st.info(f"**ภาพรวม: {avg_label}** — {avg_advice}")

# ---- แผนที่ ----
layer = pdk.Layer(
    "ScatterplotLayer", view, get_position=["lon", "lat"],
    get_fill_color="color", get_radius=8000, pickable=True, opacity=0.8,
)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(latitude=13.5, longitude=100.9, zoom=5),
    tooltip={"text": "{สถานี}\nPM2.5: {PM2.5} µg/m³\n{ระดับ}"},
))

# ---- ตารางอันดับ ----
st.subheader("10 สถานีที่ฝุ่นสูงสุด")
st.dataframe(
    view.nlargest(10, "PM2.5")[["สถานี", "พื้นที่", "PM2.5", "ระดับ", "เวลา"]],
    hide_index=True, use_container_width=True,
)
st.caption("แหล่งข้อมูล: Air4Thai กรมควบคุมมลพิษ")
