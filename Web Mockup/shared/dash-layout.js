(function () {
  function debounce(fn, ms) {
    var t;
    return function () {
      clearTimeout(t);
      var args = arguments;
      var self = this;
      t = setTimeout(function () {
        fn.apply(self, args);
      }, ms);
    };
  }

  function resizeCharts() {
    try {
      if (typeof Chart !== "undefined") {
        if (typeof Chart.getChart === "function") {
          document.querySelectorAll("canvas").forEach(function (el) {
            var c = Chart.getChart(el);
            if (c) c.resize();
          });
        } else if (Chart.instances) {
          Object.values(Chart.instances).forEach(function (c) {
            if (c && c.resize) c.resize();
          });
        }
      }
    } catch (e) {}
  }

  /* ใน iframe ของ dashboard.html — ปุ่ม ☰ สั่ง shell ให้เปิด/ปิดเมนู (ไม่รู้สถานะเมนู จึงไม่ใส่ aria-expanded) */
  function wireIframeMenuButton() {
    if (window.self === window.top) return;
    var btn = document.querySelector(".filters .dash-menu-btn");
    if (!btn) {
      var bar = document.querySelector(".filters .static-filters");
      if (!bar) return;
      btn = document.createElement("button");
      btn.type = "button";
      btn.className = "dash-menu-btn";
      btn.innerHTML = '<i class="dash-menu-icon" aria-hidden="true"></i>';
      bar.insertBefore(btn, bar.firstChild);
    }
    btn.removeAttribute("aria-expanded");
    btn.setAttribute("aria-label", "แสดง/ซ่อนเมนู");
    btn.setAttribute("title", "แสดง/ซ่อนเมนู");

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      try {
        window.parent.postMessage("fda-dash-toggle-sidebar", "*");
      } catch (e2) {}
    });
  }

  function observeFlexChartBoxes() {
    if (typeof ResizeObserver === "undefined") return;
    var ro = new ResizeObserver(debounce(resizeCharts, 60));
    document
      .querySelectorAll(
        ".chart-box--donut-fill, .card--chart-grow .chart-box, .card--chart-grow #mapEl"
      )
      .forEach(function (el) {
        ro.observe(el);
      });
  }

  function init() {
    wireIframeMenuButton();
    window.addEventListener("load", function () {
      resizeCharts();
      setTimeout(function () {
        resizeCharts();
        observeFlexChartBoxes();
      }, 200);
    });
    window.addEventListener("resize", debounce(resizeCharts, 120));
    window.addEventListener(
      "orientationchange",
      function () {
        setTimeout(resizeCharts, 200);
      }
    );
  }

  window.dashLayoutResize = resizeCharts;

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
