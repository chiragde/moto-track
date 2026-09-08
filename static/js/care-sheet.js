(function () {
  const fab = document.getElementById("care-fab");
  const emptyAdd = document.getElementById("care-empty-add");
  const backdrop = document.getElementById("care-sheet-backdrop");
  const sheet = document.getElementById("care-sheet");
  const segments = document.querySelectorAll("[data-care-panel]");
  const panels = {
    log: document.getElementById("care-panel-log"),
    reminder: document.getElementById("care-panel-reminder"),
  };

  if (!fab || !sheet) return;

  function openSheet(panel) {
    if (panel && panels[panel]) {
      showPanel(panel);
    }
    fab.classList.add("is-open");
    fab.setAttribute("aria-expanded", "true");
    backdrop.hidden = false;
    sheet.setAttribute("aria-hidden", "false");
    requestAnimationFrame(function () {
      backdrop.classList.add("is-open");
      sheet.classList.add("is-open");
    });
  }

  function closeSheet() {
    fab.classList.remove("is-open");
    fab.setAttribute("aria-expanded", "false");
    backdrop.classList.remove("is-open");
    sheet.classList.remove("is-open");
    sheet.setAttribute("aria-hidden", "true");
    setTimeout(function () {
      backdrop.hidden = true;
    }, 350);
  }

  function showPanel(name) {
    segments.forEach(function (btn) {
      const active = btn.getAttribute("data-care-panel") === name;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    Object.keys(panels).forEach(function (key) {
      if (panels[key]) panels[key].hidden = key !== name;
    });
  }

  fab.addEventListener("click", function () {
    if (sheet.classList.contains("is-open")) {
      closeSheet();
    } else {
      openSheet("log");
    }
  });

  if (emptyAdd) {
    emptyAdd.addEventListener("click", function () {
      openSheet("log");
    });
  }

  backdrop.addEventListener("click", closeSheet);

  segments.forEach(function (btn) {
    btn.addEventListener("click", function () {
      showPanel(btn.getAttribute("data-care-panel"));
    });
  });
})();
