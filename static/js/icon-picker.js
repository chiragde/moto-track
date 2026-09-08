function initIconPicker(containerSelector, hiddenInputId) {
  const container = document.querySelector(containerSelector);
  const hidden = document.getElementById(hiddenInputId);
  if (!container || !hidden) return;

  container.querySelectorAll(".icon-picker-option").forEach(function (btn) {
    btn.addEventListener("click", function () {
      container.querySelectorAll(".icon-picker-option").forEach(function (el) {
        el.classList.remove("active");
        el.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      hidden.value = btn.dataset.value;
    });
  });
}

function initIconSelect(selectId, displayId) {
  const select = document.getElementById(selectId);
  const display = document.getElementById(displayId);
  if (!select || !display) return;

  function update() {
    const opt = select.options[select.selectedIndex];
    const icon = opt.dataset.icon || "wrench";
    const label = opt.textContent;
    display.innerHTML =
      '<i data-lucide="' + icon + '"></i><span>' + label + "</span>";
    if (window.lucide) lucide.createIcons();
  }

  select.addEventListener("change", update);
  update();
}
