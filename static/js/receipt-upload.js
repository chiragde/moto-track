(function () {
  function setStatus(container, message, type) {
    const status = container.querySelector(".receipt-status");
    if (!message) {
      status.hidden = true;
      status.textContent = "";
      status.className = "receipt-status";
      return;
    }
    status.hidden = false;
    status.textContent = message;
    status.className = "receipt-status flash flash-" + (type || "success");
  }

  function setPreview(container, file) {
    const preview = container.querySelector(".receipt-preview");
    const image = container.querySelector(".receipt-preview-image");
    const clearBtn = container.querySelector(".receipt-clear-btn");

    if (!file) {
      preview.hidden = true;
      image.removeAttribute("src");
      clearBtn.hidden = true;
      return;
    }

    image.src = URL.createObjectURL(file);
    preview.hidden = false;
    clearBtn.hidden = false;
  }

  function fillField(form, name, value) {
    const field = form.querySelector('[name="' + name + '"]');
    if (!field || value === null || value === undefined || value === "") {
      return;
    }
    if (field.type === "radio") {
      const option = form.querySelector('[name="' + name + '"][value="' + value + '"]');
      if (option) {
        option.checked = true;
      }
      return;
    }
    field.value = value;
  }

  function clearReceipt(container) {
    const form = container.closest("form");
    const fileInput = container.querySelector(".receipt-file-input");
    const pathInput = container.querySelector(".receipt-path-input");
    fileInput.value = "";
    pathInput.value = "";
    setPreview(container, null);
    setStatus(container, "", "");
  }

  async function scanReceipt(container, file) {
    const form = container.closest("form");
    const entryType = container.dataset.entryType;
    const scanEnabled = container.dataset.scanEnabled === "true";
    const pathInput = container.querySelector(".receipt-path-input");
    const scanBtn = container.querySelector(".receipt-scan-btn");

    setPreview(container, file);
    scanBtn.disabled = true;
    setStatus(container, scanEnabled ? "Scanning receipt..." : "Attaching image...", "success");

    if (!scanEnabled) {
      pathInput.value = "";
      setStatus(
        container,
        "Image attached. Enter details manually, or set OPENAI_API_KEY for auto-fill.",
        "success"
      );
      scanBtn.disabled = false;
      return;
    }

    const body = new FormData();
    body.append("image", file);
    body.append("type", entryType);

    try {
      const response = await fetch("/api/parse-receipt", {
        method: "POST",
        body: body,
        credentials: "same-origin",
      });
      const payload = await response.json();
      if (!response.ok || !payload.ok) {
        throw new Error(payload.error || "Could not scan receipt.");
      }

      pathInput.value = payload.receipt_path || "";
      const data = payload.data || {};
      fillField(form, "entry_date", data.entry_date);
      fillField(form, "liters", data.liters);
      fillField(form, "cost", data.cost);
      fillField(form, "odometer", data.odometer);
      fillField(form, "notes", data.notes);
      fillField(form, "description", data.description);
      fillField(form, "entry_type", data.entry_type);

      setStatus(
        container,
        payload.message || "Receipt scanned. Review the fields before saving.",
        payload.manual_only ? "error" : "success"
      );
    } catch (error) {
      pathInput.value = "";
      setStatus(container, error.message, "error");
    } finally {
      scanBtn.disabled = false;
    }
  }

  document.querySelectorAll(".receipt-scanner").forEach((container) => {
    const fileInput = container.querySelector(".receipt-file-input");
    const scanBtn = container.querySelector(".receipt-scan-btn");
    const clearBtn = container.querySelector(".receipt-clear-btn");

    scanBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      if (!file) {
        return;
      }
      scanReceipt(container, file);
    });

    clearBtn.addEventListener("click", () => clearReceipt(container));
  });
})();
