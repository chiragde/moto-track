(function () {
  const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const STAGGER = 0.055;
  const NAV_SETTLE_MS = 320;
  const filters = document.querySelectorAll(".timeline-filter");
  const main = document.querySelector(".timeline-animate");
  let entries = document.querySelectorAll(".timeline-entry");

  if (main) {
    document.body.classList.add("timeline-page");
  }

  function isEntryVisible(entry) {
    return entry.style.display !== "none";
  }

  function isMonthVisible(month) {
    return month.style.display !== "none";
  }

  function markEntryDone(entry) {
    const card = entry.querySelector(".timeline-card");
    if (!card) return;
    card.addEventListener(
      "animationend",
      function () {
        entry.classList.add("timeline-entry--done");
      },
      { once: true }
    );
  }

  function resetAnimations() {
    document.querySelectorAll(".timeline-month").forEach(function (month) {
      month.classList.remove("timeline-month--shown");
      month.style.removeProperty("--timeline-delay");
    });
    entries.forEach(function (entry) {
      entry.classList.remove("timeline-entry--shown", "timeline-entry--done");
      entry.style.removeProperty("--timeline-delay");
    });
  }

  function showAllImmediately() {
    document.querySelectorAll(".timeline-month").forEach(function (month) {
      if (!isMonthVisible(month)) return;
      month.classList.add("timeline-month--shown");
    });
    entries.forEach(function (entry) {
      if (!isEntryVisible(entry)) return;
      entry.classList.add("timeline-entry--shown", "timeline-entry--done");
    });
  }

  function runSequence() {
    let step = 0;

    document.querySelectorAll(".timeline-month").forEach(function (month) {
      if (!isMonthVisible(month)) return;

      const visibleEntries = Array.from(month.querySelectorAll(".timeline-entry")).filter(isEntryVisible);
      if (!visibleEntries.length) return;

      month.style.setProperty("--timeline-delay", step * STAGGER + "s");
      month.classList.add("timeline-month--shown");
      step += 1;

      visibleEntries.forEach(function (entry) {
        entry.style.setProperty("--timeline-delay", step * STAGGER + "s");
        entry.classList.add("timeline-entry--shown");
        markEntryDone(entry);
        step += 1;
      });
    });

    main.classList.add("timeline-ready");
  }

  function animateSequence(waitForNav) {
    if (!main) return;

    resetAnimations();

    if (REDUCED_MOTION) {
      showAllImmediately();
      main.classList.add("timeline-ready");
      return;
    }

    const start = function () {
      requestAnimationFrame(runSequence);
    };

    if (waitForNav) {
      window.setTimeout(start, NAV_SETTLE_MS);
    } else {
      requestAnimationFrame(function () {
        requestAnimationFrame(runSequence);
      });
    }
  }

  function applyFilter(kind) {
    entries.forEach(function (entry) {
      const show = kind === "all" || entry.dataset.timelineKind === kind;
      entry.style.display = show ? "" : "none";
    });

    document.querySelectorAll(".timeline-month").forEach(function (month) {
      const visible = Array.from(month.querySelectorAll(".timeline-entry")).some(isEntryVisible);
      month.style.display = visible ? "" : "none";
    });

    animateSequence(false);
  }

  if (filters.length) {
    filters.forEach(function (btn) {
      btn.addEventListener("click", function () {
        const kind = btn.dataset.filter;
        filters.forEach(function (f) {
          f.classList.toggle("active", f === btn);
        });
        applyFilter(kind);
      });
    });
  }

  function init() {
    entries = document.querySelectorAll(".timeline-entry");
    if (main && entries.length) {
      animateSequence(true);
    } else if (main) {
      main.classList.add("timeline-ready");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
