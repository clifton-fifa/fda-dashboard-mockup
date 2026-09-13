# DASHBORD_NEW — แหล่งหลัก Mockup / KNIME หน้าจอ 1–10

โฟลเดอร์นี้เป็น **source of truth** สำหรับหน้าตาแดชบอร์ด (Web Mockup) และสคริปต์ KNIME ที่อ้างอิง mockup เดียวกัน

> **กติกาแก้ UI / layout / sidebar / แถบ filter**  
> แก้เฉพาะ `DASHBORD_NEW/Web Mockup/` (รวม `Web Mockup/shared/`)  
> **อย่า** แก้ไฟล์ใน `07_Output/CleansingConsole/` โดยตรง — โฟลเดอร์นั้นเป็น output/deploy เก่า  
> ถ้าต้องการให้ console ตาม mockup ให้ **คุณ** รัน `sync_dashbord_new_to_console.py` เองเมื่อพร้อม

## โครงสร้าง

| path | ความหมาย |
|------|-----------|
| `Web Mockup/d1_NEW.html` | หน้าจอที่ 1 — build จาก `04_Scripts/knime_dash1_view_real.py` + ข้อมูลจำลอง |
| `Web Mockup/shared/dash-sidebar.css` | **ฐานขนาดเมนูซ้าย** (280px / ฟอนต์ 20px) — ทุกแดชใช้ไฟล์นี้ |
| `Web Mockup/dashboard.html` | Shell: เมนูไฟล์เดียว + iframe สลับ d1–d10 |
| `Web Mockup/d2.html` … `d10.html` | Mockup หน้าจอ 2–10 |
| `Web Mockup/Backup/` | สำรองก่อนแก้ (d1, d3 ฯลฯ) |
| `Knime/knime_dash1_v4.py` | โหนด KNIME หน้าจอ 1 (สาย `view_real`) |
| `Knime/knime_dash3_v3.py` | โหนด KNIME หน้าจอ 3 (ตรง `Web Mockup/d3.html`) |

## โลโก้ อย.

- ไฟล์ต้นฉบับ: `../Logo_of_the_Food_and_Drug_Administration.svg` (รากโปรเจกต FDA)
- หน้าจอ 1 ที่ build แล้วฝังเป็น **base64 ใน HTML** (ไม่ต้องมี path แยกตอนเปิดไฟล์)

## Workflow หน้าจอที่ 1

```bash
# 1) แก้ logic / UI ที่ต้นฉบับ
#    04_Scripts/knime_dash1_view_real.py

# 2) สร้าง mockup ข้อมูลจำลอง
python3 04_Scripts/build_d1_new_mockup.py
# → Web Mockup/d1_NEW.html

# 3) (ถ้าต้องการ demo ใน CleansingConsole / Render)
python3 04_Scripts/sync_dashbord_new_to_console.py
# → 07_Output/CleansingConsole/dashboards/d1.html … d10.html
```

## เปิดดู mockup โดยตรง

```bash
cd "Web Mockup"
python3 -m http.server 8765
# แนะนำ — sidebar ไฟล์เดียว สลับเฉพาะเนื้อหาใน iframe:
# http://localhost:8765/dashboard.html
# http://localhost:8765/dashboard.html#dash3
#
# เปิดทีละหน้า (standalone) ยังใช้ได้:
# http://localhost:8765/d1_NEW.html
```

> เปิดด้วย `file://` ได้ แต่แนะนำ HTTP server เพื่อหลีกเลี่ยงข้อจำกัดเบราว์เซอร์

## Deploy web app (CleansingConsole)

หลัง sync แล้ว:

```bash
cd 07_Output/CleansingConsole
python3 app.py
```

iframe โหลด `dashboards/d1.html` ซึ่ง copy มาจาก `d1_NEW.html` ในโฟลเดอร์นี้

## Deploy ขึ้น GitHub (Pages)

โฟลเดอร์นี้เป็น repo แยกจากราก `FDA/` (ไม่ push เอกสาร/ข้อมูลภายในโปรเจกตใหญ่)

### ครั้งแรก — สร้าง repo และ push

```bash
cd "DASHBORD_NEW"

# ถ้ายังไม่ login GitHub CLI
gh auth login

# สร้าง repo สาธารณะ + push (เปลี่ยนชื่อ repo ได้)
gh repo create fda-dashboard-mockup --public --source=. --remote=origin --push
```

หรือสร้าง repo เองที่ github.com แล้ว:

```bash
git init
git add .
git commit -m "Initial commit: FDA dashboard mockup d1–d10"
git branch -M main
git remote add origin https://github.com/<USER>/<REPO>.git
git push -u origin main
```

### เปิด GitHub Pages

1. Repo → **Settings** → **Pages**
2. **Build and deployment** → Source: **GitHub Actions**
3. หลัง push ครั้งแรก workflow `Deploy dashboard to GitHub Pages` จะรันอัตโนมัติ
4. URL ประมาณ `https://<user>.github.io/<repo>/dashboard.html`

> ข้อมูลใน mockup เป็นข้อมูลจำลองสำหรับสาธิต UI เท่านั้น

## Cloudflare Pages (fda-dashboard-mockup.pages.dev)

ใน Cloudflare → โปรเจกต → **Settings** → **Build**:

| ช่อง | ค่า |
|------|-----|
| Build command | *(ว่าง)* |
| **Deploy command** | `npx wrangler pages deploy "Web Mockup" --project-name=fda-dashboard-mockup` |

**อย่าใช้** `npx wrangler deploy` (เป็น Worker จะ error Missing entry-point)

จากนั้น **Retry deployment** หรือ push commit ใหม่
