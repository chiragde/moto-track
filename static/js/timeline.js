(function () {
  const filters = document.querySelectorAll(".timeline-filter");
  const entries = document.querySelectorAll(".timeline-entry");
  if (!filters.length) return;

  function applyFilter(kind) {
    entries.forEach(function (entry) {
      const show = kind === "all" || entry.dataset.timelineKind === kind;
      entry.style.display = show ? "" : "none";
    });

    document.querySelectorAll(".timeline-month").forEach(function (month) {
      const visible = Array.from(month.querySelectorAll(".timeline-entry")).some(function (el) {
        return el.style.display !== "none";
      });
      month.style.display = visible ? "" : "none";
    });
  }

  filters.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const kind = btn.dataset.filter;
      filters.forEach(function (f) {
        f.classList.toggle("active", f === btn);
      });
      applyFilter(kind);
    });
  });
})();
