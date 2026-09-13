from __future__ import annotations

import json

import numpy as np
import pandas as pd

import knime.scripting.io as knio

GROUP_COLOR = {"DRUG": "#1F6FB2", "MDC": "#12A594", "FOOD": "#3E9F55",
               "CMT": "#E8A317", "HERB": "#7E57C2", "TXC": "#C0392B",
               "NCT": "#7F8C8D"}
GROUP_NAME_TH = {"DRUG": "ยา", "FOOD": "อาหาร", "MDC": "เครื่องมือแพทย์",
                 "CMT": "เครื่องสำอาง", "HERB": "สมุนไพร", "TXC": "วัตถุอันตราย",
                 "NCT": "วัตถุเสพติด"}
TH_MONTH_ABBR = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                 "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

# มูลค่าการผลิตภาคอุตสาหกรรม (Manufacturing GDP ณ ราคาประจำปี, ล้านบาท) รายไตรมาส
# ปฏิทิน — จาก NESDC Production_gdp.xlsx, Table 3 (Gross Domestic Product at Current
# Market Prices), คอลัมน์ "Manufacturing (6)" *** เป็นภาพรวมภาคการผลิตทั้งประเทศ
# (อาหาร เคมีภัณฑ์ เครื่องจักร สิ่งทอ ฯลฯ รวมกัน) ไม่ได้เจาะจงเฉพาะผลิตภัณฑ์สุขภาพ 7 กลุ่ม
# ของ อย. (ยังไม่มีสถิติแยกเฉพาะอุตสาหกรรมยา/เครื่องมือแพทย์/เครื่องสำอาง) ใช้เป็นตัวชี้วัด
# เศรษฐกิจภาคการผลิตระดับประเทศแทนไปก่อน ต้องบอกผู้ใช้ตรง ๆ ว่าไม่ใช่ค่าเฉพาะสุขภาพ ***
# อัปเดต: รัน 04_Scripts/export_nesdc_gdp_quarterly.py ใหม่ แล้วอ่านค่าไตรมาสล่าสุดจาก
# Table 3 คอลัมน์ Manufacturing (6) มาต่อท้าย list นี้ (ปี ค.ศ., ไตรมาสปฏิทิน 1-4, ล้านบาท)
MANUFACTURING_GDP_QUARTERLY = [
    (2023, 1, 1131277), (2023, 2, 1068966), (2023, 3, 1144071), (2023, 4, 1151259),
    (2024, 1, 1118471), (2024, 2, 1116112), (2024, 3, 1150582), (2024, 4, 1143665),
    (2025, 1, 1123255), (2025, 2, 1114284), (2025, 3, 1119544), (2025, 4, 1147960),
]  # ไตรมาสล่าสุด (2025 Q4) เป็นตัวเลขเบื้องต้น (preliminary) ตามที่ NESDC ระบุไว้

# โลโก้ อย. ฝัง base64 ไว้ตรงนี้เลย (ไม่อ่านจากไฟล์ตอนรัน) เพราะสคริปต์นี้ถูกก็อป
# ไปวางในโหนด Python View ของ KNIME ตรง ๆ ซึ่งอาจรันบนเครื่อง/user context ที่ไม่มี
# path /Users/thanaponchueaboonmee/Downloads/FDA/... อยู่จริง — ต้นฉบับ SVG อยู่ที่
# Logo_of_the_Food_and_Drug_Administration.svg ถ้าจะเปลี่ยนโลโก้ ให้เข้ารหัส base64
# ไฟล์ใหม่แล้วแทนที่ค่าคงที่นี้
_FDA_LOGO_B64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz48c3ZnIGlkPSJiIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNDAiIGhlaWdodD0iMjQwIiB2aWV3Qm94"
    "PSIwIDAgMjQwIDI0MCI+PGRlZnM+PHN0eWxlPi5ke2ZpbGw6IzAwNGNhZjt9PC9zdHlsZT48L2RlZnM+PGcgaWQ9ImMiPjxwYXRoIGNsYXNzPSJkIiBkPSJtMTE5LjE1LDBjLTIzLjcuMTctNDYuODEsNy4zNS02Ni40MywyMC42NC0xOS42MiwxMy4yOS0zNC44NywzMi4wOS00My44Miw1NC4wM0MtLjA2LDk2LjYxLTIuMzIsMTIwLjcxLDIuNDEsMTQzLjkzYzQuNzMsMjMuMjIsMTYuMjIsNDQuNTIsMzMuMDQsNjEuMjIsMTYuODIsMTYuNywzOC4yLDI4LjA0LDYxLjQ1LDMyLjYsMjMuMjUsNC41Niw0Ny4zNCwyLjEzLDY5LjIyLTYuOTcsMjEuODgtOS4xMSw0MC41Ny0yNC40OSw1My43Mi00NC4yLDEzLjE1LTE5LjcyLDIwLjE2LTQyLjg4LDIwLjE2LTY2LjU4LS4xMS0zMS45NC0xMi45MS02Mi41Mi0zNS41OC04NS4wM0MxODEuNzYsMTIuNDcsMTUxLjA5LS4xMSwxMTkuMTUsMFptMCwyMjQuN2MtMTQuOS4xLTI5LjY0LTIuOTctNDMuMjYtOS4wMi0xMy42MS02LjA1LTI1Ljc4LTE0LjkzLTM1LjY5LTI2LjA2LTkuOTEtMTEuMTItMTcuMzMtMjQuMjMtMjEuNzYtMzguNDUtNC40NC0xNC4yMi01Ljc5LTI5LjIyLTMuOTctNDQuMDFoNzAuNTljMS44LDAsMi4zNS41OCwyLjM1LDIuNDUtLjA1LDIxLjMxLS4wNiw0Mi42MS0uMDQsNjMuOTIsMCwuNTUuMjEsMS4xNi0uMzgsMS43OGwtMjYuNTItMjkuNTNoOC44OHEzLjEsMCwzLjExLTMuMTljMC0zLjEyLS4wNS02LjI0LDAtOS4zNS4wMy0xLjU1LS40OC0yLjI1LTIuMDQtMi4yNS0xMy4wOS4wMy0yNi4xOCwwLTM5LjI2LjAyLS41NCwwLTEuMjktLjE1LTEuNDcuNTEtLjE5LjY2LjQ4LDEuMTQuOSwxLjYsNi45Miw3LjY1LDEzLjg1LDE1LjMsMjAuNzgsMjIuOTUsMTMuNjcsMTUuMTIsMjcuMzQsMzAuMjUsNDEsNDUuMzcsMi43MSwyLjk5LDIuMDQsMi45NCw0LjY2LDAsMTMuNDItMTUuMTgsMjYuODItMzAuMzksNDAuMTktNDUuNjMsOS4xOS0xMC40MiwxOC4zOS0yMC44MywyNy42LTMxLjIzLDguOTUtMTAuMTMsMTcuODktMjAuMjYsMjYuODMtMzAuMzkuMTgtLjE5LjMzLS4zOS40Ny0uNi4yNS0uNDIuODgtLjcyLjY3LTEuMjlzLS44Ny0uMzgtMS4zMy0uMzhjLTQuNDksMC04Ljk3LDAtMTMuNDYtLjAyLS40Ny0uMDEtLjk0LjA4LTEuMzYuMjgtLjQzLjItLjguNDktMS4wOS44Ni04LjI4LDkuMzUtMTYuNTcsMTguNjktMjQuODcsMjguMDQtNS4wNyw1LjcyLTEwLjE0LDExLjQ1LTE1LjIsMTcuMTgtMTAuNTcsMTEuOTItMjEuMTUsMjMuODQtMzEuNzIsMzUuNzUtLjMuNDItLjU3Ljg2LS44LDEuMzMtLjI2LS4zMy0uNDUtLjcxLS41Ni0xLjEyLS4xMS0uNDEtLjEzLS44My0uMDYtMS4yNS0uMDItOC4xOC0uMDItMTYuMzcsMC0yNC41NSwwLTIuNTEuMDgtMi41OSwyLjU2LTIuNiw0LjExLDAsOC4yMy0uMDQsMTIuMzQsMCwxLjUyLjAyLDIuMTEtLjUzLDIuMDgtMi4xNi0uMDktMy41MS0uMDktNy4wMSwwLTEwLjUyLjA0LTEuNjQtLjU5LTIuMTYtMi4wOC0yLjE0LTQuMTcuMDYtOC4zNC0uMDUtMTIuNTMuMDUtMS43Ny4wNC0yLjQyLS41OS0yLjM5LTIuNDYuMDgtNi4zLjA4LTEyLjYsMC0xOC45LS4wMi0xLjgzLjUyLTIuNTQsMi4zNC0yLjUsNC4yNC4xMSw4LjQ4LDAsMTIuNzEuMDYsMS42My4wMywyLjIyLS42NCwyLjE5LTIuMy0uMDYtMy40NCwwLTYuODksMC0xMC4zMywwLTIuNjgtLjAzLTIuNy0yLjYzLTIuN0gxNy41M2M1LjEyLTE4Ljk4LDE1LjQ1LTM2LjE0LDI5LjgyLTQ5LjU2LDE0LjM3LTEzLjQxLDMyLjIxLTIyLjU0LDUxLjQ5LTI2LjM0LDE5LjI4LTMuOCwzOS4yNS0yLjE0LDU3LjY0LDQuODEsMTguMzksNi45NSwzNC40NiwxOC45MSw0Ni40MSwzNC41MiwxMS45NSwxNS42MSwxOS4yOSwzNC4yNSwyMS4xOSw1My44MiwxLjksMTkuNTYtMS43MSwzOS4yNy0xMC40Miw1Ni44OS04LjcxLDE3LjYyLTIyLjE4LDMyLjQ1LTM4Ljg4LDQyLjgyLTE2LjcsMTAuMzYtMzUuOTcsMTUuODUtNTUuNjMsMTUuODNaIi8+PC9nPjwvc3ZnPg=="
)


def _logo_data_uri() -> str:
    """Embed the FDA logo into the KNIME HTML view without external file loading."""
    return "data:image/svg+xml;base64," + _FDA_LOGO_B64


def _payload(kpi, spark, trend, share, cagr, country, health,
             by_group, country_by_group, as_of_label, fy_complete,
             has_cagr: bool = False) -> dict:
    spark = spark.copy()
    spark["period_month"] = pd.to_datetime(spark["period_month"])
    by_group = by_group.copy()
    by_group["period_month"] = pd.to_datetime(by_group["period_month"])

    sparks = {code: g.sort_values("period_month")["value"].round(2).tolist()
              for code, g in spark.groupby("kpi_code")}

    tr = trend.copy()
    fys = sorted(tr.fy.unique())
    series = []
    for name in ("import", "export", "balance"):
        d = tr[tr.series == name].set_index("fy").reindex(fys)
        series.append({
            "key": name,
            "values": [None if pd.isna(v) else round(float(v), 1) for v in d.value_mb],
            "isFc": [bool(x) for x in d.is_forecast.fillna(False)],
            "lo": [None if pd.isna(v) else round(float(v), 1)
                   for v in d.get("ci_lower_mb", pd.Series(index=d.index, dtype=float))],
            "hi": [None if pd.isna(v) else round(float(v), 1)
                   for v in d.get("ci_upper_mb", pd.Series(index=d.index, dtype=float))],
        })

    if "production_value_mb" not in by_group.columns:
        by_group = by_group.assign(production_value_mb=0.0)
    detail = by_group.assign(m=by_group.period_month.dt.strftime("%Y-%m"))
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
               fy_complete: int, has_cagr: bool = False) -> str:
    data = _payload(kpi, spark, trend, share, cagr, country, health,
                    by_group, country_by_group, as_of_label, fy_complete,
                    has_cagr)
    html = TEMPLATE.replace("/*__PAYLOAD__*/null",
                            json.dumps(data, ensure_ascii=False, allow_nan=False))
    return html.replace("__FDA_LOGO_SRC__", _logo_data_uri())


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
  }
  *{box-sizing:border-box}
  html,body{margin:0;padding:0}
  body{
    background:var(--canvas);
    color:var(--ink);
    font-family:"TH Sarabun New","TH SarabunPSK","Sarabun","Noto Sans Thai",
                "Leelawadee UI",system-ui,-apple-system,sans-serif;
    font-size:23px; line-height:1.45; font-weight:600; -webkit-font-smoothing:antialiased;
    text-rendering:optimizeLegibility;
  }
  /* ── แถบหัวเรื่อง ─────────────────────────────────────────── */
  header{background:var(--navy);
         color:#fff; padding:16px 26px 14px;
         display:flex; justify-content:space-between; align-items:center; gap:16px;
         flex-wrap:wrap; position:relative; border-bottom:3px solid var(--gold)}
  header .brand{display:flex; align-items:center; gap:14px}
  header .brandLogo{width:50px; height:50px; object-fit:contain; background:#fff;
                    border-radius:6px; padding:5px; box-shadow:0 0 0 1px rgba(255,255,255,.25)}
  header h1{margin:0; font-size:33.5px; font-weight:700; letter-spacing:.2px;
            line-height:1.25}
  header .sub{color:#B7C7DC; font-size:20.5px; letter-spacing:.2px; margin-top:2px}
  header .right{text-align:right; font-size:21px}
  header .right .asof{font-weight:600}
  header .right .org{color:#B7C7DC; font-size:19px; margin-top:3px}

  /* ── แถบตัวกรอง ───────────────────────────────────────────── */
  .filters{background:#fff; border-bottom:1px solid var(--line); padding:8px 26px;
           display:grid; grid-template-columns:max-content minmax(0,1fr);
           gap:10px 16px; align-items:center; position:sticky; top:0; z-index:20}
  .static-filters{grid-column:1; justify-self:start; max-width:100%}
  /* ชิปกลุ่ม: แถวเดียวกับ label — เลื่อนแนวนอนแทนขึ้นหลายแถว */
  .filterGroups{grid-column:2; justify-self:stretch; display:flex; align-items:center;
                justify-content:flex-end; gap:8px; flex-wrap:nowrap; min-width:0;
                max-width:100%}
  .filters .lbl{color:var(--muted); font-size:18px; font-weight:600; white-space:nowrap;
                 flex:none}
  /* label ชิดชิป — ทั้งก้อนอยู่ขวา ไม่กินพื้นที่เต็มแถวแล้วดัน chip หลุดไป */
  #chips{display:flex; flex:0 1 auto; gap:6px; flex-wrap:nowrap; justify-content:flex-start;
         min-width:0; max-width:calc(100% - 8.5em); overflow-x:auto; overflow-y:hidden;
         padding:2px 0; scrollbar-width:thin; scrollbar-color:var(--line) transparent}
  #chips::-webkit-scrollbar{height:5px}
  #chips::-webkit-scrollbar-thumb{background:var(--line); border-radius:4px}
  .chip{border:1px solid var(--line); background:#fff; color:var(--ink);
        border-radius:6px; padding:4px 14px; font:inherit; font-size:20.5px;
        cursor:pointer; display:inline-flex; align-items:center; gap:7px; flex:none;
        transition:background .13s, color .13s, border-color .13s}
  .filters .chip{padding:3px 10px; font-size:17px; gap:5px; border-radius:5px}
  .filters .chip .dot{width:8px; height:8px}
  .chip:hover{border-color:#9FB6D0}
  .chip[aria-pressed="true"]{background:var(--navy); color:#fff; border-color:var(--navy)}
  .chip .dot{width:9px; height:9px; border-radius:50%; flex:none}
  .static-filters{display:flex; gap:14px; color:var(--muted); font-size:19px;
                  flex-wrap:wrap; align-items:center; flex:0 1 auto}
  .static-filters span{white-space:nowrap; padding-left:14px; border-left:1px solid var(--line)}
  .static-filters span:first-child{padding-left:0; border-left:none}
  .static-filters select{font:inherit; font-size:18px; color:var(--ink); background:#fff;
                         border:1px solid var(--line); border-radius:5px; padding:2px 6px;
                         margin:0 2px}
  .reset-btn{font:inherit; font-size:17.5px; font-weight:600; color:var(--navy);
             background:#fff; border:1px solid var(--line); border-radius:5px;
             padding:2px 10px; margin-left:6px; cursor:pointer}
  .reset-btn:hover{background:var(--line2)}

  /* ── ตาราง 12 คอลัมน์ ตามมาตรฐานในตารางที่ 13 ─────────────── */
  main{padding:16px 20px 10px; display:grid; grid-template-columns:repeat(12,1fr);
       gap:14px; max-width:2000px; margin:0 auto}
  .card{background:var(--card); border:1px solid var(--line); border-radius:var(--r);
        padding:15px 17px 13px; min-width:0; box-shadow:var(--sh-1)}
  /* ขีดสีสั้น ๆ หน้าหัวข้อ — แยกลำดับชั้นหัวข้อกับคำอธิบายให้ชัดโดยไม่เพิ่มเส้นกรอบ */
  .card > h2{margin:0; font-size:26px; font-weight:700; letter-spacing:.1px;
             display:flex; align-items:center; gap:9px}
  .card > h2::before{content:""; width:4px; height:17px; border-radius:2px;
                     background:var(--navy); flex:none}
  .card > .cap{margin:4px 0 11px 13px; color:var(--muted); font-size:19px;
               line-height:1.4}

  /* ── ตัวเลือกช่วงเวลารายการ์ด ─────────────────────────────── */
  /* ปุ่มไอคอน + เมนู dropdown เลือกช่วงเวลาต่อการ์ด อิสระจากตัวกรอง Year/Month
     ด้านบนของหน้าจอ (คนละกลไกกัน) — เผื่อ user อยากดูกราฟนึงช่วงสั้น อีกกราฟช่วงยาว
     พร้อมกันได้ ซ่อนอัตโนมัติในโหมดข้อมูลมอค (ดูฟังก์ชัน period* ใน script) เพราะ
     กราฟมอคยังไม่รองรับตัวกรองนี้ */
  .periodPick{position:relative; margin-left:auto; flex:none}
  .periodBtn{width:30px; height:30px; border-radius:7px; border:1px solid var(--line);
             background:#fff; color:var(--muted); cursor:pointer; display:inline-flex;
             align-items:center; justify-content:center; line-height:1;
             transition:background .13s, color .13s, border-color .13s}
  .periodBtn:hover{background:var(--line2); color:var(--ink)}
  .periodMenu{display:none; position:absolute; right:0; top:36px; z-index:30;
              background:#fff; border:1px solid var(--line); border-radius:8px;
              box-shadow:0 10px 26px rgba(8,24,46,.16); padding:12px; min-width:210px}
  .periodMenu.open{display:block}
  .periodRow{display:flex; align-items:center; gap:8px; margin-bottom:8px}
  .periodRow label{width:36px; flex:none; color:var(--muted); font-size:15px; font-weight:600}
  .periodRow input[type="month"]{flex:1; min-width:0; font:inherit; font-size:15px;
      color:var(--ink); border:1px solid var(--line); border-radius:6px; padding:5px 7px}
  .periodActions{display:flex; justify-content:space-between; gap:8px; margin-top:10px}
  .periodActions button{flex:1; font:inherit; font-size:14.5px; font-weight:600;
      border-radius:6px; padding:7px 6px; cursor:pointer}
  .periodClear{border:1px solid var(--line); background:#fff; color:var(--muted)}
  .periodClear:hover{background:var(--line2); color:var(--ink)}
  .periodApply{border:1px solid var(--navy); background:var(--navy); color:#fff}
  .periodApply:hover{background:var(--navy2)}

  /* ── การ์ดตัวชี้วัดหลัก ───────────────────────────────────── */
  /* auto-fit แทนการตรึง 6 คอลัมน์ — ปรับตามจำนวนการ์ดจริงเอง (มอค 6 ใบ / จริง 4 ใบ
     ตอนนี้) ไม่ต้องแก้ CSS ทุกครั้งที่จำนวนการ์ดเปลี่ยน */
  .kpis{grid-column:span 12; display:grid;
        grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:14px}
  .kpi{background:var(--card); border:1px solid var(--line); border-radius:var(--r);
       overflow:hidden; position:relative; cursor:default; box-shadow:var(--sh-1)}
  .kpi .bar{height:4px}
  .kpi .body{padding:11px 15px 18px}
  .kpi .name{color:var(--muted); font-size:21px; font-weight:600; letter-spacing:.1px}
  .kpi .val{font-size:48.5px; font-weight:700; line-height:1.1; letter-spacing:-.7px;
            font-variant-numeric:tabular-nums; margin-top:1px}
  .kpi .unit{color:var(--muted); font-size:19px; margin-top:0}
  /* ต้องตรึงขนาด ไม่งั้นกฎ svg{width:100%} ด้านล่างจะขยายจนทับตัวเลข */
  /* เลื่อนลงอีกรอบตามตัวเลขค่าการ์ดที่ใหญ่ขึ้นอีก (40.5px→48.5px) */
  .kpi .spark{position:absolute; top:58px; right:14px; width:96px; height:36px}

  .trend{grid-column:span 8}
  /* คำอธิบายสีอยู่นอก SVG — ไม่แย่งพื้นที่ plot กับตัวอักษรที่ scale ตามความกว้างการ์ด */
  .trendLegend{display:flex; flex-wrap:wrap; gap:6px 18px; margin:0 0 8px 13px;
               font-size:16px; font-weight:600; color:var(--muted)}
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
  table.health{width:100%; border-collapse:collapse; font-size:17px}
  table.health tr.healthRow td{padding:11px 0; border-bottom:1px solid var(--line2);
          vertical-align:top}
  table.health tr.healthRow:last-child td{border-bottom:0}
  table.health .hrLabel{display:flex; align-items:flex-start; gap:8px;
          color:var(--muted); font-weight:600; font-size:15.5px; line-height:1.35}
  table.health .hrLabel .st{width:8px; height:8px; border-radius:50%; flex:none;
          margin-top:5px}
  table.health .hrVal{margin:5px 0 0 16px; font-weight:700; font-size:18px;
          line-height:1.25; font-variant-numeric:tabular-nums; color:var(--ink)}
  table.health .hrSub{margin:3px 0 0 16px; font-size:14.5px; line-height:1.4;
          color:var(--muted); overflow-wrap:break-word}


  svg{display:block; width:100%; height:auto; overflow:visible}
  .gridline{stroke:var(--line2); stroke-width:1}
  .axis{fill:var(--muted); font-size:17.5px; font-weight:700}
  .barlbl{fill:var(--ink); font-size:18px; font-weight:700}
  .hit{cursor:pointer; transition:opacity .15s}
  .hit:hover{opacity:.82}
  .dim{opacity:.22}

  #tip{position:fixed; pointer-events:none; opacity:0; transition:opacity .1s;
       background:rgba(14,39,73,.97); color:#fff; padding:8px 12px; border-radius:8px;
       font-size:20.5px; line-height:1.4; z-index:99; max-width:290px;
       box-shadow:0 10px 26px rgba(8,24,46,.34)}
  #tip b{font-weight:700}

  @media (max-width:1300px){
    .kpis{grid-template-columns:repeat(3,1fr)}
    .trend{grid-column:span 12}
    .treemapCard{grid-column:span 5}
    .cagrCard{grid-column:span 7}
    .countryCard{grid-column:span 7}
    .healthCard{grid-column:span 5}
  }
  @media (max-width:980px){
    .filters{grid-template-columns:1fr; gap:8px}
    .static-filters,.filterGroups{grid-column:1; justify-self:stretch}
    #chips{justify-content:flex-start}
    .kpis{grid-template-columns:repeat(2,1fr)}
    .treemapCard,.cagrCard,.countryCard,.healthCard{grid-column:span 12}
  }
  @media (max-width:700px){
    header .brandLogo{width:42px; height:42px}
    header h1{font-size:28px}
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
</head>
<body>

<header>
  <div class="brand">
    <img class="brandLogo" src="__FDA_LOGO_SRC__" alt="อย.">
    <div>
      <h1>ระบบวิเคราะห์ข้อมูลเศรษฐกิจผลิตภัณฑ์สุขภาพ</h1>
      <div class="sub">หน้าจอที่ 1 · ภาพรวมเศรษฐกิจผลิตภัณฑ์สุขภาพ (Executive Overview)</div>
    </div>
  </div>
  <div class="right">
    <div class="asof">ข้อมูล ณ <span id="asOf"></span></div>
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
  const im = sumByFy(rows, fy, "im"), ex = sumByFy(rows, fy, "ex");
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
    "แสดงข้อมูลจริงรายเดือน — ยังไม่มีค่าพยากรณ์ (SARIMAX ต้องการข้อมูล ≥12 เดือนต่อรอบ)"
    + periodLabel(periodTrend);
}

/* ── กราฟแนวโน้มรายปีงบประมาณสำหรับข้อมูลจริง (สลับได้จากตัวเลือก "มุมมอง") ──
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
    "แสดงข้อมูลจริงรายปีงบประมาณ — ยังไม่มีค่าพยากรณ์" + periodLabel(periodTrend);
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
  // ยังไม่มีพยากรณ์รายปี → สลับรายเดือน/รายปีตาม "มุมมอง"
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
           style="fill:${NAVY};opacity:.58;font-size:12.5px">ช่วงพยากรณ์</text>`;
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
  s += `<text class="axis" x="${P.l-52}" y="${P.t + 4}" style="font-size:13px">ล้านบาท</text>`;
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
               style="fill:#16222E;font-size:18.5px;font-weight:700">${esc(d.name_th)} (${d.product_group})</text>
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
             style="fill:#16222E;font-size:18.5px;font-weight:700">${esc(d.name_th)} (${d.product_group})</text>
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
       style="fill:#16222E;font-size:18.5px;font-weight:700">${esc(d.name)}</text>`;
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

document.getElementById("asOf").textContent = DATA.meta.asOf;
populateYearMonthFilters();
renderAll();
</script>
</body>
</html>
"""

MB = 1e6
GROUPS = ["DRUG", "MDC", "FOOD", "CMT", "HERB", "TXC", "NCT"]

# ตาราง Country ของ อย. เก็บแค่รหัส + ชื่ออังกฤษ ไม่มีชื่อไทย — แปลเองสำหรับ
# คู่ค้าหลักที่เจอบ่อย ประเทศอื่นนอกลิสต์นี้ fallback ไปใช้ชื่ออังกฤษจาก DB แทน
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


def fiscal_year(ts: pd.Timestamp) -> int:
    return ts.year + 543 + (1 if ts.month >= 10 else 0)


TREND_DISPLAY_YEARS = 5  # จำนวนปีงบประมาณบนกราฟแนวโน้ม (รวมปีที่มีส่วนพยากรณ์)
# ย้อนหลัง ~6 ปีปฏิทิน เพื่อให้ครบ 5 ปีงบ (ต.ค.–ก.ย.) + เดือนล่าสุด
DASHBOARD_LOOKBACK_MONTHS = (TREND_DISPLAY_YEARS + 1) * 12 - 1


def _sarimax_forecast(y: pd.Series, steps: int) -> pd.DataFrame:
    """พยากรณ์รายเดือน SARIMAX(1,1,1)(1,1,1,12) — ถอยเป็นแนวโน้ม+ฤดูกาลถ้า fit ไม่ได้"""
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
    except Exception as e:  # pragma: no cover
        print(f"[เตือน] SARIMAX ใช้ไม่ได้ ({e}) — ถอยไปใช้แนวโน้มเชิงเส้น")
        t = np.arange(len(y))
        slope, intercept = np.polyfit(t, y.to_numpy(), 1)
        seas = (y.to_numpy() - (slope * t + intercept))[-12:]
        base = slope * np.arange(len(y), len(y) + steps) + intercept
        yhat = base + np.resize(seas, steps)
        sd = float(np.std(y.to_numpy() - (slope * t + intercept)))
        return pd.DataFrame({"yhat": yhat, "lo": yhat - 1.28 * sd,
                             "hi": yhat + 1.28 * sd}, index=idx)


def _trend_actual_only(detail: pd.DataFrame, fy_first: int) -> pd.DataFrame:
    """ยอดรวมรายปีงบประมาณจากข้อมูลจริงเท่านั้น (ไม่มีพยากรณ์)"""
    fy_flow = (detail.groupby("fy")[
        ["import_value_thb", "export_value_thb", "trade_balance_thb"]].sum() / MB)
    fy_flow = fy_flow[fy_flow.index >= fy_first]
    trend = pd.concat([
        fy_flow[[c]].rename(columns={c: "value_mb"}).assign(series=s)
        for s, c in (("import", "import_value_thb"), ("export", "export_value_thb"),
                     ("balance", "trade_balance_thb"))
    ], axis=1).reset_index()
    trend["is_forecast"] = False
    trend["ci_lower_mb"] = np.nan
    trend["ci_upper_mb"] = np.nan
    return trend


def _build_trend_with_forecast(detail: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """
    แนวโน้มรายปีงบประมาณ + พยากรณ์สิ้นปีงบประมาณที่กำลังเดิน (ระดับรวมประเทศ)
    ใช้ข้อมูลรายเดือนในหน้าต่างที่โหลดมา — พอมี ≥24 เดือน จะ fit SARIMAX ได้
    """
    monthly = (detail.groupby("period_month")[["import_value_thb", "export_value_thb"]]
               .sum().sort_index())
    as_of_month = monthly.index.max()
    complete = detail.groupby("fy")["period_month"].nunique()
    if (complete >= 12).any():
        fy_complete = int(complete[complete >= 12].index.max())
    else:
        fy_complete = int(detail["fy"].max())
    fy_first = fy_complete - TREND_DISPLAY_YEARS + 2

    fy_current_end = pd.Timestamp(year=fy_complete + 1 - 543, month=9, day=1)
    forecast_months = max(0, (fy_current_end.year - as_of_month.year) * 12
                          + fy_current_end.month - as_of_month.month)

    y_len = len(monthly)
    if y_len < 24 or forecast_months <= 0:
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
    """
    *** ใช้ "นำเข้าจากศุลกากร" เป็นตัวหลัก ไม่ใช่ "นำเข้าจาก อย." ***
    ไฟล์มีมูลค่านำเข้า 2 ชุด ต่างกัน 25 เท่า (อย. เก็บเฉพาะใบขนที่ผ่านระบบตัวเอง)
    ดุลการค้าต้องเทียบแหล่งเดียวกัน ไม่งั้นจะได้ "เกินดุล" ซึ่งผิดความจริง
    """
    df = df.rename(columns={"GROUP_CD": "product_group", "Period_month": "period_month",
                            "import_value_thb": "import_fda_thb",
                            "import_value_thb (Right)": "import_value_thb"})
    df["period_month"] = pd.to_datetime(df["period_month"].astype(str) + "-01")
    df["trade_balance_thb"] = df["export_value_thb"] - df["import_value_thb"]
    return df[["period_month", "product_group", "import_value_thb",
               "export_value_thb", "trade_balance_thb", "import_fda_thb"]]


def prep_stock(df: pd.DataFrame, value_name: str) -> tuple[pd.DataFrame, float]:
    """แถวที่ PERIOD_FINAL ว่างวางบนแกนเวลาไม่ได้ ต้องตัดออก แต่ไม่ใช่ศูนย์ — คืนยอดไปแสดงเป็นหมายเหตุ"""
    excluded = float(df.loc[df["PERIOD_FINAL"].isna(), "backlog"].clip(lower=0).sum())
    df = df[df["PERIOD_FINAL"].notna()].copy()
    df["period_month"] = pd.to_datetime(df["PERIOD_FINAL"].astype(str) + "-01")
    df = df.rename(columns={"GROUP_CD_FINAL": "product_group", "backlog": value_name})
    df = df[["period_month", "product_group", value_name]]
    df = df.groupby(["product_group", "period_month"], as_index=False)[value_name].last()
    return df, excluded


def country_name_th(code, name_en) -> str:
    if isinstance(code, str) and code in COUNTRY_NAME_TH:
        return COUNTRY_NAME_TH[code]
    if isinstance(name_en, str) and name_en.strip():
        return name_en.strip().title()
    return UNKNOWN_COUNTRY_TH


def prep_country(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    รวม (GROUP_CD, CountryCode) → country_by_group และรวมทุกกลุ่ม → country (top 6)
    เพื่อแทนที่ MART_D1_COUNTRY(_BY_GROUP).csv มอคเดิม — คอลัมน์คงชื่อ/รูปแบบ
    เดิมทุกอย่าง (rank/country_name_th/import_value_mb) ฝั่ง JS จะได้ไม่ต้องแก้
    """
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


trade = prep_trade(input_port(0, "มูลค่านำเข้า-ส่งออก"))
prod, _ = prep_stock(input_port(1, "ผลิตภัณฑ์ที่ได้รับอนุญาต"), "product_stock")
ent, _ = prep_stock(input_port(2, "ผู้ประกอบการ"), "active_entity")
app, _ = prep_stock(input_port(3, "คำขอคงค้าง"), "backlog")
country, country_by_group = prep_country(input_port(4, "ประเทศต้นทาง"))

# *** สำคัญ: ต้องรวมช่วงเวลาจากทั้ง 4 สาย ไม่ใช่แค่สายการค้าเพียงสายเดียว ***
# แต่ละสายมาจากตารางคนละตัว (ProductReleasedInfo, PRODUCT_INFO, LOCATION_INFO,
# DOC_REQ) ช่วงข้อมูลจริงยาวไม่เท่ากัน — ถ้ายึดแค่ months ของสายการค้าเป็นแกน
# อีก 3 สายที่ข้อมูลยาวกว่าจะถูกตัดทิ้งไปเงียบ ๆ ตอน merge (as_of ก็จะผิดตามไปด้วย)
all_dates = pd.concat([trade["period_month"], prod["period_month"],
                       ent["period_month"], app["period_month"]])
# ตัดทั้งวันที่อนาคตไกลเกินจริง (เช่น EXP_DATE คีย์ผิดเป็นปี 2033 ที่เจอใน HERB)
# และวันที่เก่าเดี่ยว ๆ ที่หลุดมาจากข้อมูลหลัก (เจอ APP_DATE ปี 2021 หลุดมา 1 แถว
# ใน NCT ทั้งที่ข้อมูลจริงเริ่ม 2024) — ใช้หน้าต่างย้อนหลังจากวันนี้แทน
# การรวมทั้งประวัติศาสตร์แบบไม่มีขอบเขต กันกราฟยืดว่างเปล่าเพราะข้อมูลเพี้ยนแค่จุดเดียว
today = pd.Timestamp.now().normalize().replace(day=1)
window_start = today - pd.DateOffset(months=DASHBOARD_LOOKBACK_MONTHS)
months = sorted(all_dates[(all_dates >= window_start) & (all_dates <= today)].unique())
as_of = pd.Timestamp(months[-1])
fy = fiscal_year(as_of)
# *** บั๊กที่แก้: เดิมใช้ MonthEnd เสมอ ทำให้ขึ้น "30 ก.ย." ทั้งที่วันนี้เพิ่งวันที่ 10 ***
# ถ้าเดือนล่าสุดในข้อมูล = เดือนปัจจุบันจริง ให้โชว์วันที่ปัจจุบันจริง (ข้อมูลเดือนนี้
# ยังไม่จบเดือน) ส่วนเดือนที่ผ่านไปแล้วเต็มเดือน ค่อยโชว์เป็นวันสุดท้ายของเดือนนั้น
real_today = pd.Timestamp.now().normalize()
# หัวข้อ "ข้อมูล ณ ..." ใช้วันที่ปัจจุบัน (ส่วนคำนวณ KPI ยังอิงเดือนล่าสุดในชุดข้อมูล)
as_of_label = (f"{real_today.day} "
               f"{TH_MONTH_ABBR[real_today.month - 1]} {real_today.year + 543}")

grid = pd.MultiIndex.from_product(
    [months, GROUPS], names=["period_month", "product_group"]).to_frame(index=False)
detail = (grid.merge(trade, on=["period_month", "product_group"], how="left")
              .merge(prod, on=["period_month", "product_group"], how="left")
              .merge(ent, on=["period_month", "product_group"], how="left")
              .merge(app, on=["period_month", "product_group"], how="left"))

# เดือนไหนไม่มีธุรกรรมนำเข้า-ส่งออกจริง ๆ = ศูนย์ได้เลย
flow_cols = ["import_value_thb", "export_value_thb", "trade_balance_thb"]
detail[flow_cols] = detail[flow_cols].fillna(0.0)

# *** ตัวเลข "ยอดคงเหลือสะสม" ต่างจากตัวเลข "กระแส" — ห้าม fillna(0) เฉย ๆ ***
# เดือนที่ไม่มีแถว = ไม่มีเหตุการณ์ใหม่เดือนนั้น ไม่ใช่ยอดหายไปเป็นศูนย์
# ต้องลากค่าของเดือนก่อนหน้ามาต่อ (forward fill) แยกตามกลุ่ม ไม่งั้นกราฟจะเห็น
# ยอดดิ่งลง 0 ผิด ๆ ทุกเดือนที่ไม่มีสถานที่/ผลิตภัณฑ์/คำขอใหม่เข้ามาพอดี
stock_cols = ["product_stock", "active_entity", "backlog"]
detail = detail.sort_values(["product_group", "period_month"])
detail[stock_cols] = detail.groupby("product_group")[stock_cols].ffill()
detail[stock_cols] = detail[stock_cols].fillna(0.0)   # ก่อนมีข้อมูลจริงเดือนแรกของกลุ่ม
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
})

def month_label(ts: pd.Timestamp) -> str:
    return f"{TH_MONTH_ABBR[ts.month - 1]} {ts.year + 543}"


flow = detail[["import_value_thb", "export_value_thb", "trade_balance_thb"]].sum() / MB
latest = detail[detail.period_month == as_of]
first_m = pd.Timestamp(months[0])
# ช่วงเวลาคำนวณจากข้อมูลจริงที่โหลดมา ไม่ hardcode — ยาวขึ้นเองถ้า DB มีประวัติยาวขึ้น
# ไม่ต่อ "— ข้อมูลจริง" ท้ายทุกการ์ดแล้ว (ซ้ำ 6 ครั้ง) — พูดรวมไว้ที่บรรทัด
# "ข้อมูล ณ ... ของทั้งหมดนี้" เหนือการ์ดแทนที่เดียว (ดู kpiAsOf ใน template)
basis_flow = f"รวม {len(months)} เดือน ({month_label(first_m)}–{month_label(as_of)})"
basis_stock = f"ณ สิ้นเดือน {TH_MONTH_ABBR[as_of.month - 1]} {as_of.year + 543}"

# ข้อมูลจริงมีแค่ 3 เดือน เทียบปีต่อปีไม่ได้ → ใส่ 0 (json ไม่รับ NaN)
# *** เอาการ์ด "ผลิตภัณฑ์ที่ได้รับอนุญาต"/"ผู้ประกอบการที่ยังดำเนินการ"/"คำขอที่อยู่
# ระหว่างพิจารณา" ออกจากแถว KPI ตามที่ผู้ใช้ขอ — ค่า product_stock/active_entity/backlog
# ยังใช้อยู่ที่อื่นเหมือนเดิม (การ์ดอันดับผู้ประกอบการ, ตารางสถานะข้อมูล) ไม่กระทบ ***

kpi = pd.DataFrame([
    dict(kpi_code="import_value", kpi_name_th="มูลค่านำเข้าผลิตภัณฑ์สุขภาพ",
         value=flow["import_value_thb"], unit="ล้านบาท", yoy_pct=0.0,
         higher_is_better=True, basis=basis_flow, drill_to="หน้าจอที่ 2"),
    dict(kpi_code="export_value", kpi_name_th="มูลค่าส่งออกผลิตภัณฑ์สุขภาพ",
         value=flow["export_value_thb"], unit="ล้านบาท", yoy_pct=0.0,
         higher_is_better=True, basis=basis_flow, drill_to="หน้าจอที่ 2"),
    dict(kpi_code="trade_balance", kpi_name_th="ดุลการค้า",
         value=flow["trade_balance_thb"], unit="ล้านบาท", yoy_pct=0.0,
         higher_is_better=True, basis=basis_flow, drill_to="หน้าจอที่ 2"),
    # *** ใส่ 0 ไปก่อนตามที่ผู้ใช้ขอ — ยังไม่ยืนยันว่าตัวเลข NESDC Manufacturing GDP
    # (_gdp_value_mb ด้านบน) เหมาะจะใช้แทน "มูลค่าการผลิต" ของ 7 กลุ่มผลิตภัณฑ์ อย. หรือไม่
    # เพราะเป็นยอดรวมภาคการผลิตทั้งประเทศทุกอุตสาหกรรม (อาหาร เคมีภัณฑ์ เครื่องจักร ฯลฯ)
    # ไม่ได้แยกเฉพาะยา/เครื่องมือแพทย์/เครื่องสำอาง ฯลฯ ให้ ค้างค่าคงที่ MANUFACTURING_GDP_
    # QUARTERLY ไว้เผื่อใช้ภายหลังถ้ายืนยันแล้วว่าใช้ได้ หรือเปลี่ยนไปใช้แหล่งข้อมูลอื่น ***
    dict(kpi_code="production_value", kpi_name_th="มูลค่าการผลิตภาคอุตสาหกรรม",
         value=0.0, unit="ล้านบาท", yoy_pct=0.0,
         higher_is_better=True, basis=basis_flow, drill_to=None),
])

monthly = detail.groupby("period_month")[
    ["import_value_thb", "export_value_thb", "trade_balance_thb",
     "product_stock", "active_entity", "backlog"]].sum().sort_index()
spark = pd.concat([s.rename("value").reset_index().assign(kpi_code=k) for k, s in {
    "import_value": monthly["import_value_thb"] / MB,
    "export_value": monthly["export_value_thb"] / MB,
    "trade_balance": monthly["trade_balance_thb"] / MB,
    "product_stock": monthly["product_stock"],
    "active_entity": monthly["active_entity"],
    "backlog": monthly["backlog"],
}.items()], ignore_index=True)[["kpi_code", "period_month", "value"]]

# แนวโน้มรายปีงบประมาณ + พยากรณ์ SARIMAX ระดับรวม (mockup/ข้อมูลไม่ครบปีใช้เติมส่วนที่ขาด)
trend, fy_trend_complete = _build_trend_with_forecast(detail)
fy = fy_trend_complete

g = detail.groupby("product_group")[["import_value_thb", "export_value_thb"]].sum()
share = pd.DataFrame({
    "product_group": g.index, "name_th": [GROUP_NAME_TH[x] for x in g.index],
    "trade_value_mb": (g["import_value_thb"] + g["export_value_thb"]).to_numpy() / MB})
tot = share["trade_value_mb"].sum()
share["share_pct"] = share["trade_value_mb"] / tot * 100 if tot else 0.0
share = share.sort_values("trade_value_mb", ascending=False).reset_index(drop=True)

# *** CAGR 3 ปี — คำนวณจาก "trade" ตรง ๆ (ก่อนตัดหน้าต่าง 35 เดือนของ detail) ***
# มูลค่าศุลกากรจริง (External2.csv) มีประวัติยาวถึง 5 ปี (2564-2568) แต่ก่อนหน้านี้
# การ์ดนี้เคยสลับไปโชว์ "จำนวนผู้ประกอบการ" แทนเพราะเข้าใจผิดว่าข้อมูลมีแค่ ~22 เดือน
# — จริง ๆ แล้วตัวจำกัดคือ Joiner (#68) ในเวิร์กโฟลว์ KNIME ที่ INNER JOIN สายการค้า
# อย. (เริ่มมีข้อมูลจริงทีหลัง) เข้ากับศุลกากร ทำให้แถวศุลกากรของปีเก่า ๆ ที่ยังไม่มี
# คู่ฝั่ง อย. ถูกตัดทิ้งไปเงียบ ๆ ตั้งแต่ต้นทาง (ต้องแก้ Joiner ให้เก็บแถวศุลกากรที่ไม่มี
# คู่ไว้ด้วย — "รวมแถวที่ไม่ตรงกันจากตารางขวา" — ถึงจะเห็นผลจริงที่นี่)
# ต้องมี "ปีงบประมาณที่ครบ 12 เดือน" 2 ปีห่างกัน 3 ปี ถึงจะคำนวณได้ ถ้ายังไม่ครบ
# (Joiner ยังไม่ได้แก้) ให้ cagr_3y_pct = 0 ไปก่อน ไม่ error — ฝั่ง JS จะ fallback
# ไปโชว์จำนวนผู้ประกอบการแทนเองผ่านแฟล็ก has_cagr (ดู renderCagr)
_trade_fy = trade.assign(
    fy=trade["period_month"].map(fiscal_year),
    trade_value_thb=trade["import_value_thb"] + trade["export_value_thb"])
_fy_month_count = _trade_fy.groupby("fy")["period_month"].nunique()
_complete_fys = sorted(_fy_month_count[_fy_month_count >= 12].index)
if len(_complete_fys) >= 4 and (_complete_fys[-1] - 3) in _complete_fys:
    _cagr_fy_end, _cagr_fy_start = _complete_fys[-1], _complete_fys[-1] - 3
    _fy_totals = _trade_fy.groupby(["product_group", "fy"])["trade_value_thb"].sum()

    def _cagr_pct(g: str) -> float:
        v_end = _fy_totals.get((g, _cagr_fy_end))
        v_start = _fy_totals.get((g, _cagr_fy_start))
        if v_end and v_start and v_start > 0:
            return round(((v_end / v_start) ** (1 / 3) - 1) * 100, 2)
        return 0.0

    cagr_by_group = {g: _cagr_pct(g) for g in GROUPS}
    has_cagr = True
else:
    cagr_by_group = {g: 0.0 for g in GROUPS}
    has_cagr = False

entity_by_group = latest.set_index("product_group")["active_entity"]
cagr = pd.DataFrame({"product_group": share["product_group"],
                     "name_th": share["name_th"],
                     "cagr_3y_pct": [cagr_by_group.get(g, 0.0) for g in share["product_group"]],
                     "active_entity_count": entity_by_group.reindex(
                         share["product_group"]).fillna(0.0).to_numpy()})

completeness = float((detail[["import_value_thb", "product_stock",
                              "active_entity", "backlog"]] != 0).to_numpy().mean() * 100)
health = pd.DataFrame([
    dict(metric_code="completeness", metric_name_th="ความถูกต้องข้อมูล",
         value=round(completeness, 1), unit="%", detail_th=None, display_text=None,
         status="ปกติ" if completeness >= 95 else "เฝ้าระวัง"),
    dict(metric_code="coverage", metric_name_th="ช่วงข้อมูล",
         value=np.nan, unit=None,
         display_text=f"{month_label(first_m)}–{month_label(as_of)}",
         detail_th=None, status="ปกติ"),
    dict(metric_code="last_refresh", metric_name_th="อัปเดตล่าสุด",
         value=np.nan, unit=None, display_text=as_of_label, detail_th=None,
         status="ปกติ"),
])

html = build_html(kpi, spark, trend, share, cagr, country, health,
                  by_group, country_by_group, as_of_label, fy, has_cagr)

# ── ส่งออกเป็นหน้าจอของโหนด Python View ──────────────────────────────────
knio.output_view = knio.view_html(html)

print(f"เรนเดอร์แล้ว {len(html)/1024:.0f} KB — ข้อมูลจริง {len(months)} เดือน (ปีงบประมาณ {fy})")
for r in kpi.itertuples(index=False):
    print(f"   {r.kpi_name_th:<32} {r.value:>14,.0f} {r.unit}")
