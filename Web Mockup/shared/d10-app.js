/* หน้า 10 — ตามรูปที่ 9 (Data Quality & Lineage Monitoring) ในเอกสาร 4.3.4
   โหลดแยกจาก HTML เพื่อไม่ให้ inline script ล้ม (CSP / parse) · ข้อมูลจำลอง ค่าเริ่มต้นตรงกับรูป */
(function () {
  "use strict";

  /* รอบข้อมูล — k = ส่วนต่างคุณภาพเทียบรอบล่าสุด */
  var ROUNDS = [
    {id: "R0", label: "30 มิ.ย. 2569", date: "30/06/2569", k: 0,
     kpi: {tables: [25, "ครบถ้วน", false], ext: [24, "ครบถ้วน", false], comp: [98.6, "0.4 จุด", false, true], valid: [96.2, "1.1 จุด", false, true], failed: [2, "1 งาน", true, false]}},
    {id: "R1", label: "31 มี.ค. 2569", date: "31/03/2569", k: 1,
     kpi: {tables: [25, "ครบถ้วน", false], ext: [23, "ขาด 1 แหล่ง", true], comp: [98.2, "0.6 จุด", false, true], valid: [95.1, "0.8 จุด", false, true], failed: [3, "1 งาน", true, true]}},
    {id: "R2", label: "31 ธ.ค. 2568", date: "31/12/2568", k: 2,
     kpi: {tables: [24, "ขาด 1 ตาราง", true], ext: [23, "ครบถ้วน", false], comp: [97.6, "0.3 จุด", false, true], valid: [94.3, "0.2 จุด", true, false], failed: [2, "1 งาน", false, false]}}
  ];
  var SPARKS = {
    tables: [21, 22, 22, 23, 23, 24, 24, 24, 25, 25], ext: [18, 19, 20, 20, 21, 22, 22, 23, 24, 24],
    comp: [96.9, 97.1, 97.0, 97.4, 97.6, 97.5, 97.9, 98.2, 98.2, 98.6], valid: [92.8, 93.1, 93.6, 93.4, 94.3, 94.6, 94.9, 95.1, 95.1, 96.2],
    failed: [1, 2, 1, 3, 2, 2, 4, 3, 3, 2]
  };

  /* ตารางต้นทาง — [type, source key, domain, table, fields, records, completeness, validity, duplicate, mapping, time] */
  var TABLES = [
    ["INT", "IM",  "Index 5 นำเข้า",     "IM_PRODUCTRELEASEDINFO",  32, 4182640, 99.2, 97.8, 0.4, 94.2, "02:05"],
    ["INT", "IM",  "Index 5 นำเข้า",     "IM_UNUMBERPRODUCT",       10, 862140,  99.6, 98.4, 0.2, 96.8, "02:08"],
    ["INT", "REG", "Index 7 ทะเบียน",    "DRUG_PRODUCT_INFO",       31, 146820,  98.8, 96.4, 0.6, 92.4, "02:15"],
    ["INT", "REG", "Index 7 ทะเบียน",    "MDC_PRODUCT_INFO",        30, 98460,   97.4, 94.2, 1.2, 88.6, "02:26"],
    ["INT", "REQ", "Index 6 คำขอ",       "MDC_DOC_REQ",             45, 412380,  96.2, 92.8, 1.8, 86.4, "02:38"],
    ["INT", "LOC", "Index 8 สถานที่",    "CMT_LOCATION_INFO",       52, 64120,   94.8, 90.6, 2.4, 82.1, "02:44"],
    ["INT", "LAB", "Index 11 วิเคราะห์", "ANALYSIS_REPORT_ANLYSIS", 29, 28640,   99.1, 97.2, 0.3, 95.4, "02:21"],
    ["EXT", "CUS", "ภายนอก ศุลกากร",     "CUSTOMS_TRADE_HS8",       18, 2846300, 99.4, 98.1, 0.1, 91.8, "01:40"],
    ["EXT", "BOT", "ภายนอก ธปท.",        "BOT_FX_INTERBANK",        6,  1460,    100,  100,  0,   100,  "01:32"],
    ["EXT", "NES", "ภายนอก สศช.",        "NESDC_GDP_QUARTERLY",     12, 64,      100,  99.2, 0,   100,  "01:35"]
  ];
  var SOURCES = [
    {key: "IM", label: "ระบบนำเข้า (IM)", type: "INT"}, {key: "REG", label: "ระบบทะเบียนผลิตภัณฑ์", type: "INT"},
    {key: "REQ", label: "ระบบคำขอ (DOC_REQ)", type: "INT"}, {key: "LOC", label: "ระบบสถานที่", type: "INT"},
    {key: "LAB", label: "ระบบผลวิเคราะห์", type: "INT"}, {key: "CUS", label: "กรมศุลกากร", type: "EXT"},
    {key: "BOT", label: "ธนาคารแห่งประเทศไทย", type: "EXT"}, {key: "NES", label: "สศช.", type: "EXT"}
  ];
  /* เกณฑ์สถานะ */
  var RULES = {
    ok:    {comp: 98, valid: 95, dup: 1, map: 90},
    watch: {comp: 95, valid: 90, dup: 2, map: 85}
  };
  var STATUS_TEXT = "ปกติ: Completeness ≥ 98%, Validity ≥ 95%, Duplicate ≤ 1%, Mapping ≥ 90%\n" +
    "เฝ้าระวัง: Completeness ≥ 95%, Validity ≥ 90%, Duplicate ≤ 2%, Mapping ≥ 85%\n" +
    "ต้องแก้ไข: ต่ำกว่าเกณฑ์เฝ้าระวังอย่างน้อย 1 ด้าน";
  /* ขั้นตอน Data Pipeline — ค่าตามรูปของ IM_PRODUCTRELEASEDINFO รอบล่าสุด */
  var PIPE_STEPS = [["รับข้อมูล (Acquisition)", "#2F6FC2"], ["ตรวจโครงสร้าง (Schema)", "#12A594"], ["ตรวจความครบถ้วน", "#1F9D62"],
    ["ตรวจความถูกต้อง (Validity)", "#E8A317"], ["ตรวจข้อมูลซ้ำ (Duplicate)", "#7E57C2"], ["ผ่านเข้าสู่ Integration", "#D0463B"]];
  var PIPE_FIG = [4182640, 4174210, 4128460, 4036820, 4020140, 4020140];

  var LINEAGE = [
    {id: "IMPORT", label: "มูลค่านำเข้าผลิตภัณฑ์สุขภาพรายกลุ่ม", stages: [
      ["ต้นทาง", ["IM_PRODUCT|RELEASEDINFO", "IM_UNUMBER|PRODUCT", "IM_|COUNTRY"]], ["Staging", ["STG_IMPORT|_RELEASE"]],
      ["Cleansing", ["CLN_IMPORT|_RELEASE", ["(Standardize + Validity)"]]], ["Integration", ["FACT_TRADE|_IMPORT", "DIM_PRODUCT|_GROUP", "DIM_|COUNTRY"]],
      ["Data Mart", ["MART_|ECONOMIC|_TRADE"]], ["Dashboard", ["KPI:", "Import Value", "รายกลุ่มผลิตภัณฑ์"]]]},
    {id: "TTM", label: "ระยะเวลาพิจารณาเฉลี่ยจริง", stages: [
      ["ต้นทาง", ["DRUG_|DOC_REQ", "MDC_|DOC_REQ", "CMT_|DOC_REQ"]], ["Staging", ["STG_|DOC_REQ"]],
      ["Cleansing", ["CLN_|DOC_REQ", ["(Date parsing + Stop Clock)"]]], ["Integration", ["FACT_|REQUEST", "DIM_|MILESTONE", "DIM_PRODUCT|_GROUP"]],
      ["Data Mart", ["MART_|REGULATORY|_PROCESS"]], ["Dashboard", ["KPI:", "ระยะเวลา|พิจารณาเฉลี่ย", ["(หน้าจอที่ 4)"]]]]},
    {id: "PRODUCT", label: "จำนวนผลิตภัณฑ์ที่ได้รับอนุญาต", stages: [
      ["ต้นทาง", ["DRUG_PRODUCT|_INFO", "MDC_PRODUCT|_INFO", "CMT_PRODUCT|_INFO"]], ["Staging", ["STG_PRODUCT|_INFO"]],
      ["Cleansing", ["CLN_|PRODUCT", ["(Fuzzy match + Dedup)"]]], ["Integration", ["FACT_|PRODUCT|_LICENSE", "DIM_|ENTREPRENEUR", "DIM_PRODUCT|_GROUP"]],
      ["Data Mart", ["MART_|PRODUCT|_ENTREPRENEUR"]], ["Dashboard", ["KPI:", "ผลิตภัณฑ์สะสม", ["(หน้าจอที่ 3, 6)"]]]]}
  ];
  var LIN_COLORS = ["#2F6FC2", "#12A594", "#1F9D62", "#E8A317", "#7E57C2", "#D0463B"];
  var LIN_ROLES = ["ฐานข้อมูลต้นทาง", "พักข้อมูลดิบ", "ทำความสะอาด", "เชื่อมโยงข้อมูล", "พร้อมใช้วิเคราะห์", "แสดงผล"];

  /* บันทึกเหตุการณ์ — [type, time, job, category, detail, status] */
  var LOGS = [
    ["INT", "02:44", "LOAD_CMT_LOCATION", "คุณภาพข้อมูล", "ค่าพิกัดภูมิศาสตร์ว่าง 2,412 ระเบียน", "ต้องแก้ไข"],
    ["INT", "02:38", "LOAD_MDC_DOC_REQ", "คุณภาพข้อมูล", "Mapping HS Code ไม่สำเร็จ 13.6%", "เฝ้าระวัง"],
    ["INT", "02:26", "LOAD_MDC_PRODUCT", "คุณภาพข้อมูล", "ค่าซ้ำในคีย์ธุรกิจ 1,182 ระเบียน", "เฝ้าระวัง"],
    ["INT", "02:12", "REFRESH_MART_ECON", "ประมวลผล", "ปรับปรุง Data Mart สำเร็จ", "ปกติ"],
    ["EXT", "01:40", "LOAD_CUSTOMS_HS8", "นำเข้าภายนอก", "รับข้อมูลการค้า HS 8 หลัก 2,846,300 ระเบียน", "ปกติ"],
    ["EXT", "01:32", "LOAD_BOT_FX", "นำเข้าภายนอก", "รับอัตราแลกเปลี่ยนรายวันผ่าน API สำเร็จ", "ปกติ"]
  ];

  var FILTER = {round: "R0", source: "ALL", type: "ALL", table: "IM_PRODUCTRELEASEDINFO", lineage: "IMPORT"};
  var $ = function (id) { return document.getElementById(id); };
  var fmt = function (n, d) { return Number(n).toLocaleString("th-TH", {minimumFractionDigits: d || 0, maximumFractionDigits: d || 0}); };
  var curRound = function () { return ROUNDS.filter(function (r) { return r.id === FILTER.round; })[0]; };

  function rowValues(t) {
    var k = curRound().k, ext = t[0] === "EXT";
    var clamp = function (v) { return Math.max(0, Math.min(100, v)); };
    return {
      type: t[0], source: t[1], domain: t[2], name: t[3], fields: t[4],
      records: Math.round(t[5] * (1 - 0.03 * k)),
      comp: clamp(t[6] - (ext ? 0 : 0.5 * k)), valid: clamp(t[7] - (ext ? 0 : 1.0 * k)),
      dup: +(t[8] + (ext ? 0 : 0.1 * k)).toFixed(1), map: clamp(t[9] - (ext ? 0 : 1.5 * k)),
      time: curRound().date + " " + t[10]
    };
  }
  function statusOf(r) {
    var pass = function (rule) { return r.comp >= rule.comp && r.valid >= rule.valid && r.dup <= rule.dup && r.map >= rule.map; };
    return pass(RULES.ok) ? ["ปกติ", "st-ok"] : pass(RULES.watch) ? ["เฝ้าระวัง", "st-watch"] : ["ต้องแก้ไข", "st-fix"];
  }
  function statusCls(text) { return text === "ปกติ" ? "st-ok" : text === "เฝ้าระวัง" ? "st-watch" : "st-fix"; }

  /* ── KPI ── */
  function sparkSvg(vals, color) {
    var w = 110, h = 26, lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var pts = vals.map(function (v, i) { return (i / (vals.length - 1) * w).toFixed(1) + "," + (hi === lo ? h / 2 : h - (v - lo) / (hi - lo) * (h - 6) - 3).toFixed(1); }).join(" ");
    return '<svg class="spark" viewBox="0 0 ' + w + " " + h + '" preserveAspectRatio="none" aria-hidden="true"><polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" opacity=".8"/></svg>';
  }
  function renderKpis() {
    var k = curRound().kpi;
    var items = [
      ["ตารางต้นทางที่เชื่อมต่อ", k.tables[0] + " ตาราง", k.tables, "#2F6FC2", SPARKS.tables, "จำนวนตารางต้นทางภายใน อย. ที่เชื่อมต่อกับ Data Pipeline ในรอบข้อมูลนี้"],
      ["แหล่งข้อมูลภายนอก", k.ext[0] + " แหล่ง", k.ext, "#12A594", SPARKS.ext, "จำนวนแหล่งข้อมูลภายนอกที่รับข้อมูลสำเร็จในรอบข้อมูลนี้"],
      ["ความครบถ้วนเฉลี่ย", fmt(k.comp[0], 1) + "%", k.comp, "#1F9D62", SPARKS.comp, "ค่าเฉลี่ย Completeness ของทุกตารางต้นทาง · เปลี่ยนแปลงเทียบรอบก่อน"],
      ["ความถูกต้องตามกฎ", fmt(k.valid[0], 1) + "%", k.valid, "#1F9D62", SPARKS.valid, "ค่าเฉลี่ย Validity (ผ่านกฎตรวจสอบรูปแบบและช่วงค่า) · เปลี่ยนแปลงเทียบรอบก่อน"],
      ["งานประมวลผลที่ล้มเหลว", k.failed[0] + " งาน", k.failed, "#D0463B", SPARKS.failed, "จำนวนงาน ETL ที่ล้มเหลวหรือหยุดกลางคันในรอบข้อมูลนี้ · เปลี่ยนแปลงเทียบรอบก่อน"]
    ];
    $("dqKpi").innerHTML = items.map(function (it) {
      var d = it[2], up = d.length > 3 ? d[3] : !d[2];
      return '<div class="kpi" title="' + it[5] + '"><div class="bar" style="background:' + it[3] + '"></div><div class="body"><div class="name">' + it[0] +
        '</div><div class="val">' + it[1] + '</div><div class="foot-row"><span class="delta' + (d[2] ? " bad" : "") + '">' + (up ? "▲ " : "▼ ") + d[1] +
        "</span>" + sparkSvg(it[4], it[3]) + "</div></div></div>";
    }).join("");
  }

  /* ── ตัวกรอง ── */
  function visibleTables() {
    return TABLES.map(rowValues).filter(function (r) {
      var typeOk = FILTER.type === "EXT" ? r.type === "EXT" : r.type === "INT";   // ภายใน + ภายนอก = แสดงตารางต้นทางภายใน (รูปที่ 9)
      if (FILTER.source !== "ALL") return r.source === FILTER.source;
      return typeOk;
    });
  }
  function fillSources() {
    var list = SOURCES.filter(function (x) { return FILTER.type === "ALL" || x.type === FILTER.type; });
    $("sourceSel").innerHTML = '<option value="ALL">ทั้งหมด</option>' + list.map(function (x) { return '<option value="' + x.key + '">' + x.label + "</option>"; }).join("");
    if (!list.some(function (x) { return x.key === FILTER.source; })) FILTER.source = "ALL";
    $("sourceSel").value = FILTER.source;
  }

  /* ── Scorecard ── */
  function renderTable() {
    var rows = visibleTables();
    if (!rows.some(function (r) { return r.name === FILTER.table; })) FILTER.table = rows.length ? rows[0].name : null;
    if (!rows.length) { $("dqBody").innerHTML = '<tr class="empty-row"><td colspan="10">ไม่มีตารางตามตัวกรองที่เลือก</td></tr>'; return; }
    $("dqBody").innerHTML = rows.map(function (r) {
      var st = statusOf(r);
      return '<tr data-t="' + r.name + '"' + (r.name === FILTER.table ? ' class="sel"' : "") + ' title="คลิกเพื่อดูผลการตรวจสอบรายขั้นตอนของ ' + r.name + '">' +
        "<td>" + r.domain + '</td><td><span class="clip clip-name">' + r.name + '</span></td><td class="num">' + r.fields + '</td><td class="num">' + fmt(r.records) +
        '</td><td class="num">' + fmt(r.comp, 1) + '%</td><td class="num">' + fmt(r.valid, 1) + '%</td><td class="num">' + fmt(r.dup, 1) + '%</td><td class="num">' + fmt(r.map, 1) +
        '%</td><td><span class="clip clip-time">' + r.time + '</span></td><td class="' + st[1] + '">' + st[0] + "</td></tr>";
    }).join("");
  }

  /* ── Pipeline ── */
  function pipelineFor(r) {
    if (r.name === "IM_PRODUCTRELEASEDINFO" && FILTER.round === "R0") return PIPE_FIG.slice();
    var a = r.records, s1 = a * (1 - 0.002), s2 = s1 * (1 - (100 - r.comp) * 0.0137), s3 = s2 * (1 - (100 - r.valid) / 100), s4 = s3 * (1 - r.dup / 100);
    return [a, s1, s2, s3, s4, s4].map(Math.round);
  }
  function renderPipe() {
    var r = visibleTables().filter(function (x) { return x.name === FILTER.table; })[0];
    if (!r) { $("pipe").innerHTML = ""; $("pipeCap").textContent = "เลือกตารางเพื่อดูผลการตรวจสอบรายขั้นตอน"; return; }
    var v = pipelineFor(r), max = v[0];
    $("pipeCap").textContent = r.name + " · ระเบียนที่ผ่านแต่ละขั้นตอน";
    $("pipe").innerHTML = PIPE_STEPS.map(function (st, i) {
      var pct = i > 0 && i < 5 ? (v[i] / v[i - 1] - 1) * 100 : null;
      var pctTxt = pct === null ? "" : (Math.abs(pct) < 1 ? pct.toFixed(2) : pct.toFixed(1)) + "%";
      var tip = st[0] + ": ผ่าน " + fmt(v[i]) + " ระเบียน" + (i > 0 ? " · ไม่ผ่าน " + fmt(v[i - 1] - v[i]) + " ระเบียน" : "");
      return '<div class="pipe-row" title="' + tip + '"><span class="lbl">' + st[0] + '</span><span class="bar-wrap"><span class="bar" style="width:' + (v[i] / max * 100).toFixed(1) +
        "%;background:" + st[1] + '">' + fmt(v[i]) + '</span></span><span class="pct">' + pctTxt + "</span></div>";
    }).join("");
  }

  /* ── Lineage ── */
  function renderLineage() {
    var L = LINEAGE.filter(function (x) { return x.id === FILTER.lineage; })[0];
    $("lineage").innerHTML = L.stages.map(function (st, i) {
      var body = st[1].map(function (item) { return Array.isArray(item) ? '<div class="note">' + item[0] + "</div>" : "<div>" + item.replace(/\|/g, "&#8203;") + "</div>"; }).join("");
      return (i ? '<span class="lin-arrow" aria-hidden="true">▶</span>' : "") + '<div class="lin-box" style="--c:' + LIN_COLORS[i] + '"><div class="hd">' + st[0] + '</div><div class="bd">' + body + '</div><div class="role">' + LIN_ROLES[i] + "</div></div>";
    }).join("");
  }

  /* ── Alert log ── */
  function renderLog() {
    var rows = LOGS.filter(function (l) { return FILTER.type === "ALL" ? l[0] === "INT" : l[0] === FILTER.type; });
    $("logBody").innerHTML = rows.map(function (l) {
      return "<tr><td>" + l[1] + "</td><td>" + l[2] + "</td><td>" + l[3] + "</td><td>" + l[4] + '</td><td class="' + statusCls(l[5]) + '">' + l[5] + "</td></tr>";
    }).join("") || '<tr class="empty-row"><td colspan="5">ไม่มีเหตุการณ์</td></tr>';
  }

  function applyFilters() {
    renderKpis(); renderTable(); renderPipe(); renderLog();
  }

  function wire() {
    $("roundSel").innerHTML = ROUNDS.map(function (r) { return '<option value="' + r.id + '">' + r.label + "</option>"; }).join("");
    $("lineageSel").innerHTML = LINEAGE.map(function (l) { return '<option value="' + l.id + '">' + l.label + "</option>"; }).join("");
    $("statusInfo").title = STATUS_TEXT;
    fillSources();
    $("roundSel").addEventListener("change", function (e) { FILTER.round = e.target.value; applyFilters(); });
    $("sourceSel").addEventListener("change", function (e) { FILTER.source = e.target.value; applyFilters(); });
    $("typeSel").addEventListener("change", function (e) { FILTER.type = e.target.value; fillSources(); applyFilters(); });
    $("lineageSel").addEventListener("change", function (e) { FILTER.lineage = e.target.value; renderLineage(); });
    $("dqBody").addEventListener("click", function (e) {
      var tr = e.target.closest("tr[data-t]");
      if (!tr) return;
      FILTER.table = tr.getAttribute("data-t"); renderTable(); renderPipe();
    });
    $("resetFiltersBtn").addEventListener("click", function () {
      FILTER = {round: "R0", source: "ALL", type: "ALL", table: "IM_PRODUCTRELEASEDINFO", lineage: "IMPORT"};
      $("roundSel").value = "R0"; $("typeSel").value = "ALL"; $("lineageSel").value = "IMPORT";
      fillSources(); applyFilters(); renderLineage();
    });
  }

  function renderHeaderAsOf() {
    var el = $("asOf");
    if (!el) return;
    var M = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."], d = new Date();
    el.textContent = d.getDate() + " " + M[d.getMonth()] + " " + (d.getFullYear() + 543);
  }

  function boot() {
    var page = $("dashPage");
    if (page) page.classList.add("dash-page");
    wire();
    renderHeaderAsOf();
    applyFilters();
    renderLineage();
    try { window.parent.postMessage("fda-dash-iframe-ready", "*"); } catch (e) {}
    if (window.dashLayoutResize) window.dashLayoutResize();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
