"""หน้าจอที่ 1 — สคริปต์โหนด Python View ของ KNIME (ไฟล์เดียวจบ วางในโหนดได้ตรง ๆ)

knime_dash1_v7.py = knime_dash1_v6.py + ฝังฟอนต์ TH Sarabun New ในหน้าจอ (เปิดเครื่องที่ไม่มีฟอนต์ก็ไม่เพี้ยน)
TEMPLATE มาจาก DASHBORD_NEW/Web Mockup/d1_NEW.html — ฝัง CSS จาก shared/ ไว้ในไฟล์, ไม่มีเมนู sidebar

ถ้ามอคเปลี่ยน ให้รัน 04_Scripts/build_knime_views_from_mockup.py 1 แทนการแก้ TEMPLATE ตรง ๆ
(สคริปต์นั้นเปลี่ยนเฉพาะ TEMPLATE และคงส่วน Python ของไฟล์นี้ไว้)

วิธีใช้ใน KNIME: เปิดโหนด Python View ของหน้าจอที่ 1 → Configure → เลือกทั้งหมด (Cmd+A)
→ วางเนื้อหาไฟล์นี้ทับ → Execute (สายขาเข้าต่อเหมือนเดิม ไม่ต้องรื้อ)
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

import knime.scripting.io as knio

# ── พอร์ตขาเข้า ────────────────────────────────────────────────────────────
#  0 มูลค่านำเข้า-ส่งออก      GROUP_CD, Period_month (YYYY-MM), export_value_thb,
#                            import_value_thb (ผ่านระบบ อย.), "import_value_thb (Right)" (ศุลกากร)
#  1 ผลิตภัณฑ์ที่ได้รับอนุญาต  ┐
#  2 ผู้ประกอบการ             ├ PERIOD_FINAL (YYYY-MM), GROUP_CD_FINAL, backlog
#  3 คำขอคงค้าง               ┘ (คอลัมน์ backlog = ยอดสะสมของสายนั้น ๆ ทั้ง 3 สาย)
#  4 ประเทศต้นทาง            GROUP_CD, CountryCode, CountryName, import_value_thb

MB = 1e6
GROUPS = ["DRUG", "MDC", "FOOD", "CMT", "HERB", "TXC", "NCT"]
GROUP_COLOR = {"DRUG": "#1F6FB2", "MDC": "#12A594", "FOOD": "#3E9F55",
               "CMT": "#E8A317", "HERB": "#7E57C2", "TXC": "#C0392B",
               "NCT": "#7F8C8D"}
GROUP_NAME_TH = {"DRUG": "ยา", "FOOD": "อาหาร", "MDC": "เครื่องมือแพทย์",
                 "CMT": "เครื่องสำอาง", "HERB": "สมุนไพร", "TXC": "วัตถุอันตราย",
                 "NCT": "วัตถุเสพติด"}
TH_MONTH_ABBR = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                 "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

TREND_DISPLAY_YEARS = 5   # จำนวนปีงบประมาณบนกราฟแนวโน้ม (รวมปีที่มีส่วนพยากรณ์)
# ย้อนหลังพอให้ครบ 5 ปีงบประมาณ (ต.ค.–ก.ย.) + เดือนล่าสุด
DASHBOARD_LOOKBACK_MONTHS = (TREND_DISPLAY_YEARS + 1) * 12 - 1

# ตาราง Country ของ อย. มีแค่รหัส + ชื่ออังกฤษ — แปลเฉพาะคู่ค้าที่เจอบ่อย ที่เหลือใช้ชื่ออังกฤษ
COUNTRY_NAME_TH = {
    "CN": "จีน", "US": "สหรัฐอเมริกา", "JP": "ญี่ปุ่น", "DE": "เยอรมนี",
    "KR": "เกาหลีใต้", "IN": "อินเดีย", "FR": "ฝรั่งเศส", "GB": "สหราชอาณาจักร",
    "IT": "อิตาลี", "CH": "สวิตเซอร์แลนด์", "NL": "เนเธอร์แลนด์", "BE": "เบลเยียม",
    "MY": "มาเลเซีย", "SG": "สิงคโปร์", "TW": "ไต้หวัน", "ID": "อินโดนีเซีย",
    "VN": "เวียดนาม", "PH": "ฟิลิปปินส์", "MM": "เมียนมา", "KH": "กัมพูชา",
    "LA": "ลาว", "AU": "ออสเตรเลีย", "NZ": "นิวซีแลนด์", "CA": "แคนาดา",
    "ES": "สเปน", "SE": "สวีเดน", "IE": "ไอร์แลนด์", "IL": "อิสราเอล",
    "BR": "บราซิล", "HK": "ฮ่องกง", "DK": "เดนมาร์ก", "NO": "นอร์เวย์",
    "AT": "ออสเตรีย", "FI": "ฟินแลนด์", "PL": "โปแลนด์", "TH": "ไทย",
    "AE": "สหรัฐอาหรับเอมิเรตส์", "ZA": "แอฟริกาใต้", "RU": "รัสเซีย",
    "PK": "ปากีสถาน", "BD": "บังกลาเทศ", "TR": "ตุรกี", "MX": "เม็กซิโก",
    "AR": "อาร์เจนตินา", "EG": "อียิปต์", "SA": "ซาอุดีอาระเบีย",
}
UNKNOWN_COUNTRY_TH = "ไม่ระบุประเทศ"

# โลโก้ อย. ฝังเป็น base64 — สคริปต์ถูกวางในโหนด KNIME ตรง ๆ จึงอ่านไฟล์ข้างเคียงไม่ได้
# (ต้นฉบับ: Logo_of_the_Food_and_Drug_Administration.svg — เปลี่ยนโลโก้ให้เข้ารหัสไฟล์ใหม่มาแทน)
_FDA_LOGO_B64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIGlkPSJiIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNDAiIGhlaWdodD0iMjQwIiB2aWV3Qm94"
    "PSIwIDAgMjQwIDI0MCI+PGRlZnM+PHN0eWxlPi5ke2ZpbGw6IzAwNGNhZjt9PC9zdHlsZT48L2RlZnM+PGcgaWQ9ImMiPjxwYXRoIGNsYXNzPSJkIiBkPSJtMTE5LjE1LDBjLTIzLjcuMTctNDYuODEsNy4zNS02Ni40MywyMC42NC0xOS42MiwxMy4yOS0zNC44NywzMi4wOS00My44Miw1NC4wM0MtLjA2LDk2LjYxLTIuMzIsMTIwLjcxLDIuNDEsMTQzLjkzYzQuNzMsMjMuMjIsMTYuMjIsNDQuNTIsMzMuMDQsNjEuMjIsMTYuODIsMTYuNywzOC4yLDI4LjA0LDYxLjQ1LDMyLjYsMjMuMjUsNC41Niw0Ny4zNCwyLjEzLDY5LjIyLTYuOTcsMjEuODgtOS4xMSw0MC41Ny0yNC40OSw1My43Mi00NC4yLDEzLjE1LTE5LjcyLDIwLjE2LTQyLjg4LDIwLjE2LTY2LjU4LS4xMS0zMS45NC0xMi45MS02Mi41Mi0zNS41OC04NS4wM0MxODEuNzYsMTIuNDcsMTUxLjA5LS4xMSwxMTkuMTUsMFptMCwyMjQuN2MtMTQuOS4xLTI5LjY0LTIuOTctNDMuMjYtOS4wMi0xMy42MS02LjA1LTI1Ljc4LTE0LjkzLTM1LjY5LTI2LjA2LTkuOTEtMTEuMTItMTcuMzMtMjQuMjMtMjEuNzYtMzguNDUtNC40NC0xNC4yMi01Ljc5LTI5LjIyLTMuOTctNDQuMDFoNzAuNTljMS44LDAsMi4zNS41OCwyLjM1LDIuNDUtLjA1LDIxLjMxLS4wNiw0Mi42MS0uMDQsNjMuOTIsMCwuNTUuMjEsMS4xNi0uMzgsMS43OGwtMjYuNTItMjkuNTNoOC44OHEzLjEsMCwzLjExLTMuMTljMC0zLjEyLS4wNS02LjI0LDAtOS4zNS4wMy0xLjU1LS40OC0yLjI1LTIuMDQtMi4yNS0xMy4wOS4wMy0yNi4xOCwwLTM5LjI2LjAyLS41NCwwLTEuMjktLjE1LTEuNDcuNTEtLjE5LjY2LjQ4LDEuMTQuOSwxLjYsNi45Miw3LjY1LDEzLjg1LDE1LjMsMjAuNzgsMjIuOTUsMTMuNjcsMTUuMTIsMjcuMzQsMzAuMjUsNDEsNDUuMzcsMi43MSwyLjk5LDIuMDQsMi45NCw0LjY2LDAsMTMuNDItMTUuMTgsMjYuODItMzAuMzksNDAuMTktNDUuNjMsOS4xOS0xMC40MiwxOC4zOS0yMC44MywyNy42LTMxLjIzLDguOTUtMTAuMTMsMTcuODktMjAuMjYsMjYuODMtMzAuMzkuMTgtLjE5LjMzLS4zOS40Ny0uNi4yNS0uNDIuODgtLjcyLjY3LTEuMjlzLS44Ny0uMzgtMS4zMy0uMzhjLTQuNDksMC04Ljk3LDAtMTMuNDYtLjAyLS40Ny0uMDEtLjk0LjA4LTEuMzYuMjgtLjQzLjItLjguNDktMS4wOS44Ni04LjI4LDkuMzUtMTYuNTcsMTguNjktMjQuODcsMjguMDQtNS4wNyw1LjcyLTEwLjE0LDExLjQ1LTE1LjIsMTcuMTgtMTAuNTcsMTEuOTItMjEuMTUsMjMuODQtMzEuNzIsMzUuNzUtLjMuNDItLjU3Ljg2LS44LDEuMzMtLjI2LS4zMy0uNDUtLjcxLS41Ni0xLjEyLS4xMS0uNDEtLjEzLS44My0uMDYtMS4yNS0uMDItOC4xOC0uMDItMTYuMzcsMC0yNC41NSwwLTIuNTEuMDgtMi41OSwyLjU2LTIuNiw0LjExLDAsOC4yMy0uMDQsMTIuMzQsMCwxLjUyLjAyLDIuMTEtLjUzLDIuMDgtMi4xNi0uMDktMy41MS0uMDktNy4wMSwwLTEwLjUyLjA0LTEuNjQtLjU5LTIuMTYtMi4wOC0yLjE0LTQuMTcuMDYtOC4zNC0uMDUtMTIuNTMuMDUtMS43Ny4wNC0yLjQyLS41OS0yLjM5LTIuNDYuMDgtNi4zLjA4LTEyLjYsMC0xOC45LS4wMi0xLjgzLjUyLTIuNTQsMi4zNC0yLjUsNC4yNC4xMSw4LjQ4LDAsMTIuNzEuMDYsMS42My4wMywyLjIyLS42NCwyLjE5LTIuMy0uMDYtMy40NCwwLTYuODksMC0xMC4zMywwLTIuNjgtLjAzLTIuNy0yLjYzLTIuN0gxNy41M2M1LjEyLTE4Ljk4LDE1LjQ1LTM2LjE0LDI5LjgyLTQ5LjU2LDE0LjM3LTEzLjQxLDMyLjIxLTIyLjU0LDUxLjQ5LTI2LjM0LDE5LjI4LTMuOCwzOS4yNS0yLjE0LDU3LjY0LDQuODEsMTguMzksNi45NSwzNC40NiwxOC45MSw0Ni40MSwzNC41MiwxMS45NSwxNS42MSwxOS4yOSwzNC4yNSwyMS4xOSw1My44MiwxLjksMTkuNTYtMS43MSwzOS4yNy0xMC40Miw1Ni44OS04LjcxLDE3LjYyLTIyLjE4LDMyLjQ1LTM4Ljg4LDQyLjgyLTE2LjcsMTAuMzYtMzUuOTcsMTUuODUtNTUuNjMsMTUuODNaIi8+PC9nPjwvc3ZnPg=="
)
FDA_LOGO_SRC = "data:image/svg+xml;base64," + _FDA_LOGO_B64

TEMPLATE = r"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>หน้าจอที่ 1 — ภาพรวมเศรษฐกิจผลิตภัณฑ์สุขภาพ | อย.</title>
<style>
  :root{
    --navy:#0E2A4F; --navy2:#1B4A82; --gold:#B7922E; --ink:#1A2430; --muted:#5B6B7E;
    --line:#D8E0EA; --line2:#EAEFF4; --canvas:#F2F4F7; --card:#FFFFFF;
    --good:#1F7A45; --warn:#A66A00; --bad:#B4382A;
    --sh-1:0 1px 3px rgba(18,48,91,.08);
    --r:8px;
    /* สเกล KPI (คงที่) vs UI รอง (ปรับได้) — โหมดอ่านง่าย */
    --fs-kpi:54px; --fs-kpi-name:25px; --fs-kpi-unit:22px;
    --fs-base:28px; --fs-h2:33px;
    /* แถบบน + ตัวกรอง — เล็กกว่าเนื้อหา เพื่อโฟกัส KPI/กราฟ */
    --fs-chrome-h1:30px; --fs-chrome-sub:20px; --fs-chrome-meta:19px; --fs-chrome-org:17px;
    --fs-filter:19px; --fs-filter-chip:18px;
    --fs-ui:24px; --fs-ui-md:22px; --fs-ui-sm:20px;
    --fs-axis:22px; --fs-chart-lbl:23px; --fs-tip:26px; --fs-period:20px;
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--canvas);
    color:var(--ink);
    font-family:"TH Sarabun New","TH SarabunPSK","Sarabun","Noto Sans Thai",
                "Leelawadee UI",system-ui,-apple-system,sans-serif;
    font-size:var(--fs-base); line-height:1.5; font-weight:600;
    -webkit-font-smoothing:antialiased;
    text-rendering:optimizeLegibility;
  }
  /* ── แถบหัวเรื่อง ─────────────────────────────────────────── */
  header{background:var(--navy);
         color:#fff; padding:11px 22px 10px;
         display:flex; justify-content:space-between; align-items:center; gap:12px;
         flex-wrap:wrap; position:relative; border-bottom:3px solid var(--gold)}
  header .brand{display:flex; align-items:center; gap:11px}
  header .brandLogo{width:46px; height:46px; object-fit:contain; background:#fff;
                    border-radius:6px; padding:4px; box-shadow:0 0 0 1px rgba(255,255,255,.25)}
  header h1{margin:0; font-size:var(--fs-chrome-h1); font-weight:700; letter-spacing:.15px;
            line-height:1.22}
  header .sub{color:#B7C7DC; font-size:var(--fs-chrome-sub); letter-spacing:.15px;
             margin-top:2px; line-height:1.3}
  header .right{text-align:right; font-size:var(--fs-chrome-meta); line-height:1.35}
  header .right .asof{font-weight:600}
  header .right .org{color:#B7C7DC; font-size:var(--fs-chrome-org); margin-top:2px;
                     line-height:1.3}

  /* ── แถบตัวกรอง ───────────────────────────────────────────── */
  .filters{background:#fff; border-bottom:1px solid var(--line); padding:6px 16px 6px 22px;
           display:grid; grid-template-columns:1fr auto; gap:8px 10px; align-items:center;
           position:sticky; top:0; z-index:20}
  .static-filters{grid-column:1; justify-self:start; min-width:0}
  /* คอลัมน์ auto ชิดขวา — ใช้พื้นที่กลางให้ชิปครบโดยไม่โดนตัด */
  .filterGroups{grid-column:2; justify-self:end; display:flex; align-items:center;
                gap:6px; flex-wrap:nowrap; width:max-content; max-width:100%}
  .filters .lbl{color:var(--muted); font-size:var(--fs-filter); font-weight:600;
                 white-space:nowrap; flex:none}
  #chips{display:flex; flex:0 0 auto; gap:5px; flex-wrap:nowrap; justify-content:flex-end;
         min-width:0; padding:2px 0}
  .chip{border:1px solid var(--line); background:#fff; color:var(--ink);
        border-radius:6px; padding:5px 15px; font:inherit; font-size:24px;
        cursor:pointer; display:inline-flex; align-items:center; gap:8px; flex:none;
        transition:background .13s, color .13s, border-color .13s}
  .filters .chip{padding:3px 8px; font-size:var(--fs-filter-chip); gap:4px;
                 border-radius:5px; font-weight:600}
  .filters .chip .dot{width:8px; height:8px}
  .chip:hover{border-color:#9FB6D0}
  .chip[aria-pressed="true"]{background:var(--navy); color:#fff; border-color:var(--navy)}
  .chip .dot{width:9px; height:9px; border-radius:50%; flex:none}
  .static-filters{display:flex; gap:12px; color:var(--muted); font-size:var(--fs-filter);
                  flex-wrap:wrap; align-items:center; flex:0 1 auto}
  .static-filters span{white-space:nowrap; padding-left:12px; border-left:1px solid var(--line)}
  .static-filters span:first-child{padding-left:0; border-left:none}
  .static-filters select{font:inherit; font-size:var(--fs-filter-chip); color:var(--ink);
                         background:#fff; border:1px solid var(--line); border-radius:5px;
                         padding:2px 7px; margin:0 2px}
  .reset-btn{font:inherit; font-size:var(--fs-filter-chip); font-weight:600; color:var(--navy);
             background:#fff; border:1px solid var(--line); border-radius:5px;
             padding:2px 10px; margin-left:4px; cursor:pointer}
  .reset-btn:hover{background:var(--line2)}

  /* ── ตาราง 12 คอลัมน์ ตามมาตรฐานในตารางที่ 13 ─────────────── */
  main{padding:16px 20px 10px; display:grid; grid-template-columns:repeat(12,1fr);
       gap:14px; max-width:2000px; margin:0 auto}
  .card{background:var(--card); border:1px solid var(--line); border-radius:var(--r);
        padding:15px 17px 13px; min-width:0; box-shadow:var(--sh-1)}
  /* ขีดสีสั้น ๆ หน้าหัวข้อ — แยกลำดับชั้นหัวข้อกับคำอธิบายให้ชัดโดยไม่เพิ่มเส้นกรอบ */
  .card > h2{margin:0; font-size:var(--fs-h2); font-weight:700; letter-spacing:.1px;
             display:flex; align-items:center; gap:10px}
  .card > h2::before{content:""; width:4px; height:20px; border-radius:2px;
                     background:var(--navy); flex:none}
  .card > .cap{margin:5px 0 12px 13px; color:var(--muted); font-size:var(--fs-ui);
               line-height:1.5}

  /* ── ตัวเลือกช่วงเวลารายการ์ด ─────────────────────────────── */
  /* ปุ่มไอคอน + เมนู dropdown เลือกช่วงเวลาต่อการ์ด อิสระจากตัวกรอง Year/Month
     ด้านบนของหน้าจอ (คนละกลไกกัน) — เผื่อ user อยากดูกราฟนึงช่วงสั้น อีกกราฟช่วงยาว
     พร้อมกันได้ ซ่อนอัตโนมัติในโหมดข้อมูลมอค (ดูฟังก์ชัน period* ใน script) เพราะ
     กราฟมอคยังไม่รองรับตัวกรองนี้ */
  .periodPick{position:relative; margin-left:auto; flex:none}
  .periodBtn{width:34px; height:34px; border-radius:7px; border:1px solid var(--line);
             background:#fff; color:var(--muted); cursor:pointer; display:inline-flex;
             align-items:center; justify-content:center; line-height:1;
             transition:background .13s, color .13s, border-color .13s}
  .periodBtn:hover{background:var(--line2); color:var(--ink)}
  .periodMenu{display:none; position:absolute; right:0; top:36px; z-index:30;
              background:#fff; border:1px solid var(--line); border-radius:8px;
              box-shadow:0 10px 26px rgba(8,24,46,.16); padding:12px; min-width:210px}
  .periodMenu.open{display:block}
  .periodRow{display:flex; align-items:center; gap:8px; margin-bottom:8px}
  .periodRow label{width:44px; flex:none; color:var(--muted); font-size:var(--fs-period);
      font-weight:600}
  .periodRow input[type="month"]{flex:1; min-width:0; font:inherit; font-size:var(--fs-period);
      color:var(--ink); border:1px solid var(--line); border-radius:6px; padding:7px 9px}
  .periodActions{display:flex; justify-content:space-between; gap:8px; margin-top:10px}
  .periodActions button{flex:1; font:inherit; font-size:var(--fs-period); font-weight:600;
      border-radius:6px; padding:9px 6px; cursor:pointer}
  .periodClear{border:1px solid var(--line); background:#fff; color:var(--muted)}
  .periodClear:hover{background:var(--line2); color:var(--ink)}
  .periodApply{border:1px solid var(--navy); background:var(--navy); color:#fff}
  .periodApply:hover{background:var(--navy2)}

  /* ── การ์ดตัวชี้วัดหลัก ───────────────────────────────────── */
  /* auto-fit แทนการตรึง 6 คอลัมน์ — ปรับตามจำนวนการ์ดจริงเอง (มอค 6 ใบ / จริง 4 ใบ
     ตอนนี้) ไม่ต้องแก้ CSS ทุกครั้งที่จำนวนการ์ดเปลี่ยน */
  .kpis{grid-column:span 12; display:grid;
        grid-template-columns:repeat(auto-fit, minmax(228px, 1fr)); gap:16px}
  .kpi{background:var(--card); border:1px solid var(--line); border-radius:var(--r);
       overflow:hidden; position:relative; cursor:default; box-shadow:var(--sh-1)}
  .kpi .bar{height:4px}
  .kpi .body{padding:11px 15px 18px}
  .kpi .name{color:var(--muted); font-size:var(--fs-kpi-name); font-weight:600;
            letter-spacing:.1px; line-height:1.3}
  .kpi .val{font-size:var(--fs-kpi); font-weight:700; line-height:1.08; letter-spacing:-.5px;
            font-variant-numeric:tabular-nums; margin-top:2px}
  .kpi .unit{color:var(--muted); font-size:var(--fs-kpi-unit); margin-top:2px}
  .kpi .spark{position:absolute; top:64px; right:14px; width:96px; height:36px}

  .trend{grid-column:span 8}
  /* คำอธิบายสีอยู่นอก SVG — ไม่แย่งพื้นที่ plot กับตัวอักษรที่ scale ตามความกว้างการ์ด */
  .trendLegend{display:flex; flex-wrap:wrap; gap:6px 18px; margin:0 0 8px 13px;
               font-size:var(--fs-ui-md); font-weight:600; color:var(--muted)}
  .trendLegend .lg{display:inline-flex; align-items:center; gap:6px}
  .trendLegend .lg i{display:inline-block; width:20px; height:3px; border-radius:2px;
                     position:relative; flex:none}
  .trendLegend .lg i::after{content:""; position:absolute; left:50%; top:50%;
    width:7px; height:7px; border-radius:50%; transform:translate(-50%,-50%);
    background:inherit; box-shadow:0 0 0 1.5px #fff}
  #trendChart svg{display:block; width:100%; height:auto; max-height:320px}
  .treemapCard{grid-column:span 4}
  #treemap svg{display:block; width:100%; height:auto; max-height:320px; overflow:hidden}
  .cagrCard{grid-column:span 4}
  .countryCard{grid-column:span 5}
  .healthCard{grid-column:span 3}

  /* ── สถานะข้อมูล (label บน / ค่า+รายละเอียด ล่าง ชิดซ้าย) ─────────────── */
  table.health{width:100%; border-collapse:collapse; font-size:var(--fs-ui-md)}
  table.health tr.healthRow td{padding:12px 0; border-bottom:1px solid var(--line2);
          vertical-align:top}
  table.health tr.healthRow:last-child td{border-bottom:0}
  table.health .hrLabel{display:flex; align-items:flex-start; gap:8px;
          color:var(--muted); font-weight:600; font-size:var(--fs-ui-sm); line-height:1.45}
  table.health .hrLabel .st{width:9px; height:9px; border-radius:50%; flex:none;
          margin-top:6px}
  table.health .hrVal{margin:6px 0 0 17px; font-weight:700; font-size:var(--fs-ui);
          line-height:1.35; font-variant-numeric:tabular-nums; color:var(--ink)}
  table.health .hrSub{margin:4px 0 0 17px; font-size:var(--fs-ui-sm); line-height:1.5;
          color:var(--muted); overflow-wrap:break-word}


  svg{display:block; width:100%; height:auto; overflow:visible}
  .gridline{stroke:var(--line2); stroke-width:1}
  .axis{fill:var(--muted); font-size:var(--fs-axis); font-weight:700}
  .barlbl{fill:var(--ink); font-size:var(--fs-chart-lbl); font-weight:700}
  .hit{cursor:pointer; transition:opacity .15s}
  .hit:hover{opacity:.82}
  .dim{opacity:.22}

  #tip{position:fixed; pointer-events:none; opacity:0; transition:opacity .1s;
       background:rgba(14,39,73,.97); color:#fff; padding:10px 14px; border-radius:8px;
       font-size:var(--fs-tip); line-height:1.5; z-index:99; max-width:360px;
       box-shadow:0 10px 26px rgba(8,24,46,.34)}
  #tip b{font-weight:700}

  @media (max-width:980px){
    .filters{grid-template-columns:1fr; gap:8px}
    .static-filters,.filterGroups{grid-column:1; justify-self:stretch}
    #chips{justify-content:flex-start}
    .kpis{grid-template-columns:repeat(2,1fr)}
    .treemapCard,.cagrCard,.countryCard,.healthCard{grid-column:span 12}
  }
  @media (max-width:700px){
    header .brandLogo{width:42px; height:42px}
    header h1{font-size:26px}
    header .right{text-align:left}
    .kpis{grid-template-columns:1fr}
  }
  @media print{
    body{background:#fff}
    .filters{position:static; background:#fff}
    .filters .chip{display:none}
    .card,.kpi{box-shadow:none}
    main{padding:8px}
  }
</style>
<style>/* ฝังจาก Web Mockup/shared/dash-layout.css */
/* Responsive + overflow สำหรับทุกแดชบอร์ด mockup */

/* มาตรฐานขนาด UI (zoom เดียวกันทุกหน้า d1–d10) — ค่าคงที่ ไม่ใช้ vw/vh */
body[data-dash] {
  --fs-base: 28px;
  --fs-h2: 33px;
  --fs-kpi: 54px;
  --fs-kpi-name: 25px;
  --fs-kpi-unit: 22px;
  --fs-ui: 24px;
  --fs-ui-md: 22px;
  --fs-ui-sm: 20px;
  --fs-axis: 22px;
  --fs-chart-lbl: 23px;
  --fs-chrome-h1: 30px;
  --fs-chrome-sub: 20px;
  --fs-chrome-meta: 19px;
  --fs-chrome-org: 17px;
  --fs-filter: 19px;
  --fs-filter-chip: 18px;
  --fs-tip: 26px;
  --fs-period: 20px;
  --dash-chart-h: 280px;
  --dash-chart-h-sm: 220px;
  --dash-chart-h-lg: 340px;
  --dash-map-h: 520px;
}

body[data-dash] .dash-page,
body[data-dash]:not(.dash-with-sidebar) {
  font-size: var(--fs-base);
}

/* ใน iframe (CleansingConsole) ไม่มี .dash-page wrapper */
body[data-dash]:not(.dash-with-sidebar) .chart-box {
  position: relative;
  width: 100%;
  height: var(--dash-chart-h) !important;
  min-height: var(--dash-chart-h);
  max-height: var(--dash-chart-h);
}

body[data-dash]:not(.dash-with-sidebar) .chart-box.sm {
  height: var(--dash-chart-h-sm) !important;
  min-height: var(--dash-chart-h-sm);
  max-height: var(--dash-chart-h-sm);
}

body[data-dash]:not(.dash-with-sidebar) .chart-box.lg {
  height: var(--dash-chart-h-lg) !important;
  min-height: var(--dash-chart-h-lg);
  max-height: var(--dash-chart-h-lg);
}

body[data-dash="9"]:not(.dash-with-sidebar) .chart-box.lg {
  height: var(--dash-map-h) !important;
  min-height: var(--dash-map-h);
  max-height: var(--dash-map-h);
}

body[data-dash]:not(.dash-with-sidebar) #mapEl {
  height: var(--dash-map-h) !important;
  min-height: var(--dash-map-h);
  max-height: var(--dash-map-h);
}

.dash-page {
  flex: 1;
  min-width: 0;
  max-width: 100%;
  overflow-x: visible;
}

.dash-page main,
.dash-page .kpis {
  min-width: 0;
  max-width: 100%;
}

.dash-page .card {
  min-width: 0;
  overflow: hidden;
}

.dash-page .chart-box {
  position: relative;
  width: 100%;
  height: var(--dash-chart-h) !important;
  min-height: var(--dash-chart-h);
  max-height: var(--dash-chart-h);
}

.dash-page .chart-box.sm {
  height: var(--dash-chart-h-sm) !important;
  min-height: var(--dash-chart-h-sm);
  max-height: var(--dash-chart-h-sm);
}

.dash-page .chart-box.lg {
  height: var(--dash-chart-h-lg) !important;
  min-height: var(--dash-chart-h-lg);
  max-height: var(--dash-chart-h-lg);
}

/* d9: กราฟจัดอันดับ / แผนที่ สูงกว่ามาตรฐาน */
.dash-page .chart-box.lg.tall,
body[data-dash="9"] .dash-page .chart-box.lg {
  height: var(--dash-map-h) !important;
  min-height: var(--dash-map-h);
  max-height: var(--dash-map-h);
}

.dash-page .chart-box canvas {
  display: block;
  max-width: 100% !important;
}

.dash-page #mapEl {
  height: var(--dash-map-h) !important;
  min-height: var(--dash-map-h);
  max-height: var(--dash-map-h);
}

/* d1 — SVG ให้สูงเท่ากราฟ Chart.js */
.dash-page #trendChart svg,
.dash-page #treemap svg,
.dash-page #cagrChart svg,
.dash-page #countryChart svg {
  height: var(--dash-chart-h) !important;
  max-height: var(--dash-chart-h) !important;
  width: 100% !important;
}

.dash-page .kpis {
  grid-template-columns: repeat(auto-fit, minmax(228px, 1fr)) !important;
}

.dash-page main {
  max-width: 2000px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
  box-sizing: border-box;
  overflow-x: auto;
}

.dash-page table.data {
  display: block;
  overflow-x: auto;
  max-width: 100%;
}

.dash-page .table-scroll,
.dash-page .table-wrap {
  overflow-x: auto;
  max-width: 100%;
}

/* แถบตัวกรอง → shared/dash-filters.css (โหลดหลังไฟล์นี้) */

/* ลดทีละขั้นเมื่อจอแคบ — ทุกแดชใช้ชุดเดียวกัน */
@media (max-width: 1100px) {
  body[data-dash] {
    --fs-base: 24px;
    --fs-h2: 28px;
    --fs-kpi: 46px;
    --fs-kpi-name: 22px;
    --fs-kpi-unit: 20px;
    --fs-ui: 21px;
    --fs-ui-md: 20px;
    --fs-chrome-h1: 26px;
    --dash-chart-h: 260px;
    --dash-chart-h-lg: 320px;
    --dash-map-h: 480px;
  }

  .dash-page [class*="span"],
  .dash-page .trend,
  .dash-page .treemapCard,
  .dash-page .cagrCard,
  .dash-page .countryCard,
  .dash-page .healthCard {
    grid-column: span 12 !important;
  }

  .dash-page main {
    padding-left: 12px;
    padding-right: 12px;
    gap: 12px;
  }
}

@media (max-width: 720px) {
  body[data-dash] {
    --fs-base: 20px;
    --fs-h2: 24px;
    --fs-kpi: 40px;
    --fs-kpi-name: 20px;
    --fs-chrome-h1: 24px;
    --dash-chart-h: 240px;
    --dash-chart-h-sm: 200px;
    --dash-chart-h-lg: 280px;
    --dash-map-h: 360px;
  }

  body[data-dash] .filters {
    padding-left: 12px !important;
    padding-right: 12px !important;
  }

  body[data-dash] .static-filters {
    gap: 8px 10px !important;
  }

  body[data-dash] .static-filters span {
    padding-left: 8px;
  }
}

/* เปลี่ยนหน้า — fade */
.dash-page {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.26s ease, transform 0.26s ease;
}

.dash-page.dash-page-exiting {
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
}

.dash-page.dash-page-enter {
  opacity: 0;
  transform: translateY(10px);
}

.dash-page.dash-page-enter-active {
  opacity: 1;
  transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
  .dash-page,
  .dash-page.dash-page-exiting,
  .dash-page.dash-page-enter {
    transition: none;
    transform: none;
  }
}

</style>
<style>/* ฝังจาก Web Mockup/shared/dash-filters.css */
/* แถบตัวกรอง — มาตรฐานเดียวทุก d1–d10 (ทับ inline ในแต่ละ html) */
body[data-dash] {
  --dash-filter-fs: 19px;
  --dash-filter-chip-fs: 18px;
  --dash-filter-pad-y: 8px;
  --dash-filter-pad-x: 22px;
  --dash-filter-pad-left: 22px;
  --dash-filter-min-h: 46px;
  --dash-filter-left-max: 42%;
  --dash-filter-right-min: 58%;
}

body[data-dash] .filters {
  display: grid !important;
  grid-template-columns: minmax(0, var(--dash-filter-left-max)) minmax(0, 1fr) !important;
  grid-template-rows: 1fr !important;
  align-items: center !important;
  gap: 10px 12px !important;
  width: 100% !important;
  max-width: 100% !important;
  min-height: var(--dash-filter-min-h) !important;
  padding: var(--dash-filter-pad-y) var(--dash-filter-pad-x) var(--dash-filter-pad-y) var(--dash-filter-pad-left) !important;
  box-sizing: border-box !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 30 !important;
  background: #fff !important;
  border-bottom: 1px solid #d8e0ea !important;
  overflow: visible !important;
}

body[data-dash] .static-filters {
  grid-column: 1 !important;
  grid-row: 1 !important;
  justify-self: start !important;
  align-self: center !important;
  display: flex !important;
  flex-flow: row nowrap !important;
  align-items: center !important;
  gap: 8px 12px !important;
  min-width: 0 !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
  font-size: var(--dash-filter-fs) !important;
  color: var(--muted, #5b6b7e) !important;
  scrollbar-width: thin;
}

body[data-dash] .static-filters span {
  display: inline-flex !important;
  align-items: center !important;
  flex: 0 0 auto !important;
  white-space: nowrap !important;
  padding-left: 12px !important;
  border-left: 1px solid #d8e0ea !important;
}

body[data-dash] .static-filters span:first-child {
  padding-left: 0 !important;
  border-left: none !important;
}

body[data-dash] .static-filters select,
body[data-dash] .filters .reset-btn {
  font-size: var(--dash-filter-chip-fs) !important;
  font-family: inherit !important;
}

body[data-dash] .filterGroups {
  grid-column: 2 !important;
  grid-row: 1 !important;
  justify-self: stretch !important;
  align-self: center !important;
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  justify-content: flex-end !important;
  gap: 6px !important;
  min-width: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow: hidden !important;
}

body[data-dash] .filters .lbl {
  flex: 0 0 auto !important;
  order: 0 !important;
  white-space: nowrap !important;
  font-size: var(--dash-filter-fs) !important;
  font-weight: 600 !important;
  color: var(--muted, #5b6b7e) !important;
  margin: 0 !important;
  padding: 0 !important;
}

body[data-dash] #chips,
body[data-dash] #regionChips {
  display: flex !important;
  flex: 1 1 auto !important;
  flex-flow: row nowrap !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 5px !important;
  order: 1 !important;
  min-width: 0 !important;
  max-width: 100% !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
  padding: 2px 0 !important;
  scrollbar-width: thin;
}

body[data-dash] .filters .chip {
  flex: 0 0 auto !important;
  font-size: var(--dash-filter-chip-fs) !important;
  padding: 3px 8px !important;
  gap: 4px !important;
  border-radius: 5px !important;
  font-weight: 600 !important;
  white-space: nowrap !important;
}

body[data-dash="9"] .filters {
  z-index: 1200 !important;
}

/* ทับ @media 980px ใน inline ของ d1/d2… ที่แยก 2 แถว */
@media (max-width: 980px) {
  body[data-dash] .filters {
    grid-template-columns: minmax(0, var(--dash-filter-left-max)) minmax(0, 1fr) !important;
    grid-template-rows: 1fr !important;
    min-height: var(--dash-filter-min-h) !important;
  }

  body[data-dash] .static-filters {
    grid-column: 1 !important;
    grid-row: 1 !important;
  }

  body[data-dash] .filterGroups {
    grid-column: 2 !important;
    grid-row: 1 !important;
  }
}

@media (max-width: 720px) {
  body[data-dash] .filters {
    grid-template-columns: 1fr !important;
    grid-template-rows: auto auto !important;
    min-height: 0 !important;
  }

  body[data-dash] .static-filters {
    grid-column: 1 !important;
    grid-row: 1 !important;
    flex-wrap: wrap !important;
    overflow-x: visible !important;
  }

  body[data-dash] .filterGroups {
    grid-column: 1 !important;
    grid-row: 2 !important;
    justify-content: flex-start !important;
  }
}

</style>
</head>
<body data-dash="1">

<header>
  <div class="brand">
    <img class="brandLogo" src="__FDA_LOGO_SRC__" alt="อย.">
    <div>
      <h1>ระบบวิเคราะห์ข้อมูลเศรษฐกิจผลิตภัณฑ์สุขภาพ</h1>
      <div class="sub">หน้าจอที่ 1 · ภาพรวมเศรษฐกิจผลิตภัณฑ์สุขภาพ (Executive Overview)</div>
    </div>
  </div>
  <div class="right">
    <div class="asof">อัปเดตล่าสุด <span id="asOf"></span></div>
    <div class="org">สำนักงานคณะกรรมการอาหารและยา</div>
  </div>
</header>

<div class="filters">
  <div class="static-filters">
    <span>ปี: <select id="filterYear" onchange="setFilters()"></select></span>
    <span>เดือน: <select id="filterMonth" onchange="setFilters()"></select></span>
    <span><button type="button" class="reset-btn" onclick="resetFilters()">คืนค่า</button></span>
  </div>
  <div class="filterGroups">
    <span class="lbl">กลุ่มผลิตภัณฑ์:</span>
    <span id="chips"></span>
  </div>
</div>

<main>
  <section class="kpis" id="kpis"></section>

  <section class="card trend">
    <h2>แนวโน้มมูลค่าการค้าผลิตภัณฑ์สุขภาพ
      <span class="periodPick">
        <button type="button" class="periodBtn" onclick="togglePeriod(event,'trend')" title="เลือกช่วงเวลา"><svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><path d="M1 2h14l-5.5 6.3V13.2l-3 1.3V8.3z"/></svg></button>
        <div class="periodMenu" id="periodMenu-trend" onclick="event.stopPropagation()">
          <div class="periodRow"><label>จาก</label><input type="month" id="periodFrom-trend"></div>
          <div class="periodRow"><label>ถึง</label><input type="month" id="periodTo-trend"></div>
          <div class="periodActions">
            <button type="button" class="periodClear" onclick="clearPeriodRange(event,'trend')">ทั้งหมด</button>
            <button type="button" class="periodApply" onclick="applyPeriodRange(event,'trend')">ใช้ช่วงนี้</button>
          </div>
        </div>
      </span>
    </h2>
    <div class="cap" id="trendCap"></div>
    <div class="trendLegend" id="trendLegend"></div>
    <div id="trendChart"></div>
  </section>

  <section class="card treemapCard">
    <h2>สัดส่วนมูลค่าเศรษฐกิจรายกลุ่มผลิตภัณฑ์
      <span class="periodPick">
        <button type="button" class="periodBtn" onclick="togglePeriod(event,'treemap')" title="เลือกช่วงเวลา"><svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><path d="M1 2h14l-5.5 6.3V13.2l-3 1.3V8.3z"/></svg></button>
        <div class="periodMenu" id="periodMenu-treemap" onclick="event.stopPropagation()">
          <div class="periodRow"><label>จาก</label><input type="month" id="periodFrom-treemap"></div>
          <div class="periodRow"><label>ถึง</label><input type="month" id="periodTo-treemap"></div>
          <div class="periodActions">
            <button type="button" class="periodClear" onclick="clearPeriodRange(event,'treemap')">ทั้งหมด</button>
            <button type="button" class="periodApply" onclick="applyPeriodRange(event,'treemap')">ใช้ช่วงนี้</button>
          </div>
        </div>
      </span>
    </h2>
    <div class="cap" id="shareCap"></div>
    <div id="treemap"></div>
  </section>

  <section class="card cagrCard">
    <h2 id="cagrTitle">อันดับกลุ่มผลิตภัณฑ์ตามอัตราการเติบโต
      <span class="periodPick">
        <button type="button" class="periodBtn" onclick="togglePeriod(event,'cagr')" title="เลือกช่วงเวลา"><svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor"><path d="M1 2h14l-5.5 6.3V13.2l-3 1.3V8.3z"/></svg></button>
        <div class="periodMenu" id="periodMenu-cagr" onclick="event.stopPropagation()">
          <div class="periodRow"><label>จาก</label><input type="month" id="periodFrom-cagr"></div>
          <div class="periodRow"><label>ถึง</label><input type="month" id="periodTo-cagr"></div>
          <div class="periodActions">
            <button type="button" class="periodClear" onclick="clearPeriodRange(event,'cagr')">ทั้งหมด</button>
            <button type="button" class="periodApply" onclick="applyPeriodRange(event,'cagr')">ใช้ช่วงนี้</button>
          </div>
        </div>
      </span>
    </h2>
    <div class="cap" id="cagrCap"></div>
    <div id="cagrChart"></div>
  </section>

  <section class="card countryCard">
    <h2>ประเทศคู่ค้าสำคัญ</h2>
    <div class="cap" id="countryCap"></div>
    <div id="countryChart"></div>
  </section>

  <section class="card healthCard">
    <h2>สถานะข้อมูล</h2>
    <table class="health"><tbody id="healthBody"></tbody></table>
  </section>
</main>

<div id="tip"></div>

<script>
const DATA = /*__PAYLOAD__*/null;
const NAVY = "#12305B", MUTED = "#61738A", LINE = "#DFE6EE";
const GOOD = "#217A46", BAD = "#BF3A2B", WARN = "#B87400";
const GOOD_TINT = "#E7F2EB", BAD_TINT = "#FAEAE7", WARN_TINT = "#FBF1DF";
const SERIES = {
  import:  {color:"#1F6FB2", label:"มูลค่านำเข้า"},
  export:  {color:"#12A594", label:"มูลค่าส่งออก"},
  balance: {color:"#C0392B", label:"ดุลการค้า"}
};
let selected = "ALL";
let filterYear = "ALL", filterMonth = "ALL";   // "yyyy" / "MM" (2 หลัก) หรือ "ALL"
function trendViewMode(){
  if (filterMonth !== "ALL") return "month";
  if (filterYear !== "ALL") return "month";
  return "year";
}

// ตัวเลือกช่วงเวลารายการ์ด (อิสระจาก filterYear/filterMonth ด้านบน — คนละกลไก)
// null = ทั้งหมด (ไม่กรอง) — ไม่ก็ {from:"yyyy-mm", to:"yyyy-mm"} ช่วงที่ผู้ใช้เลือกเอง
// ใช้ได้เฉพาะโหมดข้อมูลจริง (ดู isRealDataMode()) เพราะต้องมี DATA.byGroup แบบรายเดือน
// จริงมาคำนวณ กราฟมอคยังไม่รองรับ ปุ่มจะถูกซ่อนอัตโนมัติ (ดู renderAll())
let periodTrend = null, periodTreemap = null;
// การ์ด "อันดับกลุ่มผลิตภัณฑ์" ต้องโชว์ "อัตราการเติบโต" เป็นค่าเริ่มต้นเสมอ (ไม่ใช่
// จำนวนผู้ประกอบการ) — ตั้งช่วงเริ่มต้นเป็น 12 เดือนล่าสุดที่จบเดือนแล้วจริงให้อัตโนมัติ
// เทียบ 12 เดือนก่อนหน้า ผู้ใช้ค่อยกดไอคอนกรวยเปลี่ยนช่วงเองทีหลังได้ ถ้าข้อมูลย้อนหลัง
// ไม่พอ (< 24 เดือนที่จบแล้ว) ค่อย fallback เป็น null (โชว์จำนวนผู้ประกอบการแทน)
function defaultCagrPeriod(){
  const months = completeMonths();
  if (months.length < 24) return null;
  return {from: months[months.length - 12], to: months[months.length - 1]};
}
let periodCagr = defaultCagrPeriod();

/* ── helper ──────────────────────────────────────────────────────── */
const esc = s => String(s).replace(/[&<>"]/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmt = (v, d=0) => v == null || isNaN(v) ? "—"
  : v.toLocaleString("en-US", {minimumFractionDigits:d, maximumFractionDigits:d});
const tag = (n, a, inner="") =>
  `<${n} ${Object.entries(a).map(([k,v]) => `${k}="${v}"`).join(" ")}>${inner}</${n}>`;
const tip = t => `data-tip="${esc(t)}"`;

/* ── ตัวกรอง Year / Month (ตัวกรองไขว้เดียวกับกลุ่มผลิตภัณฑ์ มีผลทุกส่วนในหน้าจอ) ──
   Year = "ALL" ดูทุกปี | เลือกปีหนึ่ง ดูเฉพาะปีนั้น
   Month = "ALL" ดูทุกเดือน | เลือกเดือนหนึ่ง ดูเฉพาะเดือนนั้นของทุกปี (เทียบตามฤดูกาล) */
const TH_MONTH_NAME = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.",
                       "ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."];
function allMonths(){
  return [...new Set(DATA.byGroup.map(r => r.m))].sort();
}
function isDefaultFilter(){
  return filterYear === "ALL" && filterMonth === "ALL";
}
function populateYearMonthFilters(){
  const months = allMonths();
  const selY = document.getElementById("filterYear"), selM = document.getElementById("filterMonth");
  if (!selY || !selM) return;
  const years = [...new Set(months.map(m => m.slice(0,4)))].sort();
  selY.innerHTML = '<option value="ALL">ทั้งหมด</option>' +
    years.map(y => `<option value="${y}">${+y + 543}</option>`).join("");
  selM.innerHTML = '<option value="ALL">ทั้งหมด</option>' +
    TH_MONTH_NAME.map((n,i) => `<option value="${String(i+1).padStart(2,"0")}">${n}</option>`).join("");
  selY.value = filterYear;
  selM.value = filterMonth;
}
function setFilters(){
  filterYear = document.getElementById("filterYear").value;
  filterMonth = document.getElementById("filterMonth").value;
  renderAll();
}
function resetFilters(){
  filterYear = "ALL"; filterMonth = "ALL";
  const selY = document.getElementById("filterYear"), selM = document.getElementById("filterMonth");
  if (selY) selY.value = "ALL";
  if (selM) selM.value = "ALL";
  renderAll();
}

/* ── ตัวเลขบนการ์ด: คำนวณใหม่เมื่อเปลี่ยนกลุ่มผลิตภัณฑ์/Year/Month ───────── */
function rowsFor(g){
  let rows = g === "ALL" ? DATA.byGroup : DATA.byGroup.filter(r => r.g === g);
  if (filterYear !== "ALL") rows = rows.filter(r => r.m.slice(0,4) === filterYear);
  if (filterMonth !== "ALL") rows = rows.filter(r => r.m.slice(5,7) === filterMonth);
  return rows;
}

/* ── ตัวเลือกช่วงเวลารายการ์ด (ไอคอนกรวยมุมขวาบนของการ์ด) ───────────── */
// เดือนทั้งหมดที่ "มีข้อมูลจริงให้เชื่อได้" — ตัด 2 กรณีออก:
//  1) เดือนปัจจุบันที่ยังไม่จบ (ตามนาฬิกาเครื่องที่เปิดดู) ยอดจะต่ำเตี้ยเพราะสะสมไม่ครบ
//  2) เดือนท้าย ๆ ที่ "ไม่มีมูลค่าการค้าเลยทั้ง 7 กลุ่มพร้อมกัน" (import+export = 0 ทุกกลุ่ม)
//     ซึ่งมักเกิดจากไฟล์ต้นทาง (เช่น customs_trade_7groups_....csv) ยังอัปเดตไม่ถึงเดือนนั้น
//     ไม่ใช่การค้าจริงเป็นศูนย์ — เจอเคสนี้ตอนเลือกช่วง 12 เดือนล่าสุดแล้วดันครอบคลุมเดือน
//     ที่ไฟล์ศุลกากรยังไม่มีข้อมูล (มีถึงแค่ 2025-12 ทั้งที่วันนี้ ก.ย. 2569 แล้ว) ทำให้ค่า
//     ติดลบหลอก ๆ เท่ากันเกือบทุกกลุ่มพร้อมกัน (ไม่ใช่ธุรกิจหดตัวจริง)
// ใช้ฟังก์ชันนี้จุดเดียวทั้งกราฟเติบโตและตัวกรองช่วงเวลาการ์ดอื่น กันปัญหาซ้ำ
function completeMonths(){
  const months = [...new Set(DATA.byGroup.map(r => r.m))].sort();
  if (!months.length) return months;
  const totalByMonth = new Map();
  DATA.byGroup.forEach(r => totalByMonth.set(r.m, (totalByMonth.get(r.m) || 0) + r.im + r.ex));
  let end = months.length;
  while (end > 0 && !(totalByMonth.get(months[end - 1]) > 0)) end--;
  let out = months.slice(0, end);
  if (!out.length) return out;
  const now = new Date();
  const curYm = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}`;
  if (out[out.length - 1] === curYm) out = out.slice(0, -1);
  return out;
}
// ตัดแถวให้เหลือแค่ช่วง [from,to] (รูปแบบ "yyyy-mm" เทียบกันตรง ๆ ได้เพราะเรียงตัวอักษร
// = เรียงเวลาพอดี) — period=null คืนของเดิมทั้งหมดไม่ตัดอะไร (เท่ากับ "ทั้งหมด")
function clipRowsToPeriod(rows, period){
  if (!period) return rows;
  return rows.filter(r => r.m >= period.from && r.m <= period.to);
}
const PERIOD_KEYS = ["trend", "treemap", "cagr"];
const periodLabel = p => !p ? "" : ` — ${p.from} ถึง ${p.to}`;
function closeAllPeriodMenus(){
  PERIOD_KEYS.forEach(k => {
    const el = document.getElementById("periodMenu-" + k);
    if (el) el.classList.remove("open");
  });
}
function togglePeriod(e, key){
  e.stopPropagation();
  const el = document.getElementById("periodMenu-" + key);
  if (!el) return;
  const willOpen = !el.classList.contains("open");
  closeAllPeriodMenus();
  if (willOpen) el.classList.add("open");
}
function periodVar(key){
  return key === "trend" ? periodTrend : key === "treemap" ? periodTreemap : periodCagr;
}
function applyPeriodRange(e, key){
  e.stopPropagation();
  const from = document.getElementById("periodFrom-" + key).value;
  const to = document.getElementById("periodTo-" + key).value;
  if (!from || !to || from > to) return;   // ว่าง หรือ จาก > ถึง — ไม่ทำอะไร ให้แก้ก่อน
  const range = {from, to};
  if (key === "trend") periodTrend = range;
  else if (key === "treemap") periodTreemap = range;
  else if (key === "cagr") periodCagr = range;
  closeAllPeriodMenus();
  renderAll();
}
function clearPeriodRange(e, key){
  e.stopPropagation();
  if (key === "trend") periodTrend = null;
  else if (key === "treemap") periodTreemap = null;
  else if (key === "cagr") periodCagr = null;
  document.getElementById("periodFrom-" + key).value = "";
  document.getElementById("periodTo-" + key).value = "";
  closeAllPeriodMenus();
  renderAll();
}
// ใส่ค่าที่เลือกอยู่กลับเข้าช่อง input เวลาเปิดเมนู (ไม่งั้นเปิดใหม่แล้วช่องว่างเปล่า
// ทั้งที่มีตัวกรองอยู่) + ซ่อนปุ่มทั้งหมดถ้าเป็นโหมดข้อมูลมอค (กราฟมอคยังไม่รองรับ
// ตัวกรองนี้ ปุ่มที่กดแล้วไม่มีผลจะสร้างความสับสนมากกว่าเป็นประโยชน์)
function syncPeriodPickers(){
  const real = isRealDataMode();
  document.querySelectorAll(".periodPick").forEach(el => { el.style.display = real ? "" : "none"; });
  if (!real) return;
  PERIOD_KEYS.forEach(k => {
    const range = periodVar(k);
    const fromEl = document.getElementById("periodFrom-" + k);
    const toEl = document.getElementById("periodTo-" + k);
    if (fromEl) fromEl.value = range ? range.from : "";
    if (toEl) toEl.value = range ? range.to : "";
  });
}
document.addEventListener("click", closeAllPeriodMenus);
function sumByFy(rows, fy, key){
  return rows.reduce((s, r) => r.fy === fy ? s + r[key] : s, 0);
}
function monthlyTotals(rows, key){
  const m = new Map();
  rows.forEach(r => m.set(r.m, (m.get(r.m) || 0) + r[key]));
  return [...m.entries()].sort((a,b) => a[0] < b[0] ? -1 : 1);
}
function stockAt(rows, key, back = 0){
  const s = monthlyTotals(rows, key);
  return s.length > back ? s[s.length - 1 - back][1] : null;
}
function kpisFor(g){
  if (g === "ALL" && isDefaultFilter()) return {cards: DATA.kpi, sparks: DATA.sparks};
  const rows = rowsFor(g);
  // เลือกกลุ่ม/ช่วงเวลาเอง ต้องหาปีงบประมาณ "ล่าสุดในช่วงที่กรอง" เอง
  // ไม่ใช้ fyComplete ตายตัว เพราะผู้ใช้อาจเลือกช่วงเวลาเก่ากว่าที่ fyComplete ชี้ไว้
  const rowFys = [...new Set(rows.map(r => r.fy))];
  const fy = rowFys.length ? Math.max(...rowFys) : DATA.meta.fyComplete;
  const base = DATA.kpi;                          // ยืมชื่อ/หน่วย/ฐานเวลามาใช้ซ้ำ
  // *** โหมดข้อมูลจริง: ค่าเริ่มต้น "ทั้งหมด" (DATA.kpi ด้านบน) รวมทุกเดือนในหน้าต่าง
  // ข้อมูลทั้งหมด ไม่ใช่แค่ปีงบประมาณล่าสุด — ถ้าพอกรองเฉพาะกลุ่มแล้วดันไปรวมแค่ปีงบฯ
  // ล่าสุด (sumByFy) ยอดรวมของทุกกลุ่มบวกกันจะไม่เท่ากับยอด "ทั้งหมด" ที่เห็นตอนแรก
  // ทำให้ผู้ใช้เช็คยอดไขว้กันเองแล้วงง จึงต้องรวมทุกเดือนเหมือนกันเสมอในโหมดข้อมูลจริง
  // ส่วนโหมดมอคยังยึดกรอบปีงบประมาณเหมือนเดิม (ออกแบบไว้แบบนั้นตั้งแต่แรก) ***
  const sumAll = key => rows.reduce((s, r) => s + r[key], 0);
  const im = isRealDataMode() ? sumAll("im") : sumByFy(rows, fy, "im"),
        ex = isRealDataMode() ? sumAll("ex") : sumByFy(rows, fy, "ex");
  const ps = stockAt(rows, "ps"), ae = stockAt(rows, "ae"), bl = stockAt(rows, "bl");
  const hasPv = rows.length && rows[0].pv != null;
  const v = {import_value: im, export_value: ex, trade_balance: ex - im,
             product_stock: ps, active_entity: ae, backlog: bl};
  if (hasPv) v.production_value = sumAll("pv");
  const cards = base.map(c => ({...c, value: c.kpi_code in v ? v[c.kpi_code] : c.value}));
  const sk = {};
  [["import_value","im"],["export_value","ex"],["trade_balance","bal"],
   ["product_stock","ps"],["active_entity","ae"],["backlog","bl"]]
    .forEach(([code, key]) => sk[code] = monthlyTotals(rows, key).slice(-24).map(x => x[1]));
  if (hasPv)
    sk.production_value = monthlyTotals(rows, "pv").slice(-24).map(x => x[1]);
  return {cards, sparks: sk};
}

/* ── กราฟเส้นขนาดเล็กในการ์ด ─────────────────────────────────────── */
function sparkSvg(vals, color){
  if (!vals || vals.length < 2) return "";
  const w = 96, h = 36, lo = Math.min(...vals), hi = Math.max(...vals);
  const sx = i => i / (vals.length - 1) * w;
  const sy = v => hi === lo ? h/2 : h - (v - lo) / (hi - lo) * (h - 8) - 4;
  const pts = vals.map((v,i) => `${sx(i).toFixed(1)},${sy(v).toFixed(1)}`).join(" ");
  const ex = w, ey = sy(vals[vals.length - 1]);
  // ไล่เฉดจากเส้นลงมาให้จางหาย ดีกว่าเติมสีทึบทั้งพื้นที่ใต้เส้น
  const id = "sg" + Math.random().toString(36).slice(2, 8);
  return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${color}" stop-opacity=".22"/>
      <stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs>
    <polygon points="0,${h} ${pts} ${w},${h}" fill="url(#${id})"/>
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.8"
     stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${ex}" cy="${ey.toFixed(1)}" r="2.4" fill="${color}"
     stroke="#fff" stroke-width="1.2"/></svg>`;
}

function renderKpis(){
  const {cards, sparks} = kpisFor(selected);
  document.getElementById("kpis").innerHTML = cards.map(c => {
    const t = `${c.kpi_name_th}\n${fmt(c.value)} ${c.unit} · ${c.basis}`
            + (c.drill_to ? `\nเจาะลึกต่อที่ ${c.drill_to}` : "");
    return `<div class="kpi" ${tip(t)}>
      <div class="bar" style="background:linear-gradient(90deg,${NAVY},${NAVY}99)"></div>
      ${sparkSvg(sparks[c.kpi_code], NAVY)}
      <div class="body">
        <div class="name">${esc(c.kpi_name_th)}</div>
        <div class="val">${fmt(c.value)}</div>
        <div class="unit">${esc(c.unit)}</div>
      </div></div>`;
  }).join("");
}

/* ── ส่วนที่ 2: แนวโน้มมูลค่าการค้า ───────────────────────────────── */
function renderTrendLegend(){
  const el = document.getElementById("trendLegend");
  if (!el) return;
  el.innerHTML = Object.entries(SERIES).map(([k, v]) =>
    `<span class="lg"><i style="background:${v.color}"></i>${v.label}</span>`
  ).join("");
}
function trendPlotX(i, n, W, P){
  const plotW = W - P.l - P.r;
  const pad = n <= 6 ? plotW * 0.08 : 0;
  return P.l + pad + i * (plotW - 2 * pad) / Math.max(n - 1, 1);
}
function trendScaleY(allValues, nTicks){
  const nums = allValues.filter(v => v != null);
  if (!nums.length) return niceScale(0, 1, nTicks);
  let lo = Math.min(0, ...nums), hi = Math.max(0, ...nums);
  const span = hi - lo || Math.max(Math.abs(hi), 1);
  const pad = span * 0.06;
  return niceScale(lo - pad, hi + pad, nTicks);
}

const TREND_DISPLAY_YEARS = 5;
function sliceTrendYears(fys, series){
  if (fys.length <= TREND_DISPLAY_YEARS) return {fys, series};
  const n = TREND_DISPLAY_YEARS;
  return {
    fys: fys.slice(-n),
    series: series.map(s => ({
      key: s.key, values: s.values.slice(-n),
      isFc: (s.isFc || []).slice(-n),
      lo: (s.lo || []).slice(-n), hi: (s.hi || []).slice(-n),
    })),
  };
}
function trendSeries(){
  if (selected === "ALL" && isDefaultFilter()){
    const s = sliceTrendYears(DATA.meta.fys, DATA.trend);
    return {...s, hasFc: s.series.some(x => (x.isFc || []).some(Boolean))};
  }
  const rows = rowsFor(selected);
  const fys = [...new Set(rows.map(r => r.fy))].sort((a,b) => a - b);
  const g = k => fys.map(f => +sumByFy(rows, f, k).toFixed(1));
  const im = g("im"), ex = g("ex");
  return {fys, hasFc: false, series: [
    {key:"import",  values: im, isFc: fys.map(()=>false), lo:[], hi:[]},
    {key:"export",  values: ex, isFc: fys.map(()=>false), lo:[], hi:[]},
    {key:"balance", values: ex.map((v,i) => +(v - im[i]).toFixed(1)),
     isFc: fys.map(()=>false), lo:[], hi:[]}
  ]};
}

/* ── กราฟแนวโน้มรายเดือน — ใช้เมื่อไม่มีค่าพยากรณ์จริงในข้อมูล (โหมดข้อมูลจริง) ──
   ข้อมูลมอคมี SARIMAX พยากรณ์รายปีงบประมาณจริง เก็บ path เดิมไว้ไม่แตะเลย
   ส่วนข้อมูลจริงที่ต่อ DB ตรง ยังไม่มีพยากรณ์ (ต้องมี >=12 เดือนต่อรอบ) แสดง
   รายเดือนจะเห็นแนวโน้มได้ชัดกว่าการยุบเหลือแค่ 2-3 จุดต่อปีงบประมาณ */
function trendSeriesMonthly(){
  const rows = clipRowsToPeriod(rowsFor(selected), periodTrend);
  const xs = [...new Set(rows.map(r => r.m))].sort();
  const sumAt = (m, key) => rows.reduce((s,r) => r.m === m ? s + r[key] : s, 0);
  const g = key => xs.map(m => +sumAt(m, key).toFixed(1));
  const im = g("im"), ex = g("ex");
  return {xs, series: [
    {key:"import", values: im, isFc: xs.map(()=>false)},
    {key:"export", values: ex, isFc: xs.map(()=>false)},
    {key:"balance", values: ex.map((v,i) => +(v - im[i]).toFixed(1)), isFc: xs.map(()=>false)}
  ]};
}

function renderTrendMonthly(){
  renderTrendLegend();
  const {xs, series} = trendSeriesMonthly();
  const W = 980, H = 300, P = {t:18, r:16, b:34, l:66};
  const all = series.flatMap(s => s.values).filter(v => v != null);
  const sc = trendScaleY(all, 6);
  const lo = sc.lo, hi = sc.hi;
  const x = i => trendPlotX(i, xs.length, W, P);
  const y = v => P.t + (hi - v) / (hi - lo) * (H - P.t - P.b);

  let s = "";
  sc.ticks.forEach(v => {
    const yy = y(v);
    s += `<line class="gridline" x1="${P.l}" y1="${yy}" x2="${W-P.r}" y2="${yy}"
           ${v === 0 ? 'stroke="#B3BFCC"' : ''}/>`;
    s += `<text class="axis" x="${P.l-9}" y="${yy+4}" text-anchor="end">${fmt(v)}</text>`;
  });

  series.forEach(ser => {
    const c = SERIES[ser.key].color;
    const pts = ser.values.map((v,i) => v == null ? null : `${x(i)},${y(v)}`)
                          .filter(Boolean);
    if (pts.length > 1) s += `<polyline points="${pts.join(" ")}" fill="none"
                           stroke="${c}" stroke-width="2.2" stroke-linejoin="round"
                           stroke-linecap="round"/>`;
    ser.values.forEach((v,i) => {
      if (v == null) return;
      const t = `${SERIES[ser.key].label} ${xs[i]}\n${fmt(v)} ล้านบาท`;
      s += `<circle class="hit" cx="${x(i)}" cy="${y(v)}" r="3" fill="${c}"
             stroke="#fff" stroke-width="1.4" ${tip(t)}/>`;
    });
  });

  // เดือนเยอะจนป้ายทับกัน — โชว์แค่บางจุด (ประมาณ 10-12 ป้ายทั้งกราฟ) + จุดสุดท้ายเสมอ
  const skip = Math.max(1, Math.ceil(xs.length / 11));
  xs.forEach((m,i) => {
    if (i % skip !== 0 && i !== xs.length - 1) return;
    s += `<text class="axis" x="${x(i)}" y="${H-P.b+20}" text-anchor="middle">${m}</text>`;
  });
  s += `<text class="axis" x="${P.l-52}" y="${P.t-10}">ล้านบาท</text>`;

  document.getElementById("trendChart").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${s}</svg>`;
  document.getElementById("trendCap").textContent =
    "แสดงข้อมูลรายเดือน — ยังไม่มีค่าพยากรณ์ (SARIMAX ต้องการข้อมูล ≥12 เดือนต่อรอบ)"
    + periodLabel(periodTrend);
}

/* ── กราฟแนวโน้มรายปีงบประมาณสำหรับข้อมูลจริง (รายเดือนเมื่อเลือกปี/เดือน) ──
   ต่างจาก renderTrend()/trendSeries() (path มอค) ตรงที่ไม่มีเส้นพยากรณ์/แถบ
   ความเชื่อมั่นเลย เพราะข้อมูลจริงยังไม่มี SARIMAX ให้ใช้ */
function renderTrendYearly(){
  renderTrendLegend();
  const rows = clipRowsToPeriod(rowsFor(selected), periodTrend);
  const fys = [...new Set(rows.map(r => r.fy))].sort((a,b) => a - b);
  const g = k => fys.map(f => +sumByFy(rows, f, k).toFixed(1));
  const im = g("im"), ex = g("ex");
  const series = [
    {key:"import", values: im},
    {key:"export", values: ex},
    {key:"balance", values: ex.map((v,i) => +(v - im[i]).toFixed(1))},
  ];

  const W = 980, H = 300, P = {t:18, r:16, b:34, l:66};
  const all = series.flatMap(s => s.values).filter(v => v != null);
  const sc = trendScaleY(all, 6);
  const lo = sc.lo, hi = sc.hi;
  const x = i => trendPlotX(i, fys.length, W, P);
  const y = v => P.t + (hi - v) / (hi - lo) * (H - P.t - P.b);

  let s = "";
  sc.ticks.forEach(v => {
    const yy = y(v);
    s += `<line class="gridline" x1="${P.l}" y1="${yy}" x2="${W-P.r}" y2="${yy}"
           ${v === 0 ? 'stroke="#B3BFCC"' : ''}/>`;
    s += `<text class="axis" x="${P.l-9}" y="${yy+4}" text-anchor="end">${fmt(v)}</text>`;
  });

  series.forEach(ser => {
    const c = SERIES[ser.key].color;
    const pts = ser.values.map((v,i) => v == null ? null : `${x(i)},${y(v)}`).filter(Boolean);
    if (pts.length > 1) s += `<polyline points="${pts.join(" ")}" fill="none"
                           stroke="${c}" stroke-width="2.8" stroke-linejoin="round"
                           stroke-linecap="round"/>`;
    ser.values.forEach((v,i) => {
      if (v == null) return;
      const t = `${SERIES[ser.key].label} ปีงบประมาณ ${fys[i]}\n${fmt(v)} ล้านบาท`;
      s += `<circle class="hit" cx="${x(i)}" cy="${y(v)}" r="4.8" fill="${c}"
             stroke="#fff" stroke-width="2.6" ${tip(t)}/>`;
    });
  });

  fys.forEach((f,i) => {
    s += `<text class="axis" x="${x(i)}" y="${H-P.b+20}" text-anchor="middle">${f}</text>`;
  });
  s += `<text class="axis" x="${P.l-52}" y="${P.t-10}">ล้านบาท</text>`;

  document.getElementById("trendChart").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${s}</svg>`;
  document.getElementById("trendCap").textContent =
    "แสดงข้อมูลรายปีงบประมาณ — ยังไม่มีค่าพยากรณ์" + periodLabel(periodTrend);
}

/* ปัดช่วงแกนให้ลงตัวเป็นเลขกลม (1/2/5 x 10^n) แทนการหารช่วงดิบเท่า ๆ กัน */
function niceScale(lo, hi, n){
  const step0 = (hi - lo) / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const norm = step0 / mag;
  const step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * mag;
  const start = Math.floor(lo / step) * step, end = Math.ceil(hi / step) * step;
  const ticks = [];
  for (let v = start; v <= end + step * 1e-6; v += step) ticks.push(v);
  return {lo: start, hi: end, ticks};
}

// crossFilter = มี DATA.byGroup รายเดือน (กรองทั้งหน้าได้) — แยกจากค่าพยากรณ์
// mockup ที่มี byGroup + SARIMAX พยากรณ์รวมประเทศใช้ทั้งสองพร้อมกันได้
function isRealDataMode(){
  return !!(DATA.meta && DATA.meta.crossFilter);
}
function trendHasForecast(){
  return DATA.trend.some(s => (s.isFc || []).some(Boolean));
}

function renderTrend(){
  // ยังไม่มีพยากรณ์รายปี → รายเดือนเมื่อเลือกปี/เดือน ไม่เช่นนั้นรายปี
  // มีพยากรณ์ (มอคเต็มหรือ mockup ต่อ DB) → กราฟรายปีงบประมาณ + เส้นประ/ช่วง CI
  if (isRealDataMode() && !trendHasForecast()){
    if (trendViewMode() === "year") renderTrendYearly(); else renderTrendMonthly();
    return;
  }
  renderTrendLegend();
  const {fys, series, hasFc} = trendSeries();
  const W = 980, H = 300, P = {t:18, r:16, b:34, l:66};
  const all = series.flatMap(s => s.values.concat(s.lo || [], s.hi || []))
                    .filter(v => v != null);
  const sc = trendScaleY(all, 6);
  const lo = sc.lo, hi = sc.hi;
  const x = i => trendPlotX(i, fys.length, W, P);
  const y = v => P.t + (hi - v) / (hi - lo) * (H - P.t - P.b);

  let s = "";
  // เส้นกริดและแกนค่า
  sc.ticks.forEach(v => {
    const yy = y(v);
    s += `<line class="gridline" x1="${P.l}" y1="${yy}" x2="${W-P.r}" y2="${yy}"
           ${v === 0 ? 'stroke="#B3BFCC"' : ''}/>`;
    s += `<text class="axis" x="${P.l-9}" y="${yy+4}" text-anchor="end">${fmt(v)}</text>`;
  });
  // แรเงาช่วงพยากรณ์ พร้อมป้ายกำกับ เพื่อไม่ต้องเดาว่าแถบเทาคืออะไร
  const fcIdx = series[0].isFc.findIndex(Boolean);
  if (hasFc && fcIdx > 0){
    const step = x(fcIdx) - x(fcIdx - 1);
    const bx = x(fcIdx - 1) + step * 0.42;
    const bw = W - P.r - bx;
    s += `<rect x="${bx}" y="${P.t}" width="${bw}" height="${H-P.t-P.b}"
           fill="${NAVY}" opacity=".05"/>
          <line x1="${bx}" y1="${P.t}" x2="${bx}" y2="${H-P.b}"
           stroke="${NAVY}" stroke-width="1" stroke-dasharray="3 4" opacity=".35"/>
          <text class="axis" x="${bx + Math.min(8, bw * 0.08)}" y="${P.t + 12}"
           style="fill:${NAVY};opacity:.58;font-size:17px">ช่วงพยากรณ์</text>`;
  }
  // แถบความเชื่อมั่น
  series.forEach(ser => {
    const pts = [];
    ser.values.forEach((v,i) => { if (ser.lo[i] != null) pts.push(i); });
    if (pts.length){
      const up = pts.map(i => `${x(i)},${y(ser.hi[i])}`);
      const dn = pts.slice().reverse().map(i => `${x(i)},${y(ser.lo[i])}`);
      s += `<polygon points="${up.concat(dn).join(" ")}"
             fill="${SERIES[ser.key].color}" opacity=".13"/>`;
    }
  });
  // เส้นข้อมูลจริง (ทึบ) และเส้นพยากรณ์ (ประ)
  series.forEach(ser => {
    const c = SERIES[ser.key].color;
    const solid = [], dashed = [];
    ser.values.forEach((v,i) => {
      if (v == null) return;
      (ser.isFc[i] ? dashed : solid).push(`${x(i)},${y(v)}`);
      if (ser.isFc[i] && dashed.length === 1 && i > 0)
        dashed.unshift(`${x(i-1)},${y(ser.values[i-1])}`);
    });
    if (solid.length) s += `<polyline points="${solid.join(" ")}" fill="none"
                             stroke="${c}" stroke-width="2.8" stroke-linejoin="round"
                             stroke-linecap="round"/>`;
    if (dashed.length > 1) s += `<polyline points="${dashed.join(" ")}" fill="none"
                             stroke="${c}" stroke-width="2.4" stroke-dasharray="7 5"
                             stroke-linecap="round"/>`;
    ser.values.forEach((v,i) => {
      if (v == null) return;
      const t = `${SERIES[ser.key].label} ปีงบประมาณ ${fys[i]}${ser.isFc[i] ? " (พยากรณ์)" : ""}\n${fmt(v)} ล้านบาท`;
      // วงกลมขาวรองอีกชั้น ให้จุดข้อมูลไม่จมกับเส้นที่ตัดผ่านกัน
      s += `<circle class="hit" cx="${x(i)}" cy="${y(v)}" r="4.8"
             fill="${ser.isFc[i] ? "#fff" : c}" stroke="#fff" stroke-width="2.6" ${tip(t)}/>
            <circle class="hit" cx="${x(i)}" cy="${y(v)}" r="4.8" fill="none"
             stroke="${c}" stroke-width="2" ${tip(t)}/>`;
    });
  });
  // แกนปี
  fys.forEach((f,i) => {
    const fc = series[0].isFc[i];
    s += `<text class="axis" x="${x(i)}" y="${H-P.b+20}" text-anchor="middle">${f}${fc?"F":""}</text>`;
  });
  s += `<text class="axis" x="${P.l-52}" y="${P.t + 4}" style="font-size:17.5px">ล้านบาท</text>`;
  document.getElementById("trendChart").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${s}</svg>`;

  document.getElementById("trendCap").textContent = hasFc
    ? "เส้นทึบ = ข้อมูลจริง | เส้นประ = ค่าพยากรณ์จาก SARIMAX(1,1,1)(1,1,1,12) พร้อมช่วงความเชื่อมั่น 80%"
    : "แสดงเฉพาะข้อมูลจริง — ค่าพยากรณ์คำนวณไว้ที่ระดับยอดรวมประเทศเท่านั้น";
}

/* ── ส่วนที่ 3: Treemap ──────────────────────────────────────────── */
function squarify(vals, x, y, w, h){
  const out = [], t = vals.reduce((a,b) => a+b, 0);
  let i = 0, cx = x, cy = y, cw = w, ch = h;
  while (i < vals.length){
    const remain = vals.slice(i).reduce((a,b) => a+b, 0) / t;
    const take = Math.min(2, vals.length - i);
    const part = vals.slice(i, i+take), ps = part.reduce((a,b)=>a+b,0) / t;
    if (cw >= ch){
      const colw = cw * ps / remain; let yy = cy;
      part.forEach(v => { const hh = ch * v / (ps*t); out.push([cx, yy, colw, hh]); yy += hh; });
      cx += colw; cw -= colw;
    } else {
      const rowh = ch * ps / remain; let xx = cx;
      part.forEach(v => { const ww = cw * v / (ps*t); out.push([xx, cy, ww, rowh]); xx += ww; });
      cy += rowh; ch -= rowh;
    }
    i += take;
  }
  return out;
}

// period="ALL" (หรือโหมดมอค) ใช้ DATA.share ที่ Python คำนวณมาให้ตรง ๆ — เลือกช่วงเวลา
// อื่นคำนวณสด ๆ จาก DATA.byGroup (มีรายละเอียดรายเดือนอยู่แล้ว ไม่ต้องขอข้อมูลเพิ่ม)
function shareForPeriod(period){
  if (period === "ALL" || !isRealDataMode()) return DATA.share;
  const rows = clipRowsToPeriod(DATA.byGroup, period);
  const sums = new Map();
  rows.forEach(r => sums.set(r.g, (sums.get(r.g) || 0) + r.im + r.ex));
  const total = [...sums.values()].reduce((a,b) => a+b, 0) || 1;
  return DATA.groups.map(g => {
    const v = sums.get(g.code) || 0;
    return {product_group: g.code, name_th: g.name, trade_value_mb: v, share_pct: v / total * 100};
  }).sort((a,b) => b.trade_value_mb - a.trade_value_mb);
}

function treemapStatForCell(w, d){
  const full = `${fmt(d.trade_value_mb)} ลบ. · ${fmt(d.share_pct,1)}%`;
  const valOnly = `${fmt(d.trade_value_mb)} ลบ.`;
  const pct = `${fmt(d.share_pct,1)}%`;
  const innerW = Math.max(w - 20, 0);
  const maxChars = innerW / 7.5;
  if (full.length <= maxChars) return full;
  if (valOnly.length <= maxChars) return valOnly;
  if (innerW >= 34) return pct;
  return "";
}
function treemapStatFs(w, stat){
  if (!stat) return 14;
  if (stat.includes("·")) return w >= 140 ? 18 : (w >= 105 ? 15 : 14);
  return w >= 100 ? 16 : 14;
}
function treemapCellText(x, y, w, h, d, dim, t, SH, W, H){
  const dc = dim.trim(), area = w * h;
  const stat = treemapStatForCell(w, d);
  const big = area > W * H * 0.10;
  let s = "";
  // ช่องแคบสูง (เช่น อาหาร/เครื่องสำอาง) — ชื่อ + มูลค่า/% (ย่อตามความกว้าง)
  if (w <= 78 && h > 68){
    const fs = h > 120 ? 17.5 : 16;
    s += `<text class="hit${dim}" x="${x+9}" y="${y+20}" fill="#fff" ${SH}
           font-size="${fs}" font-weight="700" data-group="${d.product_group}" ${tip(t)}>${esc(d.name_th)}</text>`;
    if (h > 52 && stat)
      s += `<text class="${dc}" x="${x+9}" y="${y+38}" fill="#fff" font-size="${treemapStatFs(w, stat)}"
             opacity=".95" ${SH} data-group="${d.product_group}" ${tip(t)}>${stat}</text>`;
    else if (h > 40)
      s += `<text class="${dc}" x="${x+9}" y="${y+h-8}" fill="#fff" font-size="14"
             opacity=".95" ${SH} data-group="${d.product_group}" ${tip(t)}>${fmt(d.share_pct,1)}%</text>`;
    return s;
  }
  if (w <= 74 || h <= 26) return s;
  const titleFs = big ? 21 : (w > 100 ? 17.5 : 16);
  const title = w > 132 ? `${esc(d.name_th)} (${d.product_group})`
              : w > 82 ? esc(d.name_th) : d.product_group;
  s += `<text class="hit${dim}" x="${x+11}" y="${y+22}" fill="#fff" ${SH}
         font-size="${titleFs}" font-weight="700"
         data-group="${d.product_group}" ${tip(t)}>${title}</text>`;
  if (h > 46 && w > 78 && stat){
    const statFs = treemapStatFs(w, stat);
    const statY = h > 58 ? y + 42 : y + h - 10;
    s += `<text class="${dc}" x="${x+11}" y="${statY}" fill="#fff" font-size="${statFs}"
           opacity=".95" ${SH} data-group="${d.product_group}" ${tip(t)}>${stat}</text>`;
  } else if (h > 32 && w > 55 && stat){
    s += `<text class="${dc}" x="${x+11}" y="${y+h-7}" fill="#fff" font-size="14"
           opacity=".92" ${SH} data-group="${d.product_group}" ${tip(t)}>${stat}</text>`;
  }
  return s;
}

function renderTreemap(){
  const W = 420, H = 300, items = shareForPeriod(periodTreemap);
  const rects = squarify(items.map(d => d.trade_value_mb), 0, 0, W, H);
  const SH = 'style="text-shadow:0 1px 3px rgba(0,0,0,.35)"';
  const clips = rects.map(([x,y,w,h], i) =>
    `<clipPath id="tmC${i}"><rect x="${x+1.5}" y="${y+1.5}" width="${Math.max(w-3,0)}" height="${Math.max(h-3,0)}" rx="4"/></clipPath>`
  ).join("");
  const s = rects.map(([x,y,w,h], i) => {
    const d = items[i], col = (DATA.groups.find(g => g.code === d.product_group) || {}).color || NAVY;
    const dim = selected !== "ALL" && selected !== d.product_group ? " dim" : "";
    const t = `${d.name_th} (${d.product_group})\n${fmt(d.trade_value_mb)} ล้านบาท · ${fmt(d.share_pct,1)}%`;
    let inner = `<rect class="hit${dim}" x="${x+1.5}" y="${y+1.5}"
                  width="${Math.max(w-3,0)}" height="${Math.max(h-3,0)}" rx="4"
                  fill="${col}" data-group="${d.product_group}" ${tip(t)}/>`;
    inner += treemapCellText(x, y, w, h, d, dim, t, SH, W, H);
    return `<g clip-path="url(#tmC${i})">${inner}</g>`;
  }).join("");
  document.getElementById("treemap").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet"><defs>${clips}</defs>${s}</svg>`;
  document.getElementById("shareCap").textContent = isRealDataMode()
    ? `มูลค่าการค้ารวม (นำเข้า+ส่งออก) ${periodTreemap ? periodTreemap.from + " ถึง " + periodTreemap.to : "สะสมทั้งช่วงข้อมูล"}`
    : `มูลค่าการค้ารวม (นำเข้า+ส่งออก) ปีงบประมาณ ${DATA.meta.fyComplete}`;
}

/* ── ส่วนที่ 4: อันดับการเติบโต ──────────────────────────────────── */
// เปรียบเทียบมูลค่าการค้า (นำเข้า+ส่งออก) N เดือนล่าสุด กับ N เดือนก่อนหน้านั้น
// (คนละก้อนกัน ไม่ทับซ้อน) ต่อกลุ่ม — แทนที่ CAGR 3 ปีตายตัวเดิม ด้วยช่วงที่เลือกได้จริง
// period="ALL" ไม่มี "ช่วงก่อนหน้า" ให้เทียบ คืน null ไปเลย (ให้ fallback ไปโชว์จำนวน
// ผู้ประกอบการแทน) เช่นเดียวกับกรณีข้อมูลย้อนหลังไม่พอ (< 2 เท่าของ N เดือน)
function growthForPeriod(period){
  if (!period) return null;
  // ตัดเดือนปัจจุบันที่ยังไม่จบออกก่อนเสมอ (ดู completeMonths()) ไม่งั้นถ้าช่วงที่
  // เลือกดันไปชนเดือนล่าสุดที่ยังไม่จบพอดี จะได้ % เติบโตติดลบหลอก ๆ ทุกกลุ่ม
  const months = completeMonths();
  const inRange = months.filter(m => m >= period.from && m <= period.to);
  const n = inRange.length;
  const startIdx = months.indexOf(inRange[0]);
  if (n === 0 || startIdx < n) return null;   // ไม่มีช่วงก่อนหน้ายาวพอให้เทียบ
  const recentSet = new Set(inRange);
  const priorSet = new Set(months.slice(startIdx - n, startIdx));
  const sums = {};
  DATA.groups.forEach(g => sums[g.code] = {recent: 0, prior: 0});
  DATA.byGroup.forEach(r => {
    if (!(r.g in sums)) return;
    if (recentSet.has(r.m)) sums[r.g].recent += r.im + r.ex;
    else if (priorSet.has(r.m)) sums[r.g].prior += r.im + r.ex;
  });
  const out = {};
  Object.keys(sums).forEach(g => {
    const {recent, prior} = sums[g];
    out[g] = prior > 0 ? (recent - prior) / prior * 100 : 0;
  });
  return out;
}

function renderCagr(){
  const real = isRealDataMode();
  const growth = real ? growthForPeriod(periodCagr) : null;
  const titleEl = document.getElementById("cagrTitle");
  const W = 420, rowH = 36, L = 152, R = 48, barH = rowH - 15;

  if (real && !growth){
    // *** เลือก "ทั้งหมด" (ไม่มีช่วงก่อนหน้าให้เทียบ) หรือข้อมูลย้อนหลังไม่พอสำหรับ
    // ช่วงที่เลือก — โชว์ "จำนวนผู้ประกอบการที่ยังดำเนินการ" ต่อกลุ่มแทนไปก่อน เป็นค่า
    // ณ ปัจจุบัน ไม่ต้องเทียบย้อนหลังเลย จึงมีให้ดูได้เสมอ ***
    if (titleEl) titleEl.textContent = "อันดับกลุ่มผลิตภัณฑ์ตามจำนวนผู้ประกอบการที่ยังดำเนินการ";
    const items = DATA.cagr.slice().sort((a,b) => b.active_entity_count - a.active_entity_count);
    const H = items.length * rowH + 8;
    const max = Math.max(...items.map(d => d.active_entity_count)) || 1;
    const s = items.map((d,i) => {
      const y = i * rowH + 6, bw = Math.max((d.active_entity_count / max) * (W - L - R), 3);
      const col = (DATA.groups.find(g => g.code === d.product_group) || {}).color || NAVY;
      const dim = selected !== "ALL" && selected !== d.product_group ? " dim" : "";
      const t = `${d.name_th} (${d.product_group})\nผู้ประกอบการที่ยังดำเนินการ ${fmt(d.active_entity_count)} ราย`;
      return `<text class="axis" x="${L-11}" y="${y+barH/2+5}" text-anchor="end"
               style="fill:#16222E;font-size:24px;font-weight:700">${esc(d.name_th)} (${d.product_group})</text>
        <rect x="${L}" y="${y}" width="${W-L-R}" height="${barH}" rx="4" fill="#F1F4F8"/>
        <rect class="hit${dim}" x="${L}" y="${y}" width="${bw}" height="${barH}" rx="4"
         fill="${col}" data-group="${d.product_group}" ${tip(t)}/>
        <text class="barlbl" x="${L+bw+8}" y="${y+barH/2+5}">${fmt(d.active_entity_count)}</text>`;
    }).join("");
    document.getElementById("cagrChart").innerHTML =
      `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${s}</svg>`;
    document.getElementById("cagrCap").textContent = !periodCagr
      ? `จำนวนผู้ประกอบการที่ยังดำเนินการ ณ ${DATA.meta.asOf} — เลือกช่วงเวลา (ปุ่มกรวย) เพื่อดูอัตราการเติบโตแทน`
      : `ข้อมูลย้อนหลังก่อนช่วงที่เลือกยังไม่พอเทียบ — โชว์จำนวนผู้ประกอบการแทนไปก่อน`;
    return;
  }

  if (titleEl) titleEl.textContent = "อันดับกลุ่มผลิตภัณฑ์ตามอัตราการเติบโต";
  const items = (real
    ? DATA.cagr.map(d => ({...d, cagr_3y_pct: growth[d.product_group] || 0}))
    : DATA.cagr.slice()
  ).sort((a,b) => b.cagr_3y_pct - a.cagr_3y_pct);
  const H = items.length * rowH + 8;
  // แท่งแบบ diverging จากเส้นศูนย์ — บวกยื่นขวา ลบยื่นซ้าย แทนที่จะยื่นทิศเดียวกันแล้ว
  // เปลี่ยนแค่สี (ของเดิมทำให้ดูไม่ออกว่าอันไหนโต/หดจริง ต้องอ่านเครื่องหมาย +/- เอา)
  // ข้อมูลมอคเป็นบวกเสมอ (maxNeg=0) → zeroX ตกที่ L พอดี หน้าตาจะเหมือนแท่งทางเดียวเดิม
  // เผื่อ LBL_PAD ไว้ทั้ง 2 ฝั่งเสมอ กันป้าย % ของแท่งที่ยาวสุดชนชื่อกลุ่ม/ขอบกราฟ
  const LBL_PAD = 80;
  const barAreaW = W - L - R;
  const drawW = Math.max(barAreaW - LBL_PAD, barAreaW * 0.5);
  const maxPos = Math.max(0, ...items.map(d => d.cagr_3y_pct));
  const maxNeg = Math.max(0, ...items.map(d => -d.cagr_3y_pct));
  const totalRange = (maxPos + maxNeg) || 1;
  const zeroX = L + LBL_PAD / 2 + drawW * (maxNeg / totalRange);
  const s = items.map((d,i) => {
    const y = i * rowH + 6;
    const neg = d.cagr_3y_pct < 0;
    const bw = d.cagr_3y_pct === 0 ? 0
             : Math.max((Math.abs(d.cagr_3y_pct) / totalRange) * drawW, 3);
    const barX = neg ? zeroX - bw : zeroX;
    const col = neg ? BAD : ((DATA.groups.find(g => g.code === d.product_group) || {}).color || NAVY);
    const dim = selected !== "ALL" && selected !== d.product_group ? " dim" : "";
    const sign = d.cagr_3y_pct > 0 ? "+" : "";
    const growthLabel = real ? `เติบโต ${periodCagr.from} ถึง ${periodCagr.to}` : "CAGR 3 ปี";
    const t = `${d.name_th} (${d.product_group})\n${growthLabel} ${sign}${fmt(d.cagr_3y_pct,1)}%`;
    const lblX = neg ? barX - 8 : barX + bw + 8;
    const anchor = neg ? "end" : "start";
    // รางสีอ่อนเต็มความกว้าง ช่วยให้เทียบสัดส่วนแท่งกับค่าสูงสุดได้ด้วยตา
    return `<text class="axis" x="${L-11}" y="${y+barH/2+5}" text-anchor="end"
             style="fill:#16222E;font-size:24px;font-weight:700">${esc(d.name_th)} (${d.product_group})</text>
      <rect x="${L}" y="${y}" width="${barAreaW}" height="${barH}" rx="4" fill="#F1F4F8"/>
      <rect class="hit${dim}" x="${barX}" y="${y}" width="${bw}" height="${barH}" rx="4"
       fill="${col}" data-group="${d.product_group}" ${tip(t)}/>
      <text class="barlbl" x="${lblX}" y="${y+barH/2+5}" text-anchor="${anchor}">${sign}${fmt(d.cagr_3y_pct,1)}%</text>`;
  }).join("");
  // เส้นศูนย์ — ต้องมีให้เห็นชัดว่า 0% อยู่ตรงไหน (โชว์เฉพาะตอนมีทั้งบวกและลบปนกัน)
  const zeroLine = maxNeg > 0
    ? `<line x1="${zeroX}" y1="2" x2="${zeroX}" y2="${H-2}" stroke="#B7C2CE" stroke-width="1.2"/>`
    : "";
  document.getElementById("cagrChart").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${s}${zeroLine}</svg>`;
  document.getElementById("cagrCap").textContent = real
    ? `% เติบโตของมูลค่าการค้า ${periodCagr.from} ถึง ${periodCagr.to}`
    : `CAGR 3 ปี (${DATA.meta.fyComplete-3}–${DATA.meta.fyComplete})`;
}

/* ── ส่วนที่ 5: ประเทศคู่ค้าสำคัญ ────────────────────────────────── */
function countryData(){
  if (selected === "ALL")
    return DATA.country.map(d => ({name: d.country_name_th, value: d.import_value_mb}));
  return DATA.countryByGroup
    .filter(d => d.product_group === selected && d.country_name_th !== "อื่น ๆ")
    .map(d => ({name: d.country_name_th, value: d.import_value_mb}))
    .sort((a,b) => b.value - a.value).slice(0,6);
}

function renderCountry(){
  const items = countryData();
  const W = 620, H = 300, P = {t:30, b:36, l:10, r:10};
  const bw = (W - P.l - P.r) / items.length, max = Math.max(...items.map(d => d.value));
  const pal = ["#1F6FB2","#12A594","#3E9F55","#E8A317","#7E57C2","#C0392B"];
  const base = H - P.b, R = 5;
  let defs = "";
  const s = items.map((d,i) => {
    const h = (d.value / max) * (H - P.t - P.b);
    const x = P.l + i*bw + bw*0.19, w = bw*0.62, y = base - h, cx = x + w/2;
    const c = pal[i % pal.length], id = "cg" + i;
    const t = `${d.name}\nมูลค่านำเข้า ${fmt(d.value)} ล้านบาท`;
    defs += `<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${c}"/><stop offset="1" stop-color="${c}" stop-opacity=".72"/>
      </linearGradient>`;
    // มนเฉพาะมุมบน ฐานแท่งต้องชิดเส้นแกนสนิทเพื่อให้เทียบความสูงได้ตรง
    const r = Math.min(R, h);
    const path = `M${x},${base} V${y+r} Q${x},${y} ${x+r},${y} H${x+w-r}`
               + ` Q${x+w},${y} ${x+w},${y+r} V${base} Z`;
    return `<path class="hit" d="${path}" fill="url(#${id})" ${tip(t)}/>
      <text class="barlbl" x="${cx}" y="${y-9}" text-anchor="middle">${fmt(d.value)}</text>
      <text class="axis" x="${cx}" y="${base+21}" text-anchor="middle"
       style="fill:#16222E;font-size:24px;font-weight:700">${esc(d.name)}</text>`;
  }).join("");
  const axis = `<line x1="${P.l}" y1="${base}" x2="${W-P.r}" y2="${base}"
                 stroke="#C6D1DE" stroke-width="1.4"/>`;
  document.getElementById("countryChart").innerHTML =
    `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">
       <defs>${defs}</defs>${axis}${s}</svg>`;
  document.getElementById("countryCap").textContent = isRealDataMode()
    ? "มูลค่านำเข้าสูงสุด 6 อันดับแรก สะสมทั้งช่วงข้อมูล"
    : `มูลค่านำเข้าสูงสุด 6 อันดับแรก ปีงบประมาณ ${DATA.meta.fyComplete}`;
}

/* ── ส่วนที่ 6: สถานะข้อมูล ───────────────────────────────────────── */
function healthParts(h){
  const sub = h.detail_th || h.detail || "";
  if(h.display_text != null && h.display_text !== "")
    return {main: String(h.display_text), sub};
  if(h.value != null && h.value !== "" && !isNaN(h.value)){
    const u = h.unit || "";
    if(u.startsWith("% (") || u.startsWith("%(")){
      const inner = u.replace(/^%\s*\(/, "").replace(/\)\s*$/, "");
      return {main: fmt(h.value, 1) + "%", sub: sub || inner};
    }
    if(u === "%") return {main: fmt(h.value, 1) + "%", sub};
    return {main: fmt(h.value, 1) + u, sub};
  }
  let u = h.unit || "—";
  if(u.startsWith("ข้อมูล ณ ")){
    const d = u.slice("ข้อมูล ณ ".length).trim();
    u = d || (DATA.meta && DATA.meta.asOf) || "—";
  }
  return {main: u, sub};
}
function renderHealth(){
  document.getElementById("healthBody").innerHTML = DATA.health.map(h => {
    const ok = h.status === "ปกติ";
    const col = ok ? GOOD : WARN;
    const {main, sub} = healthParts(h);
    const t = `${h.metric_name_th}\n${main}${sub ? "\n" + sub : ""}\nสถานะ: ${h.status}`;
    const subHtml = sub ? `<div class="hrSub">${esc(sub)}</div>` : "";
    return `<tr class="healthRow" ${tip(t)}>
      <td colspan="2">
        <div class="hrLabel">
          <span class="st" style="background:${col};box-shadow:0 0 0 3px ${ok?GOOD_TINT:WARN_TINT}"></span>
          ${esc(h.metric_name_th)}</div>
        <div class="hrVal" style="color:${col}">${esc(main)}</div>${subHtml}
      </td></tr>`;
  }).join("");
}

/* ── ตัวกรอง ─────────────────────────────────────────────────────── */
function renderChips(){
  const mk = (code, name, color) =>
    `<button class="chip" data-group="${code}" aria-pressed="${selected===code}">
      ${color ? `<span class="dot" style="background:${color}"></span>` : ""}${esc(name)}</button>`;
  document.getElementById("chips").innerHTML =
    mk("ALL", "ทั้งหมด", null) + DATA.groups.map(g => mk(g.code, g.name, g.color)).join("");
}

function setGroup(g){
  selected = (g === selected && g !== "ALL") ? "ALL" : g;
  renderAll();
}

function renderAll(){
  renderChips(); renderKpis(); renderTrend();
  renderTreemap(); renderCagr(); renderCountry(); renderHealth();
  syncPeriodPickers();
}

/* ── tooltip + คลิกกรอง ──────────────────────────────────────────── */
const tipEl = document.getElementById("tip");
document.addEventListener("mousemove", e => {
  const el = e.target.closest("[data-tip]");
  if (!el){ tipEl.style.opacity = 0; return; }
  tipEl.innerHTML = esc(el.getAttribute("data-tip")).replace(/\n/g, "<br>");
  tipEl.style.opacity = 1;
  const r = tipEl.getBoundingClientRect();
  tipEl.style.left = Math.min(e.clientX + 14, innerWidth - r.width - 10) + "px";
  tipEl.style.top  = Math.max(e.clientY - r.height - 12, 8) + "px";
});
document.addEventListener("click", e => {
  const el = e.target.closest("[data-group]");
  if (el) setGroup(el.getAttribute("data-group"));
});

const TH_MONTH_ABBR_HDR = ["ม.ค.","ก.พ.","มี.ค.","เม.ย.","พ.ค.","มิ.ย.","ก.ค.","ส.ค.","ก.ย.","ต.ค.","พ.ย.","ธ.ค."];
function formatThaiDateToday(){
  const d = new Date();
  return d.getDate() + " " + TH_MONTH_ABBR_HDR[d.getMonth()] + " " + (d.getFullYear() + 543);
}
function renderHeaderAsOf(){
  const el = document.getElementById("asOf");
  if (el) el.textContent = formatThaiDateToday();
}
renderHeaderAsOf();
populateYearMonthFilters();
renderAll();
</script>
</body>
</html>
"""

# ── ฟอนต์ที่ฝังในหน้าจอ ─────────────────────────────────────────────────────
# TH Sarabun New ตัวปกติ + ตัวหนา (ฟอนต์แห่งชาติ SIPA, GPL + font exception แจกจ่ายได้) แปลงเป็น
# WOFF2 แบบไม่เสียคุณภาพ — ไม่ฝังตัวเอียงเพราะหน้าจอไม่ได้ใช้
# เหตุผล: เครื่องที่ไม่ได้ติดตั้งฟอนต์นี้ เบราว์เซอร์จะใช้ฟอนต์สำรองที่ตัวใหญ่กว่ามากที่ px เท่ากัน
# ข้อความจึงล้นกรอบ/ตัดบรรทัดผิดที่ • @font-face ตั้งชื่อเดียวกับใน CSS ของมอค จึงถูกใช้แทนฟอนต์
# ในเครื่องเสมอ ทุกเครื่องเห็นเหมือนกัน โดยไม่ต้องแก้ TEMPLATE
_FONT_REGULAR_WOFF2_B64 = (
    "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"
)
_FONT_BOLD_WOFF2_B64 = (
    "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"
)


def embed_fonts(html: str, redraw_js: str | None = None) -> str:
    """แทรก @font-face ก่อน </head> — redraw_js = ชื่อฟังก์ชัน JS ที่วาดกราฟ canvas ใหม่หลังฟอนต์พร้อม"""
    faces = "".join(
        f'@font-face{{font-family:"TH Sarabun New";font-style:normal;font-weight:{weight};'
        f'font-display:block;src:url(data:font/woff2;base64,{b64}) format("woff2")}}'
        for weight, b64 in ((400, _FONT_REGULAR_WOFF2_B64), (700, _FONT_BOLD_WOFF2_B64)))
    assert html.count("</head>") == 1 and html.count("</body>") == 1, "โครง TEMPLATE เปลี่ยน — หา </head>/</body> ไม่เจอ"
    html = html.replace("</head>", f"<style>{faces}</style>\n</head>")
    if redraw_js:
        # Chart.js วาดลง canvas ตอนโหลดหน้า ซึ่งอาจเกิดก่อนฟอนต์ถอดรหัสเสร็จ → วาดใหม่อีกรอบ
        html = html.replace("</body>", (
            '<script>document.fonts && Promise.all(["400", "700"].map(w => '
            'document.fonts.load(w + \' 20px "TH Sarabun New"\'))).then(() => '
            f'{{ if (typeof {redraw_js} === "function") {redraw_js}(); }});</script>\n</body>'))
    return html


# ── ตัวช่วยทั่วไป ─────────────────────────────────────────────────────────
def fiscal_year(ts: pd.Timestamp) -> int:
    """ปีงบประมาณ (พ.ศ.) — ต.ค. ขึ้นปีงบประมาณใหม่"""
    return ts.year + 543 + (1 if ts.month >= 10 else 0)


def month_label(ts: pd.Timestamp) -> str:
    return f"{TH_MONTH_ABBR[ts.month - 1]} {ts.year + 543}"


def _rounded(values, ndigits: int = 1) -> list:
    """list สำหรับ JSON — NaN เป็น None (json ไม่รับ NaN)"""
    return [None if pd.isna(v) else round(float(v), ndigits) for v in values]


# ── อ่านพอร์ต ─────────────────────────────────────────────────────────────
def input_port(port: int, label: str) -> pd.DataFrame:
    """เอาตารางจาก input port — error ทันทีถ้ายังไม่ได้ต่อสาย"""
    tables = getattr(knio, "input_tables", None) or []
    if len(tables) <= port or tables[port] is None:
        raise RuntimeError(
            f"ยังไม่ได้ต่อสายเข้า input port {port} ({label}) — "
            f"กดปุ่ม + ที่โหนดนี้เพิ่ม port แล้วลากเส้นจากปลายสาย {label} มาต่อ")
    df = tables[port].to_pandas()
    print(f"port {port} ({label}): {len(df):,} แถว")
    return df


def prep_trade(df: pd.DataFrame) -> pd.DataFrame:
    """ใช้มูลค่านำเข้าจาก "ศุลกากร" เป็นตัวหลัก ไม่ใช่จาก อย.

    ไฟล์มีมูลค่านำเข้า 2 ชุด ต่างกันราว 25 เท่า (อย. เก็บเฉพาะใบขนที่ผ่านระบบตัวเอง)
    ดุลการค้าต้องเทียบกับส่งออกจากแหล่งเดียวกัน ไม่งั้นจะได้ "เกินดุล" ซึ่งผิดความจริง
    """
    df = df.rename(columns={"GROUP_CD": "product_group", "Period_month": "period_month",
                            "import_value_thb": "import_fda_thb",
                            "import_value_thb (Right)": "import_value_thb"})
    df["period_month"] = pd.to_datetime(df["period_month"].astype(str) + "-01")
    df["trade_balance_thb"] = df["export_value_thb"] - df["import_value_thb"]
    return df[["period_month", "product_group", "import_value_thb",
               "export_value_thb", "trade_balance_thb", "import_fda_thb"]]


def prep_stock(df: pd.DataFrame, value_name: str) -> pd.DataFrame:
    """ยอดสะสมรายกลุ่ม × เดือน — แถวที่ PERIOD_FINAL ว่างวางบนแกนเวลาไม่ได้จึงตัดออก"""
    df = df[df["PERIOD_FINAL"].notna()].copy()
    df["period_month"] = pd.to_datetime(df["PERIOD_FINAL"].astype(str) + "-01")
    df = df.rename(columns={"GROUP_CD_FINAL": "product_group", "backlog": value_name})
    df = df[["period_month", "product_group", value_name]]
    return df.groupby(["product_group", "period_month"], as_index=False)[value_name].last()


def country_name_th(code, name_en) -> str:
    if isinstance(code, str) and code in COUNTRY_NAME_TH:
        return COUNTRY_NAME_TH[code]
    if isinstance(name_en, str) and name_en.strip():
        return name_en.strip().title()
    return UNKNOWN_COUNTRY_TH


def prep_country(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """คืน (top 6 ประเทศรวมทุกกลุ่ม พร้อม rank, มูลค่านำเข้ารายกลุ่ม × ประเทศ)"""
    df = df.rename(columns={"GROUP_CD": "product_group"})
    df["country_name_th"] = [
        country_name_th(c, n) for c, n in zip(df["CountryCode"], df["CountryName"])]
    df["import_value_mb"] = df["import_value_thb"] / MB

    country_by_group = (df.groupby(["product_group", "country_name_th"], as_index=False)
                          ["import_value_mb"].sum()
                          .sort_values(["product_group", "import_value_mb"],
                                       ascending=[True, False]))

    overall = (df.groupby("country_name_th", as_index=False)["import_value_mb"].sum()
                 .sort_values("import_value_mb", ascending=False)
                 .head(6).reset_index(drop=True))
    overall.insert(0, "rank", overall.index + 1)
    return overall, country_by_group


# ── แนวโน้ม + พยากรณ์ ──────────────────────────────────────────────────────
def _sarimax_forecast(y: pd.Series, steps: int) -> pd.DataFrame:
    """พยากรณ์รายเดือน SARIMAX(1,1,1)(1,1,1,12) ช่วงเชื่อมั่น 80% — fit ไม่ได้ถอยไปใช้แนวโน้ม+ฤดูกาล"""
    idx = pd.date_range(y.index[-1] + pd.DateOffset(months=1), periods=steps, freq="MS")
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        res = SARIMAX(y, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12),
                      enforce_stationarity=False,
                      enforce_invertibility=False).fit(disp=False)
        fc = res.get_forecast(steps=steps)
        ci = fc.conf_int(alpha=0.20)
        return pd.DataFrame({"yhat": fc.predicted_mean.to_numpy(),
                             "lo": ci.iloc[:, 0].to_numpy(),
                             "hi": ci.iloc[:, 1].to_numpy()}, index=idx)
    except Exception as e:
        print(f"[เตือน] SARIMAX ใช้ไม่ได้ ({e}) — ถอยไปใช้แนวโน้มเชิงเส้น")
        t = np.arange(len(y))
        slope, intercept = np.polyfit(t, y.to_numpy(), 1)
        resid = y.to_numpy() - (slope * t + intercept)
        base = slope * np.arange(len(y), len(y) + steps) + intercept
        yhat = base + np.resize(resid[-12:], steps)
        sd = float(np.std(resid))
        return pd.DataFrame({"yhat": yhat, "lo": yhat - 1.28 * sd,
                             "hi": yhat + 1.28 * sd}, index=idx)


def _trend_actual_only(detail: pd.DataFrame, fy_first: int) -> pd.DataFrame:
    """ยอดรวมรายปีงบประมาณจากข้อมูลจริงเท่านั้น (ไม่มีพยากรณ์)"""
    fy_flow = (detail.groupby("fy")[
        ["import_value_thb", "export_value_thb", "trade_balance_thb"]].sum() / MB)
    fy_flow = fy_flow[fy_flow.index >= fy_first]
    # ต่อแถวลงล่าง (ไม่ใช่ axis=1 แบบ v5 ที่ได้คอลัมน์ซ้ำ แล้วพังตอนข้อมูลน้อยกว่า 24 เดือน)
    trend = pd.concat([
        fy_flow[[c]].rename(columns={c: "value_mb"}).assign(series=s)
        for s, c in (("import", "import_value_thb"), ("export", "export_value_thb"),
                     ("balance", "trade_balance_thb"))
    ]).reset_index()
    trend["is_forecast"] = False
    trend["ci_lower_mb"] = np.nan
    trend["ci_upper_mb"] = np.nan
    return trend


def _build_trend_with_forecast(detail: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """แนวโน้มรายปีงบประมาณ + พยากรณ์ส่วนที่เหลือของปีงบประมาณที่กำลังเดิน (ระดับรวมประเทศ)

    คืน (trend, ปีงบประมาณล่าสุดที่ครบ 12 เดือน) — ข้อมูลน้อยกว่า 24 เดือน fit SARIMAX ไม่ได้
    จึงคืนเฉพาะข้อมูลจริง
    """
    monthly = (detail.groupby("period_month")[["import_value_thb", "export_value_thb"]]
               .sum().sort_index())
    as_of_month = monthly.index.max()
    months_per_fy = detail.groupby("fy")["period_month"].nunique()
    if (months_per_fy >= 12).any():
        fy_complete = int(months_per_fy[months_per_fy >= 12].index.max())
    else:
        fy_complete = int(detail["fy"].max())
    fy_first = fy_complete - TREND_DISPLAY_YEARS + 2

    fy_current_end = pd.Timestamp(year=fy_complete + 1 - 543, month=9, day=1)
    forecast_months = max(0, (fy_current_end.year - as_of_month.year) * 12
                          + fy_current_end.month - as_of_month.month)
    if len(monthly) < 24 or forecast_months <= 0:
        return _trend_actual_only(detail, fy_first), fy_complete

    trend_rows = []
    for col, series_name in (("import_value_thb", "import"),
                             ("export_value_thb", "export")):
        y = monthly[col] / MB
        fc = _sarimax_forecast(y, forecast_months)
        full = pd.concat([y.rename("yhat").to_frame().assign(lo=np.nan, hi=np.nan), fc])
        full["fy"] = full.index.year + 543 + (full.index.month >= 10).astype(int)
        full["is_fc"] = np.r_[np.zeros(len(y), bool), np.ones(len(fc), bool)]
        full["lo"] = full["lo"].fillna(full["yhat"])
        full["hi"] = full["hi"].fillna(full["yhat"])
        agg = full.groupby("fy").agg(value_mb=("yhat", "sum"), lo_mb=("lo", "sum"),
                                     hi_mb=("hi", "sum"), n_fc=("is_fc", "sum"))
        agg = agg[agg.index >= fy_first]
        for fy, r in agg.iterrows():
            trend_rows.append(dict(
                fy=int(fy), series=series_name, value_mb=float(r["value_mb"]),
                is_forecast=bool(r["n_fc"] > 0),
                ci_lower_mb=float(r["lo_mb"]) if r["n_fc"] else np.nan,
                ci_upper_mb=float(r["hi_mb"]) if r["n_fc"] else np.nan,
            ))

    trend = pd.DataFrame(trend_rows)
    if trend.empty:
        return _trend_actual_only(detail, fy_first), fy_complete

    bal = trend.pivot(index="fy", columns="series", values="value_mb")
    bal = bal.assign(series="balance", value_mb=bal["export"] - bal["import"]).reset_index()
    bal = bal.merge(trend[trend.series == "import"][["fy", "is_forecast"]], on="fy")
    bal["ci_lower_mb"] = np.nan
    bal["ci_upper_mb"] = np.nan
    trend = pd.concat([
        trend,
        bal[["fy", "series", "value_mb", "is_forecast", "ci_lower_mb", "ci_upper_mb"]],
    ], ignore_index=True).sort_values(["series", "fy"])
    return trend, fy_complete


def cagr_3y_by_group(trade: pd.DataFrame) -> tuple[dict[str, float], bool]:
    """CAGR 3 ปีของมูลค่าการค้า (นำเข้า+ส่งออก) ต่อกลุ่ม คืน (ค่าต่อกลุ่ม, คำนวณได้หรือไม่)

    ใช้ประวัติการค้าเต็มจากพอร์ต (ไม่ตัดหน้าต่างเหมือน detail) และต้องมีปีงบประมาณที่ครบ
    12 เดือน 2 ปีห่างกัน 3 ปี — ไม่ครบคืน 0 ทุกกลุ่ม ถ้าผลเป็น 0 ตลอด ให้เช็ค Joiner (#68)
    ในเวิร์กโฟลว์: ถ้ายัง INNER JOIN อยู่ แถวศุลกากรปีเก่าที่ไม่มีคู่ฝั่ง อย. จะหายตั้งแต่ต้นทาง
    """
    t = trade.assign(fy=trade["period_month"].map(fiscal_year),
                     trade_value_thb=trade["import_value_thb"] + trade["export_value_thb"])
    months_per_fy = t.groupby("fy")["period_month"].nunique()
    complete_fys = sorted(months_per_fy[months_per_fy >= 12].index)
    if len(complete_fys) < 4 or (complete_fys[-1] - 3) not in complete_fys:
        return {g: 0.0 for g in GROUPS}, False

    fy_end, fy_start = complete_fys[-1], complete_fys[-1] - 3
    totals = t.groupby(["product_group", "fy"])["trade_value_thb"].sum()
    out = {}
    for g in GROUPS:
        v_end, v_start = totals.get((g, fy_end)), totals.get((g, fy_start))
        out[g] = (round(((v_end / v_start) ** (1 / 3) - 1) * 100, 2)
                  if v_end and v_start and v_start > 0 else 0.0)
    return out, True


def _kpi(code: str, name_th: str, value: float, basis: str,
         drill_to: str | None = "หน้าจอที่ 2") -> dict:
    return dict(kpi_code=code, kpi_name_th=name_th, value=value, unit="ล้านบาท",
                yoy_pct=0.0, higher_is_better=True, basis=basis, drill_to=drill_to)


# ── ประกอบ JSON + HTML ────────────────────────────────────────────────────
def _payload(kpi, spark, trend, share, cagr, country, health,
             by_group, country_by_group, as_of_label, fy_complete, has_cagr) -> dict:
    spark = spark.assign(period_month=pd.to_datetime(spark["period_month"]))
    sparks = {code: g.sort_values("period_month")["value"].round(2).tolist()
              for code, g in spark.groupby("kpi_code")}

    fys = sorted(trend.fy.unique())
    series = []
    for name in ("import", "export", "balance"):
        d = trend[trend.series == name].set_index("fy").reindex(fys)
        series.append({"key": name,
                       "values": _rounded(d.value_mb),
                       "isFc": [bool(x) for x in d.is_forecast.fillna(False)],
                       "lo": _rounded(d.ci_lower_mb),
                       "hi": _rounded(d.ci_upper_mb)})

    # ชื่อคอลัมน์สั้นลง — byGroup มีหลายร้อยแถว ฝั่ง JS อ่านด้วยคีย์เหล่านี้
    detail = by_group.assign(m=pd.to_datetime(by_group["period_month"]).dt.strftime("%Y-%m"))
    detail = detail[["m", "fy", "product_group", "import_value_mb", "export_value_mb",
                     "trade_balance_mb", "product_stock", "active_entity", "backlog",
                     "production_value_mb"]]
    detail.columns = ["m", "fy", "g", "im", "ex", "bal", "ps", "ae", "bl", "pv"]
    for c in ("im", "ex", "bal", "pv"):
        detail[c] = detail[c].round(2)

    return {
        "meta": {"asOf": as_of_label, "fyComplete": int(fy_complete),
                 "fys": [int(f) for f in fys], "hasCagr": bool(has_cagr),
                 "crossFilter": len(detail) > 0},
        "groups": [{"code": c, "name": GROUP_NAME_TH.get(c, c),
                    "color": GROUP_COLOR.get(c, "#12305B")}
                   for c in share.product_group],
        "kpi": kpi.assign(value=kpi.value.round(1), yoy_pct=kpi.yoy_pct.round(1))
                  .to_dict("records"),
        "sparks": sparks,
        "trend": series,
        "share": share.round(2).to_dict("records"),
        "cagr": cagr.round(2).to_dict("records"),
        "country": country.round(1).to_dict("records"),
        "countryByGroup": country_by_group.round(1).to_dict("records"),
        "health": health.replace({np.nan: None}).to_dict("records"),
        "byGroup": detail.to_dict("records"),
    }


def build_html(kpi, spark, trend, share, cagr, country, health,
               by_group, country_by_group, as_of_label: str,
               fy_complete: int, has_cagr: bool) -> str:
    data = _payload(kpi, spark, trend, share, cagr, country, health,
                    by_group, country_by_group, as_of_label, fy_complete, has_cagr)
    html = embed_fonts(TEMPLATE).replace("/*__PAYLOAD__*/null",
                            json.dumps(data, ensure_ascii=False, allow_nan=False))
    return html.replace("__FDA_LOGO_SRC__", FDA_LOGO_SRC)


# ══ เริ่มทำงาน ═════════════════════════════════════════════════════════════
trade = prep_trade(input_port(0, "มูลค่านำเข้า-ส่งออก"))
prod = prep_stock(input_port(1, "ผลิตภัณฑ์ที่ได้รับอนุญาต"), "product_stock")
ent = prep_stock(input_port(2, "ผู้ประกอบการ"), "active_entity")
app = prep_stock(input_port(3, "คำขอคงค้าง"), "backlog")
country, country_by_group = prep_country(input_port(4, "ประเทศต้นทาง"))

# ── แกนเวลา ──
# รวมเดือนจากทั้ง 4 สาย: แต่ละสายมาจากคนละตาราง ช่วงเวลาไม่เท่ากัน ถ้ายึดสายการค้าสายเดียว
# เดือนของสายที่ยาวกว่าจะหายตอน merge • ตัดด้วยหน้าต่างย้อนหลังจากเดือนนี้ กันวันที่คีย์ผิด
# (เช่น EXP_DATE ปี 2033 หรือแถวเก่าหลุดมาเดี่ยว ๆ) ยืดแกนจนกราฟว่างเปล่า
all_dates = pd.concat([trade["period_month"], prod["period_month"],
                       ent["period_month"], app["period_month"]])
this_month = pd.Timestamp.now().normalize().replace(day=1)
window_start = this_month - pd.DateOffset(months=DASHBOARD_LOOKBACK_MONTHS)
months = sorted(all_dates[(all_dates >= window_start) & (all_dates <= this_month)].unique())
first_m, as_of = pd.Timestamp(months[0]), pd.Timestamp(months[-1])
# หัวข้อ "อัปเดตล่าสุด" ใช้วันที่รันจริง ส่วนตัวเลขทั้งหมดอิงเดือนล่าสุดในข้อมูล (as_of)
today = pd.Timestamp.now().normalize()
as_of_label = f"{today.day} {month_label(today)}"

# ── ตารางรายกลุ่ม × เดือน ──
grid = pd.MultiIndex.from_product(
    [months, GROUPS], names=["period_month", "product_group"]).to_frame(index=False)
detail = (grid.merge(trade, on=["period_month", "product_group"], how="left")
              .merge(prod, on=["period_month", "product_group"], how="left")
              .merge(ent, on=["period_month", "product_group"], how="left")
              .merge(app, on=["period_month", "product_group"], how="left"))

flow_cols = ["import_value_thb", "export_value_thb", "trade_balance_thb"]
detail[flow_cols] = detail[flow_cols].fillna(0.0)   # เดือนที่ไม่มีธุรกรรม = 0 จริง

# ยอดสะสมห้ามเติม 0 — เดือนที่ไม่มีแถว = ไม่มีเหตุการณ์ใหม่ ไม่ใช่ยอดหายเป็นศูนย์
# จึงลากค่าเดือนก่อนหน้ามาต่อแยกตามกลุ่ม ไม่งั้นกราฟดิ่งลง 0 ผิด ๆ
stock_cols = ["product_stock", "active_entity", "backlog"]
detail = detail.sort_values(["product_group", "period_month"])
detail[stock_cols] = detail.groupby("product_group")[stock_cols].ffill()
detail[stock_cols] = detail[stock_cols].fillna(0.0)   # ก่อนเดือนแรกที่กลุ่มนั้นมีข้อมูล
detail = detail.sort_values(["period_month", "product_group"]).reset_index(drop=True)
detail["fy"] = detail["period_month"].map(fiscal_year)

by_group = pd.DataFrame({
    "period_month": detail["period_month"], "fy": detail["fy"],
    "product_group": detail["product_group"],
    "import_value_mb": detail["import_value_thb"] / MB,
    "export_value_mb": detail["export_value_thb"] / MB,
    "trade_balance_mb": detail["trade_balance_thb"] / MB,
    "product_stock": detail["product_stock"],
    "active_entity": detail["active_entity"],
    "backlog": detail["backlog"],
    "production_value_mb": 0.0,   # ยังไม่มีแหล่งข้อมูลมูลค่าการผลิตรายกลุ่ม
})

# ── การ์ด KPI + sparkline ──
flow = detail[flow_cols].sum() / MB
basis_flow = f"รวม {len(months)} เดือน ({month_label(first_m)}–{month_label(as_of)})"
kpi = pd.DataFrame([
    _kpi("import_value", "มูลค่านำเข้าผลิตภัณฑ์สุขภาพ", flow["import_value_thb"], basis_flow),
    _kpi("export_value", "มูลค่าส่งออกผลิตภัณฑ์สุขภาพ", flow["export_value_thb"], basis_flow),
    _kpi("trade_balance", "ดุลการค้า", flow["trade_balance_thb"], basis_flow),
    # ใส่ 0 ไว้ก่อน — ยังไม่ยืนยันแหล่งข้อมูลมูลค่าการผลิตของ 7 กลุ่มผลิตภัณฑ์ อย.
    # (GDP ภาคการผลิตของ NESDC เป็นยอดรวมทุกอุตสาหกรรม ไม่ได้แยกเฉพาะผลิตภัณฑ์สุขภาพ)
    _kpi("production_value", "มูลค่าการผลิตภาคอุตสาหกรรม", 0.0, basis_flow, drill_to=None),
])

monthly = detail.groupby("period_month")[flow_cols + stock_cols].sum().sort_index()
spark = pd.concat([s.rename("value").reset_index().assign(kpi_code=k) for k, s in {
    "import_value": monthly["import_value_thb"] / MB,
    "export_value": monthly["export_value_thb"] / MB,
    "trade_balance": monthly["trade_balance_thb"] / MB,
    "product_stock": monthly["product_stock"],
    "active_entity": monthly["active_entity"],
    "backlog": monthly["backlog"],
}.items()], ignore_index=True)[["kpi_code", "period_month", "value"]]

# ── แนวโน้ม, สัดส่วน, อันดับ ──
trend, fy = _build_trend_with_forecast(detail)

group_trade = detail.groupby("product_group")[["import_value_thb", "export_value_thb"]].sum()
share = pd.DataFrame({
    "product_group": group_trade.index,
    "name_th": [GROUP_NAME_TH[x] for x in group_trade.index],
    "trade_value_mb": (group_trade["import_value_thb"]
                       + group_trade["export_value_thb"]).to_numpy() / MB})
tot = share["trade_value_mb"].sum()
share["share_pct"] = share["trade_value_mb"] / tot * 100 if tot else 0.0
share = share.sort_values("trade_value_mb", ascending=False).reset_index(drop=True)

cagr_by_group, has_cagr = cagr_3y_by_group(trade)
entity_by_group = detail[detail.period_month == as_of].set_index("product_group")["active_entity"]
cagr = pd.DataFrame({"product_group": share["product_group"],
                     "name_th": share["name_th"],
                     "cagr_3y_pct": [cagr_by_group.get(g, 0.0) for g in share["product_group"]],
                     "active_entity_count": entity_by_group.reindex(
                         share["product_group"]).fillna(0.0).to_numpy()})

# ── สถานะข้อมูล ──
completeness = float((detail[["import_value_thb", "product_stock",
                              "active_entity", "backlog"]] != 0).to_numpy().mean() * 100)
health = pd.DataFrame([
    dict(metric_code="completeness", metric_name_th="ความถูกต้องข้อมูล",
         value=round(completeness, 1), unit="%", detail_th=None, display_text=None,
         status="ปกติ" if completeness >= 95 else "เฝ้าระวัง"),
    dict(metric_code="coverage", metric_name_th="ช่วงข้อมูล",
         value=np.nan, unit=None, detail_th=None,
         display_text=f"{month_label(first_m)}–{month_label(as_of)}", status="ปกติ"),
    dict(metric_code="last_refresh", metric_name_th="อัปเดตล่าสุด",
         value=np.nan, unit=None, detail_th=None, display_text=as_of_label, status="ปกติ"),
])

# ── ส่งออกเป็นหน้าจอของโหนด Python View ──
html = build_html(kpi, spark, trend, share, cagr, country, health,
                  by_group, country_by_group, as_of_label, fy, has_cagr)
knio.output_view = knio.view_html(html)

print(f"เรนเดอร์แล้ว {len(html)/1024:.0f} KB — ข้อมูลจริง {len(months)} เดือน (ปีงบประมาณ {fy})")
for r in kpi.itertuples(index=False):
    print(f"   {r.kpi_name_th:<32} {r.value:>14,.0f} {r.unit}")
