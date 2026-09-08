(function () {
  const catalogEl = document.getElementById("bike-catalog-data");
  const catalog = catalogEl ? JSON.parse(catalogEl.textContent) : {};

  const fab = document.getElementById("garage-fab");
  const backdrop = document.getElementById("garage-sheet-backdrop");
  const sheet = document.getElementById("garage-sheet");
  const makeSelect = document.getElementById("make");
  const modelSelect = document.getElementById("model");
  const customFields = document.getElementById("custom-make-fields");
  const photoInput = document.getElementById("garage-photo-input");
  const photoPreview = document.getElementById("garage-photo-preview");

  if (!fab || !sheet) return;

  function openSheet() {
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

  fab.addEventListener("click", function () {
    if (sheet.classList.contains("is-open")) {
      closeSheet();
    } else {
      openSheet();
    }
  });

  backdrop.addEventListener("click", closeSheet);

  function populateModels(make) {
    modelSelect.innerHTML = "";
    const models = catalog[make] || [];
    if (!models.length) {
      modelSelect.disabled = true;
      return;
    }
    models.forEach(function (model) {
      const opt = document.createElement("option");
      opt.value = model;
      opt.textContent = model;
      modelSelect.appendChild(opt);
    });
    modelSelect.disabled = false;
    customFields.hidden = make !== "Other";
  }

  makeSelect.addEventListener("change", function () {
    populateModels(makeSelect.value);
  });

  if (photoInput && photoPreview) {
    photoInput.addEventListener("change", function () {
      const file = photoInput.files && photoInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function (e) {
        photoPreview.innerHTML = '<img src="' + e.target.result + '" alt="Preview">';
        if (window.lucide) lucide.createIcons();
      };
      reader.readAsDataURL(file);
    });
  }
})();
