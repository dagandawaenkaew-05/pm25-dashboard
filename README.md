# 😷 PM2.5 Thailand Dashboard

แดชบอร์ดแสดงค่าฝุ่น PM2.5 รายสถานีทั่วประเทศไทยแบบเกือบเรียลไทม์ ใช้ข้อมูลจาก Air4Thai (กรมควบคุมมลพิษ)

## Features
- แผนที่แสดงค่า PM2.5 แยกสีตามเกณฑ์ คพ.
- กรองตามพื้นที่ / จังหวัด
- สรุปค่าเฉลี่ยพร้อมคำแนะนำสุขภาพ
- อันดับ 10 สถานีที่ฝุ่นสูงสุด
- แคชข้อมูล 1 ชั่วโมง (ตามรอบอัปเดตของ API)

## Tech
Python, Streamlit, pandas, pydeck

## Run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Roadmap
- [ ] เก็บข้อมูลย้อนหลังและวิเคราะห์แนวโน้มรายฤดู
- [ ] แจ้งเตือนผ่าน LINE
- [ ] พยากรณ์ 24 ชม. ด้วยข้อมูลจุดความร้อน
