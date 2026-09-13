/* โหลดหลัง chart.js (+ chartjs-plugin-datalabels) และก่อน inline script ของหน้า */
(function () {
  if (!window.Chart) return;

  Chart.defaults.animation.duration = 300;
  Chart.defaults.font.family = '"Sarabun", "Noto Sans Thai", sans-serif';
  Chart.defaults.font.weight = "500";

  var ChartDataLabels = window.ChartDataLabels;
  if (ChartDataLabels) {
    Chart.register(ChartDataLabels);
    Chart.defaults.set("plugins.datalabels", { display: false });
  }

  function cssVar(name) {
    var el =
      document.body && document.body.getAttribute("data-dash")
        ? document.body
        : document.documentElement;
    return getComputedStyle(el).getPropertyValue(name).trim();
  }

  function dataLabelFontSize() {
    var dataFs = parseInt(cssVar("--fs-chart-data"), 10);
    if (dataFs && !isNaN(dataFs)) return dataFs;
    var axisFs = parseInt(cssVar("--fs-axis"), 10);
    if (axisFs && !isNaN(axisFs)) return Math.max(11, Math.round(axisFs * 0.62));
    return 13;
  }

  function chartLabelFont() {
    return {
      family: '"Sarabun", "Noto Sans Thai", sans-serif',
      size: dataLabelFontSize(),
      weight: "600",
    };
  }

  function chartAxisFontSize() {
    var axisFs = parseInt(cssVar("--fs-axis"), 10);
    if (axisFs && !isNaN(axisFs)) return axisFs;
    return 14;
  }

  function chartLegendFontSize() {
    var legFs = parseInt(cssVar("--fs-trend-legend"), 10);
    if (legFs && !isNaN(legFs)) return legFs;
    var uiMd = parseInt(cssVar("--fs-ui-md"), 10);
    if (uiMd && !isNaN(uiMd)) return uiMd;
    return 14;
  }

  /** แกนกราฟ — ป้ายหมวดแนวนอน (bar indexAxis y) ใช้ฟอนต์เล็กลง */
  function applyAxisFonts(cfg) {
    if (!cfg || !cfg.options) return cfg;
    var scales = cfg.options.scales;
    if (!scales) return cfg;
    var axisFs = chartAxisFontSize();
    var family = Chart.defaults.font.family;
    var horizBar = cfg.type === "bar" && cfg.options.indexAxis === "y";
    Object.keys(scales).forEach(function (key) {
      var sc = scales[key];
      if (!sc || sc === false) return;
      var tickFs = horizBar && key === "y" ? Math.min(13, axisFs) : axisFs;
      if (typeof sc.ticks !== "object" || sc.ticks === null || Array.isArray(sc.ticks)) {
        sc.ticks = {};
      }
      var userFont = (sc.ticks.font && typeof sc.ticks.font === "object") ? sc.ticks.font : {};
      sc.ticks.font = Object.assign({ size: tickFs, family: family }, userFont);
      if (sc.ticks.font.size > axisFs + 1) sc.ticks.font.size = tickFs;
      if (sc.pointLabels) {
        var plFont = (sc.pointLabels.font && typeof sc.pointLabels.font === "object")
          ? sc.pointLabels.font
          : {};
        sc.pointLabels.font = Object.assign(
          { size: Math.min(14, axisFs), family: family },
          plFont
        );
        if (sc.pointLabels.font.size > 16) sc.pointLabels.font.size = Math.min(14, axisFs);
      }
    });
    return cfg;
  }

  function numericValue(raw) {
    if (raw == null) return null;
    if (typeof raw === "object") {
      if (raw.y != null) return Number(raw.y);
      if (raw.x != null) return Number(raw.x);
    }
    return Number(raw);
  }

  function formatDashDataLabel(value, ctx) {
    if (value == null) return "";
    var n = numericValue(value);
    if (!isFinite(n)) return String(value);
    var chartType = ctx && ctx.chart ? ctx.chart.config.type : "";
    var abs = Math.abs(n);
    if (chartType === "line" && abs >= 10000) {
      return n.toLocaleString("th-TH", { maximumFractionDigits: 0 });
    }
    if (abs >= 1000) {
      return n.toLocaleString("th-TH", { maximumFractionDigits: 0 });
    }
    if (Number.isInteger(n)) return String(n);
    return n.toLocaleString("th-TH", { minimumFractionDigits: 0, maximumFractionDigits: 1 });
  }

  function lineLabelDisplay(ctx) {
    var labels = ctx.chart.data.labels || [];
    var i = ctx.dataIndex;
    var dsCount = ctx.chart.data.datasets.length;
    if (dsCount <= 1) return true;
    if (i === 0 || i === labels.length - 1) return true;
    if (labels.length >= 7) return i % 2 === 1;
    return true;
  }

  function lineLabelAlign(ctx) {
    var n = numericValue(ctx.dataset.data[ctx.dataIndex]);
    if (isFinite(n) && n < 0) return "bottom";
    var di = ctx.datasetIndex;
    return di % 2 === 0 ? "top" : "bottom";
  }

  function lineLabelOffset(ctx) {
    var di = ctx.datasetIndex;
    var base = 2 + (di >= 2 ? 10 : 0);
    var n = numericValue(ctx.dataset.data[ctx.dataIndex]);
    if (isFinite(n) && n < 0) return base + 2;
    return base;
  }

  function defaultDataLabelsFor(cfg) {
    var type = cfg.type;
    var indexAxis = cfg.options && cfg.options.indexAxis;
    var horizontal = type === "bar" && indexAxis === "y";
    var line = type === "line";
    var base = {
      formatter: function (val, ctx) {
        return formatDashDataLabel(val, ctx);
      },
      clamp: true,
      clip: false,
      color: function (ctx) {
        if (line) return ctx.dataset.borderColor || "#3D4F63";
        return "#3D4F63";
      },
      font: chartLabelFont(),
      padding: 0,
    };

    if (line) {
      return Object.assign(base, {
        display: lineLabelDisplay,
        anchor: "center",
        align: lineLabelAlign,
        offset: lineLabelOffset,
      });
    }

    return Object.assign(base, {
      display: true,
      anchor: horizontal ? "end" : "end",
      align: horizontal ? "end" : "top",
      offset: horizontal ? 3 : 2,
    });
  }

  function applyCircleLegend(cfg) {
    if (!cfg) return;
    cfg.options = cfg.options || {};
    cfg.options.plugins = cfg.options.plugins || {};
    var leg = cfg.options.plugins.legend;
    if (leg === false || (leg && leg.display === false)) return;
    var userLeg = leg || {};
    var userLabels = userLeg.labels || {};
    var legFs = chartLegendFontSize();
    cfg.options.plugins.legend = Object.assign({}, userLeg, {
      labels: Object.assign(
        {
          usePointStyle: true,
          pointStyle: "circle",
          boxWidth: 8,
          boxHeight: 8,
          padding: 10,
          font: Object.assign(
            { size: legFs, family: Chart.defaults.font.family, weight: "600" },
            userLabels.font || {}
          ),
        },
        userLabels,
        {
          usePointStyle:
            userLabels.usePointStyle != null ? userLabels.usePointStyle : true,
          pointStyle: userLabels.pointStyle || "circle",
        }
      ),
    });
  }

  function donutSliceTotal(ctx) {
    var data = (ctx.dataset && ctx.dataset.data) || [];
    return data.reduce(function (s, x) {
      return s + (Number(x) || 0);
    }, 0);
  }

  function applyDonutDataLabels(cfg) {
    if (!ChartDataLabels) return;
    cfg.options = cfg.options || {};
    cfg.options.plugins = cfg.options.plugins || {};
    if (cfg.options.plugins.datalabels === false) return;
    var user = cfg.options.plugins.datalabels || {};
    cfg.options.plugins.datalabels = Object.assign(
      {
        display: function (ctx) {
          var v = Number(ctx.dataset.data[ctx.dataIndex]);
          if (!isFinite(v) || v <= 0) return false;
          var total = donutSliceTotal(ctx);
          if (total <= 0) return false;
          return v / total >= 0.015;
        },
        formatter: function (value, ctx) {
          var total = donutSliceTotal(ctx);
          if (total <= 0) return "";
          var pct = (Number(value) / total) * 100;
          if (pct < 1.5) return "";
          return (
            pct.toLocaleString("th-TH", { maximumFractionDigits: 1 }) +
            "%"
          );
        },
        color: "#ffffff",
        textStrokeColor: "rgba(26, 36, 48, 0.45)",
        textStrokeWidth: 2,
        font: chartLabelFont(),
        anchor: "center",
        align: "center",
        clamp: true,
        clip: false,
      },
      user
    );
  }

  function applyScatterDataLabels(cfg) {
    if (!ChartDataLabels) return;
    cfg.options = cfg.options || {};
    cfg.options.plugins = cfg.options.plugins || {};
    if (cfg.options.plugins.datalabels === false) return;
    var user = cfg.options.plugins.datalabels || {};
    cfg.options.plugins.datalabels = Object.assign(
      {
        display: true,
        formatter: function (val, ctx) {
          var pt = ctx.dataset.data[ctx.dataIndex];
          if (pt && pt.label) return String(pt.label);
          return "";
        },
        color: "#3D4F63",
        font: chartLabelFont(),
        anchor: "end",
        align: "top",
        offset: 8,
        clamp: true,
        clip: false,
      },
      user
    );
  }

  function applyDonutLayout(cfg) {
    if (!cfg || (cfg.type !== "doughnut" && cfg.type !== "pie")) return;
    cfg.options = cfg.options || {};
    if (cfg.options.maintainAspectRatio == null) cfg.options.maintainAspectRatio = false;
    var userLayout = cfg.options.layout || {};
    var userPad = userLayout.padding || {};
    cfg.options.layout = Object.assign({}, userLayout, {
      padding: Object.assign({ top: 8, bottom: 4, left: 8, right: 8 }, userPad),
    });
    if (cfg.type === "doughnut" && cfg.options.cutout == null) {
      cfg.options.cutout = "46%";
    }
    cfg.options.plugins = cfg.options.plugins || {};
    var leg = cfg.options.plugins.legend;
    if (leg !== false && !(leg && leg.display === false)) {
      var userLeg = leg || {};
      var userLbl = userLeg.labels || {};
      cfg.options.plugins.legend = Object.assign({}, userLeg, {
        position: userLeg.position || "bottom",
        align: userLeg.align || "center",
        labels: Object.assign({ padding: 8, boxWidth: 10, boxHeight: 10 }, userLbl),
      });
    }
    if (cfg.data && cfg.data.datasets) {
      cfg.data.datasets.forEach(function (ds) {
        if (ds.radius == null) ds.radius = "94%";
        if (ds.hoverRadius == null) ds.hoverRadius = "96%";
      });
    }
    applyDonutDataLabels(cfg);
  }

  function ensureChartInteraction(cfg) {
    cfg.options = cfg.options || {};
    var interaction = Object.assign({ mode: "nearest", intersect: false }, cfg.options.interaction || {});
    if (cfg.options.indexAxis === "y") interaction.axis = "y";
    cfg.options.interaction = interaction;
    var prevHover = cfg.options.onHover;
    cfg.options.onHover = function (evt, elements) {
      if (typeof prevHover === "function") prevHover.call(this, evt, elements);
      var t = evt.native && evt.native.target;
      if (t) t.style.cursor = elements.length ? "pointer" : "default";
    };
    return cfg;
  }

  window.dashPrepareChart = function (cfg) {
    if (!cfg) return cfg;
    applyCircleLegend(cfg);
    if (cfg.type === "doughnut" || cfg.type === "pie") {
      applyDonutLayout(cfg);
      applyAxisFonts(cfg);
      return ensureChartInteraction(cfg);
    }
    if (cfg.type === "scatter" || cfg.type === "bubble") {
      cfg.options = cfg.options || {};
      if (cfg.options.maintainAspectRatio == null) cfg.options.maintainAspectRatio = false;
      var scLayout = cfg.options.layout || {};
      var scPad = scLayout.padding || {};
      cfg.options.layout = Object.assign({}, scLayout, {
        padding: Object.assign({ top: 14, bottom: 8, left: 8, right: 12 }, scPad),
      });
      applyScatterDataLabels(cfg);
      applyAxisFonts(cfg);
      return ensureChartInteraction(cfg);
    }
    if (cfg.type === "radar") {
      applyAxisFonts(cfg);
      return ensureChartInteraction(cfg);
    }
    if (cfg.type !== "bar" && cfg.type !== "line") {
      applyAxisFonts(cfg);
      return ensureChartInteraction(cfg);
    }
    cfg.options = cfg.options || {};
    cfg.options.plugins = cfg.options.plugins || {};
    if (cfg.options.indexAxis === "y") {
      cfg.options.layout = Object.assign(
        { padding: { top: 4, bottom: 4, left: 2, right: 10 } },
        cfg.options.layout || {}
      );
    }
    if (cfg.options.plugins.datalabels === false) {
      applyAxisFonts(cfg);
      return ensureChartInteraction(cfg);
    }
    if (cfg.type === "line") {
      cfg.options.layout = Object.assign(
        { padding: { top: 14, bottom: 6, left: 4, right: 8 } },
        cfg.options.layout || {}
      );
    }
    var user = cfg.options.plugins.datalabels;
    var base = defaultDataLabelsFor(cfg);
    cfg.options.plugins.datalabels = Object.assign({}, base, user || {});
    applyAxisFonts(cfg);
    return ensureChartInteraction(cfg);
  };

  /** คลิกกราฟ / legend โดนัท → กรองกลุ่มผลิตภัณฑ์ (ใช้ร่วม d2–d8) */
  window.chartClickGroup = function (chart, labels, codes, onPick) {
    if (!chart) return;
    var pick =
      onPick ||
      (typeof window.onGroupFilter === "function" ? window.onGroupFilter : null);
    if (!pick && typeof clickGroup === "function") pick = clickGroup;
    if (!pick) return;

    var type = chart.config.type;

    /* อย่าแทนที่ object ใน chart.options (Chart.js 4 proxy) — จะ stack overflow ตอน update */
    chart.$dashGroupCodes = codes;
    chart.options.onClick = function (evt, elements) {
      if (!elements || !elements.length) return;
      var el = elements[0];
      var c = chart.$dashGroupCodes;
      var idx =
        type === "radar" || type === "scatter" || type === "bubble"
          ? el.datasetIndex != null
            ? el.datasetIndex
            : el.index
          : el.index;
      if (idx == null || idx < 0) return;
      var code = c && c.length ? c[idx] : null;
      if (code) pick(code);
    };

    if (type === "doughnut" || type === "pie") {
      if (!chart.options.plugins) chart.options.plugins = {};
      if (!chart.options.plugins.legend) chart.options.plugins.legend = {};
      chart.options.plugins.legend.onClick = function (e, legendItem) {
        if (e && e.native && e.native.stopPropagation) e.native.stopPropagation();
        var c = chart.$dashGroupCodes;
        var idx = legendItem.index;
        if (idx == null || idx < 0) return;
        var code = c && c.length ? c[idx] : null;
        if (code) pick(code);
      };
    }

    if (!chart.options.interaction) chart.options.interaction = {};
    if (chart.options.interaction.mode == null) chart.options.interaction.mode = "nearest";
    if (chart.options.interaction.intersect == null) chart.options.interaction.intersect = false;
    chart.options.onHover = function (evt, elements) {
      var t = evt.native && evt.native.target;
      if (t) t.style.cursor = elements.length ? "pointer" : "default";
    };
  };

  window.dashFyFactor = function (fy, baseYear) {
    var base = baseYear == null ? 2568 : baseYear;
    var y = fy == null ? base : +fy;
    return 1 + (base - y) * 0.02;
  };
})();
