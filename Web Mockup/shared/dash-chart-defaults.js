/* โหลดหลัง chart.js (+ chartjs-plugin-datalabels) และก่อน inline script ของหน้า */
(function () {
  if (!window.Chart) return;

  Chart.defaults.animation.duration = 300;

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
    var family =
      getComputedStyle(document.body).fontFamily ||
      getComputedStyle(document.documentElement).fontFamily;
    return {
      family: family,
      size: dataLabelFontSize(),
      weight: "600",
    };
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
    cfg.options.plugins.legend = Object.assign({}, userLeg, {
      labels: Object.assign(
        {
          usePointStyle: true,
          pointStyle: "circle",
          boxWidth: 8,
          boxHeight: 8,
          padding: 12,
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

  window.dashPrepareChart = function (cfg) {
    if (!cfg) return cfg;
    applyCircleLegend(cfg);
    if (cfg.type === "doughnut" || cfg.type === "pie") {
      applyDonutLayout(cfg);
      return cfg;
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
      return cfg;
    }
    if (cfg.type !== "bar" && cfg.type !== "line") return cfg;
    cfg.options = cfg.options || {};
    cfg.options.plugins = cfg.options.plugins || {};
    if (cfg.options.plugins.datalabels === false) return cfg;
    if (cfg.type === "line") {
      cfg.options.layout = Object.assign(
        { padding: { top: 14, bottom: 6, left: 4, right: 8 } },
        cfg.options.layout || {}
      );
    }
    var user = cfg.options.plugins.datalabels;
    var base = defaultDataLabelsFor(cfg);
    cfg.options.plugins.datalabels = Object.assign({}, base, user || {});
    return cfg;
  };
})();
