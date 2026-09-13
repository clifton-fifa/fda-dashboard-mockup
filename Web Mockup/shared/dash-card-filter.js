/* ตัวกรองในการ์ด: ปุ่มกรวยอย่างเดียว (แบบ d1) → เมนูเลือกค่า, ซ่อน select */
(function () {
  var FUNNEL =
    '<svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">' +
    '<path d="M1 2h14l-5.5 6.3V13.2l-3 1.3V8.3z"/></svg>';

  function closeAllCardFilterMenus() {
    document.querySelectorAll(".cardFilterMenu.open").forEach(function (m) {
      m.classList.remove("open");
    });
    document.querySelectorAll(".card-filter-trigger[aria-expanded='true']").forEach(function (b) {
      b.setAttribute("aria-expanded", "false");
    });
  }

  function rebuildMenu(menu, select) {
    menu.innerHTML = "";
    Array.from(select.options).forEach(function (opt) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cardFilterOption";
      btn.setAttribute("role", "menuitemradio");
      btn.textContent = opt.textContent;
      btn.setAttribute("aria-pressed", opt.selected ? "true" : "false");
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        select.value = opt.value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        menu.querySelectorAll(".cardFilterOption").forEach(function (x) {
          x.setAttribute("aria-pressed", "false");
        });
        btn.setAttribute("aria-pressed", "true");
        closeAllCardFilterMenus();
      });
      menu.appendChild(btn);
    });
  }

  function initPick(pick) {
    var select = pick.querySelector("select.card-filter-select");
    if (!select || select.dataset.cardFilterReady === "1") return;
    select.dataset.cardFilterReady = "1";

    var shell = pick.querySelector(".card-filter-shell");
    if (shell) {
      while (shell.firstChild) pick.insertBefore(shell.firstChild, shell);
      shell.remove();
    }

    select.classList.add("card-filter-select-native");
    var title =
      select.getAttribute("aria-label") || select.getAttribute("title") || "ตัวกรอง";

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "periodBtn card-filter-trigger";
    btn.setAttribute("aria-expanded", "false");
    btn.setAttribute("aria-haspopup", "menu");
    btn.setAttribute("title", title);
    btn.innerHTML = FUNNEL;

    var menu = document.createElement("div");
    menu.className = "cardFilterMenu";
    menu.setAttribute("role", "menu");
    menu.addEventListener("click", function (e) {
      e.stopPropagation();
    });

    rebuildMenu(menu, select);
    pick.insertBefore(btn, select);
    pick.insertBefore(menu, select);

    function syncTriggerTitle() {
      var opt = select.options[select.selectedIndex];
      btn.setAttribute(
        "title",
        opt ? title + " · " + opt.textContent : title
      );
    }

    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var willOpen = !menu.classList.contains("open");
      closeAllCardFilterMenus();
      if (willOpen) {
        rebuildMenu(menu, select);
        menu.classList.add("open");
        btn.setAttribute("aria-expanded", "true");
      }
    });

    select.addEventListener("change", syncTriggerTitle);
    syncTriggerTitle();

    try {
      new MutationObserver(function () {
        if (menu.classList.contains("open")) rebuildMenu(menu, select);
      }).observe(select, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["selected"],
      });
    } catch (e) {}
  }

  function initAll() {
    document.querySelectorAll(".card-filter-pick").forEach(initPick);
  }

  document.addEventListener("click", closeAllCardFilterMenus);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }

  window.DashCardFilter = {
    init: initAll,
    closeAll: closeAllCardFilterMenus,
  };
})();
