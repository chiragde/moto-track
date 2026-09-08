(function () {
  const ITEM_H = 44;
  const MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];

  let overlay = null;
  let activeInput = null;
  let pickerState = { month: 0, day: 1, year: new Date().getFullYear() };

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  function daysInMonth(month, year) {
    return new Date(year, month + 1, 0).getDate();
  }

  function toISO(year, month, day) {
    return year + "-" + pad(month + 1) + "-" + pad(day);
  }

  function formatDisplay(year, month, day) {
    const d = new Date(year, month, day);
    return d.toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  function parseInputValue(value) {
    if (!value) {
      const now = new Date();
      return { year: now.getFullYear(), month: now.getMonth(), day: now.getDate() };
    }
    const parts = value.split("-");
    return {
      year: parseInt(parts[0], 10),
      month: parseInt(parts[1], 10) - 1,
      day: parseInt(parts[2], 10),
    };
  }

  function ensureOverlay() {
    if (overlay) return overlay;

    overlay = document.createElement("div");
    overlay.className = "ios-picker-overlay";
    overlay.innerHTML =
      '<div class="ios-picker-sheet" role="dialog" aria-label="Choose date">' +
      '  <div class="ios-picker-toolbar">' +
      '    <button type="button" class="ios-picker-cancel">Cancel</button>' +
      '    <span class="ios-picker-title">Date</span>' +
      '    <button type="button" class="ios-picker-done">Done</button>' +
      "  </div>" +
      '  <div class="ios-picker-wheels">' +
      '    <div class="ios-picker-highlight"></div>' +
      '    <div class="ios-picker-wheel month" data-wheel="month"></div>' +
      '    <div class="ios-picker-wheel day" data-wheel="day"></div>' +
      '    <div class="ios-picker-wheel year" data-wheel="year"></div>' +
      "  </div>" +
      "</div>";

    document.body.appendChild(overlay);

    overlay.querySelector(".ios-picker-cancel").addEventListener("click", closePicker);
    overlay.querySelector(".ios-picker-done").addEventListener("click", commitPicker);
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closePicker();
    });

    return overlay;
  }

  function buildWheel(wheelEl, items, selectedIndex) {
    wheelEl.innerHTML =
      '<div class="ios-picker-wheel-spacer"></div>' +
      items.map(function (label, i) {
        return (
          '<div class="ios-picker-item' +
          (i === selectedIndex ? " is-selected" : "") +
          '" data-index="' +
          i +
          '">' +
          label +
          "</div>"
        );
      }).join("") +
      '<div class="ios-picker-wheel-spacer"></div>';

    requestAnimationFrame(function () {
      wheelEl.scrollTop = selectedIndex * ITEM_H;
    });

    wheelEl.onscroll = function () {
      const index = Math.round(wheelEl.scrollTop / ITEM_H);
      wheelEl.querySelectorAll(".ios-picker-item").forEach(function (el, i) {
        el.classList.toggle("is-selected", i === index);
      });
    };
  }

  function getWheelIndex(wheelEl) {
    return Math.round(wheelEl.scrollTop / ITEM_H);
  }

  function populateWheels() {
    const o = ensureOverlay();
    const maxDay = daysInMonth(pickerState.month, pickerState.year);
    if (pickerState.day > maxDay) pickerState.day = maxDay;

    const monthWheel = o.querySelector('[data-wheel="month"]');
    const dayWheel = o.querySelector('[data-wheel="day"]');
    const yearWheel = o.querySelector('[data-wheel="year"]');

    const years = [];
    const thisYear = new Date().getFullYear();
    for (let y = thisYear - 10; y <= thisYear + 1; y++) years.push(String(y));

    buildWheel(monthWheel, MONTHS, pickerState.month);
    buildWheel(
      dayWheel,
      Array.from({ length: maxDay }, function (_, i) {
        return String(i + 1);
      }),
      pickerState.day - 1
    );
    buildWheel(yearWheel, years, years.indexOf(String(pickerState.year)));

    monthWheel.onscroll = function () {
      const m = getWheelIndex(monthWheel);
      if (m !== pickerState.month) {
        pickerState.month = m;
        const days = daysInMonth(pickerState.month, pickerState.year);
        if (pickerState.day > days) pickerState.day = days;
        buildWheel(
          dayWheel,
          Array.from({ length: days }, function (_, i) {
            return String(i + 1);
          }),
          pickerState.day - 1
        );
      }
      monthWheel.querySelectorAll(".ios-picker-item").forEach(function (el, i) {
        el.classList.toggle("is-selected", i === m);
      });
    };

    dayWheel.onscroll = function () {
      const d = getWheelIndex(dayWheel) + 1;
      pickerState.day = d;
      dayWheel.querySelectorAll(".ios-picker-item").forEach(function (el, i) {
        el.classList.toggle("is-selected", i === d - 1);
      });
    };

    yearWheel.onscroll = function () {
      const y = parseInt(years[getWheelIndex(yearWheel)], 10);
      pickerState.year = y;
      const days = daysInMonth(pickerState.month, pickerState.year);
      if (pickerState.day > days) pickerState.day = days;
      yearWheel.querySelectorAll(".ios-picker-item").forEach(function (el, i) {
        el.classList.toggle("is-selected", i === getWheelIndex(yearWheel));
      });
    };
  }

  function openPicker(input, displayBtn) {
    activeInput = input;
    pickerState = parseInputValue(input.value);
    populateWheels();
    const o = ensureOverlay();
    o.classList.add("is-open");
    document.body.style.overflow = "hidden";
    activeDisplayBtn = displayBtn;
  }

  let activeDisplayBtn = null;

  function closePicker() {
    if (overlay) overlay.classList.remove("is-open");
    document.body.style.overflow = "";
    activeInput = null;
    activeDisplayBtn = null;
  }

  function commitPicker() {
    if (!activeInput) return;
    const o = ensureOverlay();
    const monthWheel = o.querySelector('[data-wheel="month"]');
    const dayWheel = o.querySelector('[data-wheel="day"]');
    const yearWheel = o.querySelector('[data-wheel="year"]');

    pickerState.month = getWheelIndex(monthWheel);
    pickerState.day = getWheelIndex(dayWheel) + 1;
    const yearItems = yearWheel.querySelectorAll(".ios-picker-item");
    pickerState.year = parseInt(
      yearItems[getWheelIndex(yearWheel)].textContent,
      10
    );

    const iso = toISO(pickerState.year, pickerState.month, pickerState.day);
    activeInput.value = iso;
    activeInput.dispatchEvent(new Event("change", { bubbles: true }));

    if (activeDisplayBtn) {
      activeDisplayBtn.textContent = formatDisplay(
        pickerState.year,
        pickerState.month,
        pickerState.day
      );
    }

    closePicker();
  }

  function wrapDateInput(input) {
    if (input.dataset.iosDateReady) return;
    input.dataset.iosDateReady = "1";

    const field = document.createElement("div");
    field.className = "ios-date-field";
    input.parentNode.insertBefore(field, input);
    field.appendChild(input);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ios-date-display";
    const parsed = parseInputValue(input.value);
    btn.textContent = formatDisplay(parsed.year, parsed.month, parsed.day);
    field.appendChild(btn);

    btn.addEventListener("click", function () {
      openPicker(input, btn);
    });

    input.addEventListener("change", function () {
      const p = parseInputValue(input.value);
      btn.textContent = formatDisplay(p.year, p.month, p.day);
    });
  }

  function init() {
    document.querySelectorAll("input.ios-date-input, input[type='date']").forEach(wrapDateInput);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.initIOSDatePickers = init;
})();
