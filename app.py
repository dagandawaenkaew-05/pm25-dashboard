"""PM2.5 Thailand Dashboard - ข้อมูลจาก Air4Thai (กรมควบคุมมลพิษ)"""
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

from air4thai import fetch_stations

HISTORY = Path("data/history.csv")
STATIONS = Path("data/stations.csv")

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
def load_now() -> pd.DataFrame:
    df = fetch_stations()
    df["level"], df["color"], df["advice"] = zip(*df["pm25"].map(classify))
    return df


@st.cache_data(ttl=600)
def load_history():
    if not (HISTORY.exists() and STATIONS.exists()):
        return None
    h = pd.read_csv(HISTORY, dtype={"station_id": str}, parse_dates=["obs_time"])
    s = pd.read_csv(STATIONS, dtype={"station_id": str})
    return h.merge(s[["station_id", "name", "area"]], on="station_id", how="left")


st.set_page_config(page_title="PM2.5 Thailand", page_icon="😷", layout="wide")
st.title("😷 คุณภาพอากาศ PM2.5 ทั่วประเทศไทย")

tab_now, tab_trend = st.tabs(["ตอนนี้", "แนวโน้มย้อนหลัง"])

# ======================= แท็บ: ตอนนี้ =======================
with tab_now:
    try:
        df = load_now()
    except Exception as e:
        st.error(f"ดึงข้อมูลไม่สำเร็จ: {e}")
        st.stop()

    areas = sorted(df["area"].unique())
    picked = st.sidebar.multiselect("เลือกพื้นที่", areas)
    view = df[df["area"].isin(picked)] if picked else df

    c1, c2, c3 = st.columns(3)
    c1.metric("ค่าเฉลี่ย PM2.5", f'{view["pm25"].mean():.1f} µg/m³')
    c2.metric("สถานีที่ตรวจวัด", len(view))
    c3.metric("สถานีเกินเกณฑ์ (>37.5)", int((view["pm25"] > 37.5).sum()))

    avg_label, _, avg_advice = classify(view["pm25"].mean())
    st.info(f"**ภาพรวม: {avg_label}** — {avg_advice}")

    layer = pdk.Layer(
        "ScatterplotLayer", view, get_position=["lon", "lat"],
        get_fill_color="color", get_radius=8000, pickable=True, opacity=0.8,
    )
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=13.5, longitude=100.9, zoom=5),
        tooltip={"text": "{name}\nPM2.5: {pm25} µg/m³\n{level}"},
    ))

    st.subheader("10 สถานีที่ฝุ่นสูงสุด")
    top = view.nlargest(10, "pm25")[["name", "area", "pm25", "level", "obs_time"]]
    top.columns = ["สถานี", "พื้นที่", "PM2.5", "ระดับ", "เวลา"]
    st.dataframe(top, hide_index=True, use_container_width=True)

# ======================= แท็บ: แนวโน้มย้อนหลัง =======================
with tab_trend:
    hist = load_history()
    if hist is None or hist["obs_time"].nunique() < 2:
        st.info(
            "ยังมีข้อมูลย้อนหลังไม่พอ — รัน `python collect.py` ทิ้งไว้เป็นรายชั่วโมง "
            "(หรือเปิด GitHub Actions ตาม README) แล้วกลับมาดูใหม่"
        )
    else:
        days = st.slider("ย้อนหลัง (วัน)", 1, 90, 7)
        h = hist[hist["obs_time"] >= hist["obs_time"].max() - pd.Timedelta(days=days)]
        st.caption(
            f'ข้อมูล {h["obs_time"].min():%d/%m/%Y %H:%M} – {h["obs_time"].max():%d/%m/%Y %H:%M} '
            f'| {h["station_id"].nunique()} สถานี'
        )

        names = sorted(h["name"].dropna().unique())
        default = h.groupby("name")["pm25"].mean().nlargest(3).index.tolist()
        chosen = st.multiselect("เลือกสถานีเปรียบเทียบ", names, default=default)

        national = h.groupby("obs_time")["pm25"].mean().rename("ค่าเฉลี่ยทั้งประเทศ")
        chart = h[h["name"].isin(chosen)].pivot_table(
            index="obs_time", columns="name", values="pm25")
        st.line_chart(chart.join(national, how="outer"))

        st.subheader("สรุปรายวัน (ทั้งประเทศ)")
        daily = h.assign(วัน=h["obs_time"].dt.date).groupby("วัน")["pm25"].agg(["mean", "max"]).round(1)
        daily.columns = ["เฉลี่ย", "สูงสุด (รายสถานี)"]
        st.dataframe(daily.sort_index(ascending=False), use_container_width=True)

        st.subheader("ฝุ่นสูงช่วงเวลาไหนของวัน (เฉลี่ยทั้งประเทศ)")
        st.bar_chart(h.groupby(h["obs_time"].dt.hour)["pm25"].mean().rename("PM2.5 เฉลี่ย"))

st.caption("แหล่งข้อมูล: Air4Thai กรมควบคุมมลพิษ")
