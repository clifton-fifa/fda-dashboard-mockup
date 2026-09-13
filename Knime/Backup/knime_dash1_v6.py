"""หน้าจอที่ 1 — สคริปต์โหนด Python View ของ KNIME (ไฟล์เดียวจบ วางในโหนดได้ตรง ๆ)

knime_dash1_v6.py = knime_dash1_v5.py ที่จัดระเบียบส่วน Python แล้ว (TEMPLATE เหมือนเดิมทุกตัวอักษร)
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
    html = TEMPLATE.replace("/*__PAYLOAD__*/null",
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
