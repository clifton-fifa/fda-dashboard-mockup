/* หน้า 10 — โหลดแยกจาก HTML เพื่อไม่ให้ inline script ล้ม (CSP / parse) */
(function () {
  "use strict";

  var GROUPS = [
    { code: "DRUG", name: "ยา", color: "#1F6FB2" },
    { code: "MDC", name: "เครื่องมือแพทย์", color: "#12A594" },
    { code: "FOOD", name: "อาหาร", color: "#3E9F55" },
    { code: "CMT", name: "เครื่องสำอาง", color: "#E8A317" },
    { code: "HERB", name: "สมุนไพร", color: "#7E57C2" },
    { code: "TXC", name: "วัตถุอันตราย", color: "#C0392B" },
    { code: "NCT", name: "วัตถุเสพติด", color: "#7F8C8D" },
  ];

  var HEALTH = [
    { metric_name_th: "ความครบถ้วนของข้อมูล", value: 98.6, unit: "%", status: "ปกติ" },
    { metric_name_th: "ความถูกต้องตามกฎ", value: 96.2, unit: "%", status: "ปกติ" },
    { metric_name_th: "ข้อมูลซ้ำซ้อน", value: 0.8, unit: "%", status: "ปกติ" },
    { metric_name_th: "อัตราเชื่อมโยงรหัส HS สำเร็จ", value: 92.0, unit: "%", status: "เฝ้าระวัง" },
    { metric_name_th: "รอบปรับปรุงข้อมูลล่าสุด", value: null, unit: "30 มิ.ย. 2569", status: "ปกติ" },
    { metric_name_th: "จำนวนตารางต้นทางที่เชื่อมต่อ", value: null, unit: "25 ตาราง / 24 แหล่งภายนอก", status: "ปกติ" },
  ];

  var FILTER = { group: "ALL", fy: 2568, txn: "all", prov: "ทั่วประเทศ" };
  var charts = {};
  var TH_MONTH_NAME = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];
  var TH_MONTH_ABBR = TH_MONTH_NAME;

  function gColor(code) {
    if (code === "ALL") return "#12305B";
    for (var i = 0; i < GROUPS.length; i++) {
      if (GROUPS[i].code === code) return GROUPS[i].color;
    }
    return "#1F6FB2";
  }

  function prepareChart(cfg) {
    if (window.dashPrepareChart) return window.dashPrepareChart(cfg);
    return cfg;
  }

  function destroyChart(id) {
    if (charts[id]) {
      charts[id].destroy();
      delete charts[id];
    }
  }

  function setChart(id, cfg) {
    var el = document.getElementById(id);
    if (!el || typeof Chart === "undefined") return null;
    destroyChart(id);
    try {
      charts[id] = new Chart(el, prepareChart(cfg));
    } catch (err) {
      console.error("[d10] Chart failed:", id, err);
      return null;
    }
    return charts[id];
  }

  function syncChips(code) {
    document.querySelectorAll(".chip[data-g]").forEach(function (x) {
      x.setAttribute("aria-pressed", x.getAttribute("data-g") === code ? "true" : "false");
    });
  }

  function healthMetricDisplay(h, factor) {
    if (h.unit === "%") return (Number(h.value) * factor).toFixed(1) + "%";
    var v = h.value;
    if (v == null || (typeof v === "number" && isNaN(v))) return h.unit || "—";
    return String(v) + (h.unit ? " " + h.unit : "");
  }

  function statusBadge(status) {
    if (status === "ปกติ") return '<span class="badge badge-pass">' + status + "</span>";
    return '<span class="badge badge-warn">' + status + "</span>";
  }

  function applyFilters() {
    var g = FILTER.group;
    var factor = g === "ALL" ? 1 : g === "HERB" ? 0.97 : g === "DRUG" ? 0.99 : 1.01;
    var kpiEl = document.getElementById("healthKpi");
    var bodyEl = document.getElementById("healthBody");
    if (!kpiEl || !bodyEl) {
      console.warn("[d10] missing #healthKpi or #healthBody");
      return;
    }

    kpiEl.innerHTML = HEALTH.slice(0, 4)
      .map(function (h) {
        return (
          '<div class="kpi"><div class="bar" style="background:' +
          gColor(g) +
          '"></div><div class="body"><div class="name">' +
          h.metric_name_th +
          '</div><div class="val">' +
          healthMetricDisplay(h, factor) +
          "</div></div></div>"
        );
      })
      .join("");

    bodyEl.innerHTML = HEALTH.map(function (h) {
      return (
        "<tr><td>" +
        h.metric_name_th +
        '</td><td class="num">' +
        healthMetricDisplay(h, factor) +
        '</td><td class="cen">' +
        statusBadge(h.status) +
        "</td></tr>"
      );
    }).join("");

    var pass = Math.round(4100 * factor);
    var fail = Math.round(900 / factor);
    var qa = Math.round(48 * factor);
    setChart("cClean", {
      type: "doughnut",
      data: {
        labels: ["ผ่าน", "ไม่ผ่าน", "ตรวจสอบ", "ไม่เปลี่ยน"],
        datasets: [
          {
            data: [pass, fail, qa, 952],
            backgroundColor: ["#1F7A45", "#C0392B", "#D68910", "#9AA5B1"],
            hoverBackgroundColor: ["#1F7A45", "#C0392B", "#D68910", "#9AA5B1"],
            borderColor: "#fff",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: { top: 6, bottom: 2, left: 4, right: 4 } },
        plugins: { legend: { position: "bottom", labels: { padding: 10 } } },
      },
    });
  }

  function clickGroup(code) {
    FILTER.group = code;
    syncChips(code);
    applyFilters();
  }

  function initD1FilterBar() {
    var selM = document.getElementById("filterMonth");
    if (!selM || !selM.options || selM.options.length > 1) return;
    selM.innerHTML =
      '<option value="ALL" selected>ทั้งหมด</option>' +
      TH_MONTH_NAME.map(function (n, i) {
        return '<option value="' + String(i + 1).padStart(2, "0") + '">' + n + "</option>";
      }).join("");
  }

  function resetDashFilters() {
    FILTER.group = "ALL";
    FILTER.fy = 2568;
    FILTER.txn = "all";
    FILTER.prov = "ทั่วประเทศ";
    syncChips("ALL");
    var fy = document.getElementById("fySel");
    if (fy) fy.value = "2568";
    var txn = document.getElementById("txnSel");
    if (txn) txn.value = "all";
    var prov = document.getElementById("provSel");
    if (prov) prov.value = "ทั่วประเทศ";
    var selM = document.getElementById("filterMonth");
    if (selM) selM.value = "ALL";
    applyFilters();
  }

  function wireFilters() {
    document.querySelectorAll(".chip[data-g]").forEach(function (c) {
      c.addEventListener("click", function () {
        clickGroup(c.getAttribute("data-g"));
      });
    });
    var resetBtn = document.getElementById("resetFiltersBtn");
    if (resetBtn) resetBtn.addEventListener("click", resetDashFilters);
    var fySel = document.getElementById("fySel");
    if (fySel) {
      fySel.addEventListener("change", function (e) {
        FILTER.fy = e.target.value === "ALL" ? 2568 : +e.target.value;
        applyFilters();
      });
    }
    var txnSel = document.getElementById("txnSel");
    if (txnSel) {
      txnSel.addEventListener("change", function (e) {
        FILTER.txn = e.target.value;
        applyFilters();
      });
    }
    var provSel = document.getElementById("provSel");
    if (provSel) {
      provSel.addEventListener("change", function (e) {
        FILTER.prov = e.target.value;
        applyFilters();
      });
    }
  }

  function renderHeaderAsOf() {
    var el = document.getElementById("asOf");
    if (!el) return;
    var d = new Date();
    el.textContent = d.getDate() + " " + TH_MONTH_ABBR[d.getMonth()] + " " + (d.getFullYear() + 543);
  }

  function boot() {
    var page = document.getElementById("dashPage");
    if (page) page.classList.add("dash-page");
    initD1FilterBar();
    wireFilters();
    window.onGroupFilter = clickGroup;
    renderHeaderAsOf();
    applyFilters();
    try {
      window.parent.postMessage("fda-dash-iframe-ready", "*");
    } catch (e) {}
    if (window.dashLayoutResize) window.dashLayoutResize();
  }

  function scheduleBoot() {
    if (typeof Chart === "undefined") {
      window.addEventListener("load", boot, { once: true });
    } else {
      boot();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleBoot);
  } else {
    scheduleBoot();
  }
})();
