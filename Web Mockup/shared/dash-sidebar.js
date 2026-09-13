(function () {
  if (window.self !== window.top) return;

  var DASH_ITEMS = [
    { n: 1, label: "ภาพรวมเศรษฐกิจผลิตภัณฑ์สุขภาพ" },
    { n: 2, label: "การวิเคราะห์โอกาสทางเศรษฐกิจ" },
    { n: 3, label: "การวิเคราะห์ผลิตภัณฑ์ดาวรุ่ง" },
    { n: 4, label: "การวิเคราะห์คอขวดด้านการกำกับดูแล" },
    { n: 5, label: "เมทริกซ์โอกาสเชิงกฎระเบียบ" },
    { n: 6, label: "การวิเคราะห์ผู้ประกอบการที่มีศักยภาพ" },
    { n: 7, label: "ข้อมูลเชิงลึกรายผลิตภัณฑ์" },
    { n: 8, label: "ข้อเสนอเชิงนโยบายและการจำลองสถานการณ์" },
    { n: 9, label: "แผนที่วิเคราะห์เชิงพื้นที่" },
    { n: 10, label: "การติดตามคุณภาพข้อมูลและธรรมาภิบาลข้อมูล" }
  ];

  var STORAGE_KEY = "fdaDashSidebarCollapsed";
  /* ต้องตรงกับ transition ของ .dash-page-exiting / .dash-frame-loading */
  var EXIT_MS = 120;
  var reduceMotion = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function isShell() {
    return document.body && document.body.hasAttribute("data-dash-shell");
  }

  function onReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function detectDashNum() {
    if (isShell()) return dashNumFromHash();
    var fromBody = document.body && document.body.getAttribute("data-dash");
    if (fromBody) return parseInt(fromBody, 10);
    var m = (location.pathname || "").match(/d(\d+)(?:_NEW)?\.html/i);
    if (m) return parseInt(m[1], 10);
    return 1;
  }

  function dashNumFromHash() {
    var h = (location.hash || "#dash1").replace(/^#/, "");
    var m = h.match(/^dash(\d+)$/i);
    return m ? parseInt(m[1], 10) : 1;
  }

  function inDashboardsFolder() {
    return /\/dashboards\//i.test(location.pathname || "");
  }

  function hrefForDash(n) {
    if (n === 1) return inDashboardsFolder() ? "d1.html" : "d1_NEW.html";
    return "d" + n + ".html";
  }

  function sidebarCssHref() {
    var scripts = document.getElementsByTagName("script");
    for (var i = 0; i < scripts.length; i++) {
      var src = scripts[i].getAttribute("src") || "";
      if (src.indexOf("dash-sidebar.js") !== -1) {
        return src.replace(/dash-sidebar\.js.*$/, "dash-sidebar.css");
      }
    }
    return "shared/dash-sidebar.css";
  }

  function ensureStyles() {
    /* ใช้ <link> ใน HTML เป็นหลัก — ขนาดเมนูฐาน d1 จาก dash-sidebar.css */
    if (document.querySelector('link[data-dash-sidebar="1"]') || document.querySelector('link[href*="dash-sidebar.css"]')) {
      return;
    }
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = sidebarCssHref();
    link.setAttribute("data-dash-sidebar", "1");
    document.head.appendChild(link);
  }

  function storedCollapsed(fallback) {
    try {
      var v = localStorage.getItem(STORAGE_KEY);
      if (v === "1") return true;
      if (v === "0") return false;
    } catch (e) {}
    return fallback;
  }

  function sharedAssetHref(fileName) {
    var scripts = document.getElementsByTagName("script");
    for (var i = 0; i < scripts.length; i++) {
      var src = scripts[i].getAttribute("src") || "";
      if (src.indexOf("dash-sidebar.js") !== -1) {
        return src.replace(/dash-sidebar\.js.*$/, fileName);
      }
    }
    return "shared/" + fileName;
  }

  function applySidebarLogo() {
    var img = document.querySelector(".dash-sidebar-logo-img");
    if (!img) return;
    var src = null;
    var frame = document.getElementById("dashContentFrame");
    if (frame) {
      try {
        var doc = frame.contentDocument;
        var hLogo = doc && doc.querySelector("header .brandLogo");
        if (hLogo && hLogo.getAttribute("src")) src = hLogo.getAttribute("src");
      } catch (e) {}
    }
    if (!src) {
      var header = document.querySelector("header .brandLogo");
      if (header && header.getAttribute("src")) src = header.getAttribute("src");
    }
    if (!src && window.FDA_LOGO_DATA_URI) src = window.FDA_LOGO_DATA_URI;
    if (!src) src = sharedAssetHref("fda-logo.svg");
    img.onerror = function () {
      if (window.FDA_LOGO_DATA_URI && img.getAttribute("src") !== window.FDA_LOGO_DATA_URI) {
        img.onerror = null;
        img.setAttribute("src", window.FDA_LOGO_DATA_URI);
      }
    };
    img.style.display = "";
    img.setAttribute("src", src);
    img.setAttribute("alt", "อย.");
  }

  function afterSidebarToggle() {
    window.dispatchEvent(new Event("resize"));
    var frame = document.getElementById("dashContentFrame");
    if (frame && frame.contentWindow) {
      try {
        frame.contentWindow.dispatchEvent(new Event("resize"));
        if (frame.contentWindow.dashLayoutResize) frame.contentWindow.dashLayoutResize();
      } catch (e) {}
    }
  }

  function syncToggleUi() {
    var collapsed = document.body.classList.contains("dash-sidebar-collapsed");
    var btn = document.querySelector(".dash-page .filters .dash-menu-btn");
    if (btn) {
      var label = collapsed ? "แสดงเมนู" : "ซ่อนเมนู";
      btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
      btn.setAttribute("aria-label", label);
      btn.setAttribute("title", label);
    }
    var aside = document.querySelector(".dash-sidebar");
    if (aside) aside.setAttribute("aria-hidden", collapsed ? "true" : "false");
  }

  function setCollapsed(collapsed) {
    document.body.classList.toggle("dash-sidebar-collapsed", collapsed);
    try {
      localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch (e) {}
    syncToggleUi();
    afterSidebarToggle();
    if (window.dashLayoutResize) window.dashLayoutResize();
  }

  function setActiveNav(num) {
    var aside = document.querySelector(".dash-sidebar");
    if (!aside) return;
    aside.querySelectorAll(".dash-sidebar-link").forEach(function (a) {
      a.classList.toggle("active", parseInt(a.getAttribute("data-dash-n"), 10) === num);
    });
    document.body.setAttribute("data-dash", String(num));
  }

  function toggleSidebar() {
    setCollapsed(!document.body.classList.contains("dash-sidebar-collapsed"));
  }

  function buildSidebar(activeNum) {
    var aside = document.createElement("aside");
    aside.className = "dash-sidebar";
    aside.setAttribute("aria-label", "เมนูแดชบอร์ด");
    aside.setAttribute("aria-hidden", "true");

    var head = document.createElement("div");
    head.className = "dash-sidebar-head";
    head.innerHTML =
      '<img class="dash-sidebar-logo-img" alt="">' +
      '<div class="dash-sidebar-org">สำนักงานคณะกรรมการอาหารและยา<br>กระทรวงสาธารณสุข</div>';
    aside.appendChild(head);

    var nav = document.createElement("nav");
    nav.className = "dash-sidebar-nav";
    nav.innerHTML = '<div class="dash-sidebar-label">แดชบอร์ด · 4.3.4.3</div>';

    DASH_ITEMS.forEach(function (item) {
      var a = document.createElement("a");
      a.className = "dash-sidebar-link" + (item.n === activeNum ? " active" : "");
      a.href = hrefForDash(item.n);
      a.setAttribute("data-dash-n", String(item.n));
      a.innerHTML = '<span class="num">' + item.n + "</span><span>" + item.label + "</span>";
      nav.appendChild(a);
    });
    aside.appendChild(nav);
    return aside;
  }

  function mountBackdrop() {
    var bd = document.createElement("button");
    bd.type = "button";
    bd.className = "dash-sidebar-backdrop";
    bd.setAttribute("aria-label", "ปิดเมนู");
    bd.addEventListener("click", function () {
      setCollapsed(true);
    });
    document.body.appendChild(bd);
  }

  /* หน้าที่ build ใหม่โดยไม่มี markup ปุ่ม (เช่น d1_NEW จาก build script) — สร้างปุ่มให้ */
  function ensureMenuButton(root) {
    var btn = root.querySelector(".filters .dash-menu-btn");
    if (btn) return btn;
    var bar = root.querySelector(".filters .static-filters");
    if (!bar) return null;
    btn = document.createElement("button");
    btn.type = "button";
    btn.className = "dash-menu-btn";
    btn.innerHTML = '<i class="dash-menu-icon" aria-hidden="true"></i>';
    bar.insertBefore(btn, bar.firstChild);
    return btn;
  }

  function wireMenuButton() {
    var page = document.querySelector(".dash-page");
    var btn = page && ensureMenuButton(page);
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      toggleSidebar();
    });
    syncToggleUi();
  }

  /* ── shell: dashboard.html — เมนูคงที่ + สลับเฉพาะ iframe ─────────── */
  function initShell() {
    ensureStyles();
    var frame = document.getElementById("dashContentFrame");
    var body = document.body;
    var current = dashNumFromHash();
    var navTimer = null;

    var aside = buildSidebar(current);
    body.insertBefore(aside, frame);
    body.classList.add("dash-with-sidebar");
    body.classList.toggle("dash-sidebar-collapsed", storedCollapsed(false));
    mountBackdrop();
    applySidebarLogo();
    syncToggleUi();
    setActiveNav(current);
    if (location.hash !== "#dash" + current) history.replaceState(null, "", "#dash" + current);

    if (!frame) return;
    if (frame.getAttribute("src") !== hrefForDash(current)) frame.setAttribute("src", hrefForDash(current));

    frame.addEventListener("load", function () {
      if (navTimer) return;
      frame.classList.remove("dash-frame-loading");
      applySidebarLogo();
      afterSidebarToggle();
    });

    /* location.replace ใน iframe ไม่เพิ่ม history — history มีแค่ #hash ครั้งละ 1 รายการ */
    function show(n) {
      if (n === current) return;
      current = n;
      setActiveNav(n);
      clearTimeout(navTimer);
      frame.classList.add("dash-frame-loading");
      navTimer = setTimeout(function () {
        navTimer = null;
        frame.contentWindow.location.replace(hrefForDash(n));
      }, reduceMotion ? 0 : EXIT_MS);
    }

    aside.addEventListener("click", function (e) {
      var a = e.target.closest(".dash-sidebar-link");
      if (!a) return;
      e.preventDefault();
      var n = parseInt(a.getAttribute("data-dash-n"), 10);
      if (n === current) return;
      show(n);
      location.hash = "dash" + n;
    });

    window.addEventListener("hashchange", function () {
      show(dashNumFromHash());
    });

    window.addEventListener("message", function (e) {
      if (e && e.data === "fda-dash-toggle-sidebar") toggleSidebar();
    });
  }

  /* ── standalone: d1_NEW.html … d10.html ─────────────────────────────
     สคริปต์นี้ถูกโหลดแบบ sync ที่ต้น <div id="dashPage"> — เมนูจึงอยู่ครบก่อนเนื้อหา/กราฟถูก parse
     ไม่ต้องย้าย DOM หลังกราฟวาดเสร็จ */
  function initStandalone() {
    ensureStyles();
    var body = document.body;
    var page = document.getElementById("dashPage");
    if (!page) {
      page = document.createElement("div");
      page.id = "dashPage";
      while (body.firstChild) page.appendChild(body.firstChild);
      body.appendChild(page);
    }
    page.classList.add("dash-page");
    if (!reduceMotion) page.classList.add("dash-page-enter");

    var aside = buildSidebar(detectDashNum());
    body.insertBefore(aside, page);
    body.classList.add("dash-with-sidebar");
    body.classList.toggle("dash-sidebar-collapsed", storedCollapsed(true));
    mountBackdrop();
    syncToggleUi();

    aside.addEventListener("click", function (e) {
      var a = e.target.closest(".dash-sidebar-link");
      if (!a) return;
      e.preventDefault();
      if (a.classList.contains("active")) return;
      var href = a.getAttribute("href");
      if (reduceMotion) {
        location.href = href;
        return;
      }
      page.classList.add("dash-page-exiting");
      setTimeout(function () {
        location.href = href;
      }, EXIT_MS);
    });

    /* กลับมาด้วยปุ่ม Back (bfcache) — หน้าเดิมยังค้าง class exiting (opacity 0) */
    window.addEventListener("pageshow", function (e) {
      if (e.persisted) page.classList.remove("dash-page-exiting");
    });

    onReady(function () {
      if (!document.querySelector("script[src*='fda-logo-data.js']")) {
        var logoJs = document.createElement("script");
        logoJs.src = sharedAssetHref("fda-logo-data.js");
        logoJs.onload = applySidebarLogo;
        logoJs.onerror = applySidebarLogo;
        document.head.appendChild(logoJs);
      } else {
        applySidebarLogo();
      }
      wireMenuButton();
      if (page.classList.contains("dash-page-enter")) {
        void page.offsetWidth; /* บังคับคำนวณ style ตอน opacity 0 ก่อน ไม่งั้น transition ไม่เกิด */
        page.classList.remove("dash-page-enter");
      }
    });
  }

  window.fdaDashShell = {
    setActiveNav: setActiveNav,
    toggleSidebar: toggleSidebar,
  };

  if (isShell()) onReady(initShell);
  else if (document.getElementById("dashPage") || document.readyState !== "loading") initStandalone();
  else document.addEventListener("DOMContentLoaded", initStandalone);
})();
