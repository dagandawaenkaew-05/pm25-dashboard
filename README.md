# 😷 PM2.5 Thailand Dashboard

แดชบอร์ดแสดงค่าฝุ่น PM2.5 รายสถานีทั่วประเทศไทย พร้อมวิเคราะห์แนวโน้มย้อนหลัง ใช้ข้อมูลจาก Air4Thai (กรมควบคุมมลพิษ)

<!-- ใส่ screenshot: ![screenshot](docs/screenshot.png) -->

## Features
- **ตอนนี้:** แผนที่ค่า PM2.5 แยกสีตามเกณฑ์ คพ., กรองตามพื้นที่, สรุปค่าเฉลี่ยพร้อมคำแนะนำสุขภาพ, อันดับ 10 สถานีที่ฝุ่นสูงสุด
- **แนวโน้มย้อนหลัง:** กราฟเปรียบเทียบสถานี เทียบกับค่าเฉลี่ยทั้งประเทศ, สรุปรายวัน, รูปแบบฝุ่นตามช่วงเวลาของวัน
- **Data pipeline:** `collect.py` เก็บข้อมูลรายชั่วโมงสะสมใน `data/history.csv` (ตัดซ้ำ, เก็บ 90 วัน) รันอัตโนมัติด้วย GitHub Actions

## Tech
Python, Streamlit, pandas, pydeck, GitHub Actions

## Run
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## เก็บข้อมูลย้อนหลัง
```bash
python collect.py      # รันซ้ำทุกชั่วโมงเพื่อสะสมข้อมูล
```
หรือเปิดใช้ workflow ใน `.github/workflows/collect.yml` (แท็บ Actions > collect-pm25 > Run workflow)
ให้เก็บข้อมูลอัตโนมัติทุกชั่วโมง

## หมายเหตุ
เซิร์ฟเวอร์ Air4Thai ตั้งค่าใบรับรอง SSL ไม่ครบ โค้ดจึงลองเชื่อมต่อแบบปลอดภัยก่อน
และข้ามการตรวจใบรับรองเฉพาะเมื่อเกิดข้อผิดพลาดนี้ (ข้อมูลเป็นสาธารณะแบบอ่านอย่างเดียว)

## Roadmap
- [ ] แจ้งเตือนผ่าน LINE
- [ ] พยากรณ์ 24 ชม. ด้วยข้อมูลจุดความร้อน
