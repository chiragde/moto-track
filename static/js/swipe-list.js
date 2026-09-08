(function () {
  const OPEN_CLASS = "is-open";
  const THRESHOLD = 40;
  let openRow = null;

  function closeOpenRow() {
    if (openRow) {
      openRow.classList.remove(OPEN_CLASS);
      openRow = null;
    }
  }

  function bindRow(row) {
    const content = row.querySelector(".swipe-row-content");
    if (!content) return;

    let startX = 0;
    let currentX = 0;
    let dragging = false;

    function setOffset(px) {
      const max = -144;
      const clamped = Math.max(max, Math.min(0, px));
      content.style.transform = "translateX(" + clamped + "px)";
      currentX = clamped;
    }

    function snapOpen(open) {
      content.style.transform = "";
      row.classList.toggle(OPEN_CLASS, open);
      if (open) {
        closeOpenRow();
        openRow = row;
      } else if (openRow === row) {
        openRow = null;
      }
    }

    content.addEventListener("touchstart", function (e) {
      if (e.target.closest("a, button")) return;
      startX = e.touches[0].clientX;
      dragging = true;
      if (openRow && openRow !== row) closeOpenRow();
    }, { passive: true });

    content.addEventListener("touchmove", function (e) {
      if (!dragging) return;
      const dx = e.touches[0].clientX - startX;
      const base = row.classList.contains(OPEN_CLASS) ? -144 : 0;
      if (Math.abs(dx) > 4) row.classList.add("is-dragging");
      setOffset(base + dx);
      if (Math.abs(dx) > 10) e.preventDefault();
    }, { passive: false });

    content.addEventListener("touchend", function () {
      if (!dragging) return;
      dragging = false;
      row.classList.remove("is-dragging");
      content.style.transform = "";
      if (currentX < -THRESHOLD || (row.classList.contains(OPEN_CLASS) && currentX < -72)) {
        snapOpen(true);
      } else {
        snapOpen(false);
      }
    });

    content.addEventListener("mousedown", function (e) {
      if (e.target.closest("a, button")) return;
      startX = e.clientX;
      dragging = true;
      if (openRow && openRow !== row) closeOpenRow();
      e.preventDefault();
    });

    document.addEventListener("mousemove", function (e) {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const base = row.classList.contains(OPEN_CLASS) ? -144 : 0;
      if (Math.abs(dx) > 4) row.classList.add("is-dragging");
      setOffset(base + dx);
    });

    document.addEventListener("mouseup", function () {
      if (!dragging) return;
      dragging = false;
      row.classList.remove("is-dragging");
      content.style.transform = "";
      if (currentX < -THRESHOLD || (row.classList.contains(OPEN_CLASS) && currentX < -72)) {
        snapOpen(true);
      } else {
        snapOpen(false);
      }
    });
  }

  function init() {
    document.querySelectorAll("[data-swipe-row]").forEach(bindRow);

    document.addEventListener("click", function (e) {
      if (!e.target.closest("[data-swipe-row]")) {
        closeOpenRow();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
